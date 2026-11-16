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
    """Per role, returns queued JSON answers in order (the last one repeats); records each prompt."""
    answers: dict[str, list[str]] = {}
    prompts: list[str] = []

    @staticmethod
    def role_of(prompt):
        if "You are the Investment Advisor" in prompt:
            return "advisor"
        return "financial" if "You are the Financial Analyst" in prompt else "research"

    def call(self, messages, tools=None, callbacks=None, available_functions=None,
             from_task=None, from_agent=None, response_model=None, **kwargs):
        prompt = messages if isinstance(messages, str) else json.dumps(messages)
        self.prompts.append(prompt)
        role = self.role_of(prompt)
        queue = self.answers[role]
        count = sum(self.role_of(p) == role for p in self.prompts)
        answer = queue[min(count, len(queue)) - 1]
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
    "insight": "Scale across 912 warehouses matters more than the headline suggests.",
    "insight_evidence": [claim("The network is large.", "We operate 912 warehouses worldwide.", "10-K L2"),
                         claim("Fees rose.", "Membership fees rose.", "10-K L4")]})
def advisor_answer(**changes):
    """An Investment Advisor answer that copies only claims from GOOD."""
    network = claim("The network has 912 warehouses.", "We operate 912 warehouses worldwide.", "10-K L2")
    fees = claim("Fees rose.", "Membership fees rose.", "10-K L4")
    return json.dumps({"recommendation": "Hold",
                       "thesis": "Scale supports the business, but fee growth still needs proof.",
                       "deciding_number": network, "support": [network], "risks": [fees],
                       "what_would_change": "A filing that shows fee growth would move the view up one step.",
                       "insight": "Fee growth rests on a base of 912 warehouses.",
                       "insight_evidence": [network], **changes})


BAD = json.dumps({**json.loads(GOOD), "overview": [claim("It runs 950 stores.", "We operate 950 warehouses", "10-K L2")]})


def tag(context, start):
    """Citation tag of the first evidence line that starts with the given text."""
    return next(f"{r['source']} L{r['line']}" for r in context["evidence_lines"] if r["text"].startswith(start))


def financial_answer(context, flag=True, invent=False):
    """A Financial Analyst answer built from the fixture's Python evidence lines."""
    def py(text, quote):
        return claim(text, quote, tag(context, quote))
    # The quote holds no number, so a claim with a number must fail the check.
    margin = py("The margin rose 18 points." if invent else "The current operating margin is stated with its formula.",
                "TST current Operating margin; period=")
    flags = [py("Both review signals are True.", "Annual operating-margin change: 5.00 percentage points")] if flag \
        else [py("Debt is calculated.", "TST current Debt; period=")]
    return json.dumps({
        "operating_margin": [margin],
        "profitability_and_cash": [py("Net margin is calculated.", "TST current Net profit margin; period=")],
        "debt_and_coverage": [py("Coverage is calculated.", "TST current Interest coverage; period=")],
        "peer_comparison": [],
        "review_flags": flags,
        "insight": "Leverage rose while the margin moved 5.00 percentage points, so the gain needs a cause.",
        "insight_evidence": [py("Debt is calculated.", "TST current Debt; period="),
                             py("The margin moved.", "Annual operating-margin change: 5.00 percentage points")]})


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


class YearTests(unittest.TestCase):
    """A year names a period; the check does not treat it as a claimed amount."""
    def test_years_are_not_claimed_numbers(self):
        self.assertEqual(flow_desk.claimed_numbers("Opened 28 in 2026 (FY2025-2026, FY 2024)."), ["28"])

    def test_amounts_that_look_like_years_are_kept(self):
        self.assertEqual(flow_desk.claimed_numbers("$2026 and 2,026 and 2026% and 2026 million"),
                         ["$2026", "2,026", "2026%", "2026"])

    def test_claim_with_a_year_passes_when_its_amount_is_on_the_line(self):
        text = 'Costs rose in 2026: "Net sales increased 6% to $62.15 billion." [Exhibit 99.1 L4]'
        self.assertEqual(flow_desk.check_research({"Overview": text}, CONTEXT)["status"], "pass")

    def test_wrong_amount_still_fails_beside_a_year(self):
        text = 'Sales rose 7% in 2026: "Net sales increased 6% to $62.15 billion." [Exhibit 99.1 L4]'
        self.assertEqual(flow_desk.check_research({"Overview": text}, CONTEXT)["status"], "fail")


