NORTHROP GRUMMAN CORP /DE/ (NOC); filings read: 10-Q 0001133421-26-000038 (primary document); 8-K 0001133421-26-000037 (primary document and Exhibit 99); 10-K 0001133421-26-000003 (primary document)

## Verifier marks

Run: `NOC-invented-growth`. Verified 2026-11-05T21:05:53-05:00 by `verifier.py` (code only, no model). Skipped: run metadata above the first section and the Investment Advisor's thesis.

**59 numbers: 57 Correct, 1 Wrong, 1 Unsupported.**

Core claims (Lab 03 template):

| Core claim | Item | Mark | Mark id |
| --- | --- | --- | --- |
| 1 | Total revenue (current) | Correct | V23 |
| 2 | Revenue growth | Correct | V42 |
| 3 | Operating income (current) | Correct | V25 |
| 3 | Operating margin | Correct | V43 |
| 4 | Net income (current) | Correct | V27 |
| 5 | Diluted EPS (current) | Correct | V29 |
| 6 | Return on average equity | Correct | V44 |
| 7 | Debt to equity | Correct | V45 |
| 8 | Free cash flow | Correct | V46 |
| 9 | Latest reported quarter: Total revenue | Correct | V48 |
| 10 | Quarterly revenue growth | Correct | V52 |
| 11 | Latest reported quarter: GAAP diluted EPS | Correct | V50 |

