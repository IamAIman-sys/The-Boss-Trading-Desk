"""Deterministic tests for fiscal periods, arithmetic, SEC sources and CLI steps."""

from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import equity_desk as desk


def annual(value, end="2025-12-31", start="2025-01-01", filed="2026-02-01", **extra):
    # Deliberately use the same fy for both current and comparative facts.
    return {"val": value, "start": start, "end": end, "filed": filed,
            "accn": "0000000001-26-000001", "form": "10-K", "fy": 2025, "fp": "FY", **extra}


def instant(value, end="2025-12-31"):
    row = annual(value, end=end)
    del row["start"]
    return row


def sample_facts():
    facts = {}
    values = {"revenue": (120, 100), "operating_income": (24, 18), "net_income": (18, 12),
              "diluted_eps": (3, 2), "equity": (90, 60), "long_term_debt": (30, 25),
              "current_debt": (6, 5), "cfo": (32, 26), "capex": (8, 7)}
    for key, (_, kind, unit, tags) in desk.CONCEPTS.items():
        a, b = values[key]
        entries = ([instant(a), instant(b, "2024-12-31")] if kind == "instant" else
                   [annual(a), annual(b, "2024-12-31", "2024-01-01")])
        facts[tags[0]] = {"units": {unit: entries}}
    return {"facts": {"us-gaap": facts}}


COMPANY = {"ticker": "TEST", "cik": "0000000001", "name": "Test Issuer"}


class FactsTests(unittest.TestCase):
    def test_dates_not_fy_and_all_arithmetic(self):
        report = desk.extract_facts(sample_facts(), COMPANY)
        self.assertEqual(report["facts"]["revenue"]["prior"]["val"], 100)
        result = desk.calculate(report, Decimal("45"))
        expected = {"Revenue growth": "20", "Operating margin": "20", "Return on average equity": "24",
                    "Debt to equity": "0.4", "Free cash flow": "24", "P/E (latest fiscal-year diluted EPS)": "15"}
        for key, value in expected.items():
            self.assertEqual(Decimal(result[key]["value"]), Decimal(value))
        self.assertIn("30 + 6", result["Debt to equity"]["arithmetic"])

    def test_newest_tag_wins_and_quarter_cannot_be_annual(self):
        raw = sample_facts()
        tags = raw["facts"]["us-gaap"]
        tags["RevenueFromContractWithCustomerExcludingAssessedTax"] = {
            "units": {"USD": tags.pop(desk.CONCEPTS["revenue"][3][0])["units"]["USD"]}}
        tags[desk.CONCEPTS["revenue"][3][0]] = {"units": {"USD": [
            annual(80, "2023-12-31", "2023-01-01"),
            annual(45, "2026-03-31", "2026-01-01", form="10-Q")]}}
        report = desk.extract_facts(raw, COMPANY)
        self.assertEqual(report["facts"]["revenue"]["tag"], "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax")
        self.assertEqual(report["periods"]["current"]["end"], "2025-12-31")

    def test_total_revenue_wins_over_net_sales_in_the_same_year(self):
        raw = sample_facts()
        raw["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"] = {
            "units": {"USD": [annual(110), annual(90, "2024-12-31", "2024-01-01")]}}
        report = desk.extract_facts(raw, COMPANY)
        self.assertEqual(report["facts"]["revenue"]["current"]["val"], 120)
        self.assertEqual(report["facts"]["revenue"]["tag"], "us-gaap:Revenues")

    def test_missing_year_does_not_use_another_year_or_zero(self):
        raw = sample_facts()
        raw["facts"]["us-gaap"]["OperatingIncomeLoss"]["units"]["USD"] = [
            annual(999, "2026-12-31", "2026-01-01")]
        del raw["facts"]["us-gaap"]["LongTermDebtCurrent"]
        report = desk.extract_facts(raw, COMPANY)
        self.assertIsNone(report["facts"]["operating_income"]["current"])
        result = desk.calculate(report)
        self.assertIsNone(result["Operating margin"]["value"])
        self.assertIsNone(result["Debt to equity"]["value"])

    def test_latest_filed_comparative_is_used(self):
        raw = sample_facts()
        raw["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"].append(
            annual(19, filed="2026-04-01", form="10-K/A"))
        report = desk.extract_facts(raw, COMPANY)
        self.assertEqual(report["facts"]["net_income"]["current"]["val"], 19)

    def test_52_53_week_periods(self):
        raw = sample_facts()
        for tag in raw["facts"]["us-gaap"].values():
            for entries in tag["units"].values():
                for entry in entries:
                    is_current = entry["end"] == "2025-12-31"
                    entry["end"] = "2025-09-27" if is_current else "2024-09-28"
                    if "start" in entry:
                        entry["start"] = "2024-09-29" if is_current else "2023-09-24"
        report = desk.extract_facts(raw, COMPANY)
        self.assertEqual(report["facts"]["revenue"]["prior"]["val"], 100)
        self.assertEqual(report["facts"]["cfo"]["current"]["end"], "2025-09-27")

    def test_zero_denominator_negative_eps_and_missing_price(self):
        report = desk.extract_facts(sample_facts(), COMPANY)
        report["facts"]["equity"]["current"]["val"] = 0
        report["facts"]["diluted_eps"]["current"]["val"] = -1
        results = desk.calculate(report, Decimal("10"))
        self.assertIsNone(results["Debt to equity"]["value"])
        self.assertIn("10 / -1", results["P/E (latest fiscal-year diluted EPS)"]["reason"])
        self.assertIn("--price", desk.calculate(report)["P/E (latest fiscal-year diluted EPS)"]["reason"])

    def test_total_debt_tag_is_not_added_to_current_portion(self):
        raw = sample_facts()
        taxonomy = raw["facts"]["us-gaap"]
        del taxonomy["LongTermDebtNoncurrent"]
        taxonomy["LongTermDebt"] = {"units": {"USD": [instant(36)]}}
        self.assertIsNone(desk.extract_facts(raw, COMPANY)["facts"]["long_term_debt"]["current"])

    def test_lease_inclusive_debt_is_labeled_and_cannot_mix_definitions(self):
        raw = sample_facts()
        taxonomy = raw["facts"]["us-gaap"]
        taxonomy["LongTermDebtAndCapitalLeaseObligations"] = taxonomy.pop("LongTermDebtNoncurrent")
        taxonomy["LongTermDebtAndCapitalLeaseObligationsCurrent"] = taxonomy.pop("LongTermDebtCurrent")
        report = desk.extract_facts(raw, COMPANY)
        result = desk.calculate(report)["Debt to equity"]
        self.assertEqual(Decimal(result["value"]), Decimal("0.4"))
        self.assertIn("finance/capital lease", result["definition"])
        report["facts"]["current_debt"]["tag"] = "us-gaap:LongTermDebtCurrent"
        self.assertIsNone(desk.calculate(report)["Debt to equity"]["value"])


