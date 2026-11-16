"""Rate-limited SEC transport, form indexes, submissions and filing folders."""
from datetime import date
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dotenv import dotenv_values
from pypdf import PdfReader
import requests

from core import SeekerError, day, REGISTRATION_FORMS

SEC = "https://www.sec.gov"
US_STATES = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR VI GU AS MP".split())


class SECClient:
    def __init__(self, env_path, cache, *, session=None, sleep=time.sleep, clock=time.monotonic):
        ua = dotenv_values(env_path, interpolate=False).get("SEC_USER_AGENT")
        if not ua or not ua.strip() or any(c in ua for c in "\r\n"):
            raise SeekerError("Set SEC_USER_AGENT to your name and email in the project .env.")
        self.ua, self.cache = ua, Path(cache)
        self.session = session or requests.Session()
        self.sleep, self.clock, self.last = sleep, clock, None
        self.memory = {}

    def get(self, url, *, immutable=False, missing_ok=False):
        original = url
        if url in self.memory:
            return self.memory[url]
        path = self.cache / (sha256(url.encode()).hexdigest() + ".bin")
        if immutable and path.exists():
            data = path.read_bytes()
            self.memory[url] = data
            return data
        for attempt in range(5):
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in {"www.sec.gov", "data.sec.gov"}:
                raise SeekerError("Only HTTPS www.sec.gov and data.sec.gov requests are permitted.")
            if self.last is not None:
                self.sleep(max(0, .26 - (self.clock() - self.last)))
            self.last = self.clock()
            try:
                response = self.session.get(url, headers={"User-Agent": self.ua, "Accept-Encoding": "gzip, deflate"},
                                            timeout=(15, 60), allow_redirects=False)
            except requests.RequestException:
                if attempt == 4:
                    raise SeekerError(f"SEC connection failed: {original}") from None
                self.sleep(2 ** attempt)
                continue
            if response.status_code in {301, 302, 303, 307, 308}:
                url = urljoin(url, response.headers.get("Location", ""))
                continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 4:
                retry = response.headers.get("Retry-After", "")
                self.sleep(min(int(retry), 60) if retry.isdigit() else 2 ** attempt)
                continue
            if response.status_code == 404 and missing_ok:
                return None
            if response.status_code != 200:
                raise SeekerError(f"SEC HTTP {response.status_code}: {original}")
            self.memory[original] = response.content
            if immutable:
                self.cache.mkdir(parents=True, exist_ok=True)
                path.write_bytes(response.content)
            return response.content
        raise SeekerError(f"SEC retry/redirect limit: {original}")

    def json(self, url, **kwargs):
        data = self.get(url, **kwargs)
        if data is None:
            return None
        try:
            return json.loads(data)
        except (ValueError, UnicodeError):
            raise SeekerError(f"Invalid SEC JSON: {url}") from None


def parse_index(text, url):
    """Read SEC form.idx fixed-width columns without dropping malformed records."""
    rows = []
    for line in text.splitlines():
        match = re.match(r"^(\S+)\s+(.+?)\s+(\d{1,10})\s+(\d{4}-\d{2}-\d{2})\s+(edgar/data/\d+/\d{10}-\d{2}-\d{6}\.txt)\s*$", line)
        if not match:
            if "edgar/data/" in line:
                raise SeekerError(f"Unparsed filing row in EDGAR form index: {url}")
            continue
        form, name, cik, filed, path = match.groups()
        day(filed)
        rows.append({"form": form, "name": name.strip(), "cik": cik.zfill(10), "filed": filed,
                     "accession": path.rsplit("/", 1)[1][:-4], "index": url, "path": path})
    if not rows and "Form Type" not in text:
        raise SeekerError(f"Unrecognized EDGAR form index: {url}")
    return rows


