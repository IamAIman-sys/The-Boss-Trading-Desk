"""All fixtures are made up. Real HTTP is blocked for this entire test module."""
from argparse import Namespace
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import core
import edgar
import seeker


def setUpModule():
    global NETWORK_BLOCK
    NETWORK_BLOCK = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden in seeker tests'))
    NETWORK_BLOCK.start()


def tearDownModule():
    NETWORK_BLOCK.stop()


CIK = '0000000001'
PARENT = '0000000002'
ACC = '0000000001-25-000001'
FILING = {'cik': CIK, 'form': '10-12B', 'filed': '2025-02-01', 'accession': ACC}
TEXT = '''INFORMATION STATEMENT
THE SEPARATION AND DISTRIBUTION
Parent: Parent One | Parent CIK: 0000000002
The Parent will distribute our common shares to its stockholders in a spin-off.
Record date: February 20, 2025
Distribution date: March 1, 2025
Distribution ratio: one for five
Trading symbol: TEST
Synthetic measure: 12 million
'''


def doc(text=TEXT, filed='2025-02-01', form='10-12B', parent=False):
    return {'text': text, 'filed': filed, 'form': form, 'filing': 'https://www.sec.gov/test-index.html',
            'url': 'https://www.sec.gov/test.htm', 'parent_document': parent}


def record(text=TEXT, documents=None, filings=None):
    return core.build_record(CIK, 'Issuer One', documents or [doc(text)], filings if filings is not None else [
        {**FILING, 'form': '10-Q', 'filed': '2025-03-10'}], ['filing:Synthetic measure'], domestic=True)


def config():
    # Arbitrary test-only settings, not the student's factor selections.
    return {'window_days': 30, 'factors': [
        {'name': 'Synthetic A', 'metric': 'distribution_ratio', 'direction': 'higher', 'chapter': 'Made-up test chapter', 'weight': 2},
        {'name': 'Synthetic B', 'metric': 'days_since_distribution', 'direction': 'lower', 'chapter': 'Made-up test chapter', 'weight': 1}]}


def quote(stamp='2025-03-03', close='20', **extra):
    return {'date': stamp, 'close': close, 'currency': 'USD', 'session': 'regular',
            'kind': 'official_close', 'source': 'synthetic fixture', **extra}


def series(rows=None):
    return {'status': 'ok', 'ticker': 'TEST', 'start_date': '2025-03-02', 'end_date': '2025-03-20',
            'complete': True, 'closes': rows if rows is not None else [quote(), quote('2025-03-20', '18')]}