def index_html(exhibit=True):
    return ("<div class='infoHead'>Accepted</div><div class='info'>2026-02-02 16:05:09</div>"
            "<table class='tableFile'><tr><td>2</td><td>Earnings release</td>"
            "<td><a href='/ix?doc=/Archives/release.htm'>release.htm</a></td><td>EX-99.1</td></tr></table>"
            if exhibit else "<div class='infoHead'>Accepted</div><div class='info'>2026-02-02 16:05:09</div>").encode()


class FilingTests(unittest.TestCase):
    def test_exhibit_99_fallback_requires_explicit_primary_document_reference(self):
        selected = {form: {"document_url": f"https://www.sec.gov/{form}.htm", "accessionNumber": "a"}
                    for form in ("10-K", "10-Q", "8-K")}
        selected["8-K"]["documents"] = [{"type": "EX-99", "url": "https://www.sec.gov/release.htm"}]
        client = Mock()
        client.get.return_value = b"<p>Item 2.02. The press release is furnished as Exhibit No. 99 to this report.</p>"
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            result = desk.download_documents(client, selected, Path(tmp))
            self.assertEqual(result["earnings_release"]["exhibit_label"], "Exhibit 99")
            client.get.return_value = b"Item 2.02. The release is furnished as Exhibit 99."
            result = desk.download_documents(client, selected, Path(tmp))
            self.assertEqual(result["earnings_release"]["exhibit_label"], "Exhibit 99")
            for text in (b"Item 2.02. No identified exhibit.",
                         b"Item 2.02. The release is Exhibit 99.1.",
                         b"Item 2.02. See Exhibit 990."):
                client.get.return_value = text
                with self.assertRaises(desk.DeskError):
                    desk.download_documents(client, selected, Path(tmp))

    def test_accepted_comes_from_index_and_viewer_is_unwrapped(self):
        accepted, documents = desk.parse_index(index_html(), "https://www.sec.gov/Archives/index.html")
        self.assertEqual(accepted, "2026-02-02 16:05:09")
        self.assertEqual(documents[0]["url"], "https://www.sec.gov/Archives/release.htm")
        with self.assertRaises(desk.DeskError):
            desk.parse_index(b"<p>no accepted time</p>", "https://www.sec.gov/index")

    def test_latest_earnings_8k_is_confirmed_in_document_and_history_is_used(self):
        rows = [
            {"form": "8-K", "accessionNumber": "0000000001-26-000004", "items": "2.02", "primaryDocument": "wrong.htm", "acceptanceDateTime": "2026-02-04"},
            {"form": "8-K", "accessionNumber": "0000000001-26-000003", "items": "2.02", "primaryDocument": "earnings.htm", "acceptanceDateTime": "2026-02-03"},
            {"form": "10-Q", "accessionNumber": "0000000001-26-000002", "items": "", "primaryDocument": "q.htm", "acceptanceDateTime": "2026-02-02"},
        ]
        older = [{"form": "10-K", "accessionNumber": "0000000001-26-000001", "primaryDocument": "k.htm", "acceptanceDateTime": "2026-02-01"}]
        def columns(rows):
            return {k: [r.get(k, "") for r in rows] for k in rows[0]}
        client = Mock()
        client.json.side_effect = [{"filings": {"recent": columns(rows), "files": [{"name": "older.json"}]}}, columns(older)]
        def get(url):
            if url.endswith("wrong.htm"):
                return b"Item 5.02 Board appointments"
            if url.endswith("earnings.htm"):
                return b"<p>Item 2.02 Results of Operations and Financial Condition</p>"
            return index_html()
        client.get.side_effect = get
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            chosen = desk.select_filings(client, COMPANY, Path(tmp))
        self.assertEqual(chosen["8-K"]["accessionNumber"], rows[1]["accessionNumber"])
        self.assertEqual(chosen["10-K"]["accessionNumber"], older[0]["accessionNumber"])

    def test_four_documents_are_saved_and_release_uses_99_1(self):
        selected = {form: {"document_url": f"https://www.sec.gov/{form}.htm", "accessionNumber": "a"}
                    for form in ("10-K", "10-Q", "8-K")}
        selected["8-K"]["documents"] = [{"type": "EX-99.1", "url": "https://www.sec.gov/release.htm"}]
        client = Mock()
        client.get.return_value = b"<p>Quarterly revenue was $120.</p>"
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            records = desk.download_documents(client, selected, Path(tmp))
            self.assertEqual(len(list(Path(tmp).glob("*.txt"))), 4)
            self.assertEqual(records["earnings_release"]["url"], "https://www.sec.gov/release.htm")

    def test_text_preserves_table_rows_and_removes_hidden_xbrl(self):
        text = desk.plain_text(b"<ix:header>hidden 999</ix:header><table><tr><td>Total revenue</td><td>120</td></tr></table><p>Item <b>2.02</b></p>")
        self.assertIn("Total revenue | 120", text)
        self.assertNotIn("hidden", text)
        self.assertTrue(desk.has_item_202(text))

    def test_release_table_eps_is_not_diluted_share_count(self):
        lines = ["In millions except per-share data", "Three Months Ended | Twelve Months Ended",
                 "December 31, 2025 | December 31, 2024", "Total revenue | 120 | 100"]
        lines += ["Expense | 5"] * 20
        lines += ["Earnings per share:", "Basic | 3.10 | 2.10", "Diluted | 3.00 | 2.00",
                  "Shares used in computing earnings per share:", "Basic | 6 | 6", "Diluted | 7 | 7"]
        results = desk.release_lines("\n".join(lines))
        self.assertEqual(len(results["diluted_eps"]), 1)
        self.assertIn("3.00", results["diluted_eps"][0]["line"])
        self.assertTrue(any("Three Months" in x["line"] for x in results["diluted_eps"][0]["context"]))

    def test_week_based_quarter_common_share_eps_and_membership_revenue(self):
        text = "\n".join([
            "Results for the 16-week fourth quarter.",
            "Net sales for the quarter were $90 million.",
            "Net income for the quarter was $3 million, $1.50 per diluted share.",
            "Dollars in millions, except per share data",
            "16 Weeks Ended | 52 Weeks Ended",
            "August 30, 2026 | August 31, 2025",
            "Net sales | 90 | 80", "Membership fees | 2 | 1",
            "Total revenue | 92 | 81",
            "NET INCOME PER COMMON SHARE:", "Basic | 1.51 | 1.21",
            "Diluted | 1.50 | 1.20", "Shares used in calculation (000's):",
            "Basic | 1900 | 1900", "Diluted | 2000 | 2000",
        ])
        matches = desk.release_lines(text)
        self.assertEqual([m["line"] for m in matches["total_revenue"]], ["Total revenue | 92 | 81"])
        self.assertEqual(len(matches["diluted_eps"]), 2)
        self.assertTrue(any("per diluted share" in m["line"] for m in matches["diluted_eps"]))
        self.assertTrue(any("16 Weeks Ended" in c["line"] for m in matches["diluted_eps"] for c in m["context"]))
        self.assertFalse(any("2000" in m["line"] for m in matches["diluted_eps"]))


