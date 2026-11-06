"""Offline tests for verifier.py: the four Lab 04 tests, plus unit checks. No model, no network."""

import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

import verifier

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "checkpoint-2"))
import make_test_runs  # noqa: E402


class LabTests(unittest.TestCase):
    """Lab 04: seeded error, invented number, clean report, skip test."""

    @classmethod
    def setUpClass(cls):
        cls.temp = Path(tempfile.mkdtemp())
        cls.results = {}
        for name, report in make_test_runs.reports().items():
            out, marks = verifier.verify_run(make_test_runs.build(name, report, cls.temp))
            cls.results[name] = (out, marks)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp)

    def core(self, name):
        return {(row["claim"], row["item"]): row for row in verifier.core_summary(self.results[name][1])}

    def test_seeded_eps_is_wrong_and_corrected_from_the_10k_line(self):
        marks = self.results["seeded-eps"][1]
        eps = next(m for m in marks if m["item"] == "Diluted EPS (current)")
        self.assertEqual((eps["number"], eps["mark"], eps["correct"]), ("30.08", "Wrong", "29.08"))
        self.assertIn("us-gaap:EarningsPerShareDiluted", eps["source"])
        self.assertRegex(eps["source"], r"10-K L\d+: \"Diluted earnings per share .*29\.08")
        self.assertEqual(self.core("seeded-eps")[(5, "Diluted EPS (current)")]["mark"], "Wrong")
        text = (self.results["seeded-eps"][0] / "verified_report.md").read_text(encoding="utf-8")
        self.assertIn("~~30.08~~ **29.08**", text)

    def test_invented_growth_is_wrong_with_the_arithmetic(self):
        wrong = [m for m in self.results["invented-growth"][1] if m["mark"] == "Wrong"]
        self.assertEqual(len(wrong), 1)
        self.assertEqual((wrong[0]["number"], wrong[0]["correct"]), ("6.24", "2.24"))
        self.assertIn("(41,954,000,000 - 41,033,000,000) / 41,033,000,000", wrong[0]["why"])

    def test_clean_report_has_all_eleven_core_claims_correct(self):
        rows = verifier.core_summary(self.results["clean"][1])
        self.assertEqual({row["claim"] for row in rows}, set(range(1, 12)))
        self.assertTrue(all(row["mark"] == "Correct" for row in rows), rows)
        self.assertFalse([m for m in self.results["clean"][1] if m["mark"] == "Wrong"])

    def test_no_way_to_run_without_the_verifier(self):
        for path in ROOT.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?i)(no|skip|disable|without)[-_ ]?verif", path.name)
        desk = (ROOT / "research_desk.py").read_text(encoding="utf-8")
        report_save = desk.index('path.write_text("\\n".join(lines)')
        self.assertIn("verifier.verify_run(self.folder", desk[report_save:report_save + 800])


class UnitTests(unittest.TestCase):
    def make_run(self, report, lines=("Total sales | 41,954 | 41,033",)):
        folder = Path(tempfile.mkdtemp())
        facts = {"company": {"ticker": "TST"}, "periods": {}, "facts": {"revenue": {
            "tag": "us-gaap:Revenues", "current": {"start": "2025-01-01", "end": "2025-12-31", "val": 41954000000,
                                                   "accn": "0000000001-26-000001", "tag": "us-gaap:Revenues"},
            "prior": {"start": "2024-01-01", "end": "2024-12-31", "val": 41033000000,
                      "accn": "0000000001-26-000001", "tag": "us-gaap:Revenues"}}}}
        (folder / "facts.json").write_text(json.dumps(facts), encoding="utf-8")
        (folder / "10-K.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (folder / "report.md").write_text(report, encoding="utf-8")
        return folder

    def test_first_line_kept_and_marks_table_under_it(self):
        folder = self.make_run("TST; filings read: 10-K\n\n## Overview\n\nSales were $41.954 billion [10-K L1].\n")
        out, marks = verifier.verify_run(folder)
        text = (out / "verified_report.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual(text[0], "TST; filings read: 10-K")
        self.assertEqual(text[2], "## Verifier marks")
        self.assertEqual([m["mark"] for m in marks], ["Correct"])

    def test_number_off_its_cited_line_is_unsupported_with_the_real_line(self):
        folder = self.make_run("x\n## Overview\n\nSales were $41.954 billion [10-K L3].\n",
                               lines=("Total sales | 41,954", "Other", "Other"))
        marks = verifier.verify_run(folder)[1]
        self.assertEqual(marks[0]["mark"], "Unsupported")
        self.assertEqual(marks[0]["source"], "10-K L1")

    def test_uncited_unknown_number_is_unsupported(self):
        folder = self.make_run("x\n## Overview\n\nThe firm has 912 warehouses.\n")
        self.assertEqual(verifier.verify_run(folder)[1][0]["mark"], "Unsupported")

    def test_investment_thesis_and_metadata_are_skipped(self):
        folder = self.make_run("x\nPartner check: 777.\n## Investment Recommendation\n\nBuy: 999 upside.\n")
        self.assertEqual(verifier.verify_run(folder)[1], [])

    def test_runs_never_overwrite(self):
        folder = self.make_run("x\n## Overview\n\nSales were $41.954 billion [10-K L1].\n")
        first, second = verifier.verify_run(folder)[0], verifier.verify_run(folder)[0]
        self.assertNotEqual(first, second)
        self.assertTrue((first / "verified_report.md").exists() and (second / "verified_report.md").exists())


if __name__ == "__main__":
    unittest.main()