class QuoteRepairTests(unittest.TestCase):
    """Change 1: a near-miss quote gets the cited line's exact words; nothing else is changed."""
    LINE = "Membership fee revenue increased 11% to $5,907, driven by upgrades to Executive membership;"

    def test_near_miss_is_repaired(self):
        fixed = flow_desk.repair_quote("Membership fee revenue increased 11% to $5,907, driven by upgrades to Executive memberships", self.LINE)
        self.assertEqual(fixed[0], "Membership fee revenue increased 11% to $5,907, driven by upgrades to Executive membership;")
        self.assertGreaterEqual(fixed[1], flow_desk.REPAIR_MIN_SIMILARITY)

    def test_extra_words_before_the_line_start_do_not_crash(self):
        # The longest match is at the line's start, but the quote has words before it.
        self.assertIsNone(flow_desk.repair_quote("In the year, we said that Membership fee revenue increased 11%", self.LINE[:40]))
        fixed = flow_desk.repair_quote("The Membership fee revenue increased 11% to $5,907, driven by upgrades to Executive membership;", self.LINE)
        self.assertEqual(fixed[0], self.LINE)

    def test_advisor_quote_is_copied_from_the_analyst(self):
        context = {"evidence_lines": [{"source": "Python evidence", "line": 4, "text": "X current Net profit margin: 3.78 %; formula: a / b"}]}
        analyst = {"profitability_and_cash": [claim("Margin.", "X current Net profit margin: 3.78 %", "Python evidence L4")]}
        advisor = {"deciding_number": claim("Net margin is 3.78%.", "Current net profit margin is 3.78% for FY2026.", "Python evidence L4")}
        log = flow_desk.copy_analyst_quotes(advisor, [analyst], context)
        self.assertEqual(advisor["deciding_number"]["quote"], "X current Net profit margin: 3.78 %")
        self.assertEqual(log[0]["similarity"], "copied from the analyst")

    def test_changed_number_is_never_repaired(self):
        self.assertIsNone(flow_desk.repair_quote("Membership fee revenue increased 12% to $5,907, driven by upgrades", self.LINE))

    def test_different_statement_is_not_repaired(self):
        self.assertIsNone(flow_desk.repair_quote("Gasoline prices raised sales by $3,501 million", self.LINE))

    def test_each_part_around_skipped_words_is_repaired(self):
        fixed = flow_desk.repair_quote("Membership fee revenue increased 11% ... upgrades to Executive memberships", self.LINE)
        self.assertEqual(fixed[0], "Membership fee revenue increased 11% ... upgrades to Executive membership;")

    def test_long_unmarked_gap_is_not_repaired(self):
        self.assertIsNone(flow_desk.repair_quote("Membership fee revenue driven by Executive membership", self.LINE))

    def test_repair_claims_logs_and_fixes_in_place(self):
        context = {"evidence_lines": [{"source": "10-K", "line": 7, "text": self.LINE}]}
        output = {"overview": [claim("Fees rose 11%.", "Membership fee revenue increased 11% to $5,907, driven by upgrades to Executive memberships", "10-K L7")]}
        log = flow_desk.repair_claims(output, context)
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["citation"], "10-K L7")
        self.assertEqual(flow_desk.check_research(flow_desk.render_sections(output, {"overview": "Overview"}), context)["problems"],
                         ["Insight: no citations"])  # the repaired claim passes; only the empty Insight remains


