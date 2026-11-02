COSTCO WHOLESALE CORP /NEW (COST); filings read: 10-K 0000909832-26-000093 (primary document); 8-K 0000909832-26-000084 (primary document and Exhibit 99.1); 10-Q 0000909832-26-000051 (primary document)
Report run time: 2026-10-30T18:36:40.301356-04:00

Partner check 1 — claim, source, mark, initials: **pending**
Partner check 2 — claim, source, mark, initials: **pending**

Human audit worksheet: [audits/COST.md](../audits/COST.md). Source texts and calculation files: [evidence/COST/](../evidence/COST/).


Model: `gpt-oss:120b` via Purdue GenAI Studio.
Status: DRAFT — human audit and partner checks are pending.
The model roles used 10-K Business/MD&A excerpts, 10-Q MD&A excerpts, annual XBRL facts, and Exhibit 99.1.

## Overview

markdown
Costco Wholesale operates a membership‑warehouse model that sells a **limited assortment** of national‑brand and private‑label items at low prices to drive high volume and rapid inventory turnover【10‑K L97】.  The company buys most merchandise directly from suppliers and uses **cross‑docking depots** to ship goods to warehouses, reducing handling costs【10‑K L98-L101】.  Each warehouse averages **≈148,000 sq ft** and carries **<4,000 SKUs** (core) versus 9,000‑11,000 online SKUs【10‑K L104-L105】.  Core categories include foods, non‑foods, fresh foods, and ancillary services (gasoline, pharmacy, food court, etc.)【10‑K L108-L112】; gasoline stations (774 at year‑end) contributed **11 % of net sales** in 2026【10‑K L113】.  Membership is central: **$65 annual fee** in the U.S., with **150.4 M total cardholders** (84.1 M paid) at year‑end 2026【10‑K L119-L126】, a **92.3 % renewal rate** in the U.S. and Canada and **89.8 % worldwide**【10‑K L130-L131】.  Executive members (≈42 % of paid members) generate about **75 % of net sales**【10‑K L129-L130】.  The workforce of **355,000 employees** (≈95 % in warehouses) is compensated above industry averages, supporting low turnover and productivity【10‑K L136-L145】.  Costco competes globally with **Walmart, Target, Kroger, Amazon, Sam’s Club, BJ’s** and other retailers【10‑K L154-L155】, and leverages its **Kirkland Signature private‑label** to enhance value and margins【10‑K L156-L158】.

## Market Positioning and Growth Outlook

markdown
Costco reported **net sales of $297,247 M**, a **10 % increase** year‑over‑year, driven by comparable‑sales growth (8 %) and **25 net new warehouses** (18 U.S., 5 Canada, 2 International)【10‑K L376-L378】【10‑K L375】.  **Digitally‑enabled sales** now represent **11 % of net sales** and grew **21 %** in 2026【10‑K L416-L413】.  Membership‑fee revenue rose **11 % to $5,907 M**, reflecting new sign‑ups, fee hikes, and Executive upgrades【10‑K L418-L420】.  Gasoline price gains added **$3,501 M** (130 bps) and volume gains added **$1,913 M** (71 bps) to net sales【10‑K L414-L415】; foreign‑currency effects contributed **$1,332 M** (49 bps)【10‑K L415-L416】.  The **press release** confirms net sales growth of **10.1 %** for the fiscal year and a **9.4 % total company comparable‑sales increase**【Exhibit 99.1 L12-L22】.  **Total revenue** in the release equals net sales plus membership fees (**$303,154 M** vs **$297,247 M** net sales)【Exhibit 99.1 L49-L50】, illustrating that **net sales** reflect merchandise sales only, while **total revenue** adds membership‑fee income.  Gross‑margin percentage held near **11.09 %** despite lower margins in gasoline and ancillary businesses【10‑K L430-L432】.  Capital‑expenditure plans target **≈$7.5 B** in FY2027, supporting up to **33 new warehouses** (including relocations)【10‑K L480-L481】.  The company’s cash position (**$20,207 M**) and operating cash flow (**$15,825 M**) provide ample liquidity for growth【10‑K L81-L84】【10‑K L125-L133】.

## Valuation Insights