class FactorsTests(unittest.TestCase):
    def validate(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'factors.json'
            path.write_text(json.dumps(data))
            return core.load_factors(path)

    def test_blank_shipped_template_is_rejected_before_network_or_reader(self):
        with patch.object(seeker, 'SECClient') as client, patch.object(seeker, 'load_reader') as reader, redirect_stderr(StringIO()) as error:
            result = seeker.main(['--start-date', '2025-01-01'])
        self.assertEqual(result, 1)
        self.assertIn('empty or incomplete', error.getvalue())
        client.assert_not_called()
        reader.assert_not_called()
        template = json.loads((SCRIPTS.parent / 'factors.json').read_text())
        self.assertIsNone(template['window_days'])
        self.assertTrue(all(v in ('', None) for v in template['factors'][0].values()))

    def test_all_student_fields_required(self):
        for field in ('name', 'metric', 'direction', 'chapter', 'weight'):
            data = config()
            data['factors'][0][field] = None
            with self.subTest(field=field), self.assertRaises(core.SeekerError):
                self.validate(data)

    def test_window_direction_weights_and_duplicates(self):
        for window in (None, 0, -1, True, 1.5):
            with self.subTest(window=window), self.assertRaises(core.SeekerError):
                self.validate({**config(), 'window_days': window})
        for weight in (-1, 'NaN', 'Infinity'):
            data = config()
            data['factors'][0]['weight'] = weight
            with self.assertRaises(core.SeekerError):
                self.validate(data)
        data = config()
        data['factors'][1]['name'] = data['factors'][0]['name']
        with self.assertRaises(core.SeekerError):
            self.validate(data)
        data = config()
        data['factors'][0]['direction'] = 'guess'
        with self.assertRaises(core.SeekerError):
            self.validate(data)

    def test_zero_weight_allowed_but_not_all_zero(self):
        data = config()
        data['factors'][0]['weight'] = 0
        self.validate(data)
        data['factors'][1]['weight'] = 0
        with self.assertRaises(core.SeekerError):
            self.validate(data)

    def test_unknown_metrics_not_silently_invented(self):
        data = config()
        data['factors'][0]['metric'] = 'unimplemented hypothesis'
        with self.assertRaises(core.SeekerError):
            self.validate(data)


class ExtractionTests(unittest.TestCase):
    def test_facts_have_filing_section_and_exact_quote(self):
        item = record()
        self.assertEqual(core.value(item, 'parent'), 'Parent One')
        self.assertEqual(core.value(item, 'parent_cik'), PARENT)
        self.assertEqual(core.value(item, 'record_date'), '2025-02-20')
        self.assertEqual(core.value(item, 'distribution_date'), '2025-03-01')
        self.assertEqual(core.value(item, 'distribution_ratio'), {'numerator': '1', 'denominator': '5'})
        for field in core.CORE_FACTS:
            source = item['facts'][field]['source']
            self.assertEqual(TEXT.splitlines()[source['line'] - 1], source['quote'])
            self.assertTrue(source['section'])
            self.assertTrue(source['filing'])
        self.assertEqual(item['observations']['filing:Synthetic measure']['value'], '12000000')

    def test_unfound_fact_and_unreadable_values_stay_blank(self):
        item = record(TEXT.replace('Distribution date: March 1, 2025', 'Distribution date: [to be determined]'))
        self.assertIsNone(item['facts']['distribution_date'])
        self.assertEqual(core.classify(item, date(2025, 3, 20), date(2025, 1, 1), 30)['category'], 'unranked')

    def test_conditional_dates_are_not_established(self):
        for phrase in ('Expected distribution date: March 1, 2025', 'Distribution date: March 1, 2025, subject to approval'):
            item = record(TEXT.replace('Distribution date: March 1, 2025', phrase))
            self.assertIsNone(core.value(item, 'distribution_date'))

    def test_ambiguous_multiple_dates_not_confused(self):
        text = TEXT.replace('Distribution date: March 1, 2025',
            'On February 20, 2025 holders were recorded; on March 1, 2025 the parent distributed common shares to shareholders in the spin-off.')
        self.assertIsNone(core.value(record(text), 'distribution_date'))

    def test_invalid_calendar_date_is_blank(self):
        item = record(TEXT.replace('March 1, 2025', 'February 30, 2025'))
        self.assertIsNone(core.value(item, 'distribution_date'))

    def test_same_date_conflict_blank_later_amendment_supersedes(self):
        original = doc()
        conflict = doc(TEXT.replace('March 1, 2025', 'March 2, 2025'))
        item = record(documents=[original, conflict])
        self.assertIsNone(core.value(item, 'distribution_date'))
        self.assertTrue(any('Conflicting distribution_date' in x for x in item['issues']))
        conflict['filed'], conflict['form'] = '2025-02-02', '10-12B/A'
        self.assertEqual(core.value(record(documents=[original, conflict]), 'distribution_date'), '2025-03-02')

    def test_fund_shell_and_existing_shares_drop_with_source(self):
        for line in ('We are a registered investment fund.', 'The registrant is a shell company.',
                     'Registration of existing outstanding shares.'):
            item = record('INFORMATION STATEMENT\n' + line)
            status = core.classify(item, date(2025, 3, 20), date(2025, 1, 1), 30)
            self.assertEqual(status['category'], 'dropped')
            self.assertEqual(item['rejections'][0]['source']['quote'], line)

    def test_form10_without_information_statement_drops(self):
        item = record('FORM 10\nRegistration materials only.')
        self.assertEqual(item['rejections'][0]['reason'], 'Form 10 has no readable information statement')

    def test_partial_document_failure_does_not_claim_no_information_statement(self):
        item = core.build_record(CIK, 'Issuer One', [doc('FORM 10')], [], issues=['Unreadable PDF: fixture'], domestic=True)
        self.assertEqual(item['rejections'], [])

    def test_later_parent_distribution_rescues_prior_nonspin(self):
        old = doc('INFORMATION STATEMENT\nWe are a shell company.')
        item = record(documents=[old, doc(TEXT, '2025-03-02', '8-K')])
        self.assertFalse(item['rejections'])
        item = record(documents=[doc(TEXT), doc('We are a shell company.', '2025-03-02', '8-K')])
        self.assertTrue(item['rejections'])

    def test_same_date_conflicting_nonspin_evidence_is_not_assumed_later(self):
        item = record(documents=[doc('INFORMATION STATEMENT\nWe are a shell company.'), doc(TEXT)])
        self.assertTrue(item['rejections'])

    def test_cancelled_spin_requires_later_positive_evidence(self):
        item = record(documents=[doc(), doc('We terminated the planned spin-off.', '2025-03-02', '8-K')])
        self.assertEqual(item['rejections'][0]['reason'], 'Distribution plan cancelled')

    def test_dividend_alone_does_not_prove_spinoff(self):
        item = record('INFORMATION STATEMENT\nWe distributed common shares to stockholders as a dividend.')
        self.assertFalse(item['spinoff_evidence'])

    def test_negated_distribution_not_proof(self):
        item = record('INFORMATION STATEMENT\nWe will not distribute common shares to shareholders in a spin-off.')
        self.assertFalse(item['spinoff_evidence'])

    def test_parent_link_cik_exact_match_only(self):
        text = TEXT.replace(' | Parent CIK: 0000000002', '')
        document = doc(text)
        document['links'] = [{'text': 'Parent One', 'href': 'https://www.sec.gov/Archives/edgar/data/2/'}]
        self.assertEqual(core.value(record(documents=[document]), 'parent_cik'), PARENT)
        document['links'][0]['text'] = 'Some Other Parent'
        self.assertIsNone(core.value(record(documents=[document]), 'parent_cik'))

    def test_parent_document_must_name_the_child(self):
        parent = doc('On March 1, 2025 the parent distributed Issuer One common shares to its stockholders in a spin-off.',
                     '2025-03-02', '8-K', True)
        found = core.extract(parent, 'Issuer One')
        self.assertTrue(found['proof'])
        self.assertTrue(core.extract(parent, 'Issuer One', parent_document=True)['facts'])
        self.assertFalse(core.extract(parent, 'Different Issuer', parent_document=True)['facts'])

    def test_numeric_label_parser_wont_guess_table_units_or_columns(self):
        text = TEXT.replace('Synthetic measure: 12 million', 'Synthetic measure | 12 | 15')
        self.assertNotIn('filing:Synthetic measure', record(text)['observations'])


class StageTests(unittest.TestCase):
    def status(self, item, as_of='2025-03-20', start='2025-01-01'):
        return core.classify(item, core.day(as_of), core.day(start), 30)

    def test_registered_cert_trading_window_past(self):
        item = record(filings=[])
        self.assertEqual(self.status(item)['stage'], 'registered')
        item['filings'] = [{**FILING, 'form': 'CERT'}]
        self.assertEqual(self.status(item)['stage'], 'listing approved')
        item = record()
        self.assertEqual(self.status(item)['stage'], 'in its window')
        self.assertEqual(self.status(item, '2025-04-01')['stage'], 'past it')
        item['facts']['distribution_date'] = None
        self.assertEqual(self.status(item)['stage'], 'trading')

    def test_parent_filings_and_pre_distribution_child_filings_do_not_prove_trading(self):
        for filing in ({**FILING, 'cik': PARENT, 'form': '4', 'filed': '2025-03-05'},
                       {**FILING, 'form': '10-Q', 'filed': '2025-02-15'}):
            item = record(filings=[filing])
            self.assertEqual(self.status(item)['category'], 'watch')

    def test_form4_in_child_list_proves_trading(self):
        item = record(filings=[{**FILING, 'form': '4', 'filed': '2025-03-03'}])
        self.assertEqual(self.status(item)['stage'], 'in its window')

    def test_window_and_start_boundaries_inclusive(self):
        self.assertEqual(self.status(record(), '2025-03-31', '2025-03-01')['category'], 'window')
        self.assertEqual(self.status(record(), start='2025-03-02')['category'], 'outside')

    def test_future_distribution_and_missing_record_date_not_ranked(self):
        self.assertEqual(self.status(record(), '2025-02-25')['category'], 'watch')
        item = record()
        item['facts']['record_date'] = None
        self.assertEqual(self.status(item)['category'], 'unranked')

    def test_unknown_or_foreign_domicile_not_ranked(self):
        for domestic in (None, False):
            item = record()
            item['domestic'] = domestic
            self.assertEqual(self.status(item)['category'], 'unranked')
        self.assertTrue(edgar.domestic_status({'stateOfIncorporation': 'DE'}))
        self.assertFalse(edgar.domestic_status({'stateOfIncorporation': 'Z9'}))
        self.assertIsNone(edgar.domestic_status({}))


class PriceTests(unittest.TestCase):
    def select(self, payload):
        return core.choose_prices(payload, 'TEST', date(2025, 3, 1), date(2025, 3, 20))

    def test_first_close_strictly_after_distribution_sorted(self):
        payload = series([quote('2025-03-20', '18'), quote('2025-02-28', '22', session='when_issued'),
                          quote('2025-03-01', '21'), quote('2025-03-03', '20')])
        prices = self.select(payload)
        self.assertEqual(prices['first']['date'], '2025-03-03')
        self.assertEqual(prices['latest']['date'], '2025-03-20')
        values = core.measurements(record(), prices, date(2025, 3, 20))
        self.assertEqual(Decimal(values['return_since_first_close_pct']['value']), -10)

    def test_when_issued_adjusted_or_unknown_session_after_distribution_refused(self):
        for changed in ({'session': 'when_issued'}, {'kind': 'adjusted_close'}, {'session': None}, {'currency': 'EUR'}):
            self.assertIn('reason', self.select(series([quote(**changed), quote('2025-03-04')])))

    def test_incomplete_or_short_coverage_cannot_claim_first_close(self):
        for changed in ({'complete': False}, {'start_date': '2025-03-04'}, {'end_date': '2025-03-19'}, {'ticker': 'OTHER'}):
            self.assertIn('reason', self.select({**series(), **changed}))

    def test_invalid_and_conflicting_prices_not_used(self):
        for rows in ([quote(close='NaN')], [quote(close='0')], [quote(), quote(close='21')], [quote(source='')]):
            self.assertIn('reason', self.select(series(rows)))

    def test_missing_reader_and_reader_failure_finish_without_prices(self):
        item = record()
        self.assertIn('No closes reader', seeker.prices_for(item, None, date(2025, 3, 20))['reason'])
        reader = Mock(side_effect=RuntimeError('secret must not reach report'))
        result = seeker.prices_for(item, reader, date(2025, 3, 20))
        self.assertNotIn('secret', json.dumps(result))
        self.assertIn('reason', result)
        for payload in (None, 'not available', {'status': 'not available'}, series([])):
            self.assertIn('reason', self.select(payload))


class RankingTests(unittest.TestCase):
    def rows(self):
        return [{'cik': str(i), 'measurements': {
            'distribution_ratio': {'value': str(i)}, 'days_since_distribution': {'value': str(i * 10)}}}
            for i in (1, 2, 3)]

    def test_directions_weights_arithmetic_and_ties(self):
        rows = self.rows()
        ranked = core.rank(rows, config()['factors'])
        self.assertEqual([r['cik'] for r in ranked], ['3', '2', '1'])
        self.assertEqual(Decimal(rows[1]['points']['Synthetic A']['points']), 1)
        self.assertEqual(Decimal(rows[1]['points']['Synthetic B']['points']), Decimal('.5'))
        rows[0]['measurements']['distribution_ratio']['value'] = '2'
        core.rank(rows, config()['factors'])
        self.assertEqual(rows[0]['points']['Synthetic A']['points'], rows[1]['points']['Synthetic A']['points'])

    def test_zero_weight_changes_no_other_factor_points_even_missing_inputs(self):
        rows = self.rows()
        del rows[0]['measurements']['distribution_ratio']
        core.rank(rows, config()['factors'])
        before = [r['points']['Synthetic B'] for r in rows]
        self.assertIsNone(rows[0]['total_points'])
        changed = config()['factors']
        changed[0]['weight'] = 0
        core.rank(rows, changed)
        self.assertEqual(before, [r['points']['Synthetic B'] for r in rows])
        self.assertTrue(all('Synthetic A' not in r['points'] for r in rows))
        self.assertIsNotNone(rows[0]['total_points'])

    def test_one_item_and_missing_active_input(self):
        rows = self.rows()[:1]
        core.rank(rows, config()['factors'])
        self.assertEqual(Decimal(rows[0]['total_points']), Decimal('1.5'))
        del rows[0]['measurements']['distribution_ratio']
        self.assertEqual(core.rank(rows, config()['factors']), [])
        self.assertIn('Synthetic A', rows[0]['missing_factors'])


class NetworkAndIndexTests(unittest.TestCase):
    def test_all_request_starts_rate_limited_and_identified_even_retry_redirect(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env'
            env.write_text('SEC_USER_AGENT=Unit Test unit@example.test\n')
            session, sleep = Mock(), Mock()
            session.get.side_effect = [Mock(status_code=302, headers={'Location': 'https://data.sec.gov/next'}),
                                      Mock(status_code=429, headers={'Retry-After': '1'}),
                                      Mock(status_code=200, content=b'{}')]
            client = edgar.SECClient(env, Path(tmp) / 'cache', session=session, sleep=sleep, clock=lambda: 0)
            self.assertEqual(client.get('https://www.sec.gov/test', immutable=True), b'{}')
            self.assertEqual(session.get.call_count, 3)
            for call in session.get.call_args_list:
                self.assertEqual(call.kwargs['headers']['User-Agent'], 'Unit Test unit@example.test')
                self.assertFalse(call.kwargs['allow_redirects'])
            self.assertGreaterEqual(sum(c.args == (.26,) for c in sleep.call_args_list), 2)
            client.get('https://www.sec.gov/test', immutable=True)
            self.assertEqual(session.get.call_count, 3)

    def test_external_redirect_blocked_before_key_header_sent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env'
            env.write_text('SEC_USER_AGENT=Unit Test unit@example.test\n')
            session = Mock()
            session.get.return_value = Mock(status_code=302, headers={'Location': 'https://other.invalid/'})
            client = edgar.SECClient(env, Path(tmp) / 'cache', session=session)
            with self.assertRaises(core.SeekerError):
                client.get('https://www.sec.gov/test')
            session.get.assert_called_once()

    def test_fixed_width_index_and_form_amendments(self):
        text = 'Form Type Company Name CIK Date Filed File Name\n'
        for i, form in enumerate(('10-12B', '10-12B/A', '10-12G', 'CERT', '8-K'), 1):
            text += f'{form:<12}Synthetic Issuer {i:<20} {i:>10} 2025-01-15 edgar/data/{i}/0000000001-25-{i:06d}.txt\n'
        rows = edgar.parse_index(text, 'fixture')
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[1]['form'], '10-12B/A')
        self.assertEqual(rows[0]['cik'], CIK)
        with self.assertRaises(core.SeekerError):
            edgar.parse_index('<html>Access denied</html>', 'fixture')

    def test_unparsed_index_row_cannot_silently_disappear(self):
        with self.assertRaises(core.SeekerError):
            edgar.parse_index('Form Type\n10-12B damaged row edgar/data/1/unknown.txt', 'fixture')

    def test_plain_text_preserves_sentences_and_table_rows(self):
        text, links = edgar.plain_text(b'<h1>INFORMATION STATEMENT</h1><p>Parent will distribute <b>shares</b> to holders.</p><table><tr><td>Record date</td><td>2025-02-20</td></tr></table>', 'https://www.sec.gov/test.htm')
        self.assertIn('Parent will distribute shares to holders.', text.splitlines())
        self.assertIn('Record date | 2025-02-20', text)

    def test_older_submissions_pages_and_cutoff_are_read(self):
        def cols(form, filed, accession):
            return {'form': [form], 'filingDate': [filed], 'accessionNumber': [accession], 'primaryDocument': ['doc.htm']}
        client = Mock()
        client.json.side_effect = [
            {'filings': {'recent': cols('10-Q', '2025-03-01', ACC), 'files': [
                {'name': 'CIK0000000001-submissions-001.json', 'filingFrom': '2024-01-01'}]}},
            cols('10-12B', '2024-01-01', '0000000001-24-000001')]
        _, filings = edgar.submissions(client, CIK, date(2025, 2, 1))
        self.assertEqual([f['form'] for f in filings], ['10-12B'])
        self.assertEqual(client.json.call_count, 2)


class ReportTests(unittest.TestCase):
    def test_report_dates_sections_citations_and_last_line(self):
        rows, ranked = seeker.screen([record()], config(), date(2025, 1, 1), date(2025, 3, 20), lambda *args: series())
        report = seeker.render(rows, ranked, config(), '2025-03-21T12:00:00Z',
            [{'url': 'https://www.sec.gov/fixture', 'through': '2025-03-20'}],
            date(2025, 1, 1), date(2024, 1, 1), date(2025, 3, 20), [])
        first = report.splitlines()[0]
        for label in ('Run date:', 'Price date(s):', 'Index date:'):
            self.assertIn(label, first)
        self.assertIn('20 USD on 2025-03-03', report)
        self.assertIn('18 USD on 2025-03-20', report)
        self.assertIn('Factor points:', report)
        self.assertIn('Watch list:', report)
        self.assertIn('Dropped and why', report)
        self.assertIn('What the data cannot show', report)
        self.assertIn('section THE SEPARATION AND DISTRIBUTION', report)
        self.assertEqual(report.strip().splitlines()[-1], 'screens, not recommendations')

    def test_missing_dates_unranked_with_reason_and_null_registry(self):
        item = record()
        item['facts']['distribution_date'] = None
        rows, ranked = seeker.screen([item], config(), date(2025, 1, 1), date(2025, 3, 20))
        self.assertFalse(ranked)
        self.assertIn('Distribution date is missing', ' '.join(rows[0]['status']['reasons']))
        self.assertIsNone(rows[0]['facts']['distribution_date'])

    def test_no_price_inputs_are_invented(self):
        data = config()
        data['factors'][0]['metric'] = 'first_close'
        rows, ranked = seeker.screen([record()], data, date(2025, 1, 1), date(2025, 3, 20))
        self.assertFalse(ranked)
        self.assertIn('Synthetic A', rows[0]['missing_factors'])


class FakeSEC:
    """Full-index -> submissions -> exhibit -> parent 8-K, entirely in memory."""
    def __init__(self):
        self.urls = []
        self.responses = {}
        self.parent_accession = '0000000002-25-000001'
        registration = {**FILING, 'filed': '2024-12-01', 'accession': '0000000001-24-000001'}
        fund = {'cik': '0000000003', 'form': '10-12G', 'filed': '2025-02-01', 'accession': '0000000003-25-000001'}
        parent = {'cik': PARENT, 'form': '8-K', 'filed': '2025-03-20', 'accession': self.parent_accession}
        def index_line(filing, name):
            return f"{filing['form']:<12}{name:<30} {int(filing['cik']):>10} {filing['filed']} edgar/data/{int(filing['cik'])}/{filing['accession']}.txt\n"
        header = 'Form Type Company Name CIK Date Filed File Name\n'
        self.responses['https://www.sec.gov/Archives/edgar/full-index/2024/QTR4/form.idx'] = (header + index_line(registration, 'Issuer One')).encode()
        self.responses['https://www.sec.gov/Archives/edgar/full-index/2025/QTR1/form.idx'] = (header + index_line(fund, 'Issuer Three')).encode()
        directory = 'https://www.sec.gov/Archives/edgar/daily-index/2025/QTR1/'
        self.responses[directory + 'index.json'] = {'directory': {'item': [{'name': 'form.20250320.idx'}]}}
        self.responses[directory + 'form.20250320.idx'] = (header + index_line(parent, 'Parent One')).encode()
        def columns(filings):
            return {target: [f.get(source, '') for f in filings] for target, source in
                    (('form', 'form'), ('filingDate', 'filed'), ('accessionNumber', 'accession'), ('primaryDocument', 'primary_document'))}
        trading = {**FILING, 'form': '10-Q', 'filed': '2025-03-10'}
        self.responses[f'https://data.sec.gov/submissions/CIK{CIK}.json'] = {
            'name': 'Issuer One', 'stateOfIncorporation': 'DE', 'filings': {'recent': columns([registration, trading])}}
        self.responses['https://data.sec.gov/submissions/CIK0000000003.json'] = {
            'name': 'Issuer Three', 'stateOfIncorporation': 'DE', 'filings': {'recent': columns([fund])}}
        # Parent's daily-index filing is newer than its API response.
        self.responses[f'https://data.sec.gov/submissions/CIK{PARENT}.json'] = {'name': 'Parent One', 'filings': {'recent': columns([])}}
        def filing_pages(filing, documents):
            base = edgar.base_url(filing)
            table = '<table summary="Document Format Files"><tr><th>Document</th></tr>'
            for i, (kind, text) in enumerate(documents):
                table += f'<tr><td>{i}</td><td>Fixture</td><td><a href="{base}doc{i}.htm">doc{i}.htm</a></td><td>{kind}</td></tr>'
                self.responses[base + f'doc{i}.htm'] = text.encode()
            table += '</table>'
            self.responses[base + filing['accession'] + '-index.html'] = table.encode()
        text = TEXT.replace('Distribution date: March 1, 2025\n', '')
        html = ''.join('<p>' + line + '</p>' for line in text.splitlines())
        filing_pages(registration, [('10-12B', '<p>FORM 10 REGISTRATION</p>'), ('EX-99.1', html)])
        filing_pages(fund, [('10-12G', '<p>INFORMATION STATEMENT</p><p>We are an investment fund.</p>')])
        filing_pages(parent, [('8-K', '<p>On March 1, 2025 Parent One distributed Issuer One common shares to its stockholders in the spin-off.</p>')])

    def get(self, url, **kwargs):
        self.urls.append(url)
        result = self.responses[url]
        assert isinstance(result, bytes)
        return result

    def json(self, url, **kwargs):
        self.urls.append(url)
        return deepcopy(self.responses[url])


class PipelineTests(unittest.TestCase):
    def test_old_registration_daily_parent_filing_exhibit_registry_report_and_new_run(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            args = Namespace(start_date='2025-01-01', as_of='2025-03-20', index_start='2024-10-01', output=Path(tmp))
            client = FakeSEC()
            code = seeker.run(args, client, lambda *args: series(), config())
            self.assertEqual(code, 0)
            registry = json.loads((Path(tmp) / 'registry.json').read_text())
            issuer = registry['companies'][CIK]
            self.assertEqual(core.value(issuer, 'distribution_date'), '2025-03-01')
            self.assertEqual(core.value(issuer, 'parent_cik'), PARENT)
            self.assertTrue(any(client.parent_accession in url for url in client.urls))
            self.assertTrue(any('doc1.htm' in url for url in client.urls))
            folders = [p for p in Path(tmp).iterdir() if p.is_dir()]
            self.assertEqual(len(folders), 1)
            first = folders[0] / 'report.md'
            first_bytes = first.read_bytes()
            screen = json.loads((folders[0] / 'screen.json').read_text())
            main = next(r for r in screen['rows'] if r['cik'] == CIK)
            self.assertEqual(main['rank'], 1)
            self.assertEqual(main['prices']['first']['date'], '2025-03-03')
            self.assertEqual(next(r for r in screen['rows'] if r['cik'] == '0000000003')['status']['category'], 'dropped')
            self.assertEqual(seeker.run(args, FakeSEC(), None, config()), 0)
            self.assertEqual(len([p for p in Path(tmp).iterdir() if p.is_dir()]), 2)
            self.assertEqual(first.read_bytes(), first_bytes)

    def test_failed_company_keeps_stale_registry_but_does_not_rank_it(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            args = Namespace(start_date='2025-01-01', as_of='2025-03-20', index_start='2024-10-01', output=Path(tmp))
            seeker.save(Path(tmp) / 'registry.json', {'companies': {CIK: record()}})
            with patch.object(seeker, 'discover', return_value=([], [])), \
                 patch.object(seeker, 'collect_company', side_effect=core.SeekerError('SEC HTTP 503: fixture')):
                self.assertEqual(seeker.run(args, Mock(), None, config()), 2)
            registry = json.loads((Path(tmp) / 'registry.json').read_text())
            self.assertTrue(registry['companies'][CIK]['stale'])
            screen_path = next(Path(tmp).glob('*/screen.json'))
            self.assertEqual(json.loads(screen_path.read_text())['rows'], [])

    def test_required_index_failure_is_not_an_empty_success(self):
        client = Mock()
        client.get.side_effect = core.SeekerError('SEC HTTP 403: fixture')
        with self.assertRaises(core.SeekerError):
            edgar.discover(client, date(2025, 1, 1), date(2025, 3, 20))


if __name__ == '__main__':
    unittest.main()
