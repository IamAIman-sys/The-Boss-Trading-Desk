"""Offline tests for financial context, missing evidence and review signals."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest

import equity_desk as data
import research_evidence as evidence


def fixture():
    periods = {"current": {"start": "2025-01-01", "end": "2025-12-31"},
               "prior": {"start": "2024-01-01", "end": "2024-12-31"}}
    values = {"revenue": (1000, 1000), "operating_income": (150, 100), "net_income": (80, 60),
              "equity": (200, 200), "long_term_debt": (300, 100), "current_debt": (20, 20),
              "cfo": (100, 80), "capex": (40, 35), "diluted_eps": (8, 6)}
    report = {"company": {"ticker": "TST", "name": "Test Co", "cik": "1"}, "periods": periods, "facts": {}}
    for key, vals in values.items():
        label, kind, unit, tags = data.CONCEPTS[key]
        item = {"tag": "us-gaap:" + tags[0], "unit": unit, "label": label}
        for column, val in zip(("current", "prior"), vals):
            period = periods[column]
            item[column] = {"val": val, "unit": unit, "tag": item["tag"], "accn": "0000000001-26-000001",
                            "filing_url": "https://www.sec.gov/example", "end": period["end"]}
            if kind == "duration":
                item[column]["start"] = period["start"]
        report["facts"][key] = item
    raw = {"facts": {"us-gaap": {
        "StockholdersEquity": {"units": {"USD": [{"val": 200, "end": "2023-12-31", "accn": "0000000001-26-000001"}]}},
        "InterestExpenseNonOperating": {"units": {"USD": [
            {**periods[c], "val": val, "accn": "0000000001-26-000001"} for c, val in (("current", 50), ("prior", 20))]}}
    }}}
    return report, raw


class MetricTests(unittest.TestCase):
    def test_measures_and_provenance(self):
        report, raw = fixture(); metrics = evidence.annual_metrics(report, raw)
        self.assertEqual(metrics["current"]["Net profit margin"]["value"], "8.00")
        self.assertEqual(metrics["current"]["Return on average equity"]["value"], "40.0")
        self.assertEqual(metrics["prior"]["Return on average equity"]["value"], "30.0")
        self.assertEqual(metrics["current"]["Interest coverage"]["value"], "3")
        self.assertEqual(metrics["current"]["Interest coverage"]["inputs"][1]["tag"], "us-gaap:InterestExpenseNonOperating")
        self.assertTrue(evidence.review_signals(metrics)["roe_debt_warning"])

    def test_both_threshold_directions_and_boundary(self):
        report, raw = fixture()
        for op, expected in ((150, True), (50, True), (149, False), (51, False)):
            report["facts"]["operating_income"]["current"]["val"] = op
            signal = evidence.review_signals(evidence.annual_metrics(report, raw))
            self.assertIs(signal["high_priority_review"], expected)
            self.assertEqual(signal["threshold_basis_points"], "500")

    def test_missing_coverage_is_unknown_not_safe(self):
        report, _ = fixture(); metrics = evidence.annual_metrics(report)
        self.assertIsNone(metrics["current"]["Interest coverage"]["value"])
        self.assertIsNone(metrics["prior"]["Return on average equity"]["value"])
        self.assertIsNone(evidence.review_signals(metrics)["roe_debt_warning"])

    def test_zero_negative_and_period_mismatch(self):
        for key, field, value in (("revenue", "val", 0), ("equity", "val", -1), ("revenue", "start", "2025-07-01")):
            report, raw = fixture(); report["facts"][key]["current"][field] = value
            metrics = evidence.annual_metrics(report, raw)
            name = "Return on average equity" if key == "equity" else "Operating margin"
            self.assertIsNone(metrics["current"][name]["value"])

    def test_wrong_interest_period_or_accession_is_rejected(self):
        for field, value in (("start", "2025-07-01"), ("accn", "different")):
            report, raw = fixture()
            raw["facts"]["us-gaap"]["InterestExpenseNonOperating"]["units"]["USD"][0][field] = value
            self.assertIsNone(evidence.annual_metrics(report, raw)["current"]["Interest coverage"]["value"])

    def test_lease_definitions_cannot_be_mixed(self):
        report, raw = fixture()
        report["facts"]["long_term_debt"]["current"]["tag"] = "us-gaap:LongTermDebtAndCapitalLeaseObligations"
        self.assertIsNone(evidence.annual_metrics(report, raw)["current"]["Debt"]["value"])


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.report, raw = fixture()
        self.manifest = {"company": self.report["company"], "steps": {str(n): {"status": "complete"} for n in range(1, 8)}}
        self.selected = {"10-K": {"accessionNumber": "0000000001-26-000001"}}
        peer = copy.deepcopy(self.report); peer["company"]["ticker"] = "PEER"
        peer["periods"]["current"]["end"] = "2025-09-30"
        self.files = {"facts.json": self.report, "companyfacts.json": raw,
                      "calculations.json": {"periods": self.report["periods"], "price_usd": "100", "calculations": data.calculate(self.report, 100)},
                      "peers.json": {"PEER": {"facts": peer}}}
        self.save()

    def save(self):
        for name, obj in self.files.items():
            (self.folder / name).write_text(json.dumps(obj))

    def test_peer_periods_and_citable_arithmetic(self):
        packet, paths = evidence.financial_packet(self.folder, self.manifest, self.selected, ["PEER"])
        self.assertFalse(packet["peers"]["PEER"]["periods_match_company"])
        lines = evidence.metric_lines(packet)
        self.assertTrue(any("Net profit margin" in r["text"] and "8.00 %" in r["text"] for r in lines))
        self.assertTrue(any("us-gaap:NetIncomeLoss" in r["text"] for r in lines))
        self.assertIn("companyfacts.json", paths)
        self.assertFalse(any(re.search(r"\d\.\d{3,} (%|x|percentage)", r["text"]) for r in lines))

    def test_display_rounding(self):
        self.assertEqual(evidence.display("10.752252", "%"), "10.75")
        self.assertEqual(evidence.display("0.10228780439900498268345263", "pp"), "0.10")
        self.assertEqual(evidence.display("4757000000", "USD"), "4757000000")
        self.assertIsNone(evidence.display(None, "%"))

    def test_stale_missing_or_tampered_inputs_stop(self):
        self.manifest["steps"]["4"]["status"] = "stale"
        with self.assertRaises(data.DeskError): evidence.financial_packet(self.folder, self.manifest, self.selected)
        self.manifest["steps"]["4"]["status"] = "complete"
        self.files["calculations.json"]["calculations"]["Operating margin"]["value"] = "99"
        self.save()
        with self.assertRaisesRegex(data.DeskError, "disagrees"):
            evidence.financial_packet(self.folder, self.manifest, self.selected)

    def test_peer_selection_and_filing_must_match(self):
        with self.assertRaisesRegex(data.DeskError, "peers"):
            evidence.financial_packet(self.folder, self.manifest, self.selected, ["OTHER"])
        self.selected["10-K"]["accessionNumber"] = "wrong"
        with self.assertRaisesRegex(data.DeskError, "10-K"):
            evidence.financial_packet(self.folder, self.manifest, self.selected)


class SupplementTests(unittest.TestCase):
    def test_explicit_source_and_no_path_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); (folder / "slides.txt").write_text("Slide 4: Investment remains $20 million.")
            p = folder / "sources.json"
            row = {"file": "slides.txt", "title": "Issuer slides", "date": "2026-11-05", "url": "https://example.com/slides"}
            p.write_text(json.dumps([row])); sources, lines = evidence.supplements(p)
            self.assertEqual(lines[0]["source"], "Management supplement 1")
            self.assertEqual(sources[0]["sha256"], evidence.digest(folder / "slides.txt"))
            row["file"] = "../private.txt"; p.write_text(json.dumps([row]))
            with self.assertRaises(data.DeskError): evidence.supplements(p)
        self.assertEqual(evidence.supplements(None), ([], []))


if __name__ == "__main__":
    unittest.main()
