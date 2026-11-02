NORTHROP GRUMMAN CORP /DE/ (NOC); filings read: 10-Q 0001133421-26-000038 (primary document); 8-K 0001133421-26-000037 (primary document and Exhibit 99); 10-K 0001133421-26-000003 (primary document)
Report run time: 2026-11-01T20:44:30.132575-05:00

Model: `gpt-oss:120b` via Purdue GenAI Studio.
Status: DRAFT — human audit and partner checks are pending.
The model roles used 10-K Business/MD&A excerpts, 10-Q MD&A excerpts, annual XBRL facts, and Exhibit 99.

## Overview

Northrop Grumman is a **global aerospace and defense technology company** that delivers a broad range of products, services and solutions primarily to the U.S. Department of War and intelligence community [10-K L128]. Its portfolio spans **space systems, military aircraft, missile‑defense, advanced weapons, mission systems, networking, communications and breakthrough technologies** [10-K L129‑L130]. The firm is organized into four reportable **operating sectors** – Aeronautics Systems, Defense Systems, Mission Systems and Space Systems – each responsible for design, development, production, integration, sustainment and modernization of key programs [10-K L140‑L147]. Sales are overwhelmingly government‑driven, with the **U.S. government accounting for ~86 % of total sales** in recent years [10-K L202]. The company reports **total sales (net revenue)** of $41.9 billion for 2025, of which **organic sales** (excluding the divested training services business) are $41.8 billion [10-K L592‑L594]. Net earnings were $4.2 billion in 2025, reflecting a modest operating margin of 10.8 % [10-K L577‑L579]. The firm’s business model relies on long‑term **cost‑type and fixed‑price contracts** governed by FAR and CAS, with revenue recognized over time as costs are incurred [10-K L556‑L558].

## Market Positioning and Growth Outlook

Northrop Grumman competes with **Boeing, Lockheed Martin, General Dynamics, L3Harris and RTX**, among others, in a market characterized by long operating cycles and intense competition [10-K L203‑L205]. Its **backlog** grew to **$95.7 billion at year‑end 2025**, up from $91.5 billion in 2024, indicating a strong pipeline of future work [10-K L209]. The **third‑quarter 2026 earnings release** reported a **book‑to‑bill ratio of 1.5×** and **backlog of $109.6 billion**, a 15 % increase year‑over‑year [Exhibit 99 L18‑L21, L37‑L42, L370‑L377]. Growth drivers include the **B‑21 long‑range strike aircraft**, **F‑35 sustainment**, **Sentinel missile‑defense program**, **Space Development Agency (SDA) tracking and transport layers**, and **Cygnus CRS missions** [10‑K L148‑L155, L190‑L199, L542‑L549, L551‑L555, L195‑L200]. The **One Big Beautiful Bill Act (OBBBA)** allocated ~$150 billion for defense spending, supporting continued investment in air, missile‑defense and space modernization [10‑K L538‑L543]. The company’s **non‑seasonal** nature and **high‑margin contract mix** (≈50 % cost‑type, 50 % fixed‑price) provide resilience [10‑K L206‑L257, L255‑L257].

## Valuation Insights

### Northrop Grumman (NOC)
- **Revenue trend**: The annual *Total revenue* row (accession 0001133421‑26‑000003) shows a modest increase year‑over‑year, confirming the *Revenue growth* calculation.
- **Profitability**: *Operating income* (same accession) relative to *Total revenue* yields an operating margin just above ten percent, matching the *Operating margin* metric. The quarterly *Total sales* line (L238) indicates a higher short‑term growth rate, but the three‑month figure is not directly comparable to full‑year margins.
- **Return on equity**: Using *Net income* and the average of the two *Stockholders' equity* rows (accession 0001133421‑26‑000003) produces a ROE in the mid‑twenties percent, reflecting strong earnings generation on the equity base.
- **Leverage**: *Long‑term debt* plus *Current portion of long‑term debt* (both accession 0001133421‑26‑000003) divided by *Stockholders' equity* gives a debt‑to‑equity ratio close to one, indicating a balanced capital structure; lease obligations are excluded per the definition.
- **Cash generation**: *Cash from operations* minus *Additions to property and equipment* (both accession 0001133421‑26‑000003) results in positive free cash flow, supporting ongoing investment and dividend capacity.
- **Valuation**: The supplied share price (510.65 USD) over the latest *Diluted EPS* row (accession 0001133421‑26‑000003) yields a P/E near seventeen, a modest multiple for the sector.
- **Quarter snapshot**: The quarter *Diluted EPS* line (L256) shows a slight uplift versus prior year, consistent with the annual earnings trend.
- **Peer context**: Peer operating margins (RTX, LMT, GD) all hover around ten percent, placing NOC’s margin in line with industry peers.

