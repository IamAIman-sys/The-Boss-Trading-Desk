"""Offline tests for flow_desk.py: no API key, no SEC requests."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from crewai import BaseLLM

import equity_desk as data
import flow_desk

CONTEXT = {
    "10-K_excerpts": [{"source": "10-K", "line": 10, "text": "We operate 912 warehouses worldwide."}],
    "release": [{"source": "Exhibit 99.1", "line": 4, "text": "Net sales increased 6% to $62.15 billion."}],
}


class StubLLM(BaseLLM):
    """Returns queued JSON answers in order (the last one repeats); records each prompt."""
    answers: list[str] = []
    prompts: list[str] = []

    def call(self, messages, tools=None, callbacks=None, available_functions=None,
             from_task=None, from_agent=None, response_model=None, **kwargs):
        self.prompts.append(messages if isinstance(messages, str) else json.dumps(messages))
        answer = self.answers[min(len(self.prompts), len(self.answers)) - 1]
        if answer == "RAISE":
            raise RuntimeError("length limit was reached")
        if response_model is not None:
            return response_model.model_validate_json(answer)
        return answer

    def supports_function_calling(self):
        return False


def claim(text, quote, citation):
    return {"claim": text, "quote": quote, "citation": citation}


GOOD = json.dumps({
    "overview": [claim("The company runs a large network.", "We operate 912 warehouses worldwide.", "10-K L2")],
    "market_positioning": [claim("Scale supports its position.", "We operate 912 warehouses worldwide.", "[10-K L2]")],
    "future_developments": [claim("Fee income is growing.", "Membership fees rose.", "10\u2011K L4")],
    "insight": "Fee growth matters more than the headline suggests.",
    "insight_evidence": [claim("Fees rose.", "Membership fees rose.", "10-K L4")]})
BAD = json.dumps({**json.loads(GOOD), "overview": [claim("It runs 950 stores.", "We operate 950 warehouses", "10-K L2")]})


class CheckResearchTests(unittest.TestCase):
    def test_number_from_another_source_cannot_support_this_citation(self):
        text = 'It runs 6 warehouses: "912 warehouses" [10-K L10]'
        result = flow_desk.check_research({"Overview": text}, CONTEXT)
        self.assertEqual(result["marks"][0]["result"], "number not on cited line")

    def test_generated_and_supplement_lines_are_checked(self):
        context = {"evidence_lines": [
            {"source": "Python evidence", "line": 1, "text": "Operating margin: 15 %; formula: 150 / 1000 * 100"},
            {"source": "Management supplement 1", "line": 4, "text": "Expected investment: $20 million."}]}
        sections = {"Overview": '"Operating margin: 15 %" [Python evidence L1]',
                    "Insight": '"Expected investment: $20 million." [Management supplement 1 L4]'}
        self.assertEqual(flow_desk.check_research(sections, context)["status"], "pass")

    def test_clean_section_passes(self):
        text = 'Sales grew: "Net sales increased 6% to $62.15 billion." [Exhibit 99.1 L4]'
        result = flow_desk.check_research({"Overview": text}, CONTEXT)
        self.assertEqual(result["status"], "pass", result["problems"])
        self.assertEqual(result["citations_ok"], 1)

    def test_seeded_wrong_quote_fails(self):
        text = '"Net sales increased 9%" [Exhibit 99.1 L4]'
        result = flow_desk.check_research({"Overview": text}, CONTEXT)
        self.assertEqual(result["status"], "fail")
        self.assertIn("quote not on cited line", result["problems"][0])

    def test_every_quote_before_a_citation_is_checked(self):
        text = '"We operate 912 warehouses" and "net sales increased 6%" [10-K L10]'
        result = flow_desk.check_research({"Overview": text}, CONTEXT)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["marks"][0]["quote"], "net sales increased 6%")

    def test_invented_number_fails(self):
        text = 'It runs "912 warehouses" [10-K L10] and will open 40 more.'
        result = flow_desk.check_research({"Overview": text}, CONTEXT)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("number 40" in p for p in result["problems"]))

    def test_model_formatting_is_normalized(self):
        raw = "“Net sales increased 6%”【10‑K L10】 and “912 warehouses”【Exhibit 99.1 L4】"
        result = flow_desk.check_research({"Overview": flow_desk.clean_format(raw)}, CONTEXT)
        self.assertEqual(result["citations"], 2)
        self.assertIn("Overview: [10-K L10] quote not on cited line", result["problems"])

    def test_short_range_and_shortened_label(self):
        context = {"10-K_excerpts": [{"source": "10-K", "line": 1, "text": "Long operating"},
                                     {"source": "10-K", "line": 2, "text": "cycles apply."}], "release": []}
        ok = flow_desk.check_research({"Overview": '"Long operating cycles apply." [10-K L1-L2]'}, context)
        self.assertEqual(ok["status"], "pass", ok["problems"])
        bad = flow_desk.check_research({"Overview": '"Long operating" [10-K L1-L9]'}, context)
        self.assertIn("line range longer than 5 lines", bad["problems"][0])
        label = flow_desk.check_research({"Overview": '"Net sales" [Exhibit 99 L4]'}, CONTEXT)
        self.assertIn("unknown source line", label["problems"][0])

    def test_shortened_quote_parts_must_be_on_line_in_order(self):
        ok = flow_desk.check_research({"Overview": '"Net sales ... $62.15 billion" [Exhibit 99.1 L4]'}, CONTEXT)
        self.assertEqual(ok["status"], "pass", ok["problems"])
        wrong_order = flow_desk.check_research({"Overview": '"$62.15 billion ... Net sales" [Exhibit 99.1 L4]'}, CONTEXT)
        self.assertEqual(wrong_order["status"], "fail")
        invented = flow_desk.check_research({"Overview": '"Net sales … fell sharply" [Exhibit 99.1 L4]'}, CONTEXT)
        self.assertEqual(invented["status"], "fail")

    def test_numbers_match_by_value(self):
        context = {"evidence_lines": [{"source": "Python evidence", "line": 1, "text": "Margin change: 0.10 percentage points"}]}
        result = flow_desk.check_research({"Overview": 'Up 0.1 points: "Margin change: 0.10" [Python evidence L1]'}, context)
        self.assertEqual(result["status"], "pass", result["problems"])

    def test_oversized_input_stops_before_model(self):
        with self.assertRaisesRegex(data.DeskError, "No model call was made"):
            flow_desk.check_size("x" * int(flow_desk.MAX_INPUT_TOKENS * flow_desk.CHARS_PER_TOKEN + 100))
        self.assertLessEqual(flow_desk.check_size("short"), flow_desk.MAX_INPUT_TOKENS)

    def test_unknown_line_and_missing_citation_fail(self):
        result = flow_desk.check_research({"Overview": '"warehouses" [10-K L99]', "Insight": "No source."}, CONTEXT)
        self.assertIn("Overview: [10-K L99] unknown source line", result["problems"])
        self.assertIn("Insight: no citations", result["problems"])


class PersonaTests(unittest.TestCase):
    def write(self, body):
        folder = Path(tempfile.mkdtemp())
        path = folder / "p.md"
        path.write_text(body, encoding="utf-8")
        return path

    def test_empty_template_uses_neutral_rules(self):
        template = "\n".join(f"## {part}\n" for part in flow_desk.PERSONA_PARTS)
        self.assertEqual(flow_desk.load_persona(self.write(template)), "")

    def test_partial_persona_stops(self):
        with self.assertRaises(data.DeskError):
            flow_desk.load_persona(self.write("## Identity\nA skeptic.\n"))

    def test_full_persona_loads(self):
        body = "".join(f"## {part}\nText for {part}.\n" for part in flow_desk.PERSONA_PARTS)
        self.assertIn("Scored criteria:\nText for Scored criteria.", flow_desk.load_persona(self.write(body)))


class FlowTests(unittest.TestCase):
    def make_run(self):
        runs = Path(tempfile.mkdtemp())
        folder = runs / "Test_Co__2026-11-03_10-00-00-000000-0500"
        folder.mkdir()
        manifest = {"company": {"ticker": "TST", "name": "Test Co", "cik": "1"},
                    "steps": {str(n): {"status": "complete"} for n in range(1, 8)}}
        row = {"accessionNumber": "0000000001-26-000001", "accepted": "2026-11-01", "index_url": "u", "document_url": "u"}
        files = {"manifest.json": manifest, "selected_filings.json": {"10-K": row, "8-K": row},
                 "documents.json": {"earnings_release": {"exhibit_label": "Exhibit 99.1"}}}
        for name, content in files.items():
            (folder / name).write_text(json.dumps(content), encoding="utf-8")
        (folder / "10-K.txt").write_text("Item 1. Business\nWe operate 912 warehouses worldwide.\n"
                                         "Item 7. MD&A\nMembership fees rose.\n", encoding="utf-8")
        (folder / "earnings_release.txt").write_text("Net sales increased 6% to $62.15 billion.\n", encoding="utf-8")
        from test_research_evidence import fixture
        report, raw = fixture()
        report["company"] = manifest["company"]
        for name, payload in {"facts.json": report, "companyfacts.json": raw, "peers.json": {},
                              "calculations.json": {"periods": report["periods"], "price_usd": None,
                                                    "calculations": data.calculate(report)}}.items():
            (folder / name).write_text(json.dumps(payload))
        return runs

    def run_flow(self, answers):
        runs, stub = self.make_run(), StubLLM(model="stub", answers=answers)
        with mock.patch.object(data, "RUNS", runs), \
                mock.patch.object(flow_desk.ResearchDeskFlow, "llm_factory", staticmethod(lambda: stub)), \
                mock.patch.object(flow_desk, "PERSONA_DIR", Path(tempfile.mkdtemp())):
            flow = flow_desk.ResearchDeskFlow()
            flow.kickoff(inputs={"ticker": "TST", "reuse": True})
        return flow, stub

    def test_flow_runs_offline_and_saves(self):
        flow, stub = self.run_flow([GOOD])
        self.assertEqual(flow.state.research_check["status"], "pass", flow.state.research_check["problems"])
        self.assertEqual(flow.state.attempts, 1)
        self.assertEqual(flow.state.research["future_developments"][0]["citation"], "10-K L4")
        text = (Path(flow.state.output_folder) / "research_analyst.md").read_text(encoding="utf-8")
        self.assertIn("Insight: Fee growth matters more than the headline suggests.", text)
        self.assertIn('- Fees rose. ("Membership fees rose." [10-K L4])', text)
        self.assertTrue((Path(flow.state.output_folder) / "research_context.json").exists())
        self.assertTrue((Path(flow.state.output_folder) / "research_model_input.json").exists())
        self.assertTrue((Path(flow.state.output_folder) / "evidence" / "facts.json").exists())
        payload = flow_desk.model_context(flow.state.research_context)
        self.assertNotIn("10-K_excerpts", payload)
        self.assertIn("financial_summary", payload)
        self.assertIn("[10-K L2] We operate 912 warehouses worldwide.", payload["evidence_lines"])

    def test_failed_draft_is_sent_back_once_with_its_problems(self):
        flow, stub = self.run_flow([BAD, GOOD])
        self.assertEqual(flow.state.attempts, 2)
        self.assertEqual([h["check"]["status"] for h in flow.state.history], ["fail", "pass"])
        self.assertEqual(flow.state.research_check["status"], "pass")
        self.assertNotIn("SEND-BACK", stub.prompts[0])
        self.assertIn("SEND-BACK", stub.prompts[-1])
        self.assertIn("quote not on cited line", stub.prompts[-1])

    def test_send_back_stops_after_two_attempts(self):
        flow, stub = self.run_flow([BAD, BAD, GOOD])
        self.assertEqual(flow.state.attempts, 2)
        self.assertEqual(flow.state.research_check["status"], "fail")
        text = (Path(flow.state.output_folder) / "research_analyst.md").read_text(encoding="utf-8")
        self.assertIn("## Check problems", text)
        self.assertIn("after 2 attempt(s)", text)

    def test_failed_send_back_keeps_first_draft(self):
        flow, stub = self.run_flow([BAD, "RAISE"])
        self.assertEqual(flow.state.attempts, 2)
        self.assertEqual(flow.state.research["overview"][0]["quote"], "We operate 950 warehouses")
        text = (Path(flow.state.output_folder) / "research_analyst.md").read_text(encoding="utf-8")
        self.assertIn("Send-back attempt failed", text)
        self.assertIn("keeps the previous draft", text)

    def test_schema_requires_quote_and_citation(self):
        with self.assertRaises(ValueError):
            flow_desk.ResearchSections.model_validate({**json.loads(GOOD), "overview": [{"claim": "No quote."}]})

    def test_prepare_only_never_calls_model(self):
        with tempfile.TemporaryDirectory() as temp:
            context = {"company": {"ticker": "TST"}}
            def gather(flow):
                self.assertEqual(flow.state.ticker, "TST")
                self.assertTrue(flow.state.reuse)
                flow.state.run_folder = temp
                flow.state.research_context = context
            with mock.patch.object(flow_desk.ResearchDeskFlow, "gather_filings", gather), \
                    mock.patch.object(flow_desk.ResearchDeskFlow, "llm_factory", side_effect=AssertionError("model called")), \
                    mock.patch.object(flow_desk, "build_message", return_value="short"), \
                    mock.patch.object(flow_desk, "save_context") as save:
                self.assertEqual(flow_desk.main(["TST", "--reuse", "--prepare-only"]), 0)
                self.assertEqual(save.call_args.args[2], context)


if __name__ == "__main__":
    unittest.main()