| Id | Section | Item | Number | Mark | Filing value | Why / arithmetic | Source (tag or line) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | Overview | Overview | 86 | **Correct** |  | on the cited line | 10-K L202 |
| V2 | Overview | Overview | 41.954 | **Correct** |  | on the cited line | 10-K L592-L594 |
| V3 | Overview | Overview | 41.8 | **Correct** |  | on the cited line | 10-K L592-L594 |
| V4 | Overview | Overview | 4.182 | **Correct** |  | equals a sourced value | NOC `us-gaap:NetIncomeLoss` current, accession 0001133421-26-000003 |
| V5 | Overview | Overview | 4.511 | **Correct** |  | equals a sourced value | NOC `us-gaap:OperatingIncomeLoss` current, accession 0001133421-26-000003 |
| V6 | Overview | Overview | 41.954 | **Correct** |  | equals a sourced value | NOC `us-gaap:Revenues` current, accession 0001133421-26-000003 |
| V7 | Overview | Overview | 10.8 | **Correct** |  | recomputed operating margin: 4,511,000,000 / 41,954,000,000 × 100 | facts.json, annual current and prior periods |
| V8 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 95.7 | **Correct** |  | on the cited line | 10-K L209 |
| V9 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 91.5 | **Correct** |  | on the cited line | 10-K L209 |
| V10 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 1.5 | **Unsupported** | 1.5 | not on the cited line; the number is on Exhibit 99 L17 (citation off by 1 line(s)) | Exhibit 99 L17 |
| V11 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 109.6 | **Correct** |  | on the cited line | Exhibit 99 L18-L21, Exhibit 99 L370-L377 |
| V12 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 15 | **Correct** |  | on the cited line | Exhibit 99 L18-L21, Exhibit 99 L370-L377 |
| V13 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 150 | **Correct** |  | on the cited line | 10-K L538-L543 |
| V14 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 50 | **Correct** |  | on the cited line | 10-K L255-L257 |
| V15 | Market Positioning and Growth Outlook | Market Positioning and Growth Outlook | 50 | **Correct** |  | on the cited line | 10-K L255-L257 |
| V16 | Valuation Insights / Northrop Grumman (NOC) | Northrop Grumman (NOC): Revenue growth | 41,033 | **Correct** |  | on the cited line | 10-K L592 |
| V17 | Valuation Insights / Northrop Grumman (NOC) | Northrop Grumman (NOC): Revenue growth | 41,954 | **Correct** |  | on the cited line | 10-K L592 |
| V18 | Valuation Insights / Northrop Grumman (NOC) | Northrop Grumman (NOC): Revenue growth | 6.24 | **Wrong** | 2.24 | recomputed revenue growth: (41,954,000,000 - 41,033,000,000) / 41,033,000,000 × 100 = 2.24 | facts.json, annual current and prior periods |
| V19 | Valuation Insights / Northrop Grumman (NOC) | Northrop Grumman (NOC): Leverage | 0.941346 | **Correct** |  | recomputed debt to equity: (15,162,000,000 + 534,000,000) / 16,674,000,000 | facts.json, annual current and prior periods |
| V20 | Valuation Insights / Northrop Grumman (NOC) | Northrop Grumman (NOC): Valuation | 510.65 | **Correct** |  | equals a sourced value | supplied price, 2026-10-19, https://investor.northropgrumman.com/stock-information/historical-price-lookup |
| V21 | Valuation Insights / Northrop Grumman (NOC) | Northrop Grumman (NOC): Valuation | 29.08 | **Correct** |  | recomputed diluted eps: facts.json diluted EPS 29.08 | `us-gaap:EarningsPerShareDiluted`, 2025-01-01 to 2025-12-31, accession 0001133421-26-000003; 10-K L997: "Diluted earnings per share \| \| $ \| 29.08 \| \| \| $ \| 28.34 \| \| \| $ \| 13.53 \|" |
| V22 | Valuation Insights / Northrop Grumman (NOC) | Northrop Grumman (NOC): Valuation | 17.56 | **Correct** |  | recomputed p/e: 510.65 / 29.08 | supplied price / facts.json annual diluted EPS |
| V23 | Valuation Insights / Python evidence for the financial analysis | Total revenue (current) | 41,954,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:Revenues`, 2025-01-01 to 2025-12-31, accession 0001133421-26-000003; 10-K L2084: "Total sales \| \| $ \| 41,954 \| \| \| $ \| 41,033 \| \| \| $ \| 39,290 \|" |
| V24 | Valuation Insights / Python evidence for the financial analysis | Total revenue (prior) | 41,033,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:Revenues`, 2024-01-01 to 2024-12-31, accession 0001133421-26-000003; 10-K L2084: "Total sales \| \| $ \| 41,954 \| \| \| $ \| 41,033 \| \| \| $ \| 39,290 \|" |
| V25 | Valuation Insights / Python evidence for the financial analysis | Operating income (current) | 4,511,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:OperatingIncomeLoss`, 2025-01-01 to 2025-12-31, accession 0001133421-26-000003; 10-K L985: "Operating income \| \| 4,511 \| \| \| 4,370 \| \| \| 2,537 \|" |
| V26 | Valuation Insights / Python evidence for the financial analysis | Operating income (prior) | 4,370,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:OperatingIncomeLoss`, 2024-01-01 to 2024-12-31, accession 0001133421-26-000003; 10-K L985: "Operating income \| \| 4,511 \| \| \| 4,370 \| \| \| 2,537 \|" |
| V27 | Valuation Insights / Python evidence for the financial analysis | Net income (current) | 4,182,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:NetIncomeLoss`, 2025-01-01 to 2025-12-31, accession 0001133421-26-000003; 10-K L1118: "Net earnings \| \| 4,182 \| \| \| 4,174 \| \| \| 2,056 \|" |
| V28 | Valuation Insights / Python evidence for the financial analysis | Net income (prior) | 4,174,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:NetIncomeLoss`, 2024-01-01 to 2024-12-31, accession 0001133421-26-000003; 10-K L1118: "Net earnings \| \| 4,182 \| \| \| 4,174 \| \| \| 2,056 \|" |
| V29 | Valuation Insights / Python evidence for the financial analysis | Diluted EPS (current) | 29.08 | **Correct** |  | equals facts.json exactly | `us-gaap:EarningsPerShareDiluted`, 2025-01-01 to 2025-12-31, accession 0001133421-26-000003; 10-K L997: "Diluted earnings per share \| \| $ \| 29.08 \| \| \| $ \| 28.34 \| \| \| $ \| 13.53 \|" |
| V30 | Valuation Insights / Python evidence for the financial analysis | Diluted EPS (prior) | 28.34 | **Correct** |  | equals facts.json exactly | `us-gaap:EarningsPerShareDiluted`, 2024-01-01 to 2024-12-31, accession 0001133421-26-000003; 10-K L997: "Diluted earnings per share \| \| $ \| 29.08 \| \| \| $ \| 28.34 \| \| \| $ \| 13.53 \|" |
| V31 | Valuation Insights / Python evidence for the financial analysis | Stockholders' equity (current) | 16,674,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:StockholdersEquity`, instant to 2025-12-31, accession 0001133421-26-000003; 10-K L1126: "Total shareholders’ equity \| \| $ \| 16,674 \| \| \| $ \| 15,290 \| \| \| $ \| 14,795 \|" |
| V32 | Valuation Insights / Python evidence for the financial analysis | Stockholders' equity (prior) | 15,290,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:StockholdersEquity`, instant to 2024-12-31, accession 0001133421-26-000003; 10-K L1126: "Total shareholders’ equity \| \| $ \| 16,674 \| \| \| $ \| 15,290 \| \| \| $ \| 14,795 \|" |
| V33 | Valuation Insights / Python evidence for the financial analysis | Long-term debt, excluding current portion (current) | 15,162,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:LongTermDebtNoncurrent`, instant to 2025-12-31, accession 0001133421-26-000003; 10-K L1593: "Long-term debt, net of current portion \| \| \| \| $ \| 15,162 \| \| \| $ \| 14,692 \|" |
| V34 | Valuation Insights / Python evidence for the financial analysis | Long-term debt, excluding current portion (prior) | 14,692,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:LongTermDebtNoncurrent`, instant to 2024-12-31, accession 0001133421-26-000003; 10-K L1593: "Long-term debt, net of current portion \| \| \| \| $ \| 15,162 \| \| \| $ \| 14,692 \|" |
| V35 | Valuation Insights / Python evidence for the financial analysis | Current portion of long-term debt (current) | 534,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:LongTermDebtCurrent`, instant to 2025-12-31, accession 0001133421-26-000003 |
| V36 | Valuation Insights / Python evidence for the financial analysis | Current portion of long-term debt (prior) | 1,582,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:LongTermDebtCurrent`, instant to 2024-12-31, accession 0001133421-26-000003 |
| V37 | Valuation Insights / Python evidence for the financial analysis | Cash from operations (current) | 4,757,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2025-01-01 to 2025-12-31, accession 0001133421-26-000003; 10-K L1080: "Net cash provided by operating activities \| \| 4,757 \| \| \| 4,388 \| \| \| 3,875 \|" |
| V38 | Valuation Insights / Python evidence for the financial analysis | Cash from operations (prior) | 4,388,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:NetCashProvidedByUsedInOperatingActivities`, 2024-01-01 to 2024-12-31, accession 0001133421-26-000003; 10-K L1080: "Net cash provided by operating activities \| \| 4,757 \| \| \| 4,388 \| \| \| 3,875 \|" |
| V39 | Valuation Insights / Python evidence for the financial analysis | Additions to property and equipment (current) | 1,450,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2025-01-01 to 2025-12-31, accession 0001133421-26-000003; 10-K L1083: "Capital expenditures \| \| ( 1,450 ) \| \| \| ( 1,767 ) \| \| \| ( 1,775 ) \|" |
| V40 | Valuation Insights / Python evidence for the financial analysis | Additions to property and equipment (prior) | 1,767,000,000 | **Correct** |  | equals facts.json exactly | `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, 2024-01-01 to 2024-12-31, accession 0001133421-26-000003; 10-K L1083: "Capital expenditures \| \| ( 1,450 ) \| \| \| ( 1,767 ) \| \| \| ( 1,775 ) \|" |
| V41 | Valuation Insights / Python evidence for the financial analysis | Valuation Insights / Python evidence for the financial analysis | 510.65 | **Correct** |  | equals a sourced value | supplied price, 2026-10-19, https://investor.northropgrumman.com/stock-information/historical-price-lookup |
| V42 | Valuation Insights / Python evidence for the financial analysis | Revenue growth | 2.244535 | **Correct** |  | recomputed: (41,954,000,000 - 41,033,000,000) / 41,033,000,000 * 100 = 2.244535 | arithmetic of the stated inputs |
| V43 | Valuation Insights / Python evidence for the financial analysis | Operating margin | 10.752252 | **Correct** |  | recomputed: 4,511,000,000 / 41,954,000,000 * 100 = 10.752252 | arithmetic of the stated inputs |
| V44 | Valuation Insights / Python evidence for the financial analysis | Return on average equity | 26.166938 | **Correct** |  | recomputed: 4,182,000,000 / ((16,674,000,000 + 15,290,000,000) / 2) * 100 = 26.166938 | arithmetic of the stated inputs |
| V45 | Valuation Insights / Python evidence for the financial analysis | Debt to equity | 0.941346 | **Correct** |  | recomputed: (15,162,000,000 + 534,000,000) / 16,674,000,000 = 0.941346 | arithmetic of the stated inputs |
| V46 | Valuation Insights / Python evidence for the financial analysis | Free cash flow | 3,307,000,000 | **Correct** |  | recomputed: 4,757,000,000 - 1,450,000,000 = 3307000000.000000 | arithmetic of the stated inputs |
| V47 | Valuation Insights / Python evidence for the financial analysis | P/E (latest fiscal-year diluted EPS) | 17.560179 | **Correct** |  | recomputed: 510.65 / 29.08 = 17.560179 | arithmetic of the stated inputs |
| V48 | Valuation Insights / Latest reported quarter | Latest reported quarter: Total revenue | 11,122 | **Correct** |  | on the cited line | Exhibit 99 L238 |
| V49 | Valuation Insights / Latest reported quarter | Latest reported quarter: Total revenue | 10,423 | **Correct** |  | on the cited line | Exhibit 99 L238 |
| V50 | Valuation Insights / Latest reported quarter | Latest reported quarter: GAAP diluted EPS | 7.89 | **Correct** |  | on the cited line | Exhibit 99 L256 |
| V51 | Valuation Insights / Latest reported quarter | Latest reported quarter: GAAP diluted EPS | 7.67 | **Correct** |  | on the cited line | Exhibit 99 L256 |
| V52 | Valuation Insights / Latest reported quarter | Quarterly revenue growth | 6.706323 | **Correct** |  | recomputed: (11,122 - 10,423) / 10,423 * 100 = 6.706323 | arithmetic of the stated inputs |
| V53 | Valuation Insights / Peer operating margins | RTX | 10.496259 | **Correct** |  | recomputed: 9,300,000,000 / 88,603,000,000 * 100 = 10.496259 | arithmetic of the stated inputs |
| V54 | Valuation Insights / Peer operating margins | LMT | 10.301407 | **Correct** |  | recomputed: 7,731,000,000 / 75,048,000,000 * 100 = 10.301407 | arithmetic of the stated inputs |
| V55 | Valuation Insights / Peer operating margins | GD | 10.192198 | **Correct** |  | recomputed: 5,356,000,000 / 52,550,000,000 * 100 = 10.192198 | arithmetic of the stated inputs |
| V56 | Future Developments and Strategic Recommendations | Future Developments and Strategic Recommendations | 4.6 | **Correct** |  | on the cited line | 10-Q L710, 10-K L551-L555, Exhibit 99 L91-L92 |
| V57 | Future Developments and Strategic Recommendations | Future Developments and Strategic Recommendations | 2.0 | **Correct** |  | on the cited line | 10-Q L710, 10-K L551-L555, Exhibit 99 L91-L92 |
| V58 | Future Developments and Strategic Recommendations | Future Developments and Strategic Recommendations | 1.4 | **Correct** |  | on the cited line | 10-Q L710, 10-K L551-L555, Exhibit 99 L91-L92 |
| V59 | Future Developments and Strategic Recommendations | Future Developments and Strategic Recommendations | 1.3 | **Correct** |  | on the cited line | 10-Q L710, 10-K L551-L555, Exhibit 99 L91-L92 |