*Limitations*: All ratios rely on GAAP figures; no adjustments for non‑recurring items (e.g., divestiture gain) are reflected. Quarterly data cover only the September‑ended period and may not capture full‑year seasonality. Lease debt is excluded from the debt‑to‑equity metric.

### Python evidence for the financial analysis

All annual amounts use the fiscal periods below. Missing values are not zero.

| Annual fact | Current year | Prior year |
| --- | --- | --- |
| Total revenue | 41,954,000,000 USD; 0001133421-26-000003, `us-gaap:Revenues`, 2025-01-01 to 2025-12-31 | 41,033,000,000 USD; 0001133421-26-000003, `us-gaap:Revenues`, 2024-01-01 to 2024-12-31 |
| Operating income | 4,511,000,000 USD; 0001133421-26-000003, `us-gaap:OperatingIncomeLoss`, 2025-01-01 to 2025-12-31 | 4,370,000,000 USD; 0001133421-26-000003, `us-gaap:OperatingIncomeLoss`, 2024-01-01 to 2024-12-31 |
| Net income | 4,182,000,000 USD; 0001133421-26-000003, `us-gaap:NetIncomeLoss`, 2025-01-01 to 2025-12-31 | 4,174,000,000 USD; 0001133421-26-000003, `us-gaap:NetIncomeLoss`, 2024-01-01 to 2024-12-31 |
| Diluted EPS | 29.08 USD/shares; 0001133421-26-000003, `us-gaap:EarningsPerShareDiluted`, 2025-01-01 to 2025-12-31 | 28.34 USD/shares; 0001133421-26-000003, `us-gaap:EarningsPerShareDiluted`, 2024-01-01 to 2024-12-31 |
| Stockholders' equity | 16,674,000,000 USD; 0001133421-26-000003, `us-gaap:StockholdersEquity`, 2025-12-31 | 15,290,000,000 USD; 0001133421-26-000003, `us-gaap:StockholdersEquity`, 2024-12-31 |
| Long-term debt, excluding current portion | 15,162,000,000 USD; 0001133421-26-000003, `us-gaap:LongTermDebtNoncurrent`, 2025-12-31 | 14,692,000,000 USD; 0001133421-26-000003, `us-gaap:LongTermDebtNoncurrent`, 2024-12-31 |
| Current portion of long-term debt | 534,000,000 USD; 0001133421-26-000003, `us-gaap:LongTermDebtCurrent`, 2025-12-31 | 1,582,000,000 USD; 0001133421-26-000003, `us-gaap:LongTermDebtCurrent`, 2024-12-31 |
| Cash from operations | 4,757,000,000 USD; 0001133421-26-000003, `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2025-01-01 to 2025-12-31 | 4,388,000,000 USD; 0001133421-26-000003, `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2024-01-01 to 2024-12-31 |
| Additions to property and equipment | 1,450,000,000 USD; 0001133421-26-000003, `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2025-01-01 to 2025-12-31 | 1,767,000,000 USD; 0001133421-26-000003, `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2024-01-01 to 2024-12-31 |

Definitions: operating margin uses total revenue; ROE uses the average of the two annual equity balances. Debt includes its current portion. Free cash flow is cash from operations minus additions to PP&E. P/E = the supplied share price / latest fiscal-year GAAP diluted EPS. This uses annual EPS, not quarterly, trailing-twelve-month, or forward EPS.

Price input: 510.65 USD/share; date: 2026-10-19; source supplied with the run: https://investor.northropgrumman.com/stock-information/historical-price-lookup. The reader should check that source.

- Revenue growth: (41,954,000,000 - 41,033,000,000) / 41,033,000,000 * 100 = 2.244535 %. Inputs: annual facts above.
- Operating margin: 4,511,000,000 / 41,954,000,000 * 100 = 10.752252 %. Inputs: annual facts above.
- Return on average equity: 4,182,000,000 / ((16,674,000,000 + 15,290,000,000) / 2) * 100 = 26.166938 %. Inputs: annual facts above.
- Debt to equity: (15,162,000,000 + 534,000,000) / 16,674,000,000 = 0.941346 x. Inputs: annual facts above.
  Definition: Long-term debt including current portion, excluding lease obligations, divided by stockholders' equity.
- Free cash flow: 4,757,000,000 - 1,450,000,000 = 3,307,000,000 USD. Inputs: annual facts above.
- P/E (latest fiscal-year diluted EPS): 510.65 / 29.08 = 17.560179 x. Inputs: annual facts above.

