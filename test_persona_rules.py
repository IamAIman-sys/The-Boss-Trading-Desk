"""Offline tests for the Investment Advisor persona's rules, applied in code."""
import unittest

import flow_desk
import persona_rules as rules


def context(npm=("55.60", "-0.44"), median=None, coverage="503.42", ocf=("47.57", "-3.14")):
    rows = [f"TST current Net profit margin; period={{'start': '2025-01-01', 'end': '2025-12-31'}}: {npm[0]} %; formula: x",
            f"TST prior-year change, Net profit margin: a vs b; change c percentage points; relative change {npm[1]} % of the size",
            f"TST current Operating cash flow margin; period={{'start': '2025-01-01', 'end': '2025-12-31'}}: {ocf[0]} %; formula: x",
            f"TST prior-year change, Operating cash flow margin: a vs b; change c; relative change {ocf[1]} % of the size"]
    if coverage is not None:
        rows.append(f"TST current Interest coverage; period={{'start': '2025-01-01', 'end': '2025-12-31'}}: {coverage} x; formula: x")
    rows.append(f"Peer median current Net profit margin: {median} %; peers: A" if median else
                "Peer median current Net profit margin: unavailable (no peer)")
    return {"company": {"ticker": "TST"},
            "evidence_lines": [{"source": "Python evidence", "line": n, "text": t} for n, t in enumerate(rows, 1)]}


def numbers(text):
    return {flow_desk._digits(t) for t in flow_desk.claimed_numbers(text)}


class ExpectationTests(unittest.TestCase):
    def test_persona_text_is_the_one_these_rules_were_written_for(self):
        self.assertEqual(rules.criteria_sha(), rules.PERSONA_SHA)

    def test_band_makes_a_small_change_hold_and_cash_flow_does_not_override(self):
        self.assertEqual(rules.expectation(context())["allowed"], {"Hold"})

    def test_band_edges(self):
        self.assertEqual(rules.expectation(context(npm=("5", "2.00")))["allowed"], {"Hold"})
        self.assertEqual(rules.expectation(context(npm=("5", "2.01")))["allowed"], {"Buy"})
        self.assertEqual(rules.expectation(context(npm=("5", "-7.78")))["allowed"], {"Sell"})

    def test_peer_median_rules(self):
        self.assertEqual(rules.expectation(context(npm=("12.83", "10"), median="14.89"))["allowed"], {"Hold"})
        self.assertEqual(rules.expectation(context(npm=("15", "10"), median="14.89"))["allowed"], {"Buy"})
        self.assertEqual(rules.expectation(context(npm=("10", "-10"), median="14.89"))["allowed"], {"Sell"})

    def test_coverage_blocks(self):
        self.assertEqual(rules.expectation(context(npm=("5", "9"), coverage="1.2"))["allowed"], {"Hold"})
        self.assertEqual(rules.expectation(context(npm=("5", "9"), coverage="0.8"))["allowed"], {"Hold", "Sell"})
        self.assertEqual(rules.expectation(context(npm=("5", "0"), coverage="0.8"))["allowed"], {"Sell"})
        self.assertEqual(rules.expectation(context(npm=("5", "9"), coverage="1.50"))["allowed"], {"Buy"})
        self.assertEqual(rules.expectation(context(npm=("5", "9"), coverage=None))["allowed"], {"Buy", "Hold"})

    def test_negative_cash_flow_margin_blocks_buy(self):
        result = rules.expectation(context(npm=("5", "9"), ocf=("-1.0", "-50")))
        self.assertEqual(result["allowed"], {"Hold"})
        self.assertIn("Operating cash flow margin", [name for name, _, _ in result["deciding"]])

    def test_no_net_margin_means_no_check(self):
        self.assertIsNone(rules.expectation({"company": {"ticker": "TST"}, "evidence_lines": []}))


class AdvisorProblemTests(unittest.TestCase):
    def output(self, recommendation, deciding):
        return {"recommendation": recommendation,
                "deciding_number": {"claim": deciding, "quote": deciding, "citation": "Python evidence L1"}}

    def test_off_rule_answer_is_sent_back_with_the_reason(self):
        problems = rules.advisor_problems(self.output("Sell", "Cash-flow margin is 47.57 % (current quarter)"),
                                          context(), numbers)
        self.assertEqual(len(problems), 3)
        self.assertIn("must be Hold, not Sell", problems[0])
        self.assertIn("within ±2%", problems[0])
        self.assertIn("Net profit margin 55.60 [Python evidence L1]", problems[1])
        self.assertIn("quarter", problems[2])

    def test_answer_that_follows_the_rules_passes(self):
        self.assertEqual(rules.advisor_problems(self.output("Hold", "Net profit margin is 55.60 % for fiscal 2025"),
                                                context(), numbers), [])


if __name__ == "__main__":
    unittest.main()
