# Equity research data desk

`equity_desk.py` implements the data tools that support the filing analysis,
financial calculations, and peer comparisons in Section 3.1 of Francis and
Zhang (2026). The source paper is `FRL-CanAIReplaceAnalyst.pdf` in this repository,
pages 2–4. `research_desk.py` adds the four model roles through Purdue GenAI
Studio, using `gpt-oss:120b` and the official OpenAI Python SDK.

Checkpoint 1 requirements, preparation status, and the recorded student audit are in
[`checkpoint-1/`](checkpoint-1/README.md).

The main entry point is **`research_desk.py`**. Keep these files together in the
project root:

| File | Purpose |
| --- | --- |
| `research_desk.py` | Runs the seven data steps and four model roles; writes the report |
| `equity_desk.py` | Retrieves SEC filings and facts and calculates financial ratios |
| `model_client.py` | Connects to Purdue GenAI Studio using settings from `.env` |
| `requirements.txt` | Lists the Python packages to install |
| `.env.example` | Provides settings placeholders; contains no credentials |
| `.gitignore` | Excludes `.env`, `.venv`, and local generated runs |
| `README.md` | Provides setup and run instructions |

The saved Checkpoint 1 report is [NOC.md](checkpoint-1/reports/NOC.md).
Its [source evidence](checkpoint-1/evidence/NOC/) and
[human audit sheet](checkpoint-1/audits/NOC.md) are included. The audit records
Ryan Lease’s confirmed checks, including the final Buy recommendation, and
Samuel Parfait’s two partner checks. The report includes the course disclosure.
`test_equity_desk.py` and `test_research_desk.py` provide verification tests;
they are not required to run the desk. The paper and prompt library document
the design and are not runtime dependencies.

Use Python 3.10 or later. Run these commands from this folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Before running the desk, create a local `.env` from `.env.example` if you do not
already have one. Set `SEC_USER_AGENT` to your name and email, and `API_KEY` to
your Purdue GenAI Studio key. Keep `.env` private. The `.venv` directory is
created locally by the setup command; it is not part of the Git repository.

To run the full desk, including the model report:

```sh
.venv/bin/python research_desk.py NOC --peers RTX,LMT,GD --price 510.65 --price-date 2026-10-19 --price-source https://investor.northropgrumman.com/stock-information/historical-price-lookup
```

The NOC price, date, and LSEG source attribution were supplied by the student.
The source record is [price_reference.json](checkpoint-1/evidence/NOC/price_reference.json).
P/E uses the supplied price divided by latest fiscal-year GAAP diluted EPS.
The source adjusts historical prices for subsequent splits and/or dividends.
The observed 1:1 split factor does not establish that the price is unadjusted
for dividends. The report uses the displayed historical price; see the
[human price check and qualification](checkpoint-1/audits/NOC.md).
Change the ticker, peers, price and price reference for a different company.

To run only the data steps, without model calls, use this example:

```sh
.venv/bin/python equity_desk.py AAPL --peers MSFT GOOGL --price 200
```

The model settings in `.env` are:

```dotenv
API_KEY=your-purdue-genai-studio-key
SEC_USER_AGENT="Your Name your-email@example.edu"
API_BASE_URL=https://genai.rcac.purdue.edu/api
MODEL=gpt-oss:120b
```

One Purdue key serves all four roles. Calls go to Purdue, not OpenAI's hosted
API. Test the connection with `.venv/bin/python model_client.py`. The script
prints the requested and returned model IDs, without printing the key.

Add `--reuse` to `research_desk.py` to use the latest saved data run for a ticker.
The saved steps must be complete. Supplied peers must match the saved peer list.
A supplied price recalculates step 5; it does not fetch a market price. Date and
source flags must be supplied together with the price. Full source texts remain
available even when model input uses shorter excerpts.

The manager sends separate JSON tasks to Research Analyst, Financial Analyst,
Investment Advisor, and Strategy Manager. The Research Analyst receives Business
and MD&A excerpts and the release. The Financial Analyst receives annual facts,
Python calculations, quarterly evidence, peer facts, and 10-Q MD&A excerpts.
Each Business/MD&A excerpt is limited to the first 25,000 characters on complete
lines. The Investment Advisor receives only the two analysts' outputs and their
Python evidence. The manager reviews the assembled five parts and may request
one revision per role. A changed analyst output also triggers one advisor
revision. The model's review does not replace the required human audit.

Additional financial calculations use a restricted Python expression reader;
the model may request at most four expressions in one round. They can use only
known fact names, arithmetic, and constants 0, 1, 2, 100. Python supplies the
report's core numerical evidence table. Model-written claims can still be wrong.

Model outputs are `report.md`, `role_calls.json`, `quarter_facts.json`, and
`report_status.json` in the run folder. Unresolved manager corrections produce
`report_draft.md` and a nonzero exit status. Every report remains an unaudited
draft until the student and partner complete their required checks. No script
fills human marks or claims that human source verification has occurred.

The tickers and price above are example inputs. `200` is a supplied USD price,
not a fetched market price. The program has no company names or ticker defaults.
Peers can be separated by spaces or commas. A dot in a ticker is normalized to
a hyphen for SEC lookup.

