"""Offline financial inputs for the Research Analyst; no model or network calls."""

from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import equity_desk as data


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def annual_metrics(report, raw=None):
    """Use stated annual periods and sourced USD facts. Unavailable is never zero."""
    raw = raw or {}
    facts = report["facts"]
    results = {}

    def fact(key, column):
        entry = facts.get(key, {}).get(column)
        period = report["periods"].get(column)
        if not entry or not period:
            raise ValueError(f"missing {key} ({column})")
        if entry.get("unit") != "USD" or entry.get("end") != period["end"]:
            raise ValueError(f"unit/period mismatch for {key} ({column})")
        if key not in {"equity", "long_term_debt", "current_debt"} and entry.get("start") != period["start"]:
            raise ValueError(f"duration mismatch for {key} ({column})")
        if not all(entry.get(k) for k in ("tag", "accn", "filing_url")):
            raise ValueError(f"missing source metadata for {key} ({column})")
        value = Decimal(str(entry["val"]))
        if not value.is_finite():
            raise ValueError(f"nonfinite {key}")
        return value, entry

    def raw_fact(tag, period, accession, instant=False):
        entries = raw.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", [])
        matches = [e for e in entries if e.get("accn") == accession and e.get("end") == period["end"]
                   and (not e.get("start") if instant else e.get("start") == period["start"])]
        values = {str(e["val"]) for e in matches}
        if len(values) != 1:
            raise ValueError(f"missing or ambiguous {tag} for the same filing and period")
        entry = matches[0]
        base = data.archive_base(report["company"]["cik"], accession)
        return Decimal(str(entry["val"])), {**entry, "tag": "us-gaap:" + tag, "unit": "USD",
                                             "filing_url": base + accession + "-index.html"}

    for column in ("current", "prior"):
        period = report["periods"].get(column)
        metrics = {}

        def calculate(name, unit, definition, function):
            try:
                value, arithmetic, inputs = function()
                metrics[name] = {"value": str(value), "arithmetic": arithmetic, "unit": unit,
                                 "definition": definition, "period": period, "inputs": inputs}
            except (ValueError, ArithmeticError, KeyError, TypeError) as exc:
                metrics[name] = {"value": None, "reason": str(exc), "unit": unit,
                                 "definition": definition, "period": period, "inputs": []}

        def ratio(top, bottom, scale=100):
            a, ae = fact(top, column); b, be = fact(bottom, column)
            if b <= 0:
                raise ValueError(f"{bottom} denominator is not positive")
            return a / b * scale, f"{a} / {b} * {scale}", [ae, be]

        def cash():
            value, entry = fact("cfo", column)
            return value, str(value), [entry]

        def debt():
            a, ae = fact("long_term_debt", column); b, be = fact("current_debt", column)
            if ("CapitalLease" in ae["tag"]) != ("CapitalLease" in be["tag"]):
                raise ValueError("debt tags have different lease definitions")
            return a + b, f"{a} + {b}", [ae, be]

        def debt_equity():
            d, expression, inputs = debt(); e, ee = fact("equity", column)
            if e <= 0:
                raise ValueError("equity denominator is not positive")
            return d / e, f"({expression}) / {e}", inputs + [ee]

        def roe():
            n, ne = fact("net_income", column); e, ee = fact("equity", column)
            opening_date = (date.fromisoformat(period["start"]) - timedelta(days=1)).isoformat()
            if column == "current":
                p, pe = fact("equity", "prior")
                if pe["end"] != opening_date:
                    raise ValueError("opening equity date does not match the annual period")
            else:
                p, pe = raw_fact("StockholdersEquity", {"end": opening_date}, ne["accn"], instant=True)
            if e <= 0 or p <= 0:
                raise ValueError("opening or closing equity is not positive; ROE needs manual review")
            return n / ((e + p) / 2) * 100, f"{n} / (({e} + {p}) / 2) * 100", [ne, ee, pe]

        def coverage():
            op, oe = fact("operating_income", column)
            # Deliberately avoid net-interest, capitalized-interest and debt-total tags.
            try:
                interest, ie = raw_fact("InterestExpenseNonOperating", period, oe["accn"])
            except ValueError:
                interest, ie = raw_fact("InterestAndDebtExpense", period, oe["accn"])
            if interest <= 0:
                raise ValueError("interest expense is not positive")
            return op / interest, f"{op} / {interest}", [oe, ie]

        calculate("Operating margin", "%", "Operating income / total revenue * 100", lambda: ratio("operating_income", "revenue"))
        calculate("Net profit margin", "%", "Reported net income / total revenue * 100; inspect noncontrolling-interest scope", lambda: ratio("net_income", "revenue"))
        calculate("Operating cash flow", "USD", "Net cash provided by operating activities", cash)
        calculate("Operating cash flow margin", "%", "Operating cash flow / total revenue * 100; size-adjusted cash comparison", lambda: ratio("cfo", "revenue"))
        calculate("Return on average equity", "%", "Reported net income / average opening and closing book equity * 100", roe)
        debt_definition = "Long-term debt plus its current portion; excludes separate short-term borrowings. "
        debt_definition += ("Includes finance/capital leases." if "CapitalLease" in (facts.get("long_term_debt", {}).get("tag") or "") else "Excludes lease obligations.")
        calculate("Debt", "USD", debt_definition, debt)
        calculate("Debt to equity", "x", debt_definition + " Divided by book shareholders' equity.", debt_equity)
        calculate("Interest coverage", "x", "Operating income / reported interest expense (InterestExpenseNonOperating or InterestAndDebtExpense); compare the input tag before peer comparison; no net-interest substitution", coverage)
        results[column] = metrics
    return results