### Latest reported quarter

- Total revenue: 11,122 USD millions; prior-year quarter: 10,423 USD millions. 0001133421-26-000037, Exhibit 99 L238; table header: | Three Months Ended September 30 | | Nine Months Ended September 30; column dates: $ in millions, except per share amounts | 2026 | | 2025 | | 2026 | | 2025.
  Source quote: Total sales | 11,122 | | | 10,423 | | | 31,879 | | | 30,242 |
- GAAP diluted EPS: 7.89 USD/share; prior-year quarter: 7.67 USD/share. 0001133421-26-000037, Exhibit 99 L256; table header: | Three Months Ended September 30 | | Nine Months Ended September 30; column dates: $ in millions, except per share amounts | 2026 | | 2025 | | 2026 | | 2025.
  Source quote: Diluted earnings per share | $ | 7.89 | | | $ | 7.67 | | | $ | 21.72 | | | $ | 19.12 |
- Quarterly revenue growth: (11,122 - 10,423) / 10,423 * 100 = 6.706323%. Inputs: the two release revenue columns above.

### Peer operating margins

- RTX: 9,300,000,000 / 88,603,000,000 * 100 = 10.496259%. Operating income: 0000101829-26-000006, `us-gaap:OperatingIncomeLoss`, 2025-01-01 to 2025-12-31; total revenue: 0000101829-26-000006, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, 2025-01-01 to 2025-12-31.
- LMT: 7,731,000,000 / 75,048,000,000 * 100 = 10.301407%. Operating income: 0001628280-26-004195, `us-gaap:OperatingIncomeLoss`, 2025-01-01 to 2025-12-31; total revenue: 0001628280-26-004195, `us-gaap:Revenues`, 2025-01-01 to 2025-12-31.
- GD: 5,356,000,000 / 52,550,000,000 * 100 = 10.192198%. Operating income: 0000040533-26-000006, `us-gaap:OperatingIncomeLoss`, 2025-01-01 to 2025-12-31; total revenue: 0000040533-26-000006, `us-gaap:Revenues`, 2025-01-01 to 2025-12-31.

## Future Developments and Strategic Recommendations

Key catalysts for the next 12‑24 months are **accelerated B‑21 production**, pending agreement with the Air Force [10‑K L543‑L549]; **Sentinel program restructuring** and potential contract incentives [10‑K L551‑L555]; and **new awards** in 2026, including $4.6 billion for restricted programs, $2.0 billion for Sentinel, $1.4 billion for Virginia‑class submarines and $1.3 billion for F‑35 [Exhibit 99 L91‑L92]. The OBBBA’s tax provisions (full expensing of R&D, extended bonus depreciation) improve cash flow and margin potential [10‑K L610‑L615]. Recommendations: (1) **Invest in production capacity** for B‑21 and F‑35 sustainment to capture higher fixed‑price margins; (2) **Prioritize the SDA and Next‑Gen OPIR space programs** to leverage the growing demand for missile‑warning and resilient communications; (3) **Mitigate raw‑material and supply‑chain risks** by expanding strategic supplier relationships and inventory buffers, as past material shortages have not yet materially impacted performance but remain a disclosed risk [10‑K L212‑L213]; (4) **Maintain talent pipeline** for security‑clearance‑required roles to sustain execution of high‑complexity programs [10‑K L218‑L229]; (5) **Monitor regulatory and budgetary headwinds**, including potential government shutdowns, debt‑ceiling negotiations and executive‑order changes that could affect contract funding [10‑K L536‑L543, L188‑L191]. These actions should reinforce Northrop Grumman’s competitive position while managing the identified risks.

## Investment Recommendation

**Recommendation: Buy**

Northrop Grumman benefits from a robust order pipeline, highlighted by a book‑to‑bill ratio of 1.5×, indicating that new bookings are outpacing billings and supporting future revenue growth. The firm’s high‑margin cost‑type and fixed‑price contracts, strong operating margin around 10 % and a healthy backlog further reinforce its defensive position in a government‑driven market. Risks include reliance on U.S. defense appropriations, potential budgetary headwinds, and supply‑chain constraints that could affect program execution.

Recommendation: Buy

Deciding number: 1.5× (book‑to‑bill ratio) – source: third‑quarter 2026 earnings release, Exhibit 99 L18‑L21, L37‑L42, L370‑L377; definition: bookings divided by billings, >1 signals demand exceeds supply.


This is a learning exercise, not financial advice.
AI assistance: Codex and Purdue GenAI Studio (gpt-oss:120b).
Human source verification and sign-off are pending. This draft must not be presented as audited.
