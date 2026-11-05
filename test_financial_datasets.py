"""Offline checks for authentication, dates, comparisons, and desk integration."""

from argparse import Namespace
from contextlib import redirect_stdout
from copy import deepcopy
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import equity_desk as data
import financial_datasets as fd
import research_desk
from test_equity_desk import COMPANY, sample_facts


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        env = self.folder / '.env'
        env.write_text('FINANCIAL_DATASETS_API_KEY=test-secret\nSEC_USER_AGENT=Test test@example.edu\n')
        self.session = Mock()
        self.response = self.session.get.return_value
        self.response.status_code = 200
        self.client = fd.FinancialDatasetsClient(env, self.session)
        self.report = data.extract_facts(sample_facts(), COMPANY)

    def prices(self, **changes):
        row = {'time': '2025-10-20', 'close': 45, **changes}
        self.response.json.return_value = {'ticker': 'TEST', 'prices': [row]}

    def statements(self, report=None):
        report = report or self.report
        def get(path, params):
            end = params['report_period']
            column = next(k for k, v in report['periods'].items() if v and v['end'] == end)
            blocks = {}
            for concept, (statement, field) in fd.FIELDS.items():
                row = blocks.setdefault(statement, [{'ticker': 'TEST', 'period': 'annual',
                    'report_period': end, 'currency': 'USD',
                    'accession_number': '0000000001-26-000001'}])[0]
                row[field] = report['facts'][concept][column]['val']
            return {'financials': blocks}, 'https://api.financialdatasets.ai/financials'
        return get

    def test_authentication_exact_date_decimal_and_cache(self):
        self.prices(close='45.12')
        price, source = self.client.closing_price('TEST', '2025-10-20')
        self.assertEqual(price, Decimal('45.12'))
        self.assertEqual(source['date'], '2025-10-20')
        self.assertIn('Not specified', source['adjustment'])
        self.assertNotIn('test-secret', json.dumps(source))
        kwargs = self.session.get.call_args.kwargs
        self.assertEqual(kwargs['headers']['X-API-KEY'], 'test-secret')
        self.assertEqual(kwargs['headers']['User-Agent'], 'Test test@example.edu')
        self.assertFalse(kwargs['allow_redirects'])
        self.client.closing_price('TEST', '2025-10-20')
        self.session.get.assert_called_once()

    def test_price_rejects_wrong_day_duplicate_ticker_currency_and_invalid_value(self):
        for changes in ({'time': '2025-10-21'}, {'ticker': 'OTHER'}, {'currency': 'EUR'},
                        {'close': None}, {'close': 0}, {'close': 'NaN'}, {'close': -1}):
            with self.subTest(changes=changes):
                self.client.cache.clear()
                self.prices(**changes)
                with self.assertRaises(fd.FinancialDatasetsError):
                    self.client.closing_price('TEST', '2025-10-20')
        self.client.cache.clear()
        self.prices()
        self.response.json.return_value['prices'] *= 2
        with self.assertRaises(fd.FinancialDatasetsError):
            self.client.closing_price('TEST', '2025-10-20')

    def test_no_adjacent_trading_day_substitution(self):
        self.response.json.return_value = {'prices': []}
        with self.assertRaisesRegex(fd.FinancialDatasetsError, 'no other date'):
            self.client.closing_price('TEST', '2025-10-19')
        with self.assertRaises(fd.FinancialDatasetsError):
            self.client.closing_price('TEST', '2999-01-01')

    def test_http_errors_redact_bodies_and_do_not_follow_redirects(self):
        for status in (301, 401, 402, 403, 429, 500):
            self.response.status_code = status
            self.response.text = 'test-secret'
            with self.assertRaises(fd.FinancialDatasetsError) as caught:
                self.client.get('/prices', {})
            self.assertNotIn('test-secret', str(caught.exception))
            self.assertIn(str(status), str(caught.exception))
        self.response.json.assert_not_called()

    def test_malformed_json_pagination_and_unsupported_hosts_fail(self):
        for payload in ([], {'error': 'test-secret'}, {'next_page_url': 'https://other.example'}):
            self.response.json.return_value = payload
            with self.assertRaises(fd.FinancialDatasetsError):
                self.client.get('/prices', {})
        with self.assertRaises(fd.FinancialDatasetsError):
            self.client.get('https://other.example', {})

    def test_compare_both_periods_without_changing_sec_and_flag_scope(self):
        before = deepcopy(self.report)
        with patch.object(self.client, 'get', side_effect=self.statements()) as get:
            result = self.client.compare(self.report)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(len(result['rows']), 18)
        self.assertEqual(self.report, before)
        for row in result['rows']:
            self.assertTrue(row['numeric_match'])
            self.assertTrue(row['same_filing'])
            expected = 'definition_review' if row['concept'] in fd.DEFINITION_NOTES else 'numeric_match'
            self.assertEqual(row['status'], expected)

    def test_differences_missing_currency_and_wrong_period_are_not_matches(self):
        base = self.statements()
        def changed(path, params):
            payload, url = base(path, params)
            payload['financials']['income_statements'][0]['revenue'] += 1
            payload['financials']['income_statements'][0]['earnings_per_share_diluted'] = None
            payload['financials']['balance_sheets'][0]['currency'] = 'EUR'
            payload['financials']['cash_flow_statements'][0]['report_period'] = '2000-12-31'
            return payload, url
        with patch.object(self.client, 'get', side_effect=changed):
            rows = self.client.compare(self.report)['rows']
        for row in rows:
            if row['concept'] == 'revenue':
                self.assertEqual(row['status'], 'difference')
                self.assertEqual(row['difference_vendor_minus_sec'], '1')
            elif row['concept'] in ('diluted_eps', 'equity', 'current_debt', 'long_term_debt', 'cfo', 'capex'):
                self.assertEqual(row['status'], 'missing')

    def test_missing_prior_and_capex_sign_are_not_invented(self):
        self.report['periods']['prior'] = None
        for fact in self.report['facts'].values():
            fact['prior'] = None
        base = self.statements()
        def changed(path, params):
            payload, url = base(path, params)
            payload['financials']['cash_flow_statements'][0]['capital_expenditure'] = -8
            return payload, url
        with patch.object(self.client, 'get', side_effect=changed) as get:
            rows = self.client.compare(self.report)['rows']
        self.assertEqual(get.call_count, 1)
        capex = next(r for r in rows if r['concept'] == 'capex' and r['column'] == 'current')
        self.assertEqual(capex['difference_vendor_minus_sec'], '-16')
        self.assertFalse(capex['numeric_match'])
        self.assertTrue(all(r['status'] == 'missing' for r in rows if r['column'] == 'prior'))

    def test_step5_uses_fetched_price_and_saves_source_then_clears_on_manual_input(self):
        self.prices()
        run = data.Desk(None, 'TEST', [], None, None, fd_client=self.client, fetch_price_date='2025-10-20')
        run.folder = self.folder
        run.state = {'steps': {'4': {'status': 'complete'}}}
        data.save_json(self.folder / 'facts.json', self.report)
        with redirect_stdout(StringIO()):
            run.run_step(5)
        result = json.loads((self.folder / 'calculations.json').read_text())
        self.assertEqual(Decimal(result['calculations']['P/E (latest fiscal-year diluted EPS)']['value']), 15)
        self.assertEqual(result['price_reference']['date'], '2025-10-20')
        self.assertTrue((self.folder / 'price_reference.json').exists())
        rendered = research_desk.evidence_markdown(self.report, result, research_desk.quarterly_facts('', 'test'), {})
        self.assertIn('Not specified', rendered)
        run.fetch_price_date, run.price = None, Decimal('60')
        with redirect_stdout(StringIO()):
            run.run_step(5)
        self.assertFalse((self.folder / 'price_reference.json').exists())
        self.assertNotIn('price_reference', json.loads((self.folder / 'calculations.json').read_text()))

    def test_failed_comparison_invalidates_previous_result(self):
        run = data.Desk(None, 'TEST', [], None, None, fd_client=self.client)
        data.save_json(self.folder / 'financial_datasets_comparison.json', {'status': 'complete'})
        with patch.object(self.client, 'compare', side_effect=fd.FinancialDatasetsError('Request failed.')):
            with self.assertRaises(fd.FinancialDatasetsError):
                run.compare_facts(self.report, self.folder)
        self.assertEqual(json.loads((self.folder / 'financial_datasets_comparison.json').read_text())['status'], 'failed')

    def test_options_are_opt_in_and_conflicts_fail_before_network(self):
        args = Namespace(fetch_price_date=None, compare_financial_datasets=False, price=None, step=None)
        self.assertIsNone(fd.options(args)['fd_client'])
        args.fetch_price_date, args.price = '2025-10-20', Decimal('45')
        with self.assertRaises(fd.FinancialDatasetsError):
            fd.options(args)
        args.price, args.step = None, 4
        with self.assertRaises(fd.FinancialDatasetsError):
            fd.options(args)

    def test_report_reuse_compares_main_and_peer_without_refetching_sec(self):
        self.prices()
        folder = self.folder / 'Saved__2025-10-21'
        data.save_json(folder / 'manifest.json', {'company': COMPANY,
                       'steps': {str(i): {'status': 'complete'} for i in range(1, 8)}})
        data.save_json(folder / 'facts.json', self.report)
        peer = deepcopy(self.report)
        peer['company']['ticker'] = 'PEER'
        data.save_json(folder / 'peers.json', {'PEER': {'facts': peer}})
        with patch.object(data, 'RUNS', self.folder), patch.object(data, 'SECClient') as sec, \
             patch.object(fd, 'FinancialDatasetsClient', return_value=self.client), \
             patch.object(self.client, 'compare', return_value={'rows': []}) as compare, \
             patch.object(research_desk, 'ModelClient'), patch.object(research_desk, 'ReportManager') as manager, \
             redirect_stdout(StringIO()):
            code = research_desk.main(['TEST', '--reuse', '--peers', 'PEER',
                                      '--fetch-price-date', '2025-10-20', '--compare-financial-datasets'])
        self.assertEqual(code, 0)
        self.assertEqual(compare.call_count, 2)
        self.assertEqual(compare.call_args_list[1].args[0]['company']['ticker'], 'PEER')
        sec.return_value.json.assert_not_called()
        sec.return_value.get.assert_not_called()
        manager.return_value.run.assert_called_once()
        self.assertTrue((folder / 'peers' / 'PEER' / 'financial_datasets_comparison.json').exists())


if __name__ == '__main__':
    unittest.main()