class CheckInsightTests(unittest.TestCase):
    """Week 3: the Insight line states a number that the Verifier can check at its line."""
    CONTEXT = {"evidence_lines": [
        {"source": "10-K", "line": 10, "text": "We operate 912 warehouses worldwide."},
        {"source": "Exhibit 99.1", "line": 4, "text": "Net sales increased 6% to $62.15 billion."}]}

    def output(self, sentence):
        return {"insight": sentence,
                "insight_evidence": [claim("Sales grew.", "Net sales increased 6%", "Exhibit 99.1 L4"),
                                     claim("Network.", "We operate 912 warehouses", "10-K L10")]}

    def test_number_on_an_evidence_line_passes_and_gives_its_tag(self):
        result = flow_desk.check_insight(self.output("Growth of 6% rests on 912 warehouses."), self.CONTEXT)
        self.assertEqual(result["problems"], [])
        self.assertEqual(result["insight_citation"], "Exhibit 99.1 L4")
        self.assertEqual(result["insight_citations"], ["Exhibit 99.1 L4", "10-K L10"])
        run = flow_desk.RoleRun(output=self.output("Growth of 6% rests on 912 warehouses."), check=result)
        self.assertEqual(flow_desk.insight_line(run), "Insight: Growth of 6% rests on 912 warehouses [Exhibit 99.1 L4] [10-K L10].")

    def test_sentence_without_a_number_fails(self):
        result = flow_desk.check_insight(self.output("Growth rests on the network."), self.CONTEXT)
        self.assertIn("states no number", result["problems"][0])

    def test_number_not_on_any_evidence_line_fails(self):
        result = flow_desk.check_insight(self.output("Growth of 7% rests on the network."), self.CONTEXT)
        self.assertEqual(result["problems"],
                         ["Insight: number 7% is not on any line that an insight_evidence claim cites"])

    def test_number_only_on_an_uncited_line_fails(self):
        output = {"insight": "The network has 912 warehouses.",
                  "insight_evidence": [claim("Sales grew.", "Net sales increased 6%", "Exhibit 99.1 L4")]}
        self.assertTrue(flow_desk.check_insight(output, self.CONTEXT)["problems"])

    def test_research_output_check_includes_the_insight(self):
        output = {**json.loads(GOOD), "insight": "No number here."}
        result = flow_desk.check_research_output(output, {"evidence_lines": [
            {"source": "10-K", "line": 2, "text": "We operate 912 warehouses worldwide."},
            {"source": "10-K", "line": 4, "text": "Membership fees rose."}]})
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any(p.startswith("Insight: the sentence states no number") for p in result["problems"]))


class FitContextTests(unittest.TestCase):
    """Excerpts get shorter, in steps, until one send-back fits the input limit."""
    def fake_build(self, sizes):
        def build(folder, peers, manifest, chars):
            sizes.append(chars)
            return {"availability": {}, "excerpt_chars": chars}
        return build

    def fake_message(self, context, persona, rules=None):
        return "x" * int(context["excerpt_chars"] * 2 * flow_desk.CHARS_PER_TOKEN)  # tokens = 2 x chars

    def test_shortens_until_the_reserve_fits(self):
        sizes = []
        limit = 2 * 20000 + flow_desk.SEND_BACK_RESERVE_TOKENS
        with mock.patch.object(flow_desk, "build_research_context", self.fake_build(sizes)), \
                mock.patch.object(flow_desk, "build_message", self.fake_message), \
                mock.patch.object(flow_desk, "MAX_INPUT_TOKENS", limit):
            context = flow_desk.fit_context("run", None, None, {})
        self.assertEqual(sizes, [25000, 22500, 20000])
        self.assertIn("shortened from 25,000 to 20,000", context["availability"]["excerpt_size"])

    def test_full_excerpts_when_they_fit(self):
        sizes = []
        with mock.patch.object(flow_desk, "build_research_context", self.fake_build(sizes)), \
                mock.patch.object(flow_desk, "build_message", self.fake_message), \
                mock.patch.object(flow_desk, "MAX_INPUT_TOKENS", 10 ** 6):
            context = flow_desk.fit_context("run", None, None, {})
        self.assertEqual(sizes, [25000])
        self.assertNotIn("excerpt_size", context["availability"])

    def test_stops_at_the_minimum(self):
        sizes = []
        with mock.patch.object(flow_desk, "build_research_context", self.fake_build(sizes)), \
                mock.patch.object(flow_desk, "build_message", self.fake_message), \
                mock.patch.object(flow_desk, "MAX_INPUT_TOKENS", 10):
            flow_desk.fit_context("run", None, None, {})
        self.assertEqual(sizes[-1], flow_desk.MIN_EXCERPT_CHARS)


