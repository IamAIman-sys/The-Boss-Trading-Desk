# Interfaces and boundaries

## Student factor file

The shipped `factors.json` contains no selections. The student writes every value.
`window_days` is a positive integer in calendar days after distribution. Each
factor needs a unique `name`, `metric`, `direction` (`higher` or `lower`), `chapter`
(the student's source reference), and a finite nonnegative numeric `weight`.
At least one weight must be positive. More factor objects may be added by hand.
There is no default factor, weight, direction, chapter, or window.

The following are available measurements, **not recommended factors**:

| Metric key | Mechanically established input |
| --- | --- |
| `first_close` | First official regular-way USD close strictly after distribution |
| `latest_close` | Latest such close in the reader's completed covered range |
| `return_since_first_close_pct` | `(latest − first) / first × 100`, with both price dates |
| `days_since_distribution` | Calendar days from cited distribution date to as-of |
| `distribution_ratio` | Cited shares distributed divided by cited parent shares |
| `filing:<exact label>` | A whole filing line with that literal label, `:` or `|`, and one explicit number; optional `$`, `%`, `thousand`, `million`, `billion` |

Unsupported custom metrics cause a clear configuration error. A supported metric
with no established observation stays missing. The generic filing-label reader
does not infer a table's units, period or pro-forma/reported status. Its quotation
and printed units remain attached; the student must choose a sufficiently specific
label. It intentionally does not read a number out of a multi-column financial
table. Add a source-specific parser only with a made-up-data test and no issuer rule.

Each active factor has its own eligible in-window pool with that metric present.
For higher-is-better, count values strictly lower; for lower-is-better, strictly
higher. Percentile is `(worse + equal_other / 2) / (pool_size - 1)`; for one item it
is `0.5`. Points are `weight × percentile`. No rounding enters ranking. Total is
the sum of active-factor points. A missing active input prevents a total and rank.
Zero-weight factors have no points and cannot change another factor's pool or
points. CIK sorts tied totals for stable display; it conveys no economic preference.
The report prints raw values, weights, percentiles, pool counts and arithmetic.

## Closes-reader interface

No standalone official-closes reader existed in the inspected project when this
skill was built. This skill supplies the interface; it does not invent a vendor
connection or read an export. Pass the user's Python module with `--closes-reader`.
The module exports:

```python
daily_closes(ticker: str, start_date: str, end_date: str) -> dict | None
```

Both input dates are ISO calendar dates and the range is inclusive. The reader
may return `None`, `"not available"`, or `{"status": "not available"}`. To supply
prices, it returns this schema (angle-bracket values describe the schema only):

```json
{
  "status": "ok",
  "ticker": "<requested symbol>",
  "start_date": "<coverage start YYYY-MM-DD>",
  "end_date": "<coverage end YYYY-MM-DD>",
  "complete": true,
  "closes": [
    {
      "date": "<YYYY-MM-DD>",
      "close": "<positive decimal>",
      "currency": "USD",
      "session": "regular",
      "kind": "official_close",
      "source": "<vendor or exchange reference>"
    }
  ]
}
```

`complete: true` is an assertion by the reader that it has not truncated, omitted
or paginated away a regular-trading observation in the requested range. Only set
it when the provider supports that assertion. Otherwise return not available.
The seeker cannot prove exchange-calendar completeness from rows alone. It does
check declared coverage, ticker, dates, numeric validity, currency, source,
regular session and official-close kind, and rejects contradictory duplicate dates.
Out-of-range rows are excluded. A suspicious row after distribution makes the
price unavailable; it never silently chooses a later row as the first close.

The reader is the user's executable code and controls its own provider credentials,
rate limits, User-Agent and restricted-data access. Keep its raw pulls and export
files private. This skill never reads an export directly and never calls a model.

## Registry and extraction

Core facts: parent, parent CIK, distribution ratio, record date, distribution date,
and regular-way ticker. Every established fact stores its value and filing index,
document URL, filing date, section heading, line number, exact quotation, and saved
text path. The parent CIK can come from an explicit parent-CIK statement or an
EDGAR link whose anchor exactly matches the explicitly stated parent's name.
No fuzzy name matching is used. Facts not found are JSON null. A same-date conflict
is null; a later explicit filing can supersede an earlier statement. History stays
in the registry. An unreadable later document is reported as incomplete coverage.

Supported prose includes explicit `Parent:`, `Parent CIK:`, `Record date:`,
`Distribution date:`, `Distribution ratio:`, and `Trading symbol:` labels, selected
parent definitions, wholly-owned-subsidiary statements, record-holder dates and
unambiguous distribution sentences. Number words one through twenty are supported
in ratios. Ambiguous multi-date narrative distributions, conditional/proposed
dates and unreadable images remain blank. A future explicit distribution date is
recorded but cannot place a name in its window before that date.

Form 10 registration variants and amendments, CERTs, and distribution-period 8-Ks
are discovered in form indexes and the full submissions history. Filing index
pages supply the primary document and readable exhibits. The parent CIK in the
registry leads to the parent's own 8-Ks; only lines naming the candidate issuer
contribute facts from those parent documents. An unresolved parent CIK is reported.

Explicit non-spin fund/shell/existing-share registrations and registrations without
a readable information statement are dropped with evidence. Later explicit parent
distribution evidence can rescue them. No-information-statement rejection is not
made when documents could not be read. A spin-off/separation context plus an actual
parent distribution statement is required; the word "spinoff" by itself is not proof.
An own-company 10-Q, 10-K or Form 4 at or after distribution proves trading for this
lab's rule. CERT alone means listing approved. Parent Form 4s are not trading proof.

Window boundaries are inclusive. Future distributions remain on watch. A missing
record/distribution date, unknown U.S. incorporation or absent parent proof prevents
ranking. Earlier-than-start distributions and past-window names are reported
separately. A completed window does not imply that a name is attractive.

## Operations

Only existing dependencies `requests`, `beautifulsoup4`, `python-dotenv` and `pypdf`
are used. No existing project files need edits. If dependencies are missing:

```sh
.venv/bin/python -m pip install 'requests>=2.32,<3' 'beautifulsoup4>=4.12,<5' 'python-dotenv>=1,<2' 'pypdf>=5,<7'
```

Validate factors before requests, reader imports or output creation. No live run
is possible with the shipped blank factor file. Run tests with:

```sh
.venv/bin/python -m unittest discover -s .agents/skills/spinoff-seeker/tests -p 'test_*.py' -v
```

After writing factors, run:

```sh
.venv/bin/python .agents/skills/spinoff-seeker/scripts/seeker.py --start-date 2025-11-15
```

Supply a ready reader by adding `--closes-reader /absolute/path/to/reader.py`.
The full historical default can take substantial time on a first run. A deliberate
shorter discovery range uses `--index-start`; the report discloses it. Filing
document cache hits are local; indexes and submissions refresh each invocation.
Default SEC starts are spaced at least 0.26 seconds apart (under four per second).
Redirects are validated and rate-limited too. Requests have finite timeouts/retries.

Exit 0: report written (possibly with blanks or no ranked names).
Exit 1: invalid configuration, required-index failure or fatal I/O.
Exit 2: report written with one or more company retrieval failures.
An empty ranking is not proof that no spinoffs exist. Inspect the gaps section.
Reports never claim that a human source check has taken place.

Sources: [SEC access and indexes](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data),
[SEC submissions API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
[Lab 06 contract](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/lab-06-investor-skill.html).