class ClientAndStepTests(unittest.TestCase):
    def test_user_agent_from_file_is_sent_on_retries_and_redirects(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text('SEC_USER_AGENT="Research contact@example.test"\n')
            client = desk.SECClient(env)
            redirect = Mock(is_redirect=True, headers={"Location": "https://data.sec.gov/next"})
            retry = Mock(is_redirect=False, status_code=429, headers={"Retry-After": "0"})
            good = Mock(is_redirect=False, status_code=200, content=b"{}")
            headers = []
            def send(request, **kwargs):
                headers.append(request.headers["User-Agent"])
                return [redirect, retry, good][len(headers) - 1]
            with patch.object(client.session, "send", side_effect=send), patch.object(desk.time, "sleep"):
                self.assertEqual(client.get("https://www.sec.gov/test"), b"{}")
                client.get("https://www.sec.gov/test")
            self.assertEqual(headers, ["Research contact@example.test"] * 3)

    def test_step_five_uses_saved_facts_without_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(desk, "RUNS", Path(tmp)), redirect_stdout(StringIO()):
            folder = Path(tmp) / "Test_Issuer__2026-01-01"
            desk.save_json(folder / "manifest.json", {"company": COMPANY, "steps": {"4": {"status": "complete"}}})
            desk.save_json(folder / "facts.json", desk.extract_facts(sample_facts(), COMPANY))
            client = Mock()
            run = desk.Desk(client, "TEST", [], Decimal("45"), 5)
            run.run_step(5)
            client.get.assert_not_called()
            client.json.assert_not_called()
            self.assertEqual(list(run.state["steps"]), ["4", "5"])
            self.assertTrue((folder / "calculations.json").exists())

    def test_failed_prerequisite_cannot_reuse_old_facts(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(desk, "RUNS", Path(tmp)), redirect_stdout(StringIO()):
            folder = Path(tmp) / "Test_Issuer__2026-01-01"
            desk.save_json(folder / "manifest.json", {"company": COMPANY, "steps": {"4": {"status": "failed"}}})
            desk.save_json(folder / "facts.json", desk.extract_facts(sample_facts(), COMPANY))
            run = desk.Desk(Mock(), "TEST", [], None, 5)
            with self.assertRaisesRegex(desk.DeskError, "stale"):
                run.run_step(5)

    def test_missing_prerequisite_and_bad_price_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(desk, "RUNS", Path(tmp)):
            with self.assertRaisesRegex(desk.DeskError, "step 1"):
                desk.Desk(Mock(), "TEST", [], None, 5)
        for value in ("nan", "Infinity", "0", "-1", "abc"):
            with self.assertRaises(desk.argparse.ArgumentTypeError):
                desk.positive_price(value)


if __name__ == "__main__":
    unittest.main()
