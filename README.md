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
| `financial_datasets.py` | Optional closing prices and comparisons with annual SEC facts |
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

### Optional Financial Datasets connection

Set `FINANCIAL_DATASETS_API_KEY` in your existing local `.env`. Keep `API_KEY`
as your Purdue key. No extra Python packages are needed for this connection.
The provider receives `X-API-KEY` and your `SEC_USER_AGENT` on each request.
Keys and response error bodies are not printed. Redirects are not followed.

Run both optional features, with no model calls:

```sh
.venv/bin/python equity_desk.py NOC --peers RTX --fetch-price-date 2026-10-19 --compare-financial-datasets
```

To run the same data checks and then generate a new model report:

```sh
.venv/bin/python research_desk.py NOC --peers RTX --fetch-price-date 2026-10-19 --compare-financial-datasets
```

These are example inputs, not defaults. The new run goes under ignored `runs/`;
it does not replace the saved Checkpoint 1 report or its LSEG price evidence.
The Financial Datasets price is a separate source; it is not labeled as LSEG
or as an exchange quote. Check the course's source requirement before using
it in a submission.

`--fetch-price-date` requires an exact completed date before today in New York.
It cannot be combined with `--price`, `--price-date`, or `--price-source`.
If no unique price exists for that date, the command fails without selecting
another trading day. Choose the trading day you intend to use. The provider's
`close` field supplies the numerator for P/E; annual SEC GAAP diluted EPS
still supplies the denominator. The endpoint does not specify split/dividend
adjustment treatment, so the saved source and generated report state that
limitation. USD is assumed for the requested US listing if currency is absent.
A historical price does not make the latest SEC facts a point-in-time dataset.

`--compare-financial-datasets` compares all nine main-company facts and each
requested peer's facts, for the current and prior annual periods. It requires
matching ticker, annual period, period end, and USD currency. Values are compared
exactly, without rounding tolerance. It records both filing references when
available. Different filing versions, restatements, or definitions may explain
a difference; a numeric match is not a completed human audit. Vendor start dates
are unavailable, so only annual period ends can be matched. Debt and capital
expenditure always require definition review; no cash-flow sign conversion is
applied. Missing fields stay missing. SEC facts continue to drive every ratio.

Saved local evidence:

| File in the run folder | Contents |
| --- | --- |
| `price_reference.json` | Fetched price, exact date, source query, retrieval time, and adjustment limitation |
| `calculations.json` | SEC-based calculations, with the fetched price reference when requested |
| `financial_datasets_comparison.json` | Selected main-company values, differences, definitions, and filing references |
| `peers/TICKER/financial_datasets_comparison.json` | The same comparison for a peer |

Full vendor response bodies are not saved. Keep the selected vendor evidence
under ignored `runs/`; do not add it to the Checkpoint 1 evidence folder.
Endpoint errors stop the requested operation with a readable error; they do not
replace missing data with zero or a different provider.

For saved data, `research_desk.py --reuse` still avoids SEC requests, but these
optional flags make new Financial Datasets requests. They update the latest run
and generate a new report there. For the data-only desk, price lookup can run
with `--step 5`; statement comparison can run with `--step 4` or `--step 7`.
Step 4 and step 7 fetch SEC facts again. Omit both new flags to retain the prior
SEC-only behavior and manual `--price` input.

Run the offline checks:

```sh
.venv/bin/python -m unittest test_equity_desk test_research_desk test_financial_datasets
```