def review_signals(metrics):
    current, prior = metrics["current"], metrics["prior"]
    def change(name):
        a, b = current[name]["value"], prior[name]["value"]
        return None if a is None or b is None else Decimal(a) - Decimal(b)
    delta = change("Operating margin")
    debt, coverage, roe = [change(n) for n in ("Debt", "Interest coverage", "Return on average equity")]
    return {
        "comparison": "Current annual period versus prior annual period; not quarter versus year",
        "operating_margin_change_pp": str(delta) if delta is not None else None,
        "threshold_pp": "5", "threshold_basis_points": "500", "threshold_inclusive": True,
        "high_priority_review": abs(delta) >= 5 if delta is not None else None,
        "roe_debt_warning": (debt > 0 and coverage < 0 and roe > 0) if all(x is not None for x in (debt, coverage, roe)) else None,
        "policy": "These are review triggers, not recommendations. Smaller changes may merit review. A null signal cannot be assessed from the available evidence.",
    }


def financial_packet(folder, manifest, selected, peers=None):
    folder = Path(folder)
    for number in (4, 5, 7):
        if manifest["steps"].get(str(number), {}).get("status") != "complete":
            raise data.DeskError(f"Research inputs require complete data step {number}; rerun the data desk.")
    report = read_json(folder / "facts.json")
    if report["company"]["ticker"] != manifest["company"]["ticker"]:
        raise data.DeskError("Saved facts belong to a different company.")
    if report["facts"]["revenue"]["current"]["accn"] != selected["10-K"]["accessionNumber"]:
        raise data.DeskError("Saved annual facts and the selected 10-K do not match; refresh the data steps.")
    saved = read_json(folder / "calculations.json")
    if saved.get("periods") != report["periods"]:
        raise data.DeskError("Saved calculation periods differ from the facts.")
    recomputed = data.calculate(report, Decimal(str(saved["price_usd"])) if saved.get("price_usd") is not None else None)
    for name, metric in recomputed.items():
        original = saved.get("calculations", {}).get(name, {}).get("value")
        if (original is None) != (metric["value"] is None) or (original is not None and Decimal(str(original)) != Decimal(metric["value"])):
            raise data.DeskError(f"Saved calculation disagrees with facts: {name}")
    raw_path = folder / "companyfacts.json"
    raw = read_json(raw_path) if raw_path.exists() else {}
    peer_reports = read_json(folder / "peers.json")
    if peers is not None and set(peers) != set(peer_reports):
        raise data.DeskError("Requested peers differ from saved peers; use a matching run or refresh the data desk.")
    packet = {"company": report["company"], "facts": report, "metrics": annual_metrics(report, raw),
              "peers": {}, "peer_policy": "Compare only compatible definitions and fiscal periods. Raw cash-flow dollars are size-dependent; cash-flow margin supports size-adjusted comparison. No automatic peer ranking."}
    packet["signals"] = review_signals(packet["metrics"])
    paths = ["facts.json", "calculations.json", "peers.json"] + (["companyfacts.json"] if raw_path.exists() else [])
    for ticker, peer in peer_reports.items():
        if not re.fullmatch(r"[A-Z0-9.-]+", ticker):
            raise data.DeskError("Invalid peer ticker in saved data")
        if "facts" not in peer:
            packet["peers"][ticker] = {"missing": peer.get("error", "peer facts unavailable")}
            continue
        if peer["facts"]["company"]["ticker"] != ticker:
            raise data.DeskError("Peer facts have a different ticker")
        relative = f"peers/{ticker}/companyfacts.json"
        peer_raw = read_json(folder / relative) if (folder / relative).exists() else {}
        if peer_raw:
            paths.append(relative)
        packet["peers"][ticker] = {"facts": peer["facts"], "metrics": annual_metrics(peer["facts"], peer_raw),
                                   "periods_match_company": peer["facts"]["periods"] == report["periods"]}
    return packet, paths


