#!/usr/bin/env python3
"""Build the Lab 04 Verifier test runs from the audited Checkpoint 1 run. No model, no network.

Each test run is a copy of the same saved evidence plus one report:
  clean            the report as audited (all 11 core claims marked Correct by the student)
  seeded-eps       annual diluted EPS one dollar higher everywhere in the report
  invented-growth  one added revenue-growth figure 4 percentage points above the 10-K figures
Then the Verifier runs on each copy. Results go to <run>/verified/<time>/.
"""

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import verifier  # noqa: E402

SOURCE = ROOT.parent / "checkpoint-1"
EVIDENCE = ("facts.json", "quarter_facts.json", "peers.json", "price_reference.json",
            "10-K.txt", "10-Q.txt", "earnings_release.txt")
# Ticker of the audited Checkpoint 1 run; the Verifier code names no company.
TICKER = "NOC"
EPS, SEEDED_EPS = "29.08", "30.08"
GROWTH_ANCHOR = "- **Profitability**:"
INVENTED_GROWTH = ("- **Revenue growth**: Total revenue rose from USD 41,033 million to USD 41,954 million "
                   "[10-K L592], so annual revenue growth was 6.24%.\n")


def build(name, report, root=ROOT / "runs"):
    folder = Path(root) / f"{TICKER}-{name}"
    folder.mkdir(parents=True, exist_ok=True)
    for file in EVIDENCE:
        shutil.copyfile(SOURCE / "evidence" / TICKER / file, folder / file)
    (folder / "report.md").write_text(report, encoding="utf-8")
    return folder


def reports():
    audited = (SOURCE / "reports" / f"{TICKER}.md").read_text(encoding="utf-8")
    first, body = audited.split("\n", 1)
    assert EPS in body and GROWTH_ANCHOR in body
    return {"clean": audited,
            # The number and every place the report repeats it change together, so the
            # report agrees with itself. Only the saved facts and 10-K can show the error.
            "seeded-eps": first + "\n" + body.replace(EPS, SEEDED_EPS),
            "invented-growth": audited.replace(GROWTH_ANCHOR, INVENTED_GROWTH + GROWTH_ANCHOR, 1)}


def main():
    for name, report in reports().items():
        out, marks = verifier.verify_run(build(name, report))
        counts = {k: sum(m["mark"] == k for m in marks) for k in ("Correct", "Wrong", "Unsupported")}
        print(f"{name}: {counts} -> {out / 'verified_report.md'}")


if __name__ == "__main__":
    main()
