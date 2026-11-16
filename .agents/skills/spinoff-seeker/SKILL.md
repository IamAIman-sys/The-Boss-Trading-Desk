---
name: spinoff-seeker
description: Find and screen U.S. spinoff candidates from SEC form indexes, maintain filing-cited facts, and rank a distribution-date window using the student's handwritten factors. Use for the Week 4 Lab 06 seeker or a repeat spinoff screen; not for recommendations, the earnings desk, or writing the student's factors.
---

# Spinoff seeker

Run the deterministic scripts in this folder. Do not replace missing filing facts
with model knowledge. Never estimate a fact. Never use a when-issued price as the
first price. Never write the student's factors, directions, chapters, window or
weights. `factors.json` intentionally contains only blank values; validation must
fail until the student fills it in. A blank template is a deliverable, not a bug.

Read [references/contracts.md](references/contracts.md) for factor syntax, reader
integration, extraction limits and the exact ranking formula. The scripts make no
model calls and do not load or modify the desk's roles, personas or Python files.

From the project root:

```sh
.venv/bin/python .agents/skills/spinoff-seeker/scripts/seeker.py --start-date 2025-11-15
.venv/bin/python -m unittest discover -s .agents/skills/spinoff-seeker/tests -p 'test_*.py' -v
```

The start date filters **distributions**, not registrations. Default discovery reads
full form indexes back to 1994 Q3 so an older Form 10 is not silently lost. This is
a potentially long first scan. `--index-start YYYY-MM-DD` explicitly restricts
discovery; every such report states the resulting coverage limitation. Current
daily form indexes supplement the full-index bridge. Index or submissions errors
must never be presented as an exhaustive search with no candidates.

Use `--closes-reader /absolute/path/to/reader.py` only for the user's own reader
that implements the documented interface. Do not run a vendor reader or inspect
restricted exports while building this skill. If it is absent or returns no data,
finish with prices not available and leave price-dependent names unranked. Do not
substitute the optional Financial Datasets adjusted-price endpoint for official
closes. Each request made by the SEC client reads its User-Agent from the project's
`.env`, uses at least 0.26 seconds between starts, and has finite retries.

Outputs go into the already ignored `runs/spinoff-seeker/`, never the skill folder:
a persistent `registry.json`, and a new timestamp folder containing the report,
the selected registry snapshot, exact factors used, screen data and filing texts.
Raw vendor series are not saved or sent to a model. Only the first and latest
selected close, source/date and derived calculations enter the report. Cache files
contain public SEC documents only. Keep `.env` and local vendor data out of Git.

Read registry citations before treating a screen as validated. The parser is
deliberately conservative; a document it cannot interpret is not evidence that a
fact does not exist. Same-date conflicts remain blank. Report unknown fields,
source gaps and unavailable prices. Keep the run, price and index dates on the
first report line and `screens, not recommendations` on the last line.

Before changing a rule, update its made-up-data test to show the intended behavior;
then change the rule and run the offline test suite. Tests block real HTTP requests.
Human validation still requires the student's known spinoff/non-spinoff, one cited
registry row, an official close, and a recomputed factor score.

Contract: [Lab 06](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/lab-06-investor-skill.html).
See also [Week 4](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/index.html)
and the [data contract](https://cinderzhang.github.io/FIN67110-Fall2026/reference/data.html).
