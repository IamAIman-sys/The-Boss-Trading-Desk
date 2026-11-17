TYSON FOODS, INC. (TSN); filings read: 10-K 0000100493-26-000079 (primary document); 8-K 0000100493-26-000077 (primary document and Exhibit 99.1); 10-Q 0000100493-26-000058 (primary document)
Report run time: 2026-11-17T18:26:51.403323-05:00

Model: `gpt-oss:120b` via Purdue GenAI Studio. Graph: crewAI Flow (flow_desk.py).
Personas: Research Analyst: student persona; Financial Analyst: student persona; Investment Advisor: student persona.
Strategy Manager (code): Research Analyst fail after 2 attempt(s); Financial Analyst fail after 2 attempt(s); Investment Advisor pass after 2 attempt(s).
Quote repairs made in code: 3 (each is listed in the role's JSON file). Claims that failed the check are not in the five parts; see Remaining review items.
Status: DRAFT. Human audit and partner checks are pending.

## Overview

- Tyson Foods, Inc. is a world-class food company and recognized leader in protein ("Tyson Foods, Inc. ... is a world-class food company and recognized leader in protein." [10-K L92]).
- The company operates in five reportable segments: Beef, Pork, Chicken, Prepared Foods and International ("We operate in five reportable segments: Beef, Pork, Chicken, Prepared Foods and International." [10-K L99]).
- Sales grew 3.6%, or $2.0 billion, in fiscal 2026 ("Sales grew 3.6%, or $2.0 billion, in fiscal 2026" [10-K L406]).
- Total Company GAAP operating margin was 1.9% in fiscal 2026 ("Our total operating margin was 1.9% in fiscal 2026" [10-K L414]).

## Market Positioning and Growth Outlook

- Exports account for less than 10% of Tyson’s business ("Our exports account for less than 10% of our business" [10-K L412]).
- Beef segment faces limited supply of market-ready cattle and higher cattle costs ("The Beef segment continues to experience limited supply of market-ready cattle and higher cattle costs" [10-K L410]).
- Chicken segment experienced increased feed-ingredient costs in fiscal 2026 ("The Chicken segment experienced increased feed ingredient costs in fiscal 2026" [10-K L410]).
- Pork segment continues to experience adequate supplies of market-ready hogs and lower hog costs ("The Pork segment continues to experience adequate supplies of market-ready hogs and lower hog costs" [10-K L410]).
- Prepared Foods segment experienced higher raw-material costs in fiscal 2026 ("The Prepared Foods segment experienced higher raw material costs in fiscal 2026" [10-K L410]).

## Valuation Insights

### Operating Margin

- Current operating margin is 1.95% for fiscal 2026 ("TSN current Operating margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 1.95 %" [Python evidence L1]).
- Prior year operating margin was 2.02% for fiscal 2025 ("TSN prior Operating margin; period={'start': '2024-09-29', 'end': '2025-09-27'}: 2.02 %" [Python evidence L19]).
- Management said operating income was impacted by $429 million of restructuring and related charges ("In fiscal 2026, our operating income was impacted by $429 million of restructuring and related charges" [10-K L407]).

### Profitability and Cash Flow

- Current net profit margin is 0.80% for fiscal 2026 ("TSN current Net profit margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 0.80 %" [Python evidence L4]).
- Prior net profit margin was 0.87% for fiscal 2025 ("TSN prior Net profit margin; period={'start': '2024-09-29', 'end': '2025-09-27'}: 0.87 %" [Python evidence L22]).
- Net profit margin fell by 0.07 percentage points year over year ("TSN prior-year change, Net profit margin: 0.80 % vs 0.87 %; change -0.07 percentage points; ..." [Python evidence L149]).
- Operating cash-flow margin improved to 4.31% from 3.96% year over year ("TSN prior-year change, Operating cash flow margin: 4.31 % vs 3.96 %; change 0.35 percentage points; ..." [Python evidence L150]).
- Return on average equity was 2.54% in fiscal 2026 ("TSN current Return on average equity; period={'start': '2025-09-28', 'end': '2026-10-03'}: 2.54 %" [Python evidence L12]).

### Debt and Interest Coverage

- Current debt amount is unavailable in the filing ("TSN current Debt; period={'start': '2025-09-28', 'end': '2026-10-03'}: unavailable (missing current_debt (current))" [Python evidence L16]).
- Debt-to-equity ratio is unavailable for the current period ("TSN current Debt to equity; period={'start': '2025-09-28', 'end': '2026-10-03'}: unavailable (missing current_debt (current))" [Python evidence L17]).
- Interest coverage ratio is unavailable for the current period ("TSN current Interest coverage; period={'start': '2025-09-28', 'end': '2026-10-03'}: unavailable (missing or ambiguous InterestAndDebtExpense for the same filing and period)" [Python evidence L18]).

### Peer Comparison

- Peer median operating margin is unavailable due to mismatched fiscal periods ("Peer median current Operating margin: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L154]).
- Peer median net profit margin is unavailable due to mismatched fiscal periods ("Peer median current Net profit margin: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L155]).
- Peer median operating cash-flow margin is unavailable due to mismatched fiscal periods ("Peer median current Operating cash flow margin: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L156]).
- Peer median return on average equity is unavailable due to mismatched fiscal periods ("Peer median current Return on average equity: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L157]).
- Peer median debt-to-equity is unavailable due to mismatched fiscal periods ("Peer median current Debt to equity: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L158]).
- Peer median interest coverage is unavailable due to mismatched fiscal periods ("Peer median current Interest coverage: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L159]).

### Review Flags

- Review signal shows high-priority review is False ("Annual operating-margin change: -0.07 percentage points; high-priority review=False; ..." [Python evidence L161]).

Insight: not shown, because it failed the Strategy Manager's check (see Remaining review items).

### Python evidence (code-generated, unchanged)

### Python evidence for the financial analysis

All annual amounts use the fiscal periods below. Missing values are not zero.

| Annual fact | Current year | Prior year |
| --- | --- | --- |
| Total revenue | 56,419,000,000 USD; 0000100493-26-000079, `us-gaap:Revenues`, 2025-09-28 to 2026-10-03 | 54,441,000,000 USD; 0000100493-26-000079, `us-gaap:Revenues`, 2024-09-29 to 2025-09-27 |
| Operating income | 1,100,000,000 USD; 0000100493-26-000079, `us-gaap:OperatingIncomeLoss`, 2025-09-28 to 2026-10-03 | 1,098,000,000 USD; 0000100493-26-000079, `us-gaap:OperatingIncomeLoss`, 2024-09-29 to 2025-09-27 |
| Net income | 453,000,000 USD; 0000100493-26-000079, `us-gaap:NetIncomeLoss`, 2025-09-28 to 2026-10-03 | 474,000,000 USD; 0000100493-26-000079, `us-gaap:NetIncomeLoss`, 2024-09-29 to 2025-09-27 |
| Diluted EPS | 1.28 USD/shares; 0000100493-26-000079, `us-gaap:EarningsPerShareDiluted`, 2025-09-28 to 2026-10-03 | 1.33 USD/shares; 0000100493-26-000079, `us-gaap:EarningsPerShareDiluted`, 2024-09-29 to 2025-09-27 |
| Stockholders' equity | 17,614,000,000 USD; 0000100493-26-000079, `us-gaap:StockholdersEquity`, 2026-10-03 | 18,085,000,000 USD; 0000100493-26-000079, `us-gaap:StockholdersEquity`, 2025-09-27 |
| Long-term debt, excluding current portion (including finance/capital leases) | 6,902,000,000 USD; 0000100493-26-000079, `us-gaap:LongTermDebtAndCapitalLeaseObligations`, 2026-10-03 | 7,921,000,000 USD; 0000100493-26-000079, `us-gaap:LongTermDebtAndCapitalLeaseObligations`, 2025-09-27 |
| Current portion of long-term debt | Missing | Missing |
| Cash from operations | 2,433,000,000 USD; 0000100493-26-000079, `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2025-09-28 to 2026-10-03 | 2,155,000,000 USD; 0000100493-26-000079, `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2024-09-29 to 2025-09-27 |
| Additions to property and equipment | 770,000,000 USD; 0000100493-26-000079, `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2025-09-28 to 2026-10-03 | 978,000,000 USD; 0000100493-26-000079, `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2024-09-29 to 2025-09-27 |

Definitions: operating margin uses total revenue; ROE uses the average of the two annual equity balances. Debt includes its current portion. Free cash flow is cash from operations minus additions to PP&E. P/E = the supplied share price / latest fiscal-year GAAP diluted EPS. This uses annual EPS, not quarterly, trailing-twelve-month, or forward EPS.

The supplied price's market date and source have not been confirmed.

- Revenue growth: (56,419,000,000 - 54,441,000,000) / 54,441,000,000 * 100 = 3.633291 %. Inputs: annual facts above.
- Operating margin: 1,100,000,000 / 56,419,000,000 * 100 = 1.949698 %. Inputs: annual facts above.
- Return on average equity: 453,000,000 / ((17,614,000,000 + 18,085,000,000) / 2) * 100 = 2.537886 %. Inputs: annual facts above.
- Debt to equity: missing (current and noncurrent debt tags have different lease definitions).
  Definition: Long-term debt including current portion and finance/capital lease obligations, divided by stockholders' equity.
- Free cash flow: 2,433,000,000 - 770,000,000 = 1,663,000,000 USD. Inputs: annual facts above.
- P/E (latest fiscal-year diluted EPS): missing (provide --price in USD per share).

### Latest reported quarter

- Total revenue: missing. No unambiguous quarter-first table row; inspect the release manually.
- GAAP diluted EPS: -0.22 USD/share; prior-year quarter: 0.13 USD/share. 0000100493-26-000077, Exhibit 99.1 L166; table header: | Three Months Ended | | Twelve Months Ended; column dates: | October 3, 2026 | | September 27, 2025 | | October 3, 2026 | | September 27, 2025.
  Source quote: Diluted | $ | (0.22) | | | $ | 0.13 | | | $ | 1.28 | | | $ | 1.33 |
- Quarterly revenue growth: Quarterly revenue inputs missing or prior revenue is zero.

### Peer operating margins

- HRL: 718,603,000 / 12,106,160,000 * 100 = 5.935846%. Operating income: 0000048465-25-000059, `us-gaap:OperatingIncomeLoss`, 2024-10-28 to 2025-10-26; total revenue: 0000048465-25-000059, `us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax`, 2024-10-28 to 2025-10-26.
- PPC: 1,613,539,000 / 18,497,553,000 * 100 = 8.722986%. Operating income: 0000802481-26-000011, `us-gaap:OperatingIncomeLoss`, 2024-12-30 to 2025-12-28; total revenue: 0000802481-26-000011, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, 2024-12-30 to 2025-12-28.
- CAG: -1,628,400,000 / 11,281,600,000 * 100 = -14.434123%. Operating income: 0001104659-26-083905, `us-gaap:OperatingIncomeLoss`, 2025-05-26 to 2026-05-31; total revenue: 0001104659-26-083905, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, 2025-05-26 to 2026-05-31.

## Future Developments and Strategic Recommendations

- The network-optimization plan now expects total pretax net charges of $527 million for actions approved through fiscal 2026 ("We now expect to recognize total pretax net charges of $527 million for actions approved through fiscal 2026." [10-K L423]).
- Sales are expected to decrease 3.5% to 5.5% in fiscal 2027, mainly from lower Beef volumes ("We expect sales to decrease 3.5% to 5.5% in fiscal 2027 as compared to fiscal 2026, primarily due to lower Beef segment volumes" [Exhibit 99.1 L125]).

Insight: Tyson’s exports account for less than 10% of its business, limiting exposure to trade-policy shifts [10-K L412].

Insight evidence:

- Exports represent less than 10% of Tyson’s business ("Our exports account for less than 10% of our business" [10-K L412]).

## Investment Recommendation

Recommendation: **Sell**

Thesis: The current net profit margin has slipped compared with the prior year, indicating deteriorating profitability. Coupled with unavailable interest-coverage data and no peer benchmark, the outlook remains weak, leading to a Sell recommendation.

Deciding number: TSN current Net profit margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 0.80 % ("TSN current Net profit margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 0.80 %" [Python evidence L4]).

Support:

- TSN prior Net profit margin; period={'start': '2024-09-29', 'end': '2025-09-27'}: 0.87 % ("TSN prior Net profit margin; period={'start': '2024-09-29', 'end': '2025-09-27'}: 0.87 %" [Python evidence L22]).
- Operating cash-flow margin improved to 4.31% from 3.96% year over year ("TSN prior-year change, Operating cash flow margin: 4.31 % vs 3.96 %; change 0.35 percentage points; ..." [Python evidence L150]).
- Current operating margin is 1.95% for fiscal 2026 ("TSN current Operating margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 1.95 %" [Python evidence L1]).

Risks:

- Interest coverage ratio is unavailable for the current period ("TSN current Interest coverage; period={'start': '2025-09-28', 'end': '2026-10-03'}: unavailable (missing or ambiguous InterestAndDebtExpense for the same filing and period)" [Python evidence L18]).
- Peer median net profit margin is unavailable due to mismatched fiscal periods ("Peer median current Net profit margin: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L155]).

What would change it: If operating cash-flow margin turned negative in the next filing, the recommendation would move up one step to Hold.

Insight: The research note’s mention of a thin 1.9% operating margin aligns with the financial filing’s reported 1.95% operating margin, confirming continued pressure on profitability [10-K L414] [Python evidence L1].

Insight evidence:

- Our total operating margin was 1.9% in fiscal 2026 ("Our total operating margin was 1.9% in fiscal 2026" [10-K L414]).
- Current operating margin is 1.95% for fiscal 2026 ("TSN current Operating margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 1.95 %" [Python evidence L1]).

## Remaining review items

- Research Analyst: Overview: [10-K L420] quote not on cited line
- Research Analyst: Future Developments and Strategic Recommendations: [Exhibit 99.1 L136] quote not on cited line
- Research Analyst: Future Developments and Strategic Recommendations: [Exhibit 99.1 L112] quote not on cited line
- Research Analyst: Future Developments and Strategic Recommendations: [Exhibit 99.1 L118] quote not on cited line
- Financial Analyst: Operating Margin: [Python evidence L148] quote not on cited line
- Financial Analyst: Profitability and Cash Flow: [Python evidence L7] number not on cited line
- Financial Analyst: Insight: [Python evidence L148] quote not on cited line
- Research Analyst / Overview: removed from the report: Management’s strategy focuses on delivering margins in the core protein business by driving efficiencies ("Our strategy is to deliver margins in the core protein business by driving efficiencies" [10-K L420]). Problem: [10-K L420] quote not on cited line
- Research Analyst / Future Developments and Strategic Recommendations: removed from the report: Board of Directors increased the quarterly dividend to $0.52 per share ("the Board of Directors increased the quarterly dividend ... to $0.52 per share" [Exhibit 99.1 L136]). Problem: [Exhibit 99.1 L136] quote not on cited line
- Research Analyst / Future Developments and Strategic Recommendations: removed from the report: Pork segment operating income, as adjusted, is forecast $75 million to $175 million in fiscal 2027 ("We anticipate segment operating income, as adjusted, of $75 million to $175 million in fiscal 2027." [Exhibit 99.1 L112]). Problem: [Exhibit 99.1 L112] quote not on cited line
- Research Analyst / Future Developments and Strategic Recommendations: removed from the report: International segment operating income, as adjusted, is forecast $125 million to $200 million in fiscal 2027 ("We anticipate segment operating income, as adjusted, of $125 million to $200 million in fiscal 2027." [Exhibit 99.1 L118]). Problem: [Exhibit 99.1 L118] quote not on cited line
- Financial Analyst / Operating Margin: removed from the report: Operating margin decreased by 0.07 percentage points year over year ("Annual operating-margin change: -0.07 percentage points; high-priority review=False; ..." [Python evidence L148]). Problem: [Python evidence L148] quote not on cited line
- Financial Analyst / Profitability and Cash Flow: removed from the report: Operating cash flow provided $2,433 million in fiscal 2026 ("TSN current Operating cash flow; period={'start': '2025-09-28', 'end': '2026-10-03'}: 2433000000 USD" [Python evidence L7]). Problem: [Python evidence L7] number not on cited line
- Financial Analyst / Insight evidence: removed from the report: Operating margin decreased by 0.07 percentage points year over year ("Annual operating-margin change: -0.07 percentage points; high-priority review=False; ..." [Python evidence L148]). Problem: [Python evidence L148] quote not on cited line

This is a learning exercise, not financial advice.
AI assistance: Codex, Claude, Gemini, Purdue GenAI Studio (gpt-oss:120b). Human source verification and sign-off are pending.
