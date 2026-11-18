TYSON FOODS, INC. (TSN); filings read: 10-K 0000100493-26-000079 (primary document); 8-K 0000100493-26-000077 (primary document and Exhibit 99.1); 10-Q 0000100493-26-000058 (primary document)
Report run time: 2026-11-17T19:11:26.138271-05:00

Model: `gpt-oss:120b` via Purdue GenAI Studio. Graph: crewAI Flow (flow_desk.py).
Personas: Research Analyst: student persona; Financial Analyst: student persona; Investment Advisor: student persona.
Strategy Manager (code): Research Analyst fail after 2 attempt(s); Financial Analyst pass after 1 attempt(s); Investment Advisor pass after 2 attempt(s).
Quote repairs made in code: 6; citation repairs made in code: 1 (each is listed in the role's JSON file). Claims that failed the check are not in the five parts; see Remaining review items.
Status: DRAFT. Human audit and partner checks are pending.

## Overview

- Tyson Foods reported $56,419 million in sales for fiscal 2026 ("Sales | $ | 56,419" [10-K L430]).
- Operating income was $1,100 million in fiscal 2026, flat year over year ("Operating income of $1,100 million in fiscal 2026 was relatively flat" [10-K L406]).
- The company employs approximately 124,000 team members as of October 3 2026 ("approximately 124,000 employees ("team members") on October 3, 2026" [10-K L92]).
- Liquidity stood at $4.1 billion as of October 3 2026 ("Liquidity of $4.1 billion as of October 3, 2026" [Exhibit 99.1 L29]).

## Market Positioning and Growth Outlook

- Tyson Foods operates five reportable segments: Beef, Pork, Chicken, Prepared Foods and International ("We operate in five reportable segments: Beef, Pork, Chicken, Prepared Foods and International." [10-K L99]).
- Beef segment operating margin was negative 5.6% in fiscal 2026 ("•Beef - (5.6)%" [10-K L415]).
- Chicken segment operating margin was 10.0% in fiscal 2026 ("•Chicken - 10.0%" [10-K L417]).
- Prepared Foods segment operating margin was 12.6% in fiscal 2026 ("•Prepared Foods - 12.6%" [10-K L418]).
- Sales grew 3.6%, or $2.0 billion, in fiscal 2026 ("Sales grew 3.6%, or $2.0 billion, in fiscal 2026" [10-K L406]).

## Valuation Insights

### Operating Margin

- Current operating margin is 1.95 % for fiscal 2026 ("TSN current Operating margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 1.95 %" [Python evidence L1]).
- Prior-year operating margin was 2.02 % for fiscal 2025 ("TSN prior Operating margin; period={'start': '2024-09-29', 'end': '2025-09-27'}: 2.02 %" [Python evidence L21]).
- The margin declined by 0.07 percentage points year-over-year ("TSN prior-year change, Operating margin: 1.95 % vs 2.02 %; change -0.07 percentage points" [Python evidence L160]).
- Management said operating income was relatively flat, offset by segment mix and higher corporate expenses ("Operating income of $1,100 million in fiscal 2026 was relatively flat as compared to fiscal 2025, reflecting higher segment operating income in our Pork, Prepared Foods and International segments and lower amortization expense, partially offset by lower segment operating income in our Beef and Chicken segments and higher corporate expenses." [10-K L406]).

### Profitability and Cash Flow

- Current net profit margin is 0.80 % for fiscal 2026 ("TSN current Net profit margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 0.80 %" [Python evidence L4]).
- Prior-year net profit margin was 0.87 % for fiscal 2025 ("TSN prior Net profit margin; period={'start': '2024-09-29', 'end': '2025-09-27'}: 0.87 %" [Python evidence L24]).
- Operating cash-flow margin improved to 4.31 % from 3.96 % a year ago ("TSN prior-year change, Operating cash flow margin: 4.31 % vs 3.96 %; change 0.35 percentage points" [Python evidence L162]).
- Return on average equity for the current year is 2.54 % ("TSN current Return on average equity; period={'start': '2025-09-28', 'end': '2026-10-03'}: 2.54 %" [Python evidence L12]).
- Prior-year ROE is unavailable because equity data are missing or ambiguous ("TSN prior Return on average equity; period={'start': '2024-09-29', 'end': '2025-09-27'}: unavailable (missing or ambiguous StockholdersEquity for the same filing and period)" [Python evidence L32]).

### Debt and Interest Coverage

- Current interest coverage ratio is 2.71 × ("TSN current Interest coverage; period={'start': '2025-09-28', 'end': '2026-10-03'}: 2.71 x" [Python evidence L18]).
- Prior-year interest coverage was 2.45 × ("TSN prior Interest coverage; period={'start': '2024-09-29', 'end': '2025-09-27'}: 2.45 x" [Python evidence L35]).
- Debt amount is unavailable for the current period ("TSN current Debt; period={'start': '2025-09-28', 'end': '2026-10-03'}: unavailable (missing current_debt (current))" [Python evidence L16]).
- Debt-to-equity ratio is unavailable for both current and prior periods ("TSN current Debt to equity; period={'start': '2025-09-28', 'end': '2026-10-03'}: unavailable (missing current_debt (current))" [Python evidence L17]).
- Prior-year debt-to-equity is also unavailable because the prior debt figure is missing ("TSN prior Debt to equity; period={'start': '2024-09-29', 'end': '2025-09-27'}: unavailable (missing current_debt (prior))" [Python evidence L34]).

### Peer Comparison

- HRL operating-margin data cannot be compared because its fiscal period differs from Tyson’s ("HRL current Operating margin; period={'start': '2024-10-28', 'end': '2025-10-26'}: 5.94 %" [Python evidence L38]).
- PPC operating-margin data is incompatible with Tyson’s period ("PPC current Operating margin; period={'start': '2024-12-30', 'end': '2025-12-28'}: 8.72 %" [Python evidence L85]).
- CAG operating-margin data is incompatible with Tyson’s period ("CAG current Operating margin; period={'start': '2025-05-26', 'end': '2026-05-31'}: -14.43 %" [Python evidence L122]).
- Peer median operating margin is unavailable because no peer shares a matching fiscal period ("Peer median current Operating margin: unavailable (no peer with matching fiscal periods and a value; excluded: HRL fiscal periods differ, PPC fiscal periods differ, CAG fiscal periods differ)" [Python evidence L166]).

### Review Flags

- Annual operating-margin change is -0.07 pp; high-priority review flag is False and no ROE/debt/coverage warning is issued ("Annual operating-margin change: -0.07 percentage points; high-priority review=False; ROE/debt/coverage warning=None." [Python evidence L173]).

Insight: Although management stresses that operating income was flat, the operating margin actually slipped to 1.95 % (down from 2.02 %), revealing margin pressure not highlighted in the earnings release [Python evidence L1] [Python evidence L21].

Insight evidence:

- Current operating margin is 1.95 % for fiscal 2026 ("TSN current Operating margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 1.95 %" [Python evidence L1]).
- Prior-year operating margin was 2.02 % for fiscal 2025 ("TSN prior Operating margin; period={'start': '2024-09-29', 'end': '2025-09-27'}: 2.02 %" [Python evidence L21]).
- Management said operating income was relatively flat, offset by segment mix and higher corporate expenses ("Operating income of $1,100 million in fiscal 2026 was relatively flat as compared to fiscal 2025, reflecting higher segment operating income in our Pork, Prepared Foods and International segments and lower amortization expense, partially offset by lower segment operating income in our Beef and Chicken segments and higher corporate expenses." [10-K L406]).

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

- The Beef segment continues to experience limited supply of market-ready cattle and higher cattle costs ("The Beef segment continues to experience limited supply of market-ready cattle and higher cattle costs" [10-K L410]).
- The Chicken segment experienced increased feed ingredient costs in fiscal 2026 ("The Chicken segment experienced increased feed ingredient costs in fiscal 2026" [10-K L410]).
- The network optimization plan added $441 million of pretax charges in fiscal 2026 ("Company increased the estimated pretax net charges by $441 million for additional actions approved under the network optimization plan." [10-K L422]).
- Total pretax net charges are now expected to reach $527 million for actions approved through fiscal 2026 ("We now expect to recognize total pretax net charges of $527 million for actions approved through fiscal 2026." [10-K L423]).
- Exports account for less than 10% of the business, limiting exposure to trade-policy volatility ("Our exports account for less than 10% of our business" [10-K L412]).
- Catalyst rating: Strong - network optimization plan charges are quantified and disclosed ("Company increased the estimated pretax net charges by $441 million for additional actions approved under the network optimization plan." [10-K L422]).
- Business durability rating: Mixed - low export concentration but reliance on limited cattle supply ("The Beef segment continues to experience limited supply of market-ready cattle and higher cattle costs" [10-K L410]).
- Operational challenge rating: Mixed - legal contingency accruals reduced sales, with no specific remediation detailed ("Sales grew 3.6%, or $2.0 billion, in fiscal 2026, ... and $340 million of decreased legal contingency accruals recognized as a reduction to Sales" [10-K L406]).
- Unresolved milestone: the company projects sales to decrease 3.5%-5.5% in fiscal 2027, primarily due to lower Beef volumes ("We expect sales to decrease 3.5% to 5.5% in fiscal 2027 as compared to fiscal 2026, primarily due to lower Beef segment volumes" [Exhibit 99.1 L125]).

Insight: Tyson Foods held $4.1 billion of liquidity as of October 3 2026, well above its $1.0 billion minimum target [Exhibit 99.1 L29] [Exhibit 99.1 L131].

Insight evidence:

- Liquidity of $4.1 billion as of October 3, 2026 ("Liquidity of $4.1 billion as of October 3, 2026" [Exhibit 99.1 L29]).
- Minimum liquidity target is $1.0 billion ("minimum liquidity target of $1.0 billion" [Exhibit 99.1 L131]).
- Total liquidity expected to remain well above the $1.0 billion target ("We expect total liquidity, which was $4.1 billion as of October 3, 2026, to remain well above our minimum liquidity target of $1.0 billion" [Exhibit 99.1 L131]).

## Investment Recommendation

Recommendation: **Hold**

Thesis: The net profit margin of 0.80 % for fiscal 2026 is below the prior-year level, indicating weaker profitability, while interest coverage remains solid and cash-flow margin has improved, leading to a Hold recommendation.

Deciding number: Current net profit margin is 0.80 % for fiscal 2026 ("TSN current Net profit margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 0.80 %" [Python evidence L4]).

Support:

- Current interest coverage ratio is 2.71 × ("TSN current Interest coverage; period={'start': '2025-09-28', 'end': '2026-10-03'}: 2.71 x" [Python evidence L18]).
- Operating cash-flow margin improved to 4.31 % from 3.96 % a year ago ("TSN prior-year change, Operating cash flow margin: 4.31 % vs 3.96 %; change 0.35 percentage points" [Python evidence L162]).
- Operating income was flat at $1.1 billion, offset by restructuring and legal charges ("Operating income of $1,100 million in fiscal 2026 was relatively flat as compared to fiscal 2025, reflecting higher segment operating income ... and higher corporate expenses." [10-K L406]).

Risks:

- Higher feed-ingredient costs and limited cattle supply are pressuring the Chicken and Beef segments ("The Beef segment continues to experience limited supply of market-ready cattle and higher cattle costs" [10-K L410]).
- Beef segment operating margin was negative 5.6 % in fiscal 2026 ("•Beef - (5.6)%" [10-K L415]).

What would change it: If operating cash-flow margin turns negative in the next filing, the recommendation would shift from Hold to Sell.

Insight: The research note that the Beef segment posted a -5.6% margin aligns with the financial analyst’s finding that overall operating margin slipped to 1.95%, underscoring broader profitability challenges [10-K L415] [Python evidence L1].

Insight evidence:

- Beef segment operating margin was negative 5.6 % in fiscal 2026 ("•Beef - (5.6)%" [10-K L415]).
- Current operating margin is 1.95 % for fiscal 2026 ("TSN current Operating margin; period={'start': '2025-09-28', 'end': '2026-10-03'}: 1.95 %" [Python evidence L1]).

## Remaining review items

- Research Analyst: Overview: [Exhibit 99.1 L29] quote not on cited line
- Research Analyst / Overview: removed from the report: Backlog completeness rating: Weak (no periods disclosed) ("Backlog does not apply to its business." [Not applicable - no backlog disclosure in supplied material]). Problem: no citations

This is a learning exercise, not financial advice.
AI assistance: Codex, Claude, Gemini, Purdue GenAI Studio (gpt-oss:120b). Human source verification and sign-off are pending.