def display(value, unit):
    """Shown value: whole dollars for USD, 2 decimal places otherwise. JSON keeps the exact value."""
    if value is None:
        return None
    number = Decimal(str(value))
    return f"{number:.0f}" if unit == "USD" else f"{number:.2f}"


def metric_lines(packet):
    """Line-citable Python results retain every input's original tag/period/accession."""
    lines = []
    def append(text):
        lines.append({"source": "Python evidence", "line": len(lines) + 1, "text": text})
    companies = {packet["company"]["ticker"]: packet, **packet["peers"]}
    for ticker, bundle in companies.items():
        if "metrics" not in bundle:
            append(f"{ticker}: unavailable: {bundle['missing']}")
            continue
        for column, metrics in bundle["metrics"].items():
            for name, metric in metrics.items():
                label = f"{ticker} {column} {name}; period={metric['period']}"
                if metric["value"] is None:
                    append(f"{label}: unavailable ({metric['reason']})")
                    continue
                append(f"{label}: {display(metric['value'], metric['unit'])} {metric['unit']}; "
                       f"formula: {metric['arithmetic']}; definition: {metric['definition']}")
                metric["citation"] = f"[Python evidence L{len(lines)}]"
                for entry in metric["inputs"]:
                    append(f"{ticker} input: {entry['val']} {entry['unit']}; {entry['tag']}; {entry.get('start', 'instant')} to {entry['end']}; accession={entry['accn']}; {entry['filing_url']}")
    append("Review policy: at least 5 percentage points (500 basis points) in either direction; a student-selected trigger, not a filing fact.")
    signals = packet["signals"]
    append(f"Annual operating-margin change: {display(signals['operating_margin_change_pp'], 'pp')} percentage points; high-priority review={signals['high_priority_review']}; ROE/debt/coverage warning={signals['roe_debt_warning']}. Unknown is not false.")
    return lines


def supplements(path):
    """Only explicit local text sources with a title, date, URL, and captured bytes."""
    if path is None:
        return [], []
    path = Path(path).resolve()
    records = read_json(path)
    if not isinstance(records, list):
        raise data.DeskError("Supplement manifest must be a JSON list.")
    sources, lines = [], []
    for i, record in enumerate(records, 1):
        if not all(record.get(k) for k in ("file", "title", "date", "url")):
            raise data.DeskError("Each supplement needs file, title, date and url.")
        source = (path.parent / record["file"]).resolve()
        url = urlparse(record["url"])
        if not source.is_relative_to(path.parent) or source.suffix.lower() not in {".txt", ".md"}:
            raise data.DeskError("Supplement text must be a .txt or .md file within the manifest folder.")
        if url.scheme != "https" or not url.netloc or url.username or url.password:
            raise data.DeskError("Supplement source must have a public HTTPS URL without credentials.")
        date.fromisoformat(record["date"])
        if source.stat().st_size > 100000:
            raise data.DeskError("Supplement exceeds 100 KB; supply a labeled excerpt with its original page numbers.")
        text = source.read_text(encoding="utf-8")
        label = f"Management supplement {i}"
        sources.append({"source": label, "title": record["title"], "date": record["date"], "url": record["url"],
                        "sha256": digest(source), "text": text})
        lines += [{"source": label, "line": n, "text": line} for n, line in enumerate(text.splitlines(), 1)]
    return sources, lines
