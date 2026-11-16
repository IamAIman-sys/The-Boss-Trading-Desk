"""Evidence-preserving extraction and screening. No model calls or issuer rules."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import json
import re


class SeekerError(ValueError):
    pass


def day(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        raise SeekerError("Use an exact calendar date in YYYY-MM-DD form.") from None


def number(value):
    try:
        result = Decimal(str(value).replace(",", ""))
    except (InvalidOperation, TypeError):
        raise SeekerError("Expected a finite number.") from None
    if not result.is_finite():
        raise SeekerError("Expected a finite number.")
    return result


def load_factors(path):
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SeekerError(f"Cannot read factor JSON: {path}") from None
    if not isinstance(config, dict):
        raise SeekerError("Factor file must be a JSON object.")
    window = config.get("window_days")
    if type(window) is not int or window <= 0:
        raise SeekerError("Factor file is empty or incomplete: write your positive integer window_days by hand.")
    factors = config.get("factors")
    if not isinstance(factors, list) or not factors:
        raise SeekerError("Factor file is empty: write your own factors, directions, chapters and weights.")
    names = set()
    for i, factor in enumerate(factors, 1):
        if not isinstance(factor, dict):
            raise SeekerError(f"Factor {i} must be an object.")
        for key in ("name", "metric", "direction", "chapter"):
            if not isinstance(factor.get(key), str) or not factor[key].strip():
                raise SeekerError(f"Factor {i} is incomplete: fill {key} yourself.")
        if factor["name"] in names:
            raise SeekerError("Factor names must be unique.")
        names.add(factor["name"])
        if factor["direction"] not in ("higher", "lower"):
            raise SeekerError(f"Factor {i}: direction must be higher or lower.")
        weight = number(factor.get("weight"))
        if weight < 0:
            raise SeekerError("Weights must be nonnegative; use direction to choose preference.")
        metric = factor["metric"]
        if metric not in BUILTIN_METRICS and not (metric.startswith("filing:") and metric[7:].strip()):
            raise SeekerError(f"Factor {i}: unsupported metric. See references/contracts.md; no metric is guessed.")
    if not any(number(f["weight"]) > 0 for f in factors):
        raise SeekerError("At least one factor must have a positive weight.")
    return config


BUILTIN_METRICS = {"first_close", "latest_close", "return_since_first_close_pct",
                   "days_since_distribution", "distribution_ratio"}
CORE_FACTS = ("parent", "parent_cik", "distribution_ratio", "record_date", "distribution_date", "ticker")
MONTHS = {name.lower(): i for i, name in enumerate(
    ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"), 1)}
DATE = r"(?:\d{4}-\d{2}-\d{2}|(?:" + "|".join(MONTHS) + r")\s+\d{1,2},?\s+\d{4})"
WORDS = dict(zip("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split(), range(1, 21)))
COUNT = r"(?:\d+(?:\.\d+)?|" + "|".join(WORDS) + ")"


def filing_day(text):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return day(text).isoformat()
    match = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", text)
    try:
        return date(int(match[3]), MONTHS[match[1].lower()], int(match[2])).isoformat()
    except (KeyError, TypeError, ValueError):
        raise SeekerError("Invalid filing date text.") from None


def count(text):
    return Decimal(WORDS[text.lower()]) if text.lower() in WORDS else number(text)


def cite(doc, line, quote, section):
    return {"filing": doc["filing"], "document": doc["url"], "filed": doc["filed"],
            "form": doc["form"], "section": section, "line": line, "quote": quote,
            "text_file": doc.get("text_file")}


def extract(doc, issuer, metrics=(), parent_document=False):
    """Accept explicit statements only. Unsupported prose remains for human reading."""
    result = {"facts": [], "proof": [], "information": [], "rejections": [], "metrics": []}
    section = "Document text"
    lines = doc["text"].splitlines()
    spin_context = bool(re.search(r"\b(?:spin[- ]?off|separation and distribution)\b", doc["text"], re.I))
    for index, raw in enumerate(lines, 1):
        line = " ".join(raw.split())
        if not line:
            continue
        if len(line) < 140 and (line.isupper() or re.match(r"(?:Item\s+\d|#{1,6}\s)", line, re.I)):
            section = line.lstrip("# ")
        source = cite(doc, index, line, section)
        if re.fullmatch(r"(?:Preliminary\s+)?Information Statement(?:\s+dated\s+.*)?", line, re.I):
            result["information"].append(source)
        # A parent's unrelated 8-K must not contribute a fact for this issuer.
        if parent_document and issuer.lower() not in line.lower():
            continue
        negative = bool(re.search(r"\b(?:not|never|no longer|may|might|could)\b", line, re.I))
        distribution = re.search(r"\b(?:will distribute|distributed|has distributed|completed (?:the |its )?(?:spin-off|spinoff|distribution))\b", line, re.I)
        if distribution and spin_context and not negative and re.search(r"\b(?:shares?|common stock|stockholders?|shareholders?)\b", line, re.I):
            # Require recipients: a mere use of 'distribution' does not prove a spin.
            if re.search(r"\b(?:holders|stockholders|shareholders)\b", line, re.I):
                result["proof"].append(source)
        for pattern, reason in (
            (r"(?:we are|registrant is|company is|entity type\s*[:|])\s+(?:an?\s+)?(?:registered\s+)?(?:investment company|investment fund|closed-end fund|mutual fund|shell company)", "Fund or shell registration"),
            (r"(?:registering|registration of)\s+(?:our\s+)?(?:already outstanding|existing outstanding|previously issued)\s+(?:shares|common stock)", "Registration of existing shares"),
            (r"(?:abandoned|cancelled|canceled|terminated)\s+(?:the\s+)?(?:planned\s+)?(?:spin-off|spinoff|distribution)", "Distribution plan cancelled"),
        ):
            if re.search(pattern, line, re.I) and not re.search(r"\bnot\b", line, re.I):
                result["rejections"].append({"reason": reason, "source": source})

        def add(field, value):
            result["facts"].append({"field": field, "value": value, "source": source})

        if not parent_document:
            parent = re.search(r"(?:^|\|\s*)Parent(?: company)?\s*[:|]\s*([^|;]+?)(?:[,;]?\s+CIK\b|\s*\||$)", line, re.I)
            if not parent:
                parent = re.search(r"(?:wholly[- ]owned subsidiary of)\s+(.+?)(?:\s*\(|[;|]|$)", line, re.I)
            if not parent:
                parent = re.search(r'([A-Z][A-Za-z0-9 &,.-]{1,100}?)\s*\((?:the\s+)?["“]Parent["”]\)', line)
            if parent:
                add("parent", parent[1].strip().rstrip(".,"))
            cik = re.search(r"\bParent(?: company)?(?:\s+CIK)?\s*[:|].*?\bCIK\s*[:#]?\s*(\d{1,10})\b|\bParent CIK\s*[:|]\s*(\d{1,10})\b", line, re.I)
            if cik:
                add("parent_cik", (cik[1] or cik[2]).zfill(10))
            ticker = re.search(r"(?:^|\|\s*)(?:Regular[- ]way )?(?:Trading symbol|Ticker)\s*[:|]\s*[\"“]?([A-Z][A-Z0-9.-]{0,14})\b", line)
            if ticker and not re.search(r"when[- ]issued", line, re.I):
                add("ticker", ticker[1])
        # Planned/conditional dates do not establish an actual distribution.
        uncertain = re.search(r"\b(?:expected|anticipated|proposed|tentative|approximately|subject to|may|might|could|preliminary)\b", line, re.I)
        for field, label in (("record_date", "record"), ("distribution_date", "distribution")):
            direct = re.search(rf"\b{label} date\s*[:|]\s*({DATE})", line, re.I)
            narrative = None
            if field == "record_date":
                narrative = re.search(rf"\b(?:holders|stockholders|shareholders) of record\s+(?:as of |on )?(?:the close of business on )?({DATE})", line, re.I)
            elif distribution and len(set(re.findall(DATE, line, re.I))) == 1:
                narrative = re.search(rf"\bon\s+({DATE})", line, re.I)
            found = direct or narrative
            if found and not uncertain and not negative:
                try:
                    add(field, filing_day(found[1]))
                except SeekerError:
                    pass
        ratio = re.search(rf"\bdistribution ratio\s*[:|]\s*({COUNT})\s*(?:for|:|/)\s*({COUNT})\b", line, re.I)
        if not ratio:
            ratio = re.search(rf"\b({COUNT})\s+shares?\b.{{0,160}}?\bfor (?:every|each)\s+({COUNT})\s+shares?\b", line, re.I)
        if ratio and not uncertain and not negative:
            numerator, denominator = count(ratio[1]), count(ratio[2])
            if numerator > 0 and denominator > 0:
                add("distribution_ratio", {"numerator": str(numerator), "denominator": str(denominator)})
        for metric in metrics:
            if not metric.startswith("filing:"):
                continue
            label = metric[7:]
            match = re.fullmatch(re.escape(label) + r"\s*[:|]\s*([$]?\s*[-+]?\d[\d,]*(?:\.\d+)?)\s*(%|million|billion|thousand)?[.]?", line, re.I)
            if match and not uncertain:
                raw_value = number(match[1].replace("$", "").replace(" ", ""))
                multiplier = {"million": 1000000, "billion": 1000000000, "thousand": 1000}.get((match[2] or "").lower(), 1)
                result["metrics"].append({"field": metric, "value": str(raw_value * multiplier), "source": source,
                                           "arithmetic": f"{raw_value} * {multiplier}", "unit": match[2] or "as printed"})
    # A parent's CIK can also be read from an EDGAR link whose anchor is its
    # explicitly named parent. Do not fuzzy-match names or pick another CIK.
    parent_facts = [f for f in result["facts"] if f["field"] == "parent"]
    for fact in parent_facts:
        for link in doc.get("links", []):
            if link["text"].casefold().strip() != fact["value"].casefold().strip():
                continue
            match = re.search(r"https://(?:www|data)\.sec\.gov/(?:Archives/edgar/data/|submissions/CIK)(\d{1,10})(?:/|\.json)", link["href"])
            if match:
                result["facts"].append({"field": "parent_cik", "value": match[1].zfill(10),
                    "source": {**fact["source"], "parent_link": link["href"]}})
    return result


def select_fact(entries):
    """Newest filing supersedes earlier prose; same-date conflicts remain unknown."""
    if not entries:
        return None
    newest = max(item["source"]["filed"] for item in entries)
    choices = [item for item in entries if item["source"]["filed"] == newest]
    values = {json.dumps(item["value"], sort_keys=True) for item in choices}
    if len(values) != 1:
        return None
    return choices[-1]


def build_record(cik, name, documents, filings, metrics=(), issues=(), domestic=None):
    results = [extract(doc, name, metrics, doc.get("parent_document", False)) for doc in documents]
    facts = [f for result in results for f in result["facts"]]
    proof = [p for result in results for p in result["proof"]]
    information = [p for result in results for p in result["information"]]
    rejections = [p for result in results for p in result["rejections"]]
    registrations = [d for d in documents if d["form"] in REGISTRATION_FORMS and not d.get("parent_document")]
    if registrations and not information and not issues:
        last = max(registrations, key=lambda d: d["filed"])
        rejections.append({"reason": "Form 10 has no readable information statement", "source": cite(last, 1, last["text"].splitlines()[0] if last["text"] else "", "Document inventory")})
    # Later distribution evidence can rescue an earlier non-spin registration.
    active_rejections = [r for r in rejections if not any(p["filed"] > r["source"]["filed"] for p in proof)]
    record = {"cik": cik, "name": name, "facts": {}, "observations": {}, "history": facts,
              "spinoff_evidence": proof, "information_statement": information, "rejections": active_rejections,
              "documents": [{k: v for k, v in doc.items() if k != "text"} for doc in documents],
              "issues": list(issues), "domestic": domestic, "filings": filings}
    for key in CORE_FACTS:
        entries = [f for f in facts if f["field"] == key]
        record["facts"][key] = select_fact(entries)
        if entries and record["facts"][key] is None:
            record["issues"].append(f"Conflicting {key} in the newest filing date; left blank.")
    for metric in metrics:
        items = [f for result in results for f in result["metrics"] if f["field"] == metric]
        selected = select_fact(items)
        if selected:
            record["observations"][metric] = selected
    return record


REGISTRATION_FORMS = {"10", "10/A", "10-12B", "10-12B/A", "10-12G", "10-12G/A"}
TRADING_FORMS = {"10-Q", "10-Q/A", "10-K", "10-K/A", "4", "4/A"}


def value(record, field):
    fact = record["facts"].get(field)
    return fact["value"] if fact else None


def classify(record, as_of, start, window):
    result = {"stage": "registered", "category": "watch", "reasons": [], "window_end": None}
    if record["rejections"]:
        return {**result, "category": "dropped", "reasons": [r["reason"] for r in record["rejections"]]}
    if not record["spinoff_evidence"]:
        result["reasons"].append("Parent distribution not established; candidate only.")
    if not value(record, "parent"):
        result["reasons"].append("Parent identity not established.")
    if any(issue.startswith(("SEC ", "Unreadable", "No readable", "Document has", "Invalid SEC")) for issue in record["issues"]):
        result["reasons"].append("Filing coverage is incomplete; review before ranking.")
    if record.get("domestic") is not True:
        result["reasons"].append("U.S. incorporation not established." if record.get("domestic") is None else "Non-U.S. registrant; outside screen.")
    listing = [f for f in record["filings"] if f["form"] in {"CERT", "CERT/A"} and day(f["filed"]) <= as_of]
    if listing:
        result["stage"] = "listing approved"
    distribution = value(record, "distribution_date")
    # These must be the new issuer's filings, not the parent's or a CERT.
    proof = [f for f in record["filings"] if f["form"] in TRADING_FORMS and f["cik"] == record["cik"]
             and day(f["filed"]) <= as_of and (not distribution or day(f["filed"]) >= day(distribution))]
    if proof:
        result["stage"] = "trading"
        result["category"] = "unranked"
    if not distribution:
        result["reasons"].append("Distribution date is missing; no window or first price can be established.")
        return result
    distribution = day(distribution)
    if distribution < start:
        return {**result, "category": "outside", "reasons": ["Distribution precedes the requested start date."]}
    if not value(record, "record_date"):
        result["reasons"].append("Record date is missing.")
    if value(record, "record_date") and day(value(record, "record_date")) > distribution:
        result["reasons"].append("Record date is later than the distribution date; review the filing.")
    if distribution > as_of:
        result["reasons"].append("Distribution date is in the future.")
        return result
    result["window_end"] = (distribution + timedelta(days=window)).isoformat()
    if not proof:
        result["reasons"].append("No own-company 10-Q, 10-K or Form 4 after distribution to prove trading.")
        return result
    result["stage"] = "in its window" if as_of <= distribution + timedelta(days=window) else "past it"
    result["category"] = "window" if result["stage"] == "in its window" else "past"
    if result["reasons"] and result["category"] == "window":
        result["category"] = "unranked"
    return result


def choose_prices(payload, ticker, distribution, as_of):
    """Reader must attest complete coverage and official regular-way USD closes."""
    if payload is None or payload == "not available":
        return {"reason": "Closes reader: not available."}
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        return {"reason": "Closes reader did not return an available series."}
    if payload.get("complete") is not True or payload.get("ticker") != ticker:
        return {"reason": "Reader cannot attest a complete series for this ticker; first close is unknown."}
    requested_start = distribution + timedelta(days=1)
    try:
        if day(payload.get("start_date")) > requested_start or day(payload.get("end_date")) < as_of:
            return {"reason": "Reader coverage does not include the full requested date range."}
    except SeekerError:
        return {"reason": "Reader coverage dates are missing or invalid."}
    rows = payload.get("closes")
    if not isinstance(rows, list):
        return {"reason": "Reader closes must be a list."}
    accepted = {}
    rejected = 0
    for row in rows:
        try:
            stamp = day(row["date"])
            close = number(row["close"])
        except (KeyError, TypeError, SeekerError):
            return {"reason": "Reader has a malformed close; no price selected."}
        if stamp <= distribution or stamp > as_of:
            rejected += 1
            continue
        if row.get("session") != "regular" or row.get("kind") != "official_close" or row.get("currency") != "USD":
            # Do not skip a questionable first observation and call a later one 'first'.
            return {"reason": "Reader includes an unconfirmed, when-issued, adjusted or non-USD close after distribution."}
        if close <= 0 or not row.get("source"):
            return {"reason": "Reader close is nonpositive or lacks a source."}
        if stamp in accepted and number(accepted[stamp]["close"]) != close:
            return {"reason": "Reader has conflicting closes for the same date."}
        accepted[stamp] = {"date": stamp.isoformat(), "close": str(close), "source": row["source"],
                           "session": "regular", "kind": "official_close", "currency": "USD"}
    if not accepted:
        return {"reason": "No official regular-way close strictly after distribution in the requested range."}
    return {"first": accepted[min(accepted)], "latest": accepted[max(accepted)],
            "excluded_outside_dates": rejected}


def measurements(record, prices, as_of):
    values = dict(record["observations"])
    distribution = value(record, "distribution_date")
    if distribution:
        values["days_since_distribution"] = {"value": str((as_of - day(distribution)).days),
            "arithmetic": f"{as_of} - {distribution} (calendar days)", "source": record["facts"]["distribution_date"]["source"]}
    ratio = value(record, "distribution_ratio")
    if ratio:
        numerator, denominator = number(ratio["numerator"]), number(ratio["denominator"])
        values["distribution_ratio"] = {"value": str(numerator / denominator),
            "arithmetic": f"{numerator} / {denominator}", "source": record["facts"]["distribution_ratio"]["source"]}
    if "first" in prices:
        first, latest = prices["first"], prices["latest"]
        for key, quote in (("first_close", first), ("latest_close", latest)):
            values[key] = {"value": quote["close"], "source": quote}
        a, b = number(first["close"]), number(latest["close"])
        values["return_since_first_close_pct"] = {"value": str((b - a) / a * 100),
            "arithmetic": f"({b} - {a}) / {a} * 100", "source": {"first": first, "latest": latest}}
    return values


def rank(rows, factors):
    """Each factor uses its own full eligible pool, independent of other weights."""
    active = [f for f in factors if number(f["weight"]) > 0]
    for row in rows:
        row["points"] = {}
        row["total_points"] = None
        row["missing_factors"] = []
    for factor in active:
        metric = factor["metric"]
        pool = [(row, number(row["measurements"][metric]["value"])) for row in rows if metric in row["measurements"]]
        for row in rows:
            if metric not in row["measurements"]:
                row["missing_factors"].append(factor["name"])
        for row, val in pool:
            worse = sum(v < val if factor["direction"] == "higher" else v > val for _, v in pool)
            equal_other = sum(v == val for _, v in pool) - 1
            percentile = (Decimal(worse) + Decimal(equal_other) / 2) / (len(pool) - 1) if len(pool) > 1 else Decimal("0.5")
            points = number(factor["weight"]) * percentile
            row["points"][factor["name"]] = {"points": str(points), "value": str(val), "metric": metric,
                "weight": str(factor["weight"]), "direction": factor["direction"], "chapter": factor["chapter"],
                "arithmetic": f"{factor['weight']} * {percentile}", "pool_size": len(pool),
                "worse_count": worse, "equal_other_count": equal_other,
                "source": row["measurements"][metric]}
    for row in rows:
        if not row["missing_factors"]:
            row["total_points"] = str(sum((number(x["points"]) for x in row["points"].values()), Decimal(0)))
    ranked = sorted((r for r in rows if r["total_points"] is not None), key=lambda r: (-number(r["total_points"]), r["cik"]))
    for i, row in enumerate(ranked, 1):
        row["rank"] = i
    return ranked
