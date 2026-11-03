# Checkpoint 1 preparation

Status: the four model roles are implemented with Purdue's `gpt-oss:120b`.
The NOC report and evidence are saved. Ryan Lease’s student audit is recorded,
including his final Buy recommendation and Correct mark. Samuel Parfait’s two
Correct partner checks (SP, November 2, 2026) and the course disclosure are
recorded. No human mark is an AI sign-off. Nothing has been submitted to
Brightspace.

Revised deadline reported by Ryan Lease: November 3, 2026, at 11:59 PM Eastern.
This extension is student-provided; it is not represented here as independently
verified on the public schedule. Submit a GitHub commit permalink in Brightspace → Checkpoint 1. The commit must contain the desk and a
report about the company chosen by your partner. The checkpoint is individual,
worth 17.5% of the course grade, and scored 100 or 0. A course-approved fallback
report counts.

Sources:

- [Schedule](https://cinderzhang.github.io/FIN67110-Fall2026/schedule.html)
- [Lab 03 requirements](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/lab-03-make-it-yours.html)
- [Grading](https://cinderzhang.github.io/FIN67110-Fall2026/grading.html)
- [Audit rules](https://cinderzhang.github.io/FIN67110-Fall2026/reference/audit-checklist.html)
- [Fallback](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/index.html#the-fallback)

## Prepared

- Your NOC submission report: [Northrop Grumman report](reports/NOC.md), generated November 1,
  2026 with `gpt-oss:120b`. All four model roles completed; after one Advisor
  revision, the manager requested no further corrections. P/E is 17.56 times:
  the supplied October 19, 2026 price of USD 510.65 divided by latest annual
  GAAP diluted EPS of USD 29.08 for fiscal-year 2025. The student's source is
  LSEG through Northrop Grumman Historical Price Lookup; provenance is saved in
  `evidence/NOC/price_reference.json`. Peers
  are RTX, LMT, and GD. The [NOC audit sheet](audits/NOC.md) records Ryan’s
  confirmed checks, including all 11 core financial claims, additional numerical
  checks, and the five-part template. Original findings remain recorded after
  text revisions. The [NOC evidence](evidence/NOC/) includes source texts and role
  calls. The [review notes](reports/NOC-review-notes.md) distinguish confirmed
  human findings from AI source checking. The student recommendation mark and
  audit totals are recorded. Samuel Parfait’s two Correct partner checks and
  the final course disclosure are included. Final editorial corrections are
  identified separately in the review notes.
  The price source adjusts historical prices for subsequent splits and/or
  dividends; a 1:1 split factor does not establish an unadjusted price.
- Existing partner-company draft: [RTX report](reports/RTX.md). Your practice audit:
  [COST report](reports/COST.md). Both model reviews finished without requests
  for further corrections. This is not a human verification of their claims.
- Human worksheets: [RTX audit](audits/RTX.md) and [COST audit](audits/COST.md).
  Marks, error counts, and auditor names remain blank. Each report has two
  partner-check placeholders near its top, after the required opening lines.
- All 26 deterministic tests pass. The live Purdue connection and both complete
  four-role report runs also passed. The source texts, calculations, and role
  hand-offs are saved under `evidence/` for review.
- Assignment clarified by the student on November 1, 2026: the student's company
  is Northrop Grumman (NOC); the partner's company is RTX. The student reports
  completing the checks on the partner's RTX report. This statement does not
  supply the individual audit marks or identify which report version was checked.
- A standalone NOC report and its evidence are now saved. The existing RTX
  report remains a separate partner-company draft.
- Purdue GenAI Studio API connection verified; all four roles use `gpt-oss:120b`.
- `research_desk.py` runs the data steps and the four roles, saves a five-part
  Markdown report, and records the JSON hand-offs for review.
- RTX's selected earnings 8-K is `0000101829-26-000030`, accepted October 20,
  2026 at 06:57:06 on its EDGAR index. Its earnings release is labeled Exhibit
  99, not 99.1. The reader preserves the issuer's label.
- RTX's price input is USD 194.60, the October 27, 2026 close from the
  [issuer's price page](https://rtx.gcs-web.com/stock-information/historic-stock-lookup).
  That page identifies LSEG as the source and notes adjustments for splits and
  dividends. Peers are NOC, LMT, and GD.
- The seven data steps run on COST and WMT.
- COST uses the supplied price of USD 1,001.57 and peers WMT, TGT, and BJ.
  The price's market date and source have not been confirmed.
- WMT also runs with COST, TGT, and BJ as peers; no WMT price was supplied.
- A same-period revenue-tag test now prevents preferring net sales when the
  standard total-revenue tag is available for that year. Newest-year selection
  still takes priority over tag order.
- `evidence/` contains selected facts, calculations, source records, and filing
  texts from the preparation runs. These files can be committed; they contain
  no `.env` file or API key. Original full runs remain under ignored `runs/`.
- `audit-template.md` provides empty rows for the human audit.

## Submission

The submission consists of the desk, reviewed NOC report, source evidence, and
completed audit in this repository. The report’s top records Samuel’s two checks.
Ryan has already completed his checks on Samuel’s RTX report.

Submit the permanent link to the final pushed GitHub commit in Brightspace →
Checkpoint 1, then confirm receipt. A local folder or changing branch link is
not the requested commit permalink. These files do not claim that Brightspace
submission has occurred.

The COST audit is a Lab 03 exercise, not a separate Checkpoint 1 upload.

The report must contain these five parts: Overview; Market Positioning and
Growth Outlook; Valuation Insights; Future Developments and Strategic
Recommendations; Investment Recommendation. Its first line identifies the
filings and accession numbers; its second line records the run time.

## If using the fallback

Use the company chosen for you by your partner. Give a model chat the latest 10-K's income statement,
balance sheet, cash flow statement, and the latest earnings release. Ask it to
perform the four roles' tasks and produce the five report parts. Save the result
as Markdown. Name the company and filings on the first line and put `fallback`
on the second line. Audit it under the same rules, commit it, and push it.

## Repeat the full desk

```sh
.venv/bin/python research_desk.py NOC --peers RTX,LMT,GD --price 510.65 --price-date 2026-10-19 --price-source https://investor.northropgrumman.com/stock-information/historical-price-lookup
.venv/bin/python research_desk.py COST --peers WMT,TGT,BJ --price 1001.57
.venv/bin/python research_desk.py RTX --peers NOC,LMT,GD --price 194.60 --price-date 2026-10-27 --price-source https://rtx.gcs-web.com/stock-information/historic-stock-lookup
```

Add `--reuse` to use saved data. To run only the data steps, use `equity_desk.py`.
These commands do not submit anything to Brightspace.
