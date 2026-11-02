#!/usr/bin/env python3
"""SEC data tools for an equity research desk; no model or company-specific rules."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import parse_qs, quote, urljoin, urlparse

from bs4 import BeautifulSoup
from dotenv import dotenv_values
from pypdf import PdfReader
import requests

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
ANNUAL_FORMS = {"10-K", "10-K/A"}
STEPS = {
    1: "Resolve ticker to CIK",
    2: "List filings and select the latest 10-K, 10-Q, and Item 2.02 8-K",
    3: "Download filings and Exhibit 99.1; save plain text",
    4: "Read annual XBRL facts and the prior year",
    5: "Calculate financial ratios with arithmetic",
    6: "Find quarterly revenue and diluted EPS in the release",
    7: "Read peer facts and calculate operating margins",
}
# Candidate order breaks ties only. The newest annual period wins first.
# Noncurrent debt and its current portion are separate concepts. Lease-inclusive
# alternatives are labeled explicitly and must use a consistent definition.
CONCEPTS = {
    "revenue": ("Total revenue", "duration", "USD", (
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet", "Revenue",)),
    "operating_income": ("Operating income", "duration", "USD", ("OperatingIncomeLoss",)),
    "net_income": ("Net income", "duration", "USD", ("NetIncomeLoss", "ProfitLoss")),
    "diluted_eps": ("Diluted EPS", "duration", "USD/shares", ("EarningsPerShareDiluted",)),
    "equity": ("Stockholders' equity", "instant", "USD", ("StockholdersEquity",)),
    "long_term_debt": ("Long-term debt, excluding current portion", "instant", "USD", (
        "LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations")),
    "current_debt": ("Current portion of long-term debt", "instant", "USD", (
        "LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent")),
    "cfo": ("Cash from operations", "duration", "USD", ("NetCashProvidedByUsedInOperatingActivities",)),
    "capex": ("Additions to property and equipment", "duration", "USD", (
        "PaymentsToAcquirePropertyPlantAndEquipment",)),
}


class DeskError(Exception):
    """An actionable data or input error."""


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


class SECClient:
    """One HTTP path: identified requests, a 5/second ceiling, finite retries."""

    def __init__(self, env_path=ROOT / ".env"):
        ua = dotenv_values(env_path, interpolate=False).get("SEC_USER_AGENT", "")
        if not ua or not ua.strip() or "\n" in ua or "\r" in ua:
            raise DeskError("Set SEC_USER_AGENT to a valid one-line value in .env beside this script.")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": ua, "Accept-Encoding": "gzip, deflate"})
        self.last_request = 0.0
        self.cache = {}

    def get(self, url):
        if url in self.cache:
            return self.cache[url]
        # Follow redirects explicitly so they also use the request rate limit.
        target = url
        for attempt in range(6):
            host = urlparse(target).hostname or ""
            if urlparse(target).scheme != "https" or not (host == "sec.gov" or host.endswith(".sec.gov")):
                raise DeskError("Refusing a document URL outside HTTPS SEC.gov.")
            time.sleep(max(0, 0.21 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.session.get(target, timeout=(15, 90), allow_redirects=False)
            except requests.RequestException as exc:
                if attempt == 5:
                    raise DeskError(f"SEC request failed ({type(exc).__name__}): {target}") from None
                time.sleep(min(2 ** attempt, 16))
                continue
            if response.is_redirect:
                target = urljoin(target, response.headers["Location"])
                continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 5:
                retry = response.headers.get("Retry-After", "")
                time.sleep(min(float(retry), 30) if retry.isdigit() else min(2 ** attempt, 16))
                continue
            if response.status_code != 200:
                raise DeskError(f"SEC returned HTTP {response.status_code}: {target}")
            self.cache[url] = response.content
            return response.content
        raise DeskError(f"SEC request exceeded retry/redirect limit: {url}")

    def json(self, url):
        try:
            return json.loads(self.get(url))
        except (ValueError, UnicodeError):
            raise DeskError(f"SEC response is not JSON: {url}") from None


def normalize_ticker(value):
    ticker = value.strip().upper().replace(".", "-")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]{0,14}", ticker):
        raise argparse.ArgumentTypeError("Use a ticker containing letters, digits, dots, or hyphens.")
    return ticker


def resolve(client, ticker):
    for row in client.json(TICKERS_URL).values():
        if normalize_ticker(row["ticker"]) == ticker:
            return {"ticker": ticker, "cik": str(row["cik_str"]).zfill(10), "name": row["title"]}
    raise DeskError(f"Ticker {ticker} was not found in SEC company_tickers.json.")


def plain_text(content):
    """Preserve paragraphs and table rows so numbers retain their row labels."""
    if content.lstrip().startswith(b"%PDF"):
        return "\n\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(content)).pages)
    soup = BeautifulSoup(content, "html.parser")
    for node in soup.find_all(["script", "style", "noscript", "ix:hidden", "ix:header"]):
        node.decompose()
    for node in soup.select('[style*="display:none"], [style*="display: none"], [hidden]'):
        node.decompose()
    for row in list(soup.find_all("tr")):
        if row.parent is None or row.find("tr"):
            continue
        cells = row.find_all(["td", "th"], recursive=False)
        row.replace_with("\n" + " | ".join(c.get_text(" ", strip=True) for c in cells) + "\n")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for block in soup.find_all(["p", "div", "section", "h1", "h2", "h3", "h4", "li", "table"]):
        block.insert_before("\n")
        block.insert_after("\n")
    lines = [re.sub(r"[^\S\n]+", " ", x).strip() for x in soup.get_text().splitlines()]
    return "\n".join(x for x in lines if x) + "\n"


def filing_rows(columns):
    for i in range(len(columns.get("accessionNumber", []))):
        yield {k: v[i] for k, v in columns.items() if isinstance(v, list) and len(v) > i}


def archive_base(cik, accession):
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"


def document_url(base, href):
    result = urljoin(base, href)
    query = parse_qs(urlparse(result).query)
    if "doc" in query:
        result = urljoin("https://www.sec.gov", query["doc"][0])
    return result


def parse_index(content, url):
    soup = BeautifulSoup(content, "html.parser")
    accepted = None
    for head in soup.select(".infoHead"):
        if head.get_text(" ", strip=True).lower() == "accepted":
            value = head.find_next_sibling(class_="info")
            if value:
                accepted = value.get_text(" ", strip=True)
    if not accepted:
        raise DeskError(f"No Accepted time found on EDGAR index: {url}")
    documents = []
    for row in soup.select("table.tableFile tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 4:
            continue
        link = cells[2].find("a", href=True)
        if link:
            documents.append({"description": cells[1].get_text(" ", strip=True),
                              "type": cells[3].get_text(" ", strip=True).upper(),
                              "url": document_url(url, link["href"])})
    return accepted, documents


def has_item_202(text):
    return bool(re.search(r"\bitem\s*2\s*\.\s*02\b", text, re.I))


def select_filings(client, company, folder):
    cik = company["cik"]
    submissions = client.json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    save_json(folder / "submissions.json", submissions)
    rows = list(filing_rows(submissions["filings"]["recent"]))
    chosen = {}
    checked = set()

    def scan():
        for row in sorted(rows, key=lambda r: (r.get("acceptanceDateTime", ""), r["accessionNumber"]), reverse=True):
            form = row.get("form")
            acc = row["accessionNumber"]
            if form not in {"10-K", "10-Q", "8-K"} or form in chosen or acc in checked:
                continue
            checked.add(acc)
            base = archive_base(cik, acc)
            primary = base + quote(row["primaryDocument"], safe="/.-_")
            if form == "8-K":
                items = row.get("items", "")
                if items and not re.search(r"(?<!\d)2\.02(?!\d)", items):
                    continue
                if not has_item_202(plain_text(client.get(primary))):
                    continue
            index_url = base + acc + "-index.html"
            raw = client.get(index_url)
            accepted, documents = parse_index(raw, index_url)
            (folder / f"{form}_index.html").write_bytes(raw)
            chosen[form] = {**row, "index_url": index_url, "accepted": accepted,
                            "document_url": primary, "documents": documents}

    scan()
    # The current submissions response can omit older 10-K/10-Q/earnings filings.
    for part in sorted(submissions["filings"].get("files", []), key=lambda x: x.get("filingTo", ""), reverse=True):
        if len(chosen) == 3:
            break
        history = client.json("https://data.sec.gov/submissions/" + part["name"])
        save_json(folder / part["name"], history)
        rows.extend(filing_rows(history))
        scan()
    save_json(folder / "filings.json", rows)
    for row in sorted(rows, key=lambda x: (x.get("filingDate", ""), x["accessionNumber"]), reverse=True):
        print(f"  {row.get('filingDate', '?')}  {row.get('form', '?'):8}  {row['accessionNumber']}")
    for form in ("10-K", "10-Q", "8-K"):
        if form in chosen:
            row = chosen[form]
            print(f"Selected {form}: {row['accessionNumber']} | Accepted: {row['accepted']} (EDGAR index display)")
    save_json(folder / "selected_filings.json", chosen)
    missing = {"10-K", "10-Q", "8-K"} - chosen.keys()
    if missing:
        raise DeskError("No qualifying filing found for: " + ", ".join(sorted(missing)))
    return chosen


def download_documents(client, selected, folder):
    records = {}
    for form in ("10-K", "10-Q", "8-K"):
        records[form] = {"url": selected[form]["document_url"], "accession": selected[form]["accessionNumber"]}
    release = [d for d in selected["8-K"]["documents"] if re.fullmatch(r"EX-99\.0?1", d["type"])]
    if not release:
        alternatives = [d for d in selected["8-K"]["documents"] if d["type"] == "EX-99"]
        primary_text = plain_text(client.get(selected["8-K"]["document_url"]))
        if len(alternatives) == 1 and has_item_202(primary_text) and re.search(r"exhibit\s+(?:no\.?\s+)?99(?!\d|\.\d)", primary_text, re.I):
            release = alternatives
            print("  The Item 2.02 filing identifies its release as Exhibit 99; preserving that label.")
    if len(release) != 1:
        raise DeskError(f"Selected Item 2.02 8-K has {len(release)} Exhibit 99.1 documents; cannot select an unambiguous release.")
    records["earnings_release"] = {"url": release[0]["url"], "accession": selected["8-K"]["accessionNumber"],
                                    "exhibit_label": "Exhibit " + release[0]["type"].removeprefix("EX-")}
    for name, record in records.items():
        raw = client.get(record["url"])
        suffix = ".pdf" if raw.lstrip().startswith(b"%PDF") else ".html"
        (folder / (name + suffix)).write_bytes(raw)
        text = plain_text(raw)
        if not text.strip():
            raise DeskError(f"No extractable text in {name}; image-only PDFs require OCR.")
        (folder / (name + ".txt")).write_text(text, encoding="utf-8")
        record.update({"raw_file": name + suffix, "text_file": name + ".txt"})
        print(f"  Saved {name + suffix} and {name + '.txt'}")
    save_json(folder / "documents.json", records)
    return records


def annual_entries(taxonomy, tag, unit, kind):
    result = []
    for entry in taxonomy.get(tag, {}).get("units", {}).get(unit, []):
        if entry.get("form") not in ANNUAL_FORMS or not entry.get("end"):
            continue
        if kind == "duration":
            if not entry.get("start"):
                continue
            days = (date.fromisoformat(entry["end"]) - date.fromisoformat(entry["start"])).days
            if not 330 <= days <= 400:
                continue
        elif entry.get("start"):
            continue
        result.append(entry)
    return result


def choose_tag(taxonomy, tags, unit, kind):
    options = []
    for rank, tag in enumerate(tags):
        entries = annual_entries(taxonomy, tag, unit, kind)
        if entries:
            options.append((max(e["end"] for e in entries), -rank, tag, entries))
    return max(options, key=lambda x: x[:2])[2:] if options else (None, [])


def newest_filed(entries):
    return max(entries, key=lambda e: (e.get("filed", ""), e.get("accn", ""))) if entries else None


def extract_facts(raw, company):
    taxonomy = raw.get("facts", {}).get("us-gaap", {})
    _, kind, unit, tags = CONCEPTS["revenue"]
    revenue_tag, entries = choose_tag(taxonomy, tags, unit, kind)
    if not entries:
        raise DeskError("No supported annual US-GAAP total-revenue fact in USD. Review the filing manually.")
    end = max(e["end"] for e in entries)
    current = newest_filed([e for e in entries if e["end"] == end])
    start = current["start"]
    # fy identifies the filing's fiscal year, not necessarily the fact's period.
    # Use actual period dates, including 52/53-week years, for both columns.
    previous = newest_filed([e for tag in tags for e in annual_entries(taxonomy, tag, unit, kind)
                             if 0 < (date.fromisoformat(start) - date.fromisoformat(e["end"])).days <= 7])
    periods = {"current": {"start": start, "end": end},
               "prior": {"start": previous["start"], "end": previous["end"]} if previous else None}
    result = {"company": company, "periods": periods, "facts": {},
              "policy": "Annual 10-K/10-K/A facts, 330-400 days. Newest tag period first; latest filed comparative value. USD only. No missing value is zero."}
    for key, (label, kind, unit, tags) in CONCEPTS.items():
        tag, entries = choose_tag(taxonomy, tags, unit, kind)
        item = {"label": label, "tag": f"us-gaap:{tag}" if tag else None, "unit": unit}
        if tag and "CapitalLease" in tag:
            item["label"] += " (including finance/capital leases)"
        for column, period in periods.items():
            matches = [e for e in entries if period and e["end"] == period["end"]
                       and (kind == "instant" or e["start"] == period["start"])]
            entry = newest_filed(matches)
            item[column] = ({**entry, "tag": item["tag"], "unit": unit,
                             "filing_url": archive_base(company["cik"], entry["accn"]) + entry["accn"] + "-index.html"}
                            if entry else None)
        result["facts"][key] = item
    return result


def fmt(value):
    return f"{Decimal(str(value)):,.6f}".rstrip("0").rstrip(".")


def print_facts(report):
    print(f"  {report['company']['ticker']} | {report['company']['name']}")
    print(f"  Revenue fiscal period: {report['periods']['current']} | Prior: {report['periods']['prior']}")
    print("  Current year | Prior year (all values in the stated unit)")
    for item in report["facts"].values():
        columns = []
        for column in ("current", "prior"):
            entry = item[column]
            columns.append((f"{fmt(entry['val'])} {entry['unit']} [tag={entry['tag']}; end={entry['end']}; "
                            f"filing={entry['accn']}; filed={entry['filed']}]") if entry else "MISSING for this fiscal period")
        print(f"  {item['label']}: " + " | ".join(columns))


def calculate(report, price=None):
    def value(key, column="current"):
        entry = report["facts"][key][column]
        if entry is None:
            raise DeskError(f"missing {key} ({column})")
        return Decimal(str(entry["val"]))

    def divide(a, b):
        if b == 0:
            raise DeskError("denominator is zero")
        return a / b

    def growth():
        a, b = value("revenue"), value("revenue", "prior")
        return divide(a - b, b) * 100, f"({fmt(a)} - {fmt(b)}) / {fmt(b)} * 100", "%"

    def margin():
        a, b = value("operating_income"), value("revenue")
        return divide(a, b) * 100, f"{fmt(a)} / {fmt(b)} * 100", "%"

    def roe():
        n, e, p = value("net_income"), value("equity"), value("equity", "prior")
        return divide(n, (e + p) / 2) * 100, f"{fmt(n)} / (({fmt(e)} + {fmt(p)}) / 2) * 100", "%"

    def debt():
        tags = [report["facts"][key].get("tag") or "" for key in ("long_term_debt", "current_debt")]
        if ("CapitalLease" in tags[0]) != ("CapitalLease" in tags[1]):
            raise DeskError("current and noncurrent debt tags have different lease definitions")
        d, c, e = value("long_term_debt"), value("current_debt"), value("equity")
        return divide(d + c, e), f"({fmt(d)} + {fmt(c)}) / {fmt(e)}", "x"

    def fcf():
        c, p = value("cfo"), value("capex")
        return c - p, f"{fmt(c)} - {fmt(p)}", "USD"

    def pe():
        if price is None:
            raise DeskError("provide --price in USD per share")
        eps = value("diluted_eps")
        arithmetic = f"{fmt(price)} / {fmt(eps)}"
        if eps <= 0:
            raise DeskError(arithmetic + ": P/E is not meaningful when diluted EPS is zero or negative")
        return divide(price, eps), arithmetic, "x"

    results = {}
    for label, function in [("Revenue growth", growth), ("Operating margin", margin),
                            ("Return on average equity", roe), ("Debt to equity", debt),
                            ("Free cash flow", fcf), ("P/E (latest fiscal-year diluted EPS)", pe)]:
        try:
            result, arithmetic, unit = function()
            results[label] = {"value": str(result), "arithmetic": arithmetic, "unit": unit}
        except DeskError as exc:
            results[label] = {"value": None, "reason": str(exc)}
    results["Debt to equity"]["definition"] = (
        "Long-term debt including current portion and finance/capital lease obligations, divided by stockholders' equity."
        if "CapitalLease" in (report["facts"]["long_term_debt"].get("tag") or "") else
        "Long-term debt including current portion, excluding lease obligations, divided by stockholders' equity.")
    return results


def print_calculations(results):
    for label, result in results.items():
        if result["value"] is None:
            print(f"  {label}: N/A ({result['reason']})")
        else:
            print(f"  {label}: {result['arithmetic']} = {fmt(result['value'])} {result['unit']}")
        if result.get("definition"):
            print("    Definition: " + result["definition"])


def release_lines(text):
    """Return source lines, including table context; never invent extracted values."""
    lines = text.splitlines()
    result = {"total_revenue": [], "diluted_eps": []}
    quarter = re.compile(r"\bquarter(?:ly)?\b|three\s+months|\b1[2-7][ -]+weeks?\b|\bQ[1-4]\b", re.I)
    revenue = re.compile(r"\b(?:total\s+(?:net\s+)?(?:revenue[s]?|sales)|net\s+sales|revenue[s]?)\b", re.I)
    eps = re.compile(r"per\s+diluted\s+(?:common\s+)?share|diluted.{0,100}(?:earnings|EPS|per\s+(?:common\s+)?share)|(?:earnings|EPS|per\s+(?:common\s+)?share).{0,100}diluted", re.I)
    for i, line in enumerate(lines):
        # Header and row context supports statements laid out in financial tables.
        before = lines[max(0, i - 45):i]
        context = " ".join(before + [line])
        numeric = bool(re.search(r"\d", line))
        if not numeric or not quarter.search(context):
            continue
        labels = []
        table_revenue = re.match(r"^(?:total\s+)?(?:net\s+)?(?:revenues?|sales)\b[^|]*\|", line.lstrip(" |"), re.I)
        narrative_revenue = "|" not in line and revenue.search(line)
        if table_revenue or narrative_revenue:
            # Reject obvious segment/product revenue and forward-looking guidance.
            if not re.search(r"\b(?:segment|guidance|outlook|expects?|expected|forecast)\b", line, re.I):
                labels.append("total_revenue")
        nearby = " ".join(before[-5:])
        diluted_row = (re.match(r"^diluted\s*\|", line.lstrip(" |"), re.I)
                       and re.search(r"(?:earnings|income|loss).{0,40}per\s+(?:common\s+)?share", nearby, re.I)
                       and not re.search(r"shares\s+(?:used|outstanding)|weighted.average", nearby, re.I))
        if eps.search(line) or diluted_row:
            if not re.search(r"\b(?:guidance|outlook|expects?|expected|forecast|shares\s+outstanding|weighted.average)\b", line, re.I):
                labels.append("diluted_eps")
        for label in labels:
            context_indices = set(range(max(0, i - 4), i))
            # Include units, quarter/YTD headers and dates above financial rows.
            if "|" in line:
                for j in range(max(0, i - 45), i):
                    if re.search(r"three\s+months|quarters?\s+ended|\b1[2-7][ -]+weeks?\s+ended|in\s+(?:millions|thousands)", lines[j], re.I):
                        context_indices.add(j)
                        if j + 1 < i:
                            context_indices.add(j + 1)
            result[label].append({"line_number": i + 1, "line": line,
                                  "context": [{"line_number": j + 1, "line": lines[j]}
                                              for j in sorted(context_indices)]})
    # Net sales can exclude other revenue, such as membership fees. Prefer
    # explicit total revenue when the release supplies it.
    if any(re.search(r"\btotal\s+revenues?\b", m["line"], re.I) for m in result["total_revenue"]):
        result["total_revenue"] = [m for m in result["total_revenue"]
                                   if not re.search(r"\bnet\s+sales\b", m["line"], re.I)
                                   or re.search(r"\btotal\s+revenues?\b", m["line"], re.I)]
    return result


class Desk:
    def __init__(self, client, ticker, peers, price, step):
        self.client, self.ticker, self.peers, self.price = client, ticker, peers, price
        self.folder, self.state = None, {}
        if step and step != 1:
            for path in sorted(RUNS.glob("*/manifest.json"), reverse=True,
                               key=lambda p: p.parent.name.rsplit("__", 1)[-1]):
                data = json.loads(path.read_text(encoding="utf-8"))
                if data["company"]["ticker"] == ticker:
                    self.folder, self.state = path.parent, data
                    break
            if self.folder is None:
                raise DeskError(f"No saved run for {ticker}. Run --step 1 first.")

    def require(self, filename, step):
        path = self.folder / filename
        if not path.exists() or self.state["steps"].get(str(step), {}).get("status") != "complete":
            raise DeskError(f"Missing or stale {filename}. Complete --step {step} for {self.ticker} first.")
        return json.loads(path.read_text(encoding="utf-8"))

    def facts(self, company, folder):
        raw = self.client.json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{company['cik']}.json")
        save_json(folder / "companyfacts.json", raw)
        report = extract_facts(raw, company)
        save_json(folder / "facts.json", report)
        print_facts(report)
        return report

    def run_step(self, step):
        print(f"\nStep {step}/7: {STEPS[step]}", flush=True)
        if step != 1:
            # Keep old files for review, but do not read them as current results
            # after a prerequisite was rerun or failed.
            for dependent in {2: (3, 6), 3: (6,), 4: (5,)}.get(step, ()):
                if str(dependent) in self.state["steps"]:
                    self.state["steps"][str(dependent)]["status"] = "stale"
            self.state["steps"][str(step)] = {"status": "running"}
            save_json(self.folder / "manifest.json", self.state)
        if step == 1:
            company = resolve(self.client, self.ticker)
            stamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S-%f%z")
            name = re.sub(r"[^A-Za-z0-9_-]+", "_", company["name"]).strip("_")[:100]
            self.folder = RUNS / f"{name}__{stamp}"
            self.folder.mkdir(parents=True)
            self.state = {"company": company, "started_at": datetime.now().astimezone().isoformat(), "steps": {}}
            print(f"  {company['ticker']} -> CIK {company['cik']} | {company['name']}")
        elif step == 2:
            select_filings(self.client, self.state["company"], self.folder)
        elif step == 3:
            selected = self.require("selected_filings.json", 2)
            if not all(form in selected for form in ("10-K", "10-Q", "8-K")):
                raise DeskError("Selected filings are incomplete. Complete step 2 first.")
            download_documents(self.client, selected, self.folder)
        elif step == 4:
            self.facts(self.state["company"], self.folder)
        elif step == 5:
            report = self.require("facts.json", 4)
            results = calculate(report, self.price)
            print_calculations(results)
            save_json(self.folder / "calculations.json", {"price_usd": str(self.price) if self.price is not None else None,
                                                          "periods": report["periods"], "calculations": results})
        elif step == 6:
            docs = self.require("documents.json", 3)
            path = self.folder / docs["earnings_release"]["text_file"]
            result = release_lines(path.read_text(encoding="utf-8"))
            print("  Source: " + docs["earnings_release"]["url"])
            print("  Source matches retain GAAP/non-GAAP labels and comparative columns; check table headings.")
            for label, matches in result.items():
                print(f"  {label}:")
                if not matches:
                    print("    No confident quarterly line match. Review earnings_release.txt.")
                for match in matches:
                    for context in match["context"]:
                        print(f"    context L{context['line_number']}: {context['line']}")
                    print(f"    MATCH L{match['line_number']}: {match['line']}")
            save_json(self.folder / "release_lines.json", {"source": docs["earnings_release"], "matches": result})
        elif step == 7:
            peers = {}
            for ticker in self.peers:
                try:
                    company = resolve(self.client, ticker)
                    report = self.facts(company, self.folder / "peers" / ticker)
                    margin = calculate(report)["Operating margin"]
                    print_calculations({"Operating margin": margin})
                    peers[ticker] = {"facts": report, "operating_margin": margin}
                except DeskError as exc:
                    peers[ticker] = {"error": str(exc)}
                    print(f"  {ticker}: {exc}")
            save_json(self.folder / "peers.json", peers)
            if not self.peers:
                print("  No peers supplied. Use --peers TICKER TICKER.")
            if any("error" in peer for peer in peers.values()):
                raise DeskError("One or more peers failed; see peers.json.")
        self.state["steps"][str(step)] = {"status": "complete", "at": datetime.now().astimezone().isoformat()}
        save_json(self.folder / "manifest.json", self.state)


def positive_price(value):
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("Price must be a positive finite number.") from None
    if not number.is_finite() or number <= 0:
        raise argparse.ArgumentTypeError("Price must be a positive finite number.")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", type=normalize_ticker)
    parser.add_argument("--peers", nargs="*", default=[], help="Peer tickers, separated by spaces or commas")
    parser.add_argument("--price", type=positive_price, help="USD share price for fiscal-year P/E")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="Run only this step; use the latest saved run for this ticker")
    args = parser.parse_args(argv)
    try:
        peers = list(dict.fromkeys(normalize_ticker(t) for group in args.peers for t in group.split(",") if t))
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    try:
        desk = Desk(SECClient(), args.ticker, peers, args.price, args.step)
        failed = []
        for step in [args.step] if args.step else range(1, 8):
            try:
                desk.run_step(step)
            except (DeskError, OSError, ValueError) as exc:
                failed.append(step)
                print(f"  ERROR: {exc}", file=sys.stderr, flush=True)
                if desk.folder:
                    desk.state["steps"][str(step)] = {"status": "failed", "error": str(exc)}
                    save_json(desk.folder / "manifest.json", desk.state)
                if step == 1:
                    break
        if desk.folder:
            print(f"\nSaved run: {desk.folder}")
        if failed:
            print("Incomplete steps: " + ", ".join(map(str, failed)), file=sys.stderr)
        return 1 if failed else 0
    except (DeskError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