API references: [historical prices](https://docs.financialdatasets.ai/api/prices/historical)
and [all financial statements](https://docs.financialdatasets.ai/api/financials/all-financial-statements).

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

## Research Analyst evidence inputs (Week 3)

`flow_desk.py` now sends the Research Analyst the complete data desk's saved
financial inputs as well as filing excerpts. The graph remains
`gather_filings -> research_analyst -> check_research -> save_run`.
This is the Research Analyst stage only. It does not yet implement the other
three roles or the full course Verifier.

To inspect inputs without a model call:

```sh
.venv/bin/python flow_desk.py NOC --reuse --peers RTX,LMT,GD --prepare-only
```

To run this Research Analyst stage using the same saved data:

```sh
.venv/bin/python flow_desk.py NOC --reuse --peers RTX,LMT,GD
```

Without `--reuse`, Python runs SEC steps 1–7 first. `--reuse` selects a complete
run with the requested peer set; it does not silently substitute different
peers. `--run-folder PATH` selects a specific complete run. The ticker, selected
10-K, facts, periods and saved calculations are checked for consistency.

The input package includes:

- 10-K Business and MD&A excerpts; 10-Q MD&A excerpts; the earnings release.
  10-K Item 8 and 10-Q Item 1 (the financial statements) are not sent to the
  model, because Purdue's `gpt-oss:120b` accepts at most 65,536 tokens. Their
  numbers reach the model as Python evidence lines with filing tags and
  accessions. The full texts stay in the run's source snapshot.
- Annual XBRL facts and peer facts, including tags, accessions, units and periods.
- Python calculations for operating margin, net profit margin, operating cash
  flow, cash-flow margin, return on average equity, debt and debt-to-equity,
  and interest coverage where the required facts exist. Cash-flow margin is
  provided for comparing companies of different sizes.
- Current/prior annual comparisons. Prior ROE requires the earlier opening
  equity balance. Missing or nonpositive denominators remain unavailable.
- A high-priority review flag at an absolute operating-margin change of at
  least 5 percentage points (500 basis points). Smaller changes can still merit
  the analyst's review. These flags do not assign a recommendation.
- A separate debt/ROE warning when debt rises, interest coverage falls, and ROE
  rises. If any required comparison is unavailable, the flag is unknown.

Interest coverage uses operating income divided by reported interest expense,
accepting only `InterestExpenseNonOperating` or `InterestAndDebtExpense` for the
same annual period and filing. The actual tag is shown; net-interest tags are
not substituted. The debt measure is long-term debt plus its current portion;
it excludes separately reported short-term borrowings. Lease definitions are
shown and must match. These definitions must be considered before comparing
peers. No automatic peer ranking is performed.

Output and send-back: the Research Analyst returns lists of claims. Each claim
has three required fields: `claim`, `quote` and `citation`. Python writes the
report from them, so a claim cannot be saved without a quote. The check then
tests each quote and number against its cited line. A quote shortened with
"..." passes only when each part is on that line, in order. If the check fails,
the Flow sends the problem list back once (at most 2 attempts, as Week 3
allows). If the send-back call itself fails, the report keeps the first draft
and records the error. `research_analyst.json` keeps every attempt. The check
cannot judge meaning: a claim such as "coverage fell" can pass with an exact
quote that shows only one year. Human audit remains necessary.

Input size: before each model call, the Flow estimates the input at 3.5
characters per token (Purdue counted 3.5 and 3.75 on NOC inputs) and stops
with no model call above 52,000 tokens. The answer may use up to 12,000 tokens;
Purdue's limit for both together is 65,536. `--prepare-only` prints the same estimate.
Each evidence line is sent as plain text that starts with its citation tag,
for example `[10-K L128] ...`. Python evidence shows percentages and ratios
to 2 decimal places and dollars as whole numbers; JSON files keep exact values.
The check compares numbers by value, so 0.10 and 0.1 match.

`--prepare-only` saves an input package, not a report or a verification result.
Every model run saves `research_model_input.json` (the exact context sent),
`research_context.json` (the full evidence package), `financial_evidence.json`,
and snapshots of the source files under `evidence/`. Python calculations are
cited as `[Python evidence L<number>]` and retain their underlying filing tags,
periods and accessions. They are not represented as SEC quotations.

Management presentations are optional, explicit inputs. To include one, save a
text transcription or labeled excerpt next to a JSON manifest. Preserve page
or slide numbers in the text. Each manifest item needs `file`, `title`, `date`
(YYYY-MM-DD), and the original public HTTPS `url`. The file must be within the
manifest folder and use `.txt` or `.md`, with at most 100 KB per document.
Pass the manifest with `--supplements PATH`. The source text, metadata and hash
are saved with the run. No presentation supplied means "not supplied", not
"reviewed". Management statements remain claims to evaluate against filings.

Filing excerpts are capped at 25,000 characters per selected Item; the complete
source texts are retained in the run snapshot. The model must not claim to have
read omitted notes. Peer inputs are SEC XBRL facts, not complete peer filings.
The present checker matches quotes and numbers to the cited lines. It does not
establish semantic correctness, complete claim coverage, or the investment thesis.
Human review and the full Week 3 Verifier remain necessary.

## Coding-agent skills

`.agents/skills/` holds 8 skills from crewAI's official skill pack
([crewAIInc/skills](https://github.com/crewAIInc/skills), MIT license, see
`.agents/skills/CREWAI-SKILLS-LICENSE.txt`). They teach a coding agent such as
Codex the current crewAI 1.15.x API and Flows. They are tools for building the
desk. They are not desk code, and we did not write them.

---

AI assistance: Codex, Claude, Gemini, Purdue GenAI Studio (gpt-oss:120b). I verified the sources myself; the judgments are mine.