class CheckFinancialTests(unittest.TestCase):
    CONTEXT = {"evidence_lines": [
        {"source": "Python evidence", "line": 1, "text": "TST current Operating margin: 15.00 %"},
        {"source": "Python evidence", "line": 2, "text": "Annual operating-margin change: 5.00 percentage points; high-priority review=True"}],
        "financial_evidence": {"peers": {}}}

    def answer(self, **changes):
        ok = claim("Margin is stated.", "TST current Operating margin", "Python evidence L1")
        flag = claim("Review is triggered.", "high-priority review=True", "Python evidence L2")
        return {"operating_margin": [ok], "profitability_and_cash": [ok], "debt_and_coverage": [ok],
                "peer_comparison": [], "review_flags": [flag], "insight": "A 15.00 % margin needs a cause.", "insight_evidence": [ok],
                **changes}

    def test_clean_answer_without_peers_passes(self):
        result = flow_desk.check_financial(self.answer(), self.CONTEXT)
        self.assertEqual(result["status"], "pass", result["problems"])

    def test_missing_signal_flag_fails(self):
        other = claim("Margin is stated.", "TST current Operating margin", "Python evidence L1")
        result = flow_desk.check_financial(self.answer(review_flags=[other]), self.CONTEXT)
        self.assertEqual(result["status"], "fail")
        self.assertIn("Review Flags: no flag quotes the review-signal line [Python evidence L2]", result["problems"])

    def test_empty_peer_section_fails_when_peers_were_supplied(self):
        context = {**self.CONTEXT, "financial_evidence": {"peers": {"PEER": {}}}}
        result = flow_desk.check_financial(self.answer(), context)
        self.assertIn("Peer Comparison: empty, but peer evidence was supplied", result["problems"])

    def test_seeded_wrong_number_in_flag_fails(self):
        flag = claim("The change is 7 points.", "Annual operating-margin change: 5.00", "Python evidence L2")
        result = flow_desk.check_financial(self.answer(review_flags=[flag]), self.CONTEXT)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("number not on cited line" in p for p in result["problems"]), result["problems"])


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

    def run_flow(self, research, financial=None, persona_dir=None, advisor=None):
        """financial: a function of the context that returns the Financial Analyst's answers."""
        runs = self.make_run()
        context = flow_desk.build_research_context(next(runs.iterdir()))
        answers = {"research": research, "financial": (financial or (lambda c: [financial_answer(c)]))(context),
                   "advisor": advisor or [advisor_answer()]}
        stub = StubLLM(model="stub", answers=answers)
        with mock.patch.object(data, "RUNS", runs), \
                mock.patch.object(flow_desk.ResearchDeskFlow, "llm_factory", staticmethod(lambda: stub)), \
                mock.patch.object(flow_desk, "PERSONA_DIR", persona_dir or Path(tempfile.mkdtemp())):
            flow = flow_desk.ResearchDeskFlow()
            flow.kickoff(inputs={"ticker": "TST", "reuse": True})
        return flow, stub

    def prompts(self, stub, role):
        return [p for p in stub.prompts if StubLLM.role_of(p) == role]

    def test_flow_runs_offline_and_saves(self):
        flow, stub = self.run_flow([GOOD])
        research = flow.state.research
        self.assertEqual(research.check["status"], "pass", research.check["problems"])
        self.assertEqual(research.attempts, 1)
        self.assertEqual(research.output["future_developments"][0]["citation"], "10-K L4")
        text = (Path(flow.state.output_folder) / "research_analyst.md").read_text(encoding="utf-8")
        self.assertIn("Insight: Scale across 912 warehouses matters more than the headline suggests [10-K L2].", text)
        self.assertIn('- Fees rose ("Membership fees rose." [10-K L4]).', text)
        self.assertTrue((Path(flow.state.output_folder) / "research_context.json").exists())
        self.assertTrue((Path(flow.state.output_folder) / "research_model_input.json").exists())
        self.assertTrue((Path(flow.state.output_folder) / "evidence" / "facts.json").exists())
        payload = flow_desk.model_context(flow.state.research_context)
        self.assertNotIn("10-K_excerpts", payload)
        self.assertIn("financial_summary", payload)
        self.assertIn("[10-K L2] We operate 912 warehouses worldwide.", payload["evidence_lines"])

    def test_failed_draft_is_sent_back_once_with_its_problems(self):
        flow, stub = self.run_flow([BAD, GOOD])
        research = flow.state.research
        self.assertEqual(research.attempts, 2)
        self.assertEqual([h["check"]["status"] for h in research.history], ["fail", "pass"])
        self.assertEqual(research.check["status"], "pass")
        prompts = self.prompts(stub, "research")
        self.assertNotIn("SEND-BACK", prompts[0])
        self.assertIn("SEND-BACK", prompts[-1])
        self.assertIn("quote not on cited line", prompts[-1])

    def test_send_back_stops_after_two_attempts(self):
        flow, stub = self.run_flow([BAD, BAD, GOOD])
        self.assertEqual(flow.state.research.attempts, 2)
        self.assertEqual(flow.state.research.check["status"], "fail")
        text = (Path(flow.state.output_folder) / "research_analyst.md").read_text(encoding="utf-8")
        self.assertIn("## Check problems", text)
        self.assertIn("after 2 attempt(s)", text)

    def test_failed_send_back_keeps_first_draft(self):
        flow, stub = self.run_flow([BAD, "RAISE"])
        self.assertEqual(flow.state.research.attempts, 2)
        self.assertEqual(flow.state.research.output["overview"][0]["quote"], "We operate 950 warehouses")
        text = (Path(flow.state.output_folder) / "research_analyst.md").read_text(encoding="utf-8")
        self.assertIn("Send-back attempt failed", text)
        self.assertIn("keeps the previous draft", text)

    def test_failed_first_call_is_sent_back_once(self):
        flow, stub = self.run_flow(["RAISE", GOOD])
        research = flow.state.research
        self.assertEqual(research.attempts, 2)
        self.assertEqual(research.check["status"], "pass", research.check["problems"])
        self.assertEqual(research.call_error, "")
        self.assertIn("First attempt failed: length limit was reached", self.prompts(stub, "research")[-1])
        self.assertTrue((Path(flow.state.verified_folder) / "verified_report.md").exists())

    def test_failed_first_and_second_call_still_compiles_and_verifies(self):
        flow, stub = self.run_flow(["RAISE", "RAISE"])
        self.assertEqual(flow.state.research.attempts, 2)
        self.assertEqual(flow.state.research.check["status"], "fail")
        report = (Path(flow.state.output_folder) / "report.md").read_text(encoding="utf-8")
        self.assertIn("## Remaining review items", report)
        self.assertTrue((Path(flow.state.verified_folder) / "verified_report.md").exists())

    def test_near_miss_quote_is_repaired_and_logged(self):
        near = json.dumps({**json.loads(GOOD), "overview": [claim("The network is large.", "We operate 912 warehouse worldwide.", "10-K L2")]})
        flow, stub = self.run_flow([near])
        research = flow.state.research
        self.assertEqual(research.attempts, 1)
        self.assertEqual(research.check["status"], "pass", research.check["problems"])
        self.assertEqual(research.repairs[0]["new"], "We operate 912 warehouses worldwide.")
        saved = json.loads((Path(flow.state.output_folder) / "research_analyst.json").read_text(encoding="utf-8"))
        self.assertEqual(len(saved["quote_repairs"]), 1)
        self.assertIn("Quote repairs made in code: 1", (Path(flow.state.output_folder) / "report.md").read_text(encoding="utf-8"))

    def test_failed_claims_leave_the_report_body(self):
        flow, stub = self.run_flow([BAD, BAD])
        report = (Path(flow.state.output_folder) / "report.md").read_text(encoding="utf-8")
        body, review = report.split("## Remaining review items", 1)
        self.assertNotIn("950 warehouses", body)
        self.assertIn("Research Analyst / Overview: removed from the report: It runs 950 stores", review)
        self.assertIn("Overview\n\nNone passed the Strategy Manager's check.", body)

    def test_schema_requires_quote_and_citation(self):
        with self.assertRaises(ValueError):
            flow_desk.ResearchSections.model_validate({**json.loads(GOOD), "overview": [{"claim": "No quote."}]})

    def test_financial_analyst_runs_after_research_and_saves(self):
        flow, stub = self.run_flow([GOOD])
        financial = flow.state.financial
        self.assertEqual(financial.check["status"], "pass", financial.check["problems"])
        self.assertEqual(financial.attempts, 1)
        self.assertEqual([StubLLM.role_of(p) for p in stub.prompts], ["research", "financial", "advisor"])
        self.assertIn("You are the Research Analyst", stub.prompts[0])
        self.assertIn("Your work is qualitative", stub.prompts[0])
        self.assertIn("Your work is quantitative", stub.prompts[1])
        text = (Path(flow.state.output_folder) / "financial_analyst.md").read_text(encoding="utf-8")
        self.assertIn("# Financial Analyst draft: Test Co (TST)", text)
        self.assertIn("## Review Flags", text)
        self.assertIn("Annual operating-margin change: 5.00 percentage points", text)
        self.assertIn("Peer Comparison\n\nNone supplied.", text)
        saved = json.loads((Path(flow.state.output_folder) / "financial_analyst.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["check"]["status"], "pass")

    def test_financial_missing_signal_flag_is_sent_back_once(self):
        flow, stub = self.run_flow([GOOD], lambda c: [financial_answer(c, flag=False), financial_answer(c)])
        financial = flow.state.financial
        self.assertEqual(financial.attempts, 2)
        self.assertEqual([h["check"]["status"] for h in financial.history], ["fail", "pass"])
        prompts = self.prompts(stub, "financial")
        self.assertIn("no flag quotes the review-signal line", prompts[-1])
        self.assertEqual(flow.state.research.attempts, 1)  # a Financial Analyst send-back never reruns research

    def test_financial_invented_number_fails_after_two_attempts(self):
        flow, stub = self.run_flow([GOOD], lambda c: [financial_answer(c, invent=True)])
        financial = flow.state.financial
        self.assertEqual(financial.attempts, 2)
        self.assertEqual(financial.check["status"], "fail")
        self.assertTrue(any("number 18" in p for p in financial.check["problems"]), financial.check["problems"])

    def test_financial_persona_is_sent(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "financial_analyst.md").write_text(
            "".join(f"## {part}\nFA {part}.\n" for part in flow_desk.PERSONA_PARTS), encoding="utf-8")
        flow, stub = self.run_flow([GOOD], persona_dir=folder)
        self.assertIn("FA Scored criteria.", self.prompts(stub, "financial")[0])
        self.assertNotIn("FA Scored criteria.", self.prompts(stub, "research")[0])
        self.assertEqual(flow.state.financial.persona, "student persona")
        self.assertEqual(flow.state.research.persona, "neutral rules (persona file empty)")

    def test_graph_compiles_five_parts_and_always_verifies(self):
        flow, stub = self.run_flow([GOOD])
        out = Path(flow.state.output_folder)
        report = (out / "report.md").read_text(encoding="utf-8")
        positions = [report.index("## " + part) for part in flow_desk.PARTS]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(report.startswith("Test Co (TST); filings read: 10-K 0000000001-26-000001"))
        self.assertIn("Recommendation: **Hold**", report)
        self.assertIn("Insight: Fee growth rests on a base of 912 warehouses [10-K L2].", report)
        self.assertIn("### Python evidence (code-generated, unchanged)", report)
        self.assertTrue((Path(flow.state.verified_folder) / "verified_report.md").exists())
        self.assertTrue((out / "strategy_manager.json").exists() and (out / "advisor_input.json").exists())
        self.assertEqual(flow.state.manager[-1]["next"], "report_ready")
        self.assertEqual(flow.state.advisor.check["status"], "pass", flow.state.advisor.check["problems"])
        # The Verifier rebuilds the Python evidence lines from the saved facts; they equal what the roles saw.
        rebuilt = flow_desk.verifier.Run(out, "report.md", out / "evidence").texts["Python evidence"]
        sent = [r["text"] for r in flow.state.research_context["evidence_lines"] if r["source"] == "Python evidence"]
        self.assertTrue(sent)
        self.assertEqual(rebuilt, sent)

    def test_advisor_sees_only_the_analysts_outputs(self):
        flow, stub = self.run_flow([GOOD])
        prompt = self.prompts(stub, "advisor")[0]
        self.assertIn("research_analyst", prompt)
        self.assertIn("financial_analyst", prompt)
        self.assertNotIn("evidence_lines", prompt)

    def test_advisor_new_fact_is_sent_back_once(self):
        new_fact = claim("Sales rose 6%.", "Net sales increased 6%", "Exhibit 99.1 L1")
        flow, stub = self.run_flow([GOOD], advisor=[advisor_answer(support=[new_fact]), advisor_answer()])
        advisor = flow.state.advisor
        self.assertEqual(advisor.attempts, 2)
        self.assertEqual([h["check"]["status"] for h in advisor.history], ["fail", "pass"])
        self.assertIn("no analyst cited", self.prompts(stub, "advisor")[-1])
        self.assertEqual(flow.state.research.attempts, 1)

    def test_advisor_number_in_thesis_fails_after_two_attempts(self):
        flow, stub = self.run_flow([GOOD], advisor=[advisor_answer(thesis="Growth of 9% is likely.")])
        self.assertEqual(flow.state.advisor.attempts, 2)
        self.assertTrue(any("Thesis: number 9%" in p for p in flow.state.advisor.check["problems"]))
        report = (Path(flow.state.output_folder) / "report.md").read_text(encoding="utf-8")
        self.assertIn("## Remaining review items", report)

    def test_no_role_runs_more_than_twice(self):
        flow, stub = self.run_flow([BAD], lambda c: [financial_answer(c, flag=False)],
                                   advisor=[advisor_answer(thesis="Up 9%.")])
        counts = {role: sum(StubLLM.role_of(p) == role for p in stub.prompts) for role in ("research", "financial", "advisor")}
        self.assertEqual(counts, {"research": 2, "financial": 2, "advisor": 2})
        self.assertEqual(flow.state.manager[-1]["next"], "report_ready")

    def test_manager_parts_come_from_its_role_file(self):
        self.assertEqual(flow_desk.PARTS, ("Overview", "Market Positioning and Growth Outlook", "Valuation Insights",
                                           "Future Developments and Strategic Recommendations", "Investment Recommendation"))
        for name in ("research_analyst.md", "financial_analyst.md", "investment_advisor.md", "strategy_manager.md"):
            self.assertTrue((flow_desk.ROLES_DIR / name).exists(), name)

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
