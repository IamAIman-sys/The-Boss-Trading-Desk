"""The Investment Advisor persona's Buy/Hold/Sell rules, applied in code to Python's evidence lines.

The student wrote the rules in personas/investment_advisor.md ("Scored criteria"). This file
does not change them; it applies them so the Strategy Manager can check the Advisor's answer.
The model still writes the recommendation; when it differs from the rules, the Manager sends
it back once with the expected result and the reasons.

If the "Scored criteria" part of the persona changes, PERSONA_SHA no longer matches and the
check is skipped (with a note) until this file is updated to the new rules.

Rules applied (persona wording in quotes):
1. Net profit margin has "the most weight unless another criterion identifies a risk that
   blocks Buy". With a peer median: above the prior year and at or above the median -> Buy;
   below both -> Sell; else Hold. Prior year only: above -> Buy, below -> Sell. A relative
   change within +/-2% of the prior-year value is "equal" -> Hold.
2. Interest coverage below 1x "blocks Buy and moves toward Sell"; at least 1x but below 1.5x
   "blocks Buy and moves toward Hold"; 1.5x or above: no block. Unavailable: not scored.
3. A negative operating cash-flow margin blocks Buy (-> Hold). Otherwise the cash-flow margin
   has less weight and does not change the result ("retain Buy with lower confidence").
Where the persona's words allow more than one result, every such result is accepted.
"""
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path
import re

PERSONA = Path(__file__).resolve().parent / "personas" / "investment_advisor.md"
PERSONA_SHA = "918faa062023c522"  # sha256 (first 16) of the persona's "Scored criteria" text
BAND = Decimal(2)  # "within ±2% of the prior-year value"
NPM, COVERAGE, OCF = "Net profit margin", "Interest coverage", "Operating cash flow margin"


def criteria_sha(path=PERSONA):
    text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    match = re.search(r"## Scored criteria\n(.*?)\n## ", text, re.S)
    return hashlib.sha256(match.group(1).strip().encode()).hexdigest()[:16] if match else None


def _number(text):
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError):
        return None


def read_measures(context):
    """{measure: {current, tag, relative, median}} from the Python evidence lines the model saw."""
    ticker = context["company"]["ticker"]
    rows = [r for r in context.get("evidence_lines", []) if r["source"] == "Python evidence"]
    found = {}
    for name in (NPM, COVERAGE, OCF):
        item = {"current": None, "tag": None, "shown": None, "relative": None, "median": None, "median_tag": None}
        for row in rows:
            text, tag = row["text"], f"Python evidence L{row['line']}"
            current = re.match(rf"{re.escape(ticker)} current {re.escape(name)}; period=\{{[^}}]*\}}: (-?[\d.]+) ", text)
            change = re.match(rf"{re.escape(ticker)} prior-year change, {re.escape(name)}: .*relative change (-?[\d.]+) %", text)
            median = re.match(rf"Peer median current {re.escape(name)}: (-?[\d.]+) ", text)
            if current:
                item.update(current=_number(current[1]), shown=current[1], tag=tag)
            elif change:
                item["relative"] = _number(change[1])
            elif median:
                item.update(median=_number(median[1]), median_tag=tag)
        found[name] = item
    return found


def direction(item):
    """Buy, Hold, Sell or None (not scored) for one measure, by the persona's comparison rule."""
    if item["current"] is None or item["relative"] is None:
        return None
    prior = 0 if abs(item["relative"]) <= BAND else (1 if item["relative"] > 0 else -1)
    if item["median"] is None:  # "When the peer median is unavailable, you rate only against the prior year."
        return {1: "Buy", 0: "Hold", -1: "Sell"}[prior]
    if prior == 1 and item["current"] >= item["median"]:
        return "Buy"
    if prior == -1 and item["current"] < item["median"]:
        return "Sell"
    return "Hold"