A code check cannot tell whether a number on the cited line is for the period and definition the sentence claims. Human audit is still needed.

Report run time: 2026-11-01T20:44:30.132575-05:00

**Partner check 1 — FY2025 total sales:** USD 41,954 million for the year ended December 31, 2025. **Mark: Correct.**
Partner: Samuel Parfait (**SP**). Date checked: **November 2, 2026**. Filing evidence: [SEC 10-K](https://www.sec.gov/Archives/edgar/data/1133421/000113342126000003/noc-20251231.htm), accession **0001133421-26-000003**, Consolidated Statements of Earnings and Comprehensive Income, printed page **48**, Total sales row, 2025 column. Samuel reported that the value, annual period, and dollars-in-millions unit match the report.

**Partner check 2 — FY2025 GAAP diluted EPS:** USD 29.08 per share for the year ended December 31, 2025. **Mark: Correct.**
Partner: Samuel Parfait (**SP**). Date checked: **November 2, 2026**. Filing evidence: [SEC 10-K](https://www.sec.gov/Archives/edgar/data/1133421/000113342126000003/noc-20251231.htm), accession **0001133421-26-000003**, the same statement on printed page **48**, Diluted earnings per share row, 2025 column. Samuel reported that the value, period, and dollars-per-share unit match. This is GAAP diluted EPS, not adjusted EPS or weighted-average diluted shares outstanding.

Human audit worksheet: [audits/NOC.md](../audits/NOC.md). Source evidence: [evidence/NOC/](../evidence/NOC/).

Human review update — November 1, 2026: Ryan Lease marked the original book-to-bill interpretation Unsupported. The 1.5-times numerical claim remains Correct. He also checked the new B-21 capacity-investment claim against the 10-Q and marked it Correct. He marked the original backlog growth period Unsupported after comparing the filing dates; the report now states growth from December 31, 2025 to September 30, 2026. The audit retains these original findings.

Human review update — November 2, 2026: Ryan Lease checked the 10-K Contracts passage and marked the broad high-margin contract claim Unsupported. The report now describes the relative margins, cost-growth risks, and possible variation in actual margins. He also marked the sector P/E interpretation Unsupported after reviewing differences in the earnings basis of the proposed benchmarks. The numerical P/E remains Correct; the report now states the calculation and its limitation. The audit retains all four original findings. Ryan marked the leverage interpretation Correct, using balanced to mean near-equal debt and book equity amounts; that meaning is now explicit. Ryan retained Buy and marked the revised recommendation Correct on November 2, 2026. The recorded student audit is complete. Samuel Parfait’s two Correct partner checks, dated November 2, 2026 and supplied by Ryan, are recorded above. The course disclosure is included below.

Price: USD 510.65, October 19, 2026. Source supplied by the student: [LSEG through Northrop Grumman Historical Price Lookup](https://investor.northropgrumman.com/stock-information/historical-price-lookup).
P/E definition: supplied share price divided by latest fiscal-year GAAP diluted EPS. For fiscal year ended December 31, 2025: USD 510.65 / USD 29.08 = 17.56 times.

**Price qualification:** The [historical price source](https://investor.northropgrumman.com/stock-information/historical-price-lookup) adjusts its displayed historical prices for subsequent stock splits and/or dividends. The observed split adjustment factor is 1:1. That factor does not establish that the price is unadjusted for dividends. This P/E uses the displayed historical price of USD 510.65 and FY2025 GAAP diluted EPS. The source qualification was read by Codex and is also recorded in the human audit.

AI review notes: [items for human review](NOC-review-notes.md). These are not audit marks.


Model: `gpt-oss:120b` via Purdue GenAI Studio.
Status: READY FOR CHECKPOINT 1 SUBMISSION — student audit, two partner checks, and course disclosure recorded.
The model roles used 10-K Business/MD&A excerpts, 10-Q MD&A excerpts, annual XBRL facts, and Exhibit 99.

## Overview

Northrop Grumman is a **global aerospace and defense technology company** that delivers a broad range of products, services and solutions primarily to the U.S. Department of War and intelligence community [10-K L128]. Its portfolio spans **space systems, military aircraft, missile‑defense, advanced weapons, mission systems, networking, communications and breakthrough technologies** [10-K L129‑L130]. The firm is organized into four reportable **operating sectors** – Aeronautics Systems, Defense Systems, Mission Systems and Space Systems – each responsible for design, development, production, integration, sustainment and modernization of key programs [10-K L140‑L147]. Sales are overwhelmingly government‑driven, with the **U.S. government accounting for ~86 % of total sales** in recent years [10-K L202]. The company reports **total sales (net revenue)** of $41.954 billion for 2025, of which **organic sales** (excluding the divested training services business) are $41.8 billion [10-K L592‑L594]. Net earnings were $4.182 billion in 2025. Operating income of $4.511 billion divided by sales of $41.954 billion gives an operating margin of approximately 10.8% [10-K, Consolidated Statements of Earnings and Comprehensive Income, printed page 48; calculations below]. The firm’s business model relies on long‑term **cost‑type and fixed‑price contracts** governed by FAR and CAS, with revenue recognized over time as costs are incurred [10-K L556‑L558].

## Market Positioning and Growth Outlook

Northrop Grumman competes with **Boeing, Lockheed Martin, General Dynamics, L3Harris and RTX**, among others, in a market characterized by long operating cycles and intense competition [10-K L203‑L205]. Its **backlog** grew to **$95.7 billion at year‑end 2025**, up from $91.5 billion in 2024, indicating a strong pipeline of future work [10-K L209]. The **third‑quarter 2026 earnings release** reported a **book‑to‑bill ratio of ~~1.5~~ **1.5** [V10]×** and **backlog of $109.6 billion as of September 30, 2026**, up 15% from December 31, 2025 [Exhibit 99 L18–L21, L370–L377]. Growth drivers include the **B‑21 long‑range strike aircraft**, **F‑35 sustainment**, **Sentinel intercontinental ballistic missile modernization program** [10-K L158], **Space Development Agency (SDA) tracking and transport layers**, and **Cygnus CRS missions** [10‑K L148‑L155, L190‑L199, L542‑L549, L551‑L555, L195‑L200]. The **One Big Beautiful Bill Act (OBBBA)** allocated ~$150 billion for defense spending, supporting continued investment in air, missile‑defense and space modernization [10‑K L538‑L543]. No material portion of the company’s business is seasonal [10-K L207]. In 2025, approximately 50% of sales came from cost-type contracts and 50% from fixed-price contracts [10-K L255–L257]. Contract margins may vary materially; this sales mix does not by itself establish high margins [10-K L246–L248].

## Valuation Insights

### Northrop Grumman (NOC)
- **Revenue trend**: The annual *Total revenue* row (accession 0001133421‑26‑000003) shows a modest increase year‑over‑year, confirming the *Revenue growth* calculation.
- **Revenue growth**: Total revenue rose from USD 41,033 million to USD 41,954 million [10-K L592], so annual revenue growth was ~~6.24~~ **2.24** [V18]%.
- **Profitability**: *Operating income* (same accession) relative to *Total revenue* yields an operating margin just above ten percent, matching the *Operating margin* metric. The quarterly *Total sales* line (L238) indicates a higher short‑term growth rate, but the three‑month figure is not directly comparable to full‑year margins.
- **Return on equity**: Using *Net income* and the average of the two *Stockholders' equity* rows (accession 0001133421‑26‑000003) produces a ROE in the mid‑twenties percent, reflecting strong earnings generation on the equity base.
- **Leverage**: At December 31, 2025, long-term debt, including its current portion and excluding lease obligations, divided by book shareholders’ equity was 0.941346 times (10-K accession 0001133421-26-000003). In this report, a balanced capital structure means these debt and book equity amounts were nearly equal under the stated definition.
- **Cash generation**: *Cash from operations* minus *Additions to property and equipment* (both accession 0001133421‑26‑000003) results in positive free cash flow, supporting ongoing investment and dividend capacity.
- **Valuation**: Using the supplied October 19, 2026 price of USD 510.65 and FY2025 GAAP diluted EPS of USD 29.08 (10-K accession 0001133421-26-000003), NOC’s P/E is 17.56 times. This calculation alone does not establish whether the shares are inexpensive relative to peers. The historical-price adjustment qualification above applies.
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

Developments to monitor include **the agreed expansion of B-21 production capacity and aircraft production rate**, under the agreement reached with the Air Force in Q1 2026 [10-Q L710]; **Sentinel program restructuring** and potential contract incentives [10‑K L551‑L555]; and **new awards** in 2026, including $4.6 billion for restricted programs, $2.0 billion for Sentinel, $1.4 billion for Virginia‑class submarines and $1.3 billion for F‑35 [Exhibit 99 L91‑L92]. The company recognized the effects of the OBBBA’s tax provisions, including reinstated full expensing of R&D and extended bonus depreciation, in its 2025 financial statements [10-K L610–L615]. Recommendations: (1) **Invest in production capacity** for B‑21 and F‑35 sustainment to seek potential margin improvements while managing execution and cost-growth risks [10-K L246–L248]; (2) **Prioritize the SDA and Next‑Gen OPIR space programs** to leverage the growing demand for missile‑warning and resilient communications; (3) **Mitigate raw‑material and supply‑chain risks** by expanding strategic supplier relationships and inventory buffers, as past material shortages have not yet materially impacted performance but remain a disclosed risk [10‑K L212‑L213]; (4) **Maintain talent pipeline** for security‑clearance‑required roles to sustain execution of high‑complexity programs [10‑K L218‑L229]; (5) **Monitor regulatory and budgetary headwinds**, including potential government shutdowns, debt‑ceiling negotiations and executive‑order changes that could affect contract funding [10‑K L536‑L543, L188‑L191]. These actions should reinforce Northrop Grumman’s competitive position while managing the identified risks.

## Investment Recommendation

**Recommendation: Buy**

Northrop Grumman reported a Q3 2026 book-to-bill ratio of 1.5 times. Net awards exceeded sales during the quarter. [SEC earnings release](https://www.sec.gov/Archives/edgar/data/1133421/000113342126000037/noc-09302026xearningsrelea.htm). The firm’s operating margin around 10% and its backlog support the report’s positive view. Cost-type contracts generally provide lower profit margins than fixed-price contracts and less financial risk from unexpected cost growth. Fixed-price contracts offer an opportunity for higher profit margins but typically carry more financial risk from unexpected cost growth. Contract margins may vary materially. [SEC 10-K, Business, Contracts, printed page 6](https://www.sec.gov/Archives/edgar/data/1133421/000113342126000003/noc-20251231.htm) (saved 10-K.txt L246–L248). Risks include reliance on U.S. defense appropriations, potential budgetary headwinds, and supply‑chain constraints that could affect program execution.

**Deciding number: 1.5 times, the Q3 2026 book-to-bill ratio.** Northrop Grumman defines this ratio as net awards divided by sales. A ratio above 1 means net awards exceeded sales during the period. [Company definition, slide 4 (supplemental source)](https://investor.northropgrumman.com/static-files/dcb23024-298b-4464-a012-3a9f8b8dc1c1).

**Capacity caveat:** Separately, Northrop Grumman reported that it reached an agreement with the U.S. Air Force in Q1 2026 to expand B-21 production capacity and increase the aircraft production rate. It expected to invest approximately $2.5 billion over a multi-year period to expand that capacity. [Q3 2026 SEC 10-Q, MD&A, B-21 Program](https://www.sec.gov/Archives/edgar/data/1133421/000113342126000038/noc-20260930.htm) (saved 10-Q.txt L710). This is evidence of capacity expansion for that program. The book-to-bill ratio alone does not establish a company-wide supply shortage.


This is a learning exercise, not financial advice.
AI assistance: Codex, Purdue GenAI Studio (gpt-oss:120b), and Claude for supplemental research discussion. I verified the sources myself; the judgments are mine.
Any remaining errors are my own.