def quarters(start, end):
    year, quarter = start.year, (start.month - 1) // 3 + 1
    while (year, quarter) <= (end.year, (end.month - 1) // 3 + 1):
        yield year, quarter
        year, quarter = (year + 1, 1) if quarter == 4 else (year, quarter + 1)


def discover(client, index_start, as_of):
    found, index_sources = {}, []
    for year, quarter in quarters(index_start, as_of):
        url = f"{SEC}/Archives/edgar/full-index/{year}/QTR{quarter}/form.idx"
        print(f"Reading form index {year} Q{quarter}", flush=True)
        raw = client.get(url)  # Indexes can be corrected; refresh for every invocation.
        rows = parse_index(raw.decode("utf-8", errors="replace"), url)
        in_range = [r for r in rows if index_start <= day(r["filed"]) <= as_of]
        index_sources.append({"url": url, "through": max((r["filed"] for r in in_range), default=None)})
        for row in in_range:
            if row["form"] in REGISTRATION_FORMS | {"CERT", "CERT/A", "8-K", "8-K/A"}:
                found[row["accession"]] = row
    # Supplement the quarter-to-date bridge with the newest published daily indexes.
    year, quarter = as_of.year, (as_of.month - 1) // 3 + 1
    directory = f"{SEC}/Archives/edgar/daily-index/{year}/QTR{quarter}/"
    listing = client.json(directory + "index.json")
    latest = max((s["through"] for s in index_sources if s["through"]), default=index_start.isoformat())
    for item in listing.get("directory", {}).get("item", []):
        match = re.fullmatch(r"form\.(\d{8})\.idx", item.get("name", ""))
        if not match:
            continue
        stamp = date(int(match[1][:4]), int(match[1][4:6]), int(match[1][6:]))
        if not (index_start <= stamp <= as_of) or stamp.isoformat() < latest:
            continue
        url = directory + item["name"]
        raw = client.get(url)
        rows = parse_index(raw.decode("utf-8", errors="replace"), url)
        index_sources.append({"url": url, "through": stamp.isoformat()})
        for row in rows:
            if day(row["filed"]) <= as_of and row["form"] in REGISTRATION_FORMS | {"CERT", "CERT/A", "8-K", "8-K/A"}:
                found[row["accession"]] = row
    return list(found.values()), index_sources


def column_rows(columns, cik):
    for i, accession in enumerate(columns.get("accessionNumber", [])):
        def get(key):
            return columns.get(key, [""] * (i + 1))[i]
        yield {"cik": cik, "form": get("form"), "filed": get("filingDate"),
               "accession": accession, "primary_document": get("primaryDocument")}


def submissions(client, cik, as_of):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = client.json(url)
    rows = list(column_rows(data.get("filings", {}).get("recent", {}), cik))
    for old in data.get("filings", {}).get("files", []):
        if old.get("filingFrom") and day(old["filingFrom"]) > as_of:
            continue
        name = old["name"]
        if not re.fullmatch(r"CIK\d{10}-submissions-\d+\.json", name):
            raise SeekerError("Unrecognized submissions-history filename.")
        historical = client.json("https://data.sec.gov/submissions/" + name)
        rows.extend(column_rows(historical, cik))
    result = {r["accession"]: r for r in rows if r["filed"] and day(r["filed"]) <= as_of}
    return data, sorted(result.values(), key=lambda r: (r["filed"], r["accession"]))


def base_url(filing):
    cik = filing["cik"]
    accession = filing["accession"]
    if not re.fullmatch(r"\d{10}", cik) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
        raise SeekerError("Malformed filing identifier.")
    return f"{SEC}/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"


def plain_text(content, url):
    if url.lower().endswith(".pdf"):
        try:
            return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages), []
        except Exception:
            raise SeekerError(f"Unreadable PDF: {url}") from None
    soup = BeautifulSoup(content, "html.parser")
    for node in soup.find_all(["script", "style", "ix:header"]):
        node.decompose()
    links = [{"text": a.get_text(" ", strip=True), "href": urljoin(url, a.get("href", ""))}
             for a in soup.find_all("a", href=True)]
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if cells:
            row.replace_with("\n" + " | ".join(c.get_text(" ", strip=True) for c in cells) + "\n")
    # Keep a paragraph together so line references retain the full sentence.
    for node in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "li"]):
        if not node.find(["p", "div", "table", "h1", "h2", "h3", "h4", "li"]):
            node.replace_with("\n" + node.get_text(" ", strip=True) + "\n")
    return "\n".join(" ".join(line.split()) for line in soup.get_text("\n").splitlines() if line.strip()), links


def read_filing(client, filing, evidence_folder):
    base = base_url(filing)
    index_url = base + filing["accession"] + "-index.html"
    raw = client.get(index_url, immutable=True)
    soup = BeautifulSoup(raw, "html.parser")
    documents = []
    for table in soup.find_all("table"):
        if "document" not in str(table.get("summary", "")).lower() and "Document" not in table.get_text():
            continue
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            link = cells[2].find("a", href=True)
            if not link:
                continue
            href = link["href"]
            if "?doc=" in href:
                href = href.split("?doc=", 1)[1]
            url = urljoin(base, href)
            # Documents must be from this filing folder, not external references.
            if not url.startswith(base) or not re.search(r"\.(?:htm|html|txt|pdf)$", url, re.I):
                continue
            doc_type = cells[3].get_text(" ", strip=True)
            if doc_type.startswith(("EX-101", "EX-104")) or doc_type == "GRAPHIC":
                continue
            documents.append((url, cells[1].get_text(" ", strip=True)))
    if not documents:
        raise SeekerError(f"No readable filing documents: {index_url}")
    result, issues = [], []
    for url, description in dict(documents).items():
        try:
            text, links = plain_text(client.get(url, immutable=True), url)
            if not text.strip():
                raise SeekerError(f"Document has no extractable text: {url}")
            evidence_folder.mkdir(parents=True, exist_ok=True)
            filename = filing["accession"] + "__" + sha256(url.encode()).hexdigest()[:16] + ".txt"
            path = evidence_folder / filename
            path.write_text(text + "\n", encoding="utf-8")
            result.append({"filing": index_url, "url": url, "filed": filing["filed"], "form": filing["form"],
                           "cik": filing["cik"], "text": text, "links": links, "description": description,
                           "text_file": str(path.resolve())})
        except SeekerError as exc:
            issues.append(str(exc))
    return result, issues


def domestic_status(metadata):
    state = metadata.get("stateOfIncorporation")
    if not state or state in {"XX", "X1", "X0"}:
        return None
    return state in US_STATES