The program reads `SEC_USER_AGENT` directly from the `.env` beside the script.
It does not print the value. Every HTTP request, retry, and redirect uses that
header. The SEC data layer does not use `API_KEY`; the model client does. SEC requests are sequential, with at least 0.21
seconds between starts, and retries are limited. The implementation follows the
[SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
and [SEC access guidance](https://www.sec.gov/about/developer-resources).

Each full run prints seven steps:

1. Resolve the ticker from SEC `company_tickers.json` and print the CIK.
2. Print filing records from the submissions API. Select the latest original
   10-K, 10-Q, and 8-K with Item 2.02 in its primary document. Read older submission
   files if needed. Print each accession and the exact `Accepted` display value
   from its EDGAR index page. The displayed time is not converted to UTC.
3. Save all three primary documents plus the selected 8-K's Exhibit 99.1. Save
   each original and its plain text. An absent or ambiguous Exhibit 99.1 produces
   an error; the program does not silently select an older release. If an issuer
   supplies a single EX-99 and its Item 2.02 document explicitly identifies that
   exhibit, the reader accepts it and retains the actual `Exhibit 99` label.
4. Save raw company facts. Print the nine requested concepts for revenue's latest
   fiscal period, with the prior fiscal period beside it. Each available value
   includes its unit, tag, period end, accession, and filing date.
5. Calculate revenue growth, operating margin, return on average equity, debt to
   equity, free cash flow, and P/E. Print the substituted numbers and arithmetic.
6. Print source lines for quarterly revenue and diluted EPS from Exhibit 99.1,
   with line numbers and nearby context. Table matches include available period
   headings and units. Preserve GAAP/non-GAAP labels and comparative columns.
7. Fetch the same annual facts for each peer. Calculate operating income divided
   by revenue on the same definition. Each peer uses its own latest fiscal year;
   its period dates are printed so different year ends remain visible.

Outputs are saved under `runs/<SEC company name>__<local date and time>/`.
The timestamp includes the UTC offset and microseconds. Main outputs are:

| File | Contents |
| --- | --- |
| `manifest.json` | Company, run time, and step status |
| `submissions.json`, `filings.json` | Original submissions and the filing list |
| `selected_filings.json`, `*_index.html` | Selected accessions, index pages, and Accepted times |
| `10-K.txt`, `10-Q.txt`, `8-K.txt`, `earnings_release.txt` | Plain text, with original HTML or PDF beside it |
| `documents.json` | Document URLs, accessions, and local file paths |
| `companyfacts.json`, `facts.json` | Raw XBRL data and selected facts with source links |
| `calculations.json` | Price input, formulas, values, and missing-data reasons |
| `release_lines.json` | Release matches, source lines, and context |
| `peers.json`, `peers/<ticker>/` | Peer results and raw/selected peer facts |

The `.env`, Python environment, and generated runs are ignored by Git.

Use `--step` to run exactly one step. Step 1 creates a new folder. Steps 2–7 use
the most recent saved run for that ticker and require these saved results:

| Step | Required completed step |
| --- | --- |
| 1 | None |
| 2 | 1 |
| 3 | 2 |
| 4 | 1 |
| 5 | 4 |
| 6 | 3 |
| 7 | 1 |

For example, recalculate from saved facts with a different price:

```sh
.venv/bin/python equity_desk.py AAPL --step 5 --price 210
```

Pass `--peers` again when running step 7 alone. A single-step run does not execute
missing prerequisites. If a prerequisite is rerun, dependent results become
stale until those steps run again. Old files remain available for review. A full
run continues with independent steps after an error and exits with status 1 if
any step fails. Missing individual facts are marked `MISSING`; affected ratios
are `N/A`.

Fact selection uses standard US-GAAP tags and USD units. Annual duration facts
must come from 10-K or 10-K/A filings and span 330–400 days. This includes normal
52/53-week years. For each concept, the candidate tag with the newest annual
period end wins; the declared tag order breaks ties. For the same year, `Revenues`
is preferred to contract revenue because the latter can omit membership and
other income. Confirm the selected value against the consolidated income
statement; tag names alone do not prove its definition. All selected current-year
facts must match revenue's period dates. Balance sheet facts must match its end
date. Prior-year facts use the immediately preceding revenue period. The chosen
tag must also contain that prior period or the value remains missing.

For duplicate facts, the most recently filed annual disclosure wins, including
restated comparative amounts. Selection uses `start` and `end`, not the XBRL
`fy` field, which can describe the filing year for both current and comparative
values. Thus, this is a current-data tool, not a historical point-in-time backtest.

The calculator uses these definitions:

| Measure | Arithmetic |
| --- | --- |
| Revenue growth | `(current revenue - prior revenue) / prior revenue * 100` |
| Operating margin | `operating income / revenue * 100` |
| Return on average equity | `net income / ((current equity + prior equity) / 2) * 100` |
| Debt to equity | `(noncurrent long-term debt + current portion of long-term debt) / equity` |
| Free cash flow | `cash from operations - payments to acquire PP&E` |
| P/E | `supplied USD share price / latest fiscal-year diluted EPS` |

Debt excludes separately reported short-term borrowings. If the selected debt
tags include finance/capital leases, that definition is printed explicitly.
Current and noncurrent debt must use matching lease definitions or the ratio is
unavailable.
The generic `LongTermDebt` tag can include the current portion, so it is not used
as noncurrent debt. Missing debt is not treated as zero. A zero denominator gives
`N/A`. P/E also gives `N/A` for zero or negative EPS, or when `--price` is absent.
Negative equity can produce negative ROE or debt-to-equity; the arithmetic is
shown without changing its sign. If the `ProfitLoss` fallback is used for net
income, inspect its disclosed scope, including noncontrolling interests.

Some issuers use custom tags, IFRS, other currencies, unusual fiscal periods, or
different debt/capital-expenditure definitions. Unsupported facts stay missing;
the program does not substitute unrelated concepts or years. It does not OCR
image-only PDFs. Earnings-line matching is rule based. It can miss unusual
wording, and source context must be checked when a release has multiple periods,
guidance, or GAAP and non-GAAP measures. Full source text is retained for review.

Run the deterministic tests without SEC requests:

```sh
.venv/bin/python -m unittest -v
```