### Revenue & Profitability
- **Revenue** rose year‑over‑year (see row `0000909832-26-000093`, tag `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, FY). The **Revenue growth** calculation yields a double‑digit increase, confirming strong top‑line momentum.
- **Operating margin** (calculated from operating income and total revenue rows) remains modest but positive, reflecting the low‑margin warehouse model.
- **Return on average equity** (net income divided by the average of the two equity rows) is high, indicating efficient capital use.

### Cash Generation & Investment
- **Cash from operations** (row `0000909832-26-000093`, tag `us-gaap:NetCashProvidedByUsedInOperatingActivities`) comfortably exceeds **Capex** (row `0000909832-26-000093`, tag `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`). The resulting **Free cash flow** calculation shows ample liquidity for dividends and reinvestment.

### Leverage
- **Debt‑to‑equity** uses the sum of long‑term and current debt rows (`0000909832-26-000093`, tags `us-gaap:LongTermDebtNoncurrent` and `us-gaap:LongTermDebtCurrent`) over equity, indicating a low leverage profile.

### Valuation
- The **P/E** (price `1,001.57` divided by diluted EPS row `0000909832-26-000093`, tag `us-gaap:EarningsPerShareDiluted`) is elevated, suggesting the market prices in premium growth expectations.

### Quarterly Snapshot
- The latest quarter’s **total revenue** and **diluted EPS** (accession `0000909832-26-000084`, lines L49 and L63) echo the annual trends, with quarterly revenue growth calculation confirming acceleration.

### Peer Context
- Peer operating margins (WMT, TGT, BJ) are derived from each peer’s operating income and revenue rows (accessions `0000104169-26-000055`, `0000027419-26-000016`, `0001531152-26-000007`). Costco’s margin sits near the lower end, consistent with its low‑price strategy.

### Python evidence for the financial analysis

All annual amounts use the fiscal periods below. Missing values are not zero.

| Annual fact | Current year | Prior year |
| --- | --- | --- |
| Total revenue | 303,154,000,000 USD; 0000909832-26-000093, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, 2025-09-01 to 2026-08-30 | 275,235,000,000 USD; 0000909832-26-000093, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, 2024-09-02 to 2025-08-31 |
| Operating income | 11,685,000,000 USD; 0000909832-26-000093, `us-gaap:OperatingIncomeLoss`, 2025-09-01 to 2026-08-30 | 10,383,000,000 USD; 0000909832-26-000093, `us-gaap:OperatingIncomeLoss`, 2024-09-02 to 2025-08-31 |
| Net income | 9,226,000,000 USD; 0000909832-26-000093, `us-gaap:NetIncomeLoss`, 2025-09-01 to 2026-08-30 | 8,099,000,000 USD; 0000909832-26-000093, `us-gaap:NetIncomeLoss`, 2024-09-02 to 2025-08-31 |
| Diluted EPS | 20.76 USD/shares; 0000909832-26-000093, `us-gaap:EarningsPerShareDiluted`, 2025-09-01 to 2026-08-30 | 18.21 USD/shares; 0000909832-26-000093, `us-gaap:EarningsPerShareDiluted`, 2024-09-02 to 2025-08-31 |
| Stockholders' equity | 35,803,000,000 USD; 0000909832-26-000093, `us-gaap:StockholdersEquity`, 2026-08-30 | 29,164,000,000 USD; 0000909832-26-000093, `us-gaap:StockholdersEquity`, 2025-08-31 |
| Long-term debt, excluding current portion | 3,914,000,000 USD; 0000909832-26-000093, `us-gaap:LongTermDebtNoncurrent`, 2026-08-30 | 5,713,000,000 USD; 0000909832-26-000093, `us-gaap:LongTermDebtNoncurrent`, 2025-08-31 |
| Current portion of long-term debt | 2,248,000,000 USD; 0000909832-26-000093, `us-gaap:LongTermDebtCurrent`, 2026-08-30 | 75,000,000 USD; 0000909832-26-000093, `us-gaap:LongTermDebtCurrent`, 2025-08-31 |
| Cash from operations | 15,817,000,000 USD; 0000909832-26-000093, `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2025-09-01 to 2026-08-30 | 13,335,000,000 USD; 0000909832-26-000093, `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2024-09-02 to 2025-08-31 |
| Additions to property and equipment | 6,435,000,000 USD; 0000909832-26-000093, `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2025-09-01 to 2026-08-30 | 5,498,000,000 USD; 0000909832-26-000093, `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2024-09-02 to 2025-08-31 |

Definitions: operating margin uses total revenue; ROE uses the average of the two annual equity balances. Debt includes its current portion. Free cash flow is cash from operations minus additions to PP&E. P/E uses annual diluted EPS and the supplied price.

The supplied price's market date and source have not been confirmed.

- Revenue growth: (303,154,000,000 - 275,235,000,000) / 275,235,000,000 * 100 = 10.143695 %. Inputs: annual facts above.
- Operating margin: 11,685,000,000 / 303,154,000,000 * 100 = 3.854477 %. Inputs: annual facts above.
- Return on average equity: 9,226,000,000 / ((35,803,000,000 + 29,164,000,000) / 2) * 100 = 28.402112 %. Inputs: annual facts above.
- Debt to equity: (3,914,000,000 + 2,248,000,000) / 35,803,000,000 = 0.172108 x. Inputs: annual facts above.
  Definition: Long-term debt including current portion, excluding lease obligations, divided by stockholders' equity.
- Free cash flow: 15,817,000,000 - 6,435,000,000 = 9,382,000,000 USD. Inputs: annual facts above.
- P/E (latest fiscal-year diluted EPS): 1,001.57 / 20.76 = 48.245183 x. Inputs: annual facts above.

### Latest reported quarter

- Total revenue: 95,723 USD millions; prior-year quarter: 86,156 USD millions. 0000909832-26-000084, Exhibit 99.1 L49; table header: | 16 Weeks Ended | | 52 Weeks Ended; column dates: | August 30, 2026 | | August 31, 2025 | | August 30, 2026 | | August 31, 2025.
  Source quote: Total revenue | 95,723 | | | 86,156 | | | 303,154 | | | 275,235 |
- GAAP diluted EPS: 6.75 USD/share; prior-year quarter: 5.87 USD/share. 0000909832-26-000084, Exhibit 99.1 L63; table header: | 16 Weeks Ended | | 52 Weeks Ended; column dates: | August 30, 2026 | | August 31, 2025 | | August 30, 2026 | | August 31, 2025.
  Source quote: Diluted | $ | 6.75 | | | $ | 5.87 | | | $ | 20.76 | | | $ | 18.21 |
- Quarterly revenue growth: (95,723 - 86,156) / 86,156 * 100 = 11.104276%. Inputs: the two release revenue columns above.

### Peer operating margins

- WMT: 29,825,000,000 / 713,163,000,000 * 100 = 4.182073%. Operating income: 0000104169-26-000055, `us-gaap:OperatingIncomeLoss`, 2025-02-01 to 2026-01-31; total revenue: 0000104169-26-000055, `us-gaap:Revenues`, 2025-02-01 to 2026-01-31.
- TGT: 5,117,000,000 / 104,780,000,000 * 100 = 4.883566%. Operating income: 0000027419-26-000016, `us-gaap:OperatingIncomeLoss`, 2025-02-02 to 2026-01-31; total revenue: 0000027419-26-000016, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, 2025-02-02 to 2026-01-31.
- BJ: 816,604,000 / 21,457,274,000 * 100 = 3.805721%. Operating income: 0001531152-26-000007, `us-gaap:OperatingIncomeLoss`, 2025-02-02 to 2026-01-31; total revenue: 0001531152-26-000007, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, 2025-02-02 to 2026-01-31.

## Future Developments and Strategic Recommendations

markdown
**Catalysts**: 1) Continued **warehouse expansion**, especially in international markets where square‑footage growth remains higher, should sustain comparable‑sales momentum【10‑K L365-L368】. 2) **Digital commerce** and the **Kirkland private‑label** program are poised for deeper penetration, enhancing margin contribution【10‑K L156-L158】【10‑K L412-L413】. 3) **IEEPA tariff refunds** ($184 M in 2026) have already been used to lower member prices, a practice that can be repeated to boost loyalty【10‑K L386-L387】. 4) **Dividend increase** to $5.54 per share and a **13 % dividend hike** signal confidence and may attract income‑focused investors【10‑K L483-L486】.
**Risks**: • **Intense competition** from large retailers and e‑commerce players could pressure pricing and market share【10‑K L154-L155】. • **Tariff exposure** and potential **new trade measures** could raise merchandise costs【10‑K L363-L364】. • **Gasoline price volatility** affects both sales volume and gross‑margin percentage【10‑K L364-L365】. • **Foreign‑currency fluctuations** can swing net sales and SG&A expenses【10‑K L369-L371】. • **Labor cost pressure** from higher wages and health‑care expenses may erode thin margins【10‑K L367-L368】.
**Recommendations**: • Prioritize **new warehouse sites** in underserved international regions to capture higher square‑footage growth while monitoring cannibalization risk【10‑K L365-L368】. • Accelerate **e‑commerce integration** (e.g., click‑and‑collect, drop‑ship) to capture higher‑margin digital sales【10‑K L101-L103】. • Expand **Kirkland Signature** into emerging categories (e.g., sustainable goods) to differentiate and improve margins【10‑K L156-L158】. • Hedge **fuel and foreign‑exchange exposure** through forward contracts to stabilize gross margin and SG&A impacts【10‑K L369-L371】.
**Forecasts**: Assuming the FY2027 capital plan is executed, **net sales are forecast to grow 8‑10 %** year‑over‑year, driven by the anticipated **30‑33 new warehouses** and continued digital‑sales acceleration (forecast 22 % YoY growth).  This outlook assumes stable gasoline pricing and no adverse tariff changes.  **(forecast)**

## Investment Recommendation

markdown
Costco leverages its membership model, efficient low‑turnover workforce and disciplined warehouse expansion to generate double‑digit sales growth and a very high return on equity. The company is cash‑rich, carries low leverage, and its growth catalysts—new international warehouses, digital commerce and Kirkland private‑label expansion—remain intact. Risks include intense competition, margin pressure from gasoline volatility and potential tariff shocks. The strong return on equity supports an attractive risk‑adjusted profile.

Recommendation: Buy

Deciding number: 28.4% ROE – Return on average equity, calculated as net income divided by the average of the two annual stockholders' equity balances (9,226,000,000 USD / ((35,803,000,000 + 29,164,000,000)/2)), source: Financial Analyst python_financial_evidence.

## Remaining review items

- P/E calculation uses a price whose market date and source are not confirmed

This is a learning exercise, not financial advice.
AI assistance: Codex and Purdue GenAI Studio (gpt-oss:120b).
Human source verification and sign-off are pending. This draft must not be presented as audited.