def expectation(context):
    """{"allowed": set, "deciding": [(measure, shown value, tag)], "reasons": [...]} or None if not scored."""
    m = read_measures(context)
    base = direction(m[NPM])
    if base is None:
        return None
    npm = m[NPM]
    basis = (f"peer median {npm['median']} % [{npm['median_tag']}]" if npm["median"] is not None
             else "no peer median, so the prior year only")
    reasons = [f"Net profit margin (the most weight) is {npm['shown']} % [{npm['tag']}]; relative change from the "
               f"prior year {npm['relative']} % ({'within' if abs(npm['relative']) <= BAND else 'outside'} ±2%); "
               f"{basis} -> {base}."]
    allowed, deciding = {base}, [(NPM, npm["shown"], npm["tag"])]
    cov, ocf = m[COVERAGE], m[OCF]
    if cov["current"] is None:
        reasons.append("Interest coverage is unavailable: not scored; say so, and keep the uncertainty flagged.")
        if base == "Buy":
            allowed.add("Hold")  # the persona's cash-flow fallback can lower confidence
    elif cov["current"] < 1:
        reasons.append(f"Interest coverage {cov['shown']} x [{cov['tag']}] is below 1x: it blocks Buy and moves toward Sell.")
        allowed = {"Hold", "Sell"} if base == "Buy" else {"Sell"}
        deciding.append((COVERAGE, cov["shown"], cov["tag"]))
    elif cov["current"] < Decimal("1.5"):
        reasons.append(f"Interest coverage {cov['shown']} x [{cov['tag']}] is at least 1x but below 1.5x: it blocks Buy and moves toward Hold.")
        allowed = {"Hold"} if base in ("Buy", "Hold") else {"Hold", "Sell"}
        deciding.append((COVERAGE, cov["shown"], cov["tag"]))
    else:
        reasons.append(f"Interest coverage {cov['shown']} x [{cov['tag']}] is at least 1.5x: no Buy block.")
    if ocf["current"] is not None and ocf["current"] < 0:
        reasons.append(f"Operating cash-flow margin {ocf['shown']} % [{ocf['tag']}] is negative: it blocks Buy.")
        if "Buy" in allowed:
            allowed = (allowed - {"Buy"}) | {"Hold"}
            deciding.append((OCF, ocf["shown"], ocf["tag"]))
    elif ocf["current"] is not None:
        reasons.append(f"Operating cash-flow margin {ocf['shown']} % [{ocf['tag']}] is not negative: it has less weight "
                       "and does not change the result.")
    return {"allowed": allowed, "deciding": deciding, "reasons": reasons}


def advisor_problems(output, context, numbers_of):
    """Problems for the Strategy Manager, or [] when the Advisor follows the persona's rules.

    numbers_of(text) returns the numbers a text states, compared by value (flow_desk's rule)."""
    if criteria_sha() != PERSONA_SHA:
        print("Persona rule check skipped: personas/investment_advisor.md 'Scored criteria' changed; "
              "update persona_rules.py to the new rules.", flush=True)
        return []
    expected = expectation(context)
    if expected is None:
        return []
    problems = []
    why = " ".join(expected["reasons"])
    choice = output.get("recommendation")
    if choice not in expected["allowed"]:
        problems.append(f"Persona rules: the recommendation must be {' or '.join(sorted(expected['allowed']))}, "
                        f"not {choice}. {why}")
    deciding = output.get("deciding_number") or {}
    stated = numbers_of(deciding.get("claim", "") + " " + deciding.get("quote", ""))
    options = [f"{name} {shown} [{tag}]" for name, shown, tag in expected["deciding"]]
    if not any(numbers_of(shown) & stated for _, shown, _ in expected["deciding"]):
        problems.append(f"Persona rules: the deciding number must be {' or '.join(options)}."
                        + ("" if problems else f" {why}"))
    if re.search(r"\bquarter", deciding.get("claim", ""), re.I):
        problems.append("Deciding number: the Python evidence values are annual (fiscal-year) values; do not call them a quarter.")
    return problems
