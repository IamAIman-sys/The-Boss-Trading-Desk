#!/usr/bin/env python3
"""Run the Lab 06 filing-backed spinoff screen. Human factors are required."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from core import (CORE_FACTS, REGISTRATION_FORMS, SeekerError, build_record, choose_prices,
                  classify, day, load_factors, measurements, rank, value)
from edgar import SECClient, base_url, discover, domestic_status, read_filing, submissions

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]


def save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def load_reader(path):
    if path is None:
        return None
    path = Path(path).resolve()
    if not path.is_file():
        raise SeekerError("Closes-reader file does not exist. Supply your own Python reader path.")
    spec = importlib.util.spec_from_file_location("spinoff_user_closes_reader", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        raise SeekerError("Could not load closes reader; check it separately. No exception content was logged.") from None
    reader = getattr(module, "daily_closes", None)
    if not callable(reader):
        raise SeekerError("Your reader must export daily_closes(ticker, start_date, end_date). See references/contracts.md.")
    return reader


def prices_for(record, reader, as_of):
    distribution, ticker = value(record, "distribution_date"), value(record, "ticker")
    if not distribution or not ticker:
        return {"reason": "Missing distribution date or filing-backed regular-way ticker; prices not available."}
    distribution = day(distribution)
    if distribution >= as_of:
        return {"reason": "No completed date after distribution in this run's range."}
    if reader is None:
        return {"reason": "No closes reader supplied; prices not available."}
    try:
        payload = reader(ticker, (distribution + timedelta(days=1)).isoformat(), as_of.isoformat())
    except Exception:
        return {"reason": "Closes reader failed; prices not available. Check the reader separately."}
    return choose_prices(payload, ticker, distribution, as_of)


def collect_company(client, cik, index_rows, as_of, start, metrics, evidence):
    metadata, own_filings = submissions(client, cik, as_of)
    # Index rows catch records not yet incorporated into the submissions response.
    merged = {f["accession"]: f for f in index_rows if f["cik"] == cik}
    merged.update({f["accession"]: f for f in own_filings})
    own_filings = sorted(merged.values(), key=lambda f: (f["filed"], f["accession"]))
    name = metadata.get("name") or next((f["name"] for f in index_rows if f["cik"] == cik), cik)
    documents, issues = [], []
    for filing in own_filings:
        if filing["form"] not in REGISTRATION_FORMS | {"CERT", "CERT/A"} and not (
            filing["form"] in {"8-K", "8-K/A"} and day(filing["filed"]) >= start):
            continue
        try:
            docs, errors = read_filing(client, filing, evidence)
            documents.extend(docs)
            issues.extend(errors)
        except SeekerError as exc:
            issues.append(str(exc))
    record = build_record(cik, name, documents, own_filings, metrics, issues, domestic_status(metadata))
    record["incorporation_source"] = {"url": f"https://data.sec.gov/submissions/CIK{cik}.json",
                                      "stateOfIncorporation": metadata.get("stateOfIncorporation")}
    parent_cik = value(record, "parent_cik")
    if parent_cik and parent_cik != cik:
        try:
            _, parent_filings = submissions(client, parent_cik, as_of)
            parent_by_accession = {f["accession"]: f for f in index_rows if f["cik"] == parent_cik}
            parent_by_accession.update({f["accession"]: f for f in parent_filings})
            parent_filings = sorted(parent_by_accession.values(), key=lambda f: (f["filed"], f["accession"]))
            for filing in parent_filings:
                if filing["form"] not in {"8-K", "8-K/A"} or day(filing["filed"]) < start:
                    continue
                try:
                    docs, errors = read_filing(client, filing, evidence)
                    documents.extend({**doc, "parent_document": True} for doc in docs)
                    issues.extend(errors)
                except SeekerError as exc:
                    issues.append(str(exc))
        except SeekerError as exc:
            issues.append(str(exc))
        new = build_record(cik, name, documents, own_filings, metrics, issues, domestic_status(metadata))
        new["incorporation_source"] = record["incorporation_source"]
        record = new
    elif not parent_cik:
        record["issues"].append("Parent CIK not found in readable filings; parent's distribution 8-K could not be searched.")
    return record


def screen(records, config, start, as_of, reader=None):
    rows, eligible = [], []
    for record in records:
        status = classify(record, as_of, start, config["window_days"])
        prices = prices_for(record, reader, as_of) if status["category"] in {"window", "unranked", "past"} else {"reason": "No trading name eligible for a price in this section."}
        row = {"cik": record["cik"], "name": record["name"], "status": status, "prices": prices,
               "facts": record["facts"], "measurements": measurements(record, prices, as_of),
               "issues": record["issues"], "rejections": record["rejections"]}
        rows.append(row)
        if status["category"] == "window":
            eligible.append(row)
    ranked = rank(eligible, config["factors"])
    for row in eligible:
        if row["missing_factors"]:
            row["status"]["category"] = "unranked"
            row["status"]["reasons"].append("Missing active factor inputs: " + ", ".join(row["missing_factors"]))
    return rows, ranked


def safe(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def fact_value(row, key):
    item = row["facts"].get(key)
    if not item:
        return "not found"
    if key == "distribution_ratio":
        return f"{item['value']['numerator']} for {item['value']['denominator']}"
    return str(item["value"])


def source_text(source):
    if not source:
        return "not found"
    return f"{source.get('filing', '')}; {source.get('document', '')}; section {source.get('section', '')}; L{source.get('line', '')}; {source.get('quote', '')}"


def render(rows, ranked, config, run_date, index_sources, start, index_start, as_of, errors):
    price_dates = sorted({r["prices"][key]["date"] for r in rows for key in ("first", "latest") if key in r["prices"]})
    index_date = max((s["through"] for s in index_sources if s.get("through")), default="not available")
    lines = [f"Run date: {run_date} | Price date(s): {', '.join(price_dates) or 'not available'} | Index date: {index_date}", "",
             "# Spinoff screen", "", f"Distribution start: {start}; as of: {as_of}; index search starts: {index_start}.",
             f"Window: distribution date through distribution date + {config['window_days']} calendar days, inclusive. Trading proof is required.",
             "Weights and directions are the student's unvalidated hypotheses. This run does not test predictive returns.",
             "Points = weight × within-factor percentile. Percentile = (worse values + 0.5 × equal OTHER values) / (pool size − 1); a one-name pool receives 0.5. Higher/lower follows the factor file. Ties in total points use CIK for stable display order.",
             "Each factor's pool includes all otherwise eligible in-window names with that metric, even if another metric is missing. A zero weight removes only that factor's points. Missing active metrics leave the name unranked.", "",
             "## Declared factors", ""]
    for factor in config["factors"]:
        lines.append(f"- {safe(factor['name'])}: metric {safe(factor['metric'])}; direction {factor['direction']}; weight {factor['weight']}; chapter {safe(factor['chapter'])}." + (" Disabled; no points." if str(factor['weight']) in {"0", "0.0"} else ""))
    lines += ["", "## In-window names by rank", "", "| Rank | Name / CIK | Parent | Distribution | Window ends | First close | Latest close | Points |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in ranked:
        def price(key):
            item = row["prices"].get(key)
            return f"{item['close']} USD on {item['date']} ({safe(item['source'])})" if item else "not available"
        lines.append(f"| {row['rank']} | {safe(row['name'])} / {row['cik']} | {safe(fact_value(row, 'parent'))} | {fact_value(row, 'distribution_date')} | {row['status']['window_end']} | {price('first')} | {price('latest')} | {row['total_points']} |")
    if not ranked:
        lines.append("\nNo names could be ranked from the established facts and active factors.")
    for row in rows:
        if row.get("points"):
            lines += ["", f"### Factor points: {safe(row['name'])} ({row['cik']})"]
            for name, points in row["points"].items():
                lines.append(f"- {safe(name)}: value {points['value']}; {points['arithmetic']} = {points['points']} points; pool {points['pool_size']}, worse {points['worse_count']}, tied others {points['equal_other_count']}.")
                lines.append("  Input evidence: " + safe(json.dumps(points["source"], ensure_ascii=False)))
    for category, heading in (("watch", "Watch list: registered or listing approved, not yet proven trading"),
                              ("unranked", "Unranked: missing evidence or inputs"), ("dropped", "Dropped and why"),
                              ("past", "Past the window"), ("outside", "Before the requested distribution start")):
        lines += ["", "## " + heading, ""]
        subset = [r for r in rows if r["status"]["category"] == category]
        if not subset:
            lines.append("None.")
        for row in subset:
            lines.append(f"- {safe(row['name'])} ({row['cik']}): {row['status']['stage']}; distribution {fact_value(row, 'distribution_date')}; " + safe("; ".join(row["status"]["reasons"])))
            for reason in row["rejections"]:
                lines.append("  " + safe(reason["reason"] + ": " + source_text(reason["source"])))
            for key in ("first", "latest"):
                if key in row["prices"]:
                    p = row["prices"][key]
                    lines.append(f"  {key} close: {p['close']} USD on {p['date']}; {safe(p['source'])}.")
    lines += ["", "## Registry facts and citations", ""]
    for row in rows:
        lines.append(f"### {safe(row['name'])} ({row['cik']})")
        for key in CORE_FACTS:
            fact = row["facts"].get(key)
            lines.append(f"- {key}: {safe(fact_value(row, key))}. " + safe(source_text(fact["source"]) if fact else "Not found; registry value is blank."))
    lines += ["", "## What the data cannot show", "",
              "Extraction accepts explicit labels and supported sentences only. Unrecognized tables, image-only documents, indirect parent identifiers, conditional dates and ambiguous statements require manual filing review. Blank does not mean zero or absent.",
              "The screen does not establish historical index membership, forced selling, analyst coverage, standalone cost adjustments, value or investment suitability. No model estimates those facts.",
              "U.S. scope uses the SEC submissions state-of-incorporation code. Unknown domicile remains unranked. Submissions metadata is current, not a reconstructed historical snapshot.",
              "First close is strictly after the distribution date, from a reader-attested complete series of official regular-way USD closes. Same-day, when-issued and adjusted prices are never used as the first close. No reader or incomplete coverage means not available.",
              "This is a filing-date screen, not a point-in-time backtest; a same-day filing may arrive after market close. Full indexes may have publication lag. Index date above is the latest indexed filing date actually read."]
    if index_start > date(1994, 7, 1):
        lines.append("Search coverage is restricted by --index-start. Registrations before that date can be missed unless already in the registry or found through a later CERT; this screen is not an exhaustive historical universe.")
    for error in errors:
        lines.append("- Incomplete coverage: " + safe(error))
    for row in rows:
        missing = [k for k in CORE_FACTS if not row["facts"].get(k)]
        if missing:
            lines.append(f"- {row['cik']}: missing {', '.join(missing)}.")
        for issue in row["issues"]:
            lines.append(f"- {row['cik']}: {safe(issue)}")
        if "reason" in row["prices"]:
            lines.append(f"- {row['cik']}: {safe(row['prices']['reason'])}")
    lines += ["", "## Index sources", ""]
    lines.extend(f"- {s['url']} (through {s['through'] or 'no rows in range'})" for s in index_sources)
    lines += ["", "screens, not recommendations"]
    return "\n".join(lines) + "\n"


def run(args, client, reader, config):
    start, as_of, index_start = day(args.start_date), day(args.as_of), day(args.index_start)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S-%fZ")
    folder = Path(args.output) / stamp
    folder.mkdir(parents=True, exist_ok=False)
    save(folder / "factors_used.json", config)
    registry_path = Path(args.output) / "registry.json"
    previous = {}
    if registry_path.exists():
        try:
            previous = json.loads(registry_path.read_text(encoding="utf-8"))
        except ValueError:
            raise SeekerError("Existing registry is invalid JSON; restore it before running.") from None
    rows, indexes = discover(client, index_start, as_of)
    candidates = {r["cik"] for r in rows if r["form"] in REGISTRATION_FORMS | {"CERT", "CERT/A"}}
    candidates.update(previous.get("companies", {}))
    records, errors = [], []
    metrics = [f["metric"] for f in config["factors"]]
    for cik in sorted(candidates):
        print(f"Reading registration trail for CIK {cik}", flush=True)
        try:
            records.append(collect_company(client, cik, rows, as_of, start, metrics, folder / "filings"))
        except SeekerError as exc:
            errors.append(f"CIK {cik}: {exc}")
    screen_rows, ranked = screen(records, config, start, as_of, reader)
    payload = {"schema_version": 1, "run_date": stamp, "as_of": args.as_of, "start_date": args.start_date,
               "index_start": args.index_start, "index_sources": indexes, "errors": errors,
               "companies": {r["cik"]: r for r in records}}
    # Retain old rows when retrieval fails, but never rank stale rows as current.
    for cik, old in previous.get("companies", {}).items():
        if cik not in payload["companies"]:
            payload["companies"][cik] = {**old, "stale": True}
    save(folder / "registry.json", payload)
    save(registry_path, payload)
    save(folder / "screen.json", {"run_date": stamp, "rows": screen_rows, "errors": errors})
    report = render(screen_rows, ranked, config, stamp, indexes, start, index_start, as_of, errors)
    path = folder / "report.md"
    path.write_text(report, encoding="utf-8")
    print(f"Report: {path.resolve()}")
    print(f"Registry: {registry_path.resolve()}")
    return 2 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True, help="Include distributions on or after YYYY-MM-DD")
    parser.add_argument("--as-of", default=datetime.now(ZoneInfo("America/New_York")).date().isoformat())
    parser.add_argument("--index-start", default="1994-07-01", help="Registration discovery begins here; shortening this range restricts coverage")
    parser.add_argument("--factors", type=Path, default=SKILL / "factors.json")
    parser.add_argument("--env", type=Path, default=ROOT / ".env")
    parser.add_argument("--closes-reader", type=Path, help="Your own Python module with daily_closes(ticker, start_date, end_date)")
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "spinoff-seeker")
    args = parser.parse_args(argv)
    try:
        config = load_factors(args.factors)  # Before network, reader import or output creation.
        start, as_of, index_start = day(args.start_date), day(args.as_of), day(args.index_start)
        if not date(1994, 7, 1) <= index_start <= start <= as_of:
            raise SeekerError("Require 1994-07-01 <= index-start <= start-date <= as-of.")
        if as_of > datetime.now(ZoneInfo("America/New_York")).date():
            raise SeekerError("As-of cannot be in the future.")
        reader = load_reader(args.closes_reader)
        client = SECClient(args.env, args.output / "cache")
        return run(args, client, reader, config)
    except (SeekerError, OSError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
