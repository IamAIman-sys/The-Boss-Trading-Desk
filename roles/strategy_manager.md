<!-- Strategy Manager instructions. The Strategy Manager is code, not a model call:
flow_desk.py reads the required parts from the list below and applies each check.
A model never decides which node runs next. -->
# Strategy Manager

## Required parts

- Overview
- Market Positioning and Growth Outlook
- Valuation Insights
- Future Developments and Strategic Recommendations
- Investment Recommendation

## Owners

- Research Analyst: Overview; Market Positioning and Growth Outlook; Future Developments and Strategic Recommendations
- Financial Analyst: Valuation Insights
- Investment Advisor: Investment Recommendation

## Checks, in code

1. Present: each part has at least one claim, and the Investment Recommendation
   has Buy, Hold or Sell, a thesis and a deciding number.
2. Sourced: every claim has a quote and a citation; the quote is on the cited
   line; every number in the claim is on that line.
3. Insight: each role's Insight line states a number that is on a line its
   insight_evidence cites.
4. Financial Analyst: one review flag quotes the Python review-signal line;
   Peer Comparison is not empty when peers were supplied.
5. Consistent: the Investment Advisor cites only lines that an analyst cited,
   its deciding number is on its cited line, and its thesis states no number
   except the deciding number.

## Send-back

If a part fails a check, the Manager sends that part back to its owner one
time, with the list of problems. No role runs more than two times in one run.
Then the Manager compiles the report, and the Verifier runs on it.
