from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

import equity_desk as data
from model_client import ModelError
from research_desk import PARTS, ReportManager, quarterly_facts, research_excerpts, safe_calculate
from test_equity_desk import COMPANY, sample_facts

RELEASE = """Consolidated Statement of Operations
| Quarter Ended September 30 | Nine Months Ended September 30
(dollars in millions, except per share) | 2026 | 2025 | 2026 | 2025
Net sales | 120 | 100 | 350 | 300
Earnings per common share:
| Basic | 2.1 | 1.1
| Diluted | 2.0 | 1.0
Weighted average shares outstanding:
| Diluted shares | 1000 | 900
Consolidated Balance Sheets
Assets | 100 | 90
Segment results
| Quarter Ended September 30 | Nine Months Ended September 30
Net sales | 40 | 30
Adjusted diluted earnings per share | 3 | 2
"""


class ArithmeticTests(unittest.TestCase):
    def test_only_known_inputs_can_be_used(self):
        result = safe_calculate("income / ((equity + prior_equity) / 2) * 100",
                                {"income": "18", "equity": "90", "prior_equity": "60"})
        self.assertEqual(Decimal(result["value"]), Decimal("24"))
        for expression in ("__import__('os')", "income.__class__", "income ** 2", "income + 999", "income / 0", "unknown + 1"):
            with self.assertRaises((ValueError, SyntaxError)):
                safe_calculate(expression, {"income": "18"})

    def test_quarter_excludes_segment_and_adjusted_figures(self):
        result = quarterly_facts(RELEASE, "accession", "Exhibit 99")
        self.assertEqual(result["total_revenue"]["current"], "120")
        self.assertEqual(result["diluted_eps"]["current"], "2.0")
        self.assertEqual(Decimal(result["revenue_growth"]["value"]), Decimal("20"))
        self.assertEqual(result["exhibit_label"], "Exhibit 99")

    def test_year_to_date_first_is_not_a_quarter(self):
        result = quarterly_facts(RELEASE.replace("Quarter Ended September 30 | Nine Months", "Nine Months Ended September 30 | Quarter"), "accession")
        self.assertIn("missing", result["total_revenue"])

    def test_source_line_numbers_survive_excerpt_selection(self):
        text = "Item 1. | Business | 3\nItem 1A. | Risks | 4\nItem 1. Business\nBusiness description.\nMore business.\nItem 1A. Risks\nItem 7. MD&A\nResults.\nItem 7A. Market risk"
        result = research_excerpts(text)
        self.assertEqual(result[0]["line"], 3)
        self.assertTrue(any(r["line"] == 8 and r["text"] == "Results." for r in result))


class FakeClient:
    model = "test-model"
    last_metadata = {"requested_model": "test-model"}

    def __init__(self, keep_failing=False):
        self.calls = []
        self.keep_failing = keep_failing

    def complete(self, instructions, payload):
        self.calls.append(payload)
        task = payload["task"]
        if "Research Analyst task" in task:
            return {"sections": {part: "Sourced research." for part in (PARTS[0], PARTS[1], PARTS[3])}}
        if "Financial Analyst task" in task:
            return {"sections": {PARTS[2]: "See the Python evidence."}}
        if "Investment Advisor task" in task:
            return {"sections": {PARTS[4]: "Hold based on the sourced growth."}, "recommendation": "Hold", "deciding_number": "20% growth"}
        return {"revisions": [{"role": "Research Analyst", "reason": "Correct the source."}] if self.keep_failing else [], "issues": []}


class ManagerTests(unittest.TestCase):
    def folder(self, path):
        facts = data.extract_facts(sample_facts(), COMPANY)
        data.save_json(path / "manifest.json", {"company": COMPANY, "steps": {str(i): {"status": "complete"} for i in range(1, 8)}})
        data.save_json(path / "facts.json", facts)
        data.save_json(path / "calculations.json", {"price_usd": "45", "calculations": data.calculate(facts, Decimal("45"))})
        data.save_json(path / "peers.json", {})
        data.save_json(path / "documents.json", {"earnings_release": {"exhibit_label": "Exhibit 99"}})
        data.save_json(path / "selected_filings.json", {form: {"accessionNumber": "accession", "accepted": "time", "index_url": "source", "document_url": "source"} for form in ("10-K", "10-Q", "8-K")})
        (path / "earnings_release.txt").write_text(RELEASE)
        (path / "10-K.txt").write_text("Item 1. Business\nBusiness.\nItem 1A. Risks\nItem 7. MD&A\nResults.\nItem 7A. Risk")
        (path / "10-Q.txt").write_text("Item 2. MD&A\nResults.\nItem 3. Risks")

    def test_four_calls_isolated_inputs_and_five_sections(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            path = Path(tmp)
            self.folder(path)
            client = FakeClient()
            report = ReportManager(client, path).run()
            self.assertEqual(len(client.calls), 4)
            self.assertEqual(set(client.calls[2]["context"]), {"Research Analyst", "Financial Analyst"})
            text = report.read_text()
            self.assertIn("Exhibit 99)", text.splitlines()[0])
            self.assertTrue(text.splitlines()[1].startswith("Report run time:"))
            for part in PARTS:
                self.assertIn("## " + part, text)
            self.assertIn("human audit", text.lower())
            self.assertIn("Recommendation: Hold", text)
            self.assertIn("Deciding number: 20% growth", text)
            positions = [text.index("## " + part) for part in PARTS]
            self.assertEqual(positions, sorted(positions))

    def test_revision_loop_stops_and_keeps_failure_visible(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            path = Path(tmp)
            self.folder(path)
            client = FakeClient(keep_failing=True)
            with self.assertRaisesRegex(ModelError, "issues remain"):
                ReportManager(client, path).run()
            self.assertEqual(len(client.calls), 7)
            self.assertTrue((path / "report_draft.md").exists())
            status = json.loads((path / "report_status.json").read_text())
            self.assertTrue(status["manager_revisions_remaining"])


if __name__ == "__main__":
    unittest.main()
