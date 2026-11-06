# Checkpoint 2: the Verifier and its seeded-error marks

Checkpoint 2 (Lab 05 checkout): a commit permalink to this repository, which
holds the agent team "with the verifier's marks on the seeded-error test".
It is due Thursday, November 5, 2026, by 11:59 PM Eastern. It is individual and
scored 100 or 0.

## The Verifier

`verifier.py` is code only. It uses no model. It reads one saved run folder:
`report.md`, `facts.json`, the saved filing texts (`10-K.txt`, `10-Q.txt`,
`earnings_release.txt`), and, when they exist, `quarter_facts.json`,
`peers.json` and `price_reference.json`. It does not read role instructions or
role calls. From `calculations.json`, it reads only the supplied price. It
recomputes every ratio itself.

For each number in the report, it gives one mark:

- **XBRL-tagged number:** the number must equal `facts.json` exactly, for the
  same tag and period.
- **Line-sourced number:** the number must be on the cited line. The format can
  differ: 41,954 in a "$ in millions" table equals "$41.954 billion". A correct
  number on a wrong line is marked **Unsupported**, and the real line is shown
  when it is within 5 lines.
- **Ratio:** the Verifier recomputes it from the stated inputs. Each input must
  be a sourced value.
- **Named metric in prose** (revenue growth, operating margin, ROE, debt to
  equity, P/E, free cash flow, diluted EPS): the Verifier recomputes it from
  `facts.json`.
- **Number with no source:** marked **Unsupported**.

**Wrong** and **Unsupported** numbers are corrected in place in the verified
report (~~old~~ **new** [V#]). The tag or the 10-K line goes beside each
correction. The table of marks goes under the first line, and the first line
stays the filings line.

The Verifier skips 2 things: the run metadata above the first `## ` section
(this includes the human partner checks) and the Investment Advisor's thesis.

Each verification writes a new folder, `<run>/verified/<date-time>/`. It never
overwrites an earlier result.

`research_desk.py` runs the Verifier after every compiled report. No option
turns it off.

## Commands

```sh
.venv/bin/python checkpoint-2/make_test_runs.py                      # build the 3 test runs and verify each
.venv/bin/python research_desk.py --verify-only checkpoint-2/runs/NOC-seeded-eps   # Verifier only, on one saved run
.venv/bin/python -m unittest test_verifier -v                        # the 4 Lab 04 tests, offline
```

`flow_desk.py --verify-only RUN_FOLDER` does the same as the `research_desk.py`
command.

## The four Lab 04 tests

All 3 test runs are copies of the audited Checkpoint 1 NOC run
(`checkpoint-1/reports/NOC.md` and `checkpoint-1/evidence/NOC/`).

| Test | What was changed in the copy | Expected | Verifier result |
| --- | --- | --- | --- |
| 1. Seeded error | Annual GAAP diluted EPS 29.08 → 30.08, everywhere in the report, so the report agrees with itself | Wrong, corrected to the 10-K figure with the 10-K per-share line | **Wrong** (V26 table, V18 prose), corrected to **29.08**, with `us-gaap:EarningsPerShareDiluted` FY2025, accession 0001133421-26-000003, and 10-K L997 "Diluted earnings per share … 29.08". The P/E line that uses 30.08 is marked Unsupported (V44, V45). Core claim 5: **Wrong**. |
| 2. Invented number | One added sentence: annual revenue growth of 6.24%, 4 percentage points above the 2.24% that the two 10-K revenue figures give | Wrong or Unsupported, with the arithmetic | **Wrong** (V18), corrected to **2.24**, with (41,954,000,000 − 41,033,000,000) / 41,033,000,000 × 100. The 2 quoted revenue figures are Correct on 10-K L592. |
| 3. Clean report | Nothing (the report that the student audit marked Correct on all 11 core claims) | All 11 correct | **All 11 core claims Correct.** 56 numbers: 55 Correct, 0 Wrong, 1 Unsupported (see the note below). |
| 4. Skip test | Search the code for a way to run without the Verifier | None | `test_no_way_to_run_without_the_verifier` passes. No flag skips or disables the Verifier, and `research_desk.py` calls it after it saves each report. |

Verified reports with the table of marks:

- [Seeded error](runs/NOC-seeded-eps/verified/2026-11-05_21-05-53-641084/verified_report.md)
- [Invented number](runs/NOC-invented-growth/verified/2026-11-05_21-05-53-931036/verified_report.md)
- [Clean report](runs/NOC-clean/verified/2026-11-05_21-05-53-327735/verified_report.md)

**The 1 Unsupported mark in the clean report is a real finding.** The report
states a 1.5× book-to-bill ratio and cites Exhibit 99 L18–L21. The ratio is on
Exhibit 99 L17 ("Book to bill ratio of 1.5x"). The number is correct, but the
citation is off by 1 line. The student audit marked the 1.5× number Correct; it
did not check the line number.

**Partner checks** (Lab 04 asks the partner to do this). Checked by Samuel
Parfait (SP), November 5, 2026, in the 10-K for the year ended December 31,
2025 (accession 0001133421-26-000003):

| Check | What the partner found | Verifier correction | Mark |
| --- | --- | --- | --- |
| 1. FY2025 GAAP diluted EPS (test 1) | $29.08 per share, printed page 48 of the 10-K | **29.08** (V26, seeded-error run) | Correct |
| 2. FY2025 revenue growth (test 2) | Total sales $41,954 million (2025) and $41,033 million (2024); (41,954 − 41,033) ÷ 41,033 × 100 = 2.24% | **2.24** (V18, invented-number run) | Correct |

## What this Verifier cannot catch

- **A number on the cited line for a different period or definition.** The
  report says "~86 %" of sales went to the U.S. government and cites 10-K L202.
  That line gives 84 percent for 2025 and 86 percent for 2023. The code marks
  86 Correct, because 86 is on the line. Lab 04 gives this check to a model step
  ("the line states that number, for that period, in that definition"). That
  model step is not built yet.
- **Meaning, thesis and recommendation.** The Verifier does not judge these.
  Human audit is still necessary.

## Not done yet (Lab 05 and the Week 3 graph)

- The crewAI Flow (`flow_desk.py`) has the Research Analyst and Financial
  Analyst nodes. The Investment Advisor and Strategy Manager nodes are not
  built, so the Flow does not yet make a compiled report for the Verifier
  node. Until they are built, `research_desk.py` makes the compiled reports,
  and it runs the Verifier every time.
- Lab 05: the three personas in the student's own words, the Insight-line
  rules in the Strategy Manager, the run on the partner's pick, and the UI page.

This is a learning exercise, not financial advice.
AI assistance: Claude (Verifier code and tests), Codex and Purdue GenAI Studio (gpt-oss:120b) (Checkpoint 1 report). I verified the sources myself; the judgments are mine.
Any remaining errors are my own.
