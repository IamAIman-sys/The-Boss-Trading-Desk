#!/usr/bin/env python3
"""Week 3 desk as a crewAI Flow: the four roles as a graph in code, with a Verifier.

Graph (fixed in code; a model never decides which node runs next):

    gather_filings -> research_analyst -> financial_analyst -> investment_advisor
                           ^                    ^                     ^       |
                           |  revise_research   |  revise_financial   |       v
                           +--------------------+---------------------+-- strategy_manager
                                                                              |
                                                 report_ready -> compile_report -> verifier

The data node runs SEC steps 1-7 from equity_desk.py with no model. Each role is
one crewAI Agent call on Purdue GenAI Studio, with its rules from roles/ and its
persona from personas/. Each returns structured claims; each claim carries a
quote and a citation. The Strategy Manager is plain Python (roles/strategy_manager.md):
it checks the five report parts and sends a failed part back to its owner one
time, with the problems. No role runs more than 2 times in one run. Then the
report is compiled, and the Verifier runs on it every time. No option turns
the Verifier off.
"""

import argparse
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation
import difflib
import json
import os
from pathlib import Path
import re
import sys
import shutil
import threading
from dataclasses import dataclass
from typing import Literal

import research_evidence as evidence

# Keep run data on this laptop: no crewAI telemetry or tracing.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from dotenv import dotenv_values  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from crewai import LLM, Agent  # noqa: E402
from crewai.flow import Flow, listen, or_, router, start  # noqa: E402

import equity_desk as data  # noqa: E402
import verifier  # noqa: E402
from research_desk import evidence_markdown, heading_excerpts, quarterly_facts, research_excerpts, source_lines  # noqa: E402

ROOT = Path(__file__).resolve().parent
PURDUE_URL = "https://genai.rcac.purdue.edu/api"
PERSONA_DIR = ROOT / "personas"
LIVE_DIR = ROOT / "runs" / "live"
EASTERN = ZoneInfo("America/New_York")
LIVE_WINDOW = timedelta(hours=24)  # project rule: within 24 hours of the 8-K's EDGAR "Accepted" time


def live_window(accepted, now=None):
    """The live window of one earnings 8-K. accepted: EDGAR index display time, Eastern ("YYYY-MM-DD HH:MM:SS")."""
    start = datetime.strptime(accepted, "%Y-%m-%d %H:%M:%S").replace(tzinfo=EASTERN)
    now = (now or datetime.now(EASTERN)).astimezone(EASTERN)
    end = start + LIVE_WINDOW
    return {"accepted_et": start.isoformat(), "window_ends_et": end.isoformat(), "checked_et": now.isoformat(),
            "open": start <= now <= end, "hours_left": round((end - now).total_seconds() / 3600, 2)}
PERSONA_PARTS = ("Identity", "How this role reads a company", "Inputs",
                 "Scored criteria", "What would change its view", "Output")
# Purdue's limit is 65,536 tokens for input and answer together. The answer gets
# 12,000 (6,000 was too few for a send-back answer), and about 1,500 are a margin.
# Purdue counted 3.5 and 3.75 characters per token on two NOC inputs; the
# estimate uses 3.5, so it is not lower than the true count on those inputs.
MAX_OUTPUT_TOKENS = 12000
MAX_INPUT_TOKENS = 52000
CHARS_PER_TOKEN = 3.5
MAX_ATTEMPTS = 2  # Week 3: no role runs more than twice.
# A send-back adds the first draft and its problems to the same message. The
# filing excerpts are made shorter, in steps, until the largest first message
# plus this reserve fits. Saved NOC drafts were about 600-1,400 tokens; the
# reserve allows for longer drafts from fuller personas.
SEND_BACK_RESERVE_TOKENS = 4000
EXCERPT_CHARS = 25000  # per selected filing Item, on complete lines
MIN_EXCERPT_CHARS = 12500
EXCERPT_STEP = 2500
SECTIONS = {"overview": "Overview",
            "market_positioning": "Market Positioning and Growth Outlook",
            "future_developments": "Future Developments and Strategic Recommendations"}

ROLES_DIR = ROOT / "roles"
SIGNAL_LINE_START = "Annual operating-margin change:"


def role_rules(name):
    """A role's instructions: its file in roles/, sent word for word, without the leading comment."""
    text = (ROLES_DIR / name).read_text(encoding="utf-8")
    return re.sub(r"\A\s*<!--.*?-->\s*", "", text, flags=re.S)


def manager_parts():
    """The five required parts, read from the Strategy Manager's file."""
    text = (ROLES_DIR / "strategy_manager.md").read_text(encoding="utf-8")
    block = text.split("## Required parts", 1)[1].split("\n## ", 1)[0]
    return tuple(line[2:].strip() for line in block.splitlines() if line.startswith("- "))


RESEARCH_RULES = role_rules("research_analyst.md")
FINANCIAL_RULES = role_rules("financial_analyst.md")
ADVISOR_RULES = role_rules("investment_advisor.md")
if SIGNAL_LINE_START not in FINANCIAL_RULES:
    raise RuntimeError("roles/financial_analyst.md must name the review-signal line: " + SIGNAL_LINE_START)
PARTS = manager_parts()
if len(PARTS) != 5:
    raise RuntimeError("roles/strategy_manager.md must list the five required parts")


class Claim(BaseModel):
    claim: str = Field(description="The point in plain words; numbers only if they are in the quote")
    quote: str = Field(description="Words copied exactly from one evidence line, under 20 words")
    citation: str = Field(description="That line's tag without brackets, e.g. 10-K L128")


class ResearchSections(BaseModel):
    overview: list[Claim] = Field(min_length=1, description="Business model and recent developments")
    market_positioning: list[Claim] = Field(min_length=1, description="Competitive position and growth outlook")
    future_developments: list[Claim] = Field(min_length=1, description="Catalysts, risks and strategic outlook")
    insight: str = Field(description="One sentence that the release's first paragraph does not state, with at least one number copied from an insight_evidence line")
    insight_evidence: list[Claim] = Field(min_length=1, max_length=3, description="Claims that support the insight")


FINANCIAL_SECTIONS = {"operating_margin": "Operating Margin",
                      "profitability_and_cash": "Profitability and Cash Flow",
                      "debt_and_coverage": "Debt and Interest Coverage",
                      "peer_comparison": "Peer Comparison",
                      "review_flags": "Review Flags"}


class FinancialSections(BaseModel):
    operating_margin: list[Claim] = Field(min_length=1, description="Margin in both years, the change and its stated cause")
    profitability_and_cash: list[Claim] = Field(min_length=1, description="Net margin, operating cash flow and its margin, ROE")
    debt_and_coverage: list[Claim] = Field(min_length=1, description="Debt, debt to equity and interest coverage")
    peer_comparison: list[Claim] = Field(default_factory=list, description="Compatible peer metrics; empty only if no peers are supplied")
    review_flags: list[Claim] = Field(min_length=1, description="Weak or contradictory evidence; always includes the review-signal line")
    insight: str = Field(description="One sentence that the release's first paragraph does not state, with at least one number copied from an insight_evidence line")
    insight_evidence: list[Claim] = Field(min_length=1, max_length=3, description="Claims that support the insight")


class AdvisorOutput(BaseModel):
    recommendation: Literal["Buy", "Hold", "Sell"]
    thesis: str = Field(description="2 to 4 sentences in words; the only number is the deciding number")
    deciding_number: Claim = Field(description="One analyst claim, copied: the number that decides it")
    support: list[Claim] = Field(min_length=1, max_length=4, description="Analyst claims that support the thesis")
    risks: list[Claim] = Field(min_length=1, max_length=3, description="Analyst claims that could make it wrong")
    what_would_change: str = Field(description="One sentence: the one thing in the next filing that would change it")
    insight: str = Field(description="One sentence that connects the two analysts, with at least one number "
                                     "copied from an insight_evidence line")
    insight_evidence: list[Claim] = Field(min_length=1, max_length=3, description="Analyst claims that support the insight")


ADVISOR_SECTIONS = {"support": "Support", "risks": "Risks"}


@dataclass(frozen=True)
class Role:
    key: str  # the DeskState field that holds this role's run
    title: str
    persona_file: str
    rules: str
    schema: type
    sections: dict
    goal: str
    backstory: str


RESEARCH = Role("research", "Research Analyst", "research_analyst.md", RESEARCH_RULES, ResearchSections, SECTIONS,
                "Write qualitative research claims that each carry an exact quote and citation from the evidence supplied",
                "A careful equity research analyst who cites every claim.")
FINANCIAL = Role("financial", "Financial Analyst", "financial_analyst.md", FINANCIAL_RULES, FinancialSections,
                 FINANCIAL_SECTIONS,
                 "Write financial-analysis claims on margins, cash flow, returns, debt and peers, each with an exact quote and citation",
                 "A skeptical financial analyst who checks every ratio against its source.")
ADVISOR = Role("advisor", "Investment Advisor", "investment_advisor.md", ADVISOR_RULES, AdvisorOutput,
                ADVISOR_SECTIONS,
                "Combine the two analysts' claims into one thesis and a Buy, Hold or Sell recommendation",
                "An investment advisor who adds no facts of their own.")
ROLES = (RESEARCH, FINANCIAL)  # the analysts read the filings; the context is sized for them
ALL_ROLES = (RESEARCH, FINANCIAL, ADVISOR)
OWNER = {PARTS[0]: RESEARCH, PARTS[1]: RESEARCH, PARTS[2]: FINANCIAL, PARTS[3]: RESEARCH, PARTS[4]: ADVISOR}


def tidy_citation(text):
    """Accept "[10-K L128]" or "10-K L128"; keep the label's words unchanged."""
    return re.sub(r"\s+", " ", clean_format(text).strip().strip("[]").strip())


def render_claim(claim):
    """One sentence: the claim, then its quote and citation in brackets, then the full stop.

    The claim's own final full stop is moved to the end, so a sentence splitter
    (the Verifier's) keeps the claim and its citation together."""
    text = claim["claim"].strip().rstrip(".")
    return f'{text} ("{claim["quote"].strip()}" [{tidy_citation(claim["citation"])}]).'


def render_sections(output, titles=SECTIONS):
    """Text that the check reads and the report shows: one claim per bullet."""
    sections = {title: "\n".join("- " + render_claim(c) for c in output.get(key, []))
                for key, title in titles.items()}
    # The sentence itself is checked by check_insight, against these evidence lines.
    sections["Insight"] = "\n".join("- " + render_claim(c) for c in output.get("insight_evidence", []))
    return sections


def role_sections(role, output):
    """The sections a role's check reads and its report shows."""
    sections = render_sections(output, role.sections)
    if role is ADVISOR:
        deciding = output.get("deciding_number")
        sections = {"Deciding number": "- " + render_claim(deciding) if deciding else "", **sections}
    return sections


def claims_of(output):
    """Every claim in a role's output, as dicts."""
    found = []
    for value in output.values():
        if isinstance(value, dict) and "quote" in value:
            found.append(value)
        elif isinstance(value, list):
            found += [c for c in value if isinstance(c, dict) and "quote" in c]
    return found


class RoleRun(BaseModel):
    persona: str = ""
    output: dict = {}
    check: dict = {}
    attempts: int = 0
    history: list[dict] = []  # every attempt: output and check
    revision_error: str = ""  # a failed send-back keeps the first draft
    call_error: str = ""  # a failed first call: the Strategy Manager sends it back once
    repairs: list[dict] = []  # near-miss quotes replaced by the cited line's exact words, in code


class DeskState(BaseModel):
    ticker: str = ""
    reuse: bool = False
    peers: list[str] | None = None
    supplements_manifest: str | None = None
    requested_run_folder: str | None = None
    run_folder: str = ""
    output_folder: str = ""
    company: dict = {}
    research_context: dict = {}
    research: RoleRun = Field(default_factory=RoleRun)
    financial: RoleRun = Field(default_factory=RoleRun)
    advisor: RoleRun = Field(default_factory=RoleRun)
    price: str | None = None
    price_date: str | None = None
    price_source: str | None = None
    price_note: dict = {}
    manager: list[dict] = []  # every Strategy Manager review: checks and the next node
    model: str = ""
    report_path: str = ""
    verified_folder: str = ""
    verified_summary: str = ""
    live: bool = False
    live_record: dict = {}  # the 8-K accession, its Accepted time, the window, and whether the report was inside it


# One role attempt may not run longer than this. The LLM timeout (180 s) applies to each HTTP
# try, but crewAI retries the call and the agent loop, so on Nov 17, 2026 one attempt waited
# 22 minutes. After the deadline the attempt counts as failed, and the Strategy Manager sends
# it back once, as for any failed call.
ROLE_CALL_SECONDS = 600


def call_with_deadline(function, seconds):
    """function() run in a daemon thread; TimeoutError if it does not finish in time.

    A daemon thread cannot be stopped, but it does not keep the program running at exit."""
    box = {}

    def target():
        try:
            box["result"] = function()
        except BaseException as exc:  # noqa: BLE001 - passed back to the caller
            box["error"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        raise TimeoutError(f"the model call did not finish in {seconds} seconds")
    if "error" in box:
        raise box["error"]
    return box["result"]


def make_llm():
    """crewAI LLM pointed at Purdue GenAI Studio, using the same .env as research_desk.py."""
    settings = dotenv_values(ROOT / ".env", interpolate=False)
    key = settings.get("API_KEY")
    if not key or key == "paste-here":
        raise data.DeskError("Set your Purdue GenAI Studio API_KEY in .env.")
    base_url = (settings.get("API_BASE_URL") or PURDUE_URL).rstrip("/")
    if base_url != PURDUE_URL:
        raise data.DeskError("flow_desk.py expects Purdue's API_BASE_URL: " + PURDUE_URL)
    model = settings.get("MODEL") or "gpt-oss:120b"
    return LLM(model="openai/" + model, base_url=base_url, api_key=key, temperature=0,
               max_tokens=MAX_OUTPUT_TOKENS, timeout=180, max_retries=2,
               default_headers={"User-Agent": settings.get("SEC_USER_AGENT") or "ResearchDesk"})


def load_persona(path):
    """Return the persona text, or "" when all six parts are empty."""
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S) if path.exists() else ""
    parts, current = {}, None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading[1]
            parts[current] = []
        elif current:
            parts[current].append(line)
    filled = {name: "\n".join(parts.get(name, [])).strip() for name in PERSONA_PARTS}
    if not any(filled.values()):
        return ""
    missing = [name for name, body in filled.items() if not body]
    if missing:
        raise data.DeskError(f"{path.name}: fill all six persona parts or none. Empty: {', '.join(missing)}")
    return "\n\n".join(f"{name}:\n{body}" for name, body in filled.items())


def find_run(ticker, peers=None):
    """Select the latest complete data run with matching explicitly requested peers."""
    for path in sorted(data.RUNS.glob("*/manifest.json"), reverse=True,
                       key=lambda p: p.parent.name.rsplit("__", 1)[-1]):
        manifest = evidence.read_json(path)
        if manifest["company"]["ticker"] != ticker:
            continue
        if not all(manifest["steps"].get(str(n), {}).get("status") == "complete" for n in range(1, 8)):
            continue
        if peers is not None and set(evidence.read_json(path.parent / "peers.json")) != set(peers):
            continue
        return path.parent
    raise data.DeskError(f"No complete saved data run for {ticker} with the requested peers. Run without --reuse.")


def build_research_context(folder, peers=None, supplements_manifest=None, excerpt_chars=EXCERPT_CHARS):
    folder = Path(folder)
    manifest = evidence.read_json(folder / "manifest.json")
    selected = evidence.read_json(folder / "selected_filings.json")
    documents = evidence.read_json(folder / "documents.json")
    for n in range(1, 8):
        if manifest["steps"].get(str(n), {}).get("status") != "complete":
            raise data.DeskError(f"Incomplete or stale data step {n}; refresh the data desk.")
    exhibit = documents["earnings_release"].get("exhibit_label", "Exhibit 99.1")
    release = (folder / "earnings_release.txt").read_text(encoding="utf-8")
    filings = {form: {k: row[k] for k in ("accessionNumber", "accepted", "index_url", "document_url")}
               for form, row in selected.items()}
    financial, paths = evidence.financial_packet(folder, manifest, selected, peers)
    supplements, supplement_lines = evidence.supplements(supplements_manifest)
    availability = {"management_presentations": "supplied" if supplements else "not supplied; do not claim to have reviewed a presentation"}
    sections = {}
    # Purdue's gpt-oss:120b accepts 65,536 tokens. 10-K Item 8 and 10-Q Item 1 (the
    # statements) are not sent: Python evidence lines carry those numbers with tags
    # and accessions. Full texts stay in the source snapshot for human audit.
    availability["10-K_financials"] = availability["10-Q_financials"] = (
        "not sent (input size limit); statement numbers are in Python evidence lines with filing tags")
    for name, filename, items, label in (
            ("10-K_excerpts", "10-K.txt", ("1", "7"), "10-K"),
            ("10-Q_excerpts", "10-Q.txt", ("2",), "10-Q")):
        if not (folder / filename).exists():
            sections[name] = []; availability[name] = "not supplied"
            continue
        try:
            sections[name] = research_excerpts((folder / filename).read_text(encoding="utf-8"), items=items, label=label,
                                               max_chars=excerpt_chars)
            availability[name] = "supplied excerpts; full text retained in source snapshot"
        except data.DeskError as exc:
            sections[name] = []; availability[name] = str(exc)
            if label == "10-K":
                try:  # a 10-K in cross-reference format: find the sections by their headings
                    sections[name], note = heading_excerpts((folder / filename).read_text(encoding="utf-8"),
                                                            label=label, max_chars=excerpt_chars)
                    availability[name] = "supplied excerpts by heading fallback: " + note
                except data.DeskError as fallback:
                    availability[name] = f"{exc} Heading fallback: {fallback}"
    if not sections["10-K_excerpts"]:
        raise data.DeskError("Required 10-K Business/MD&A excerpts could not be located.")
    release_rows = source_lines(release, exhibit)
    calculated_lines = evidence.metric_lines(financial)
    all_lines = [r for group in sections.values() for r in group] + release_rows + calculated_lines + supplement_lines
    all_lines = list({(r["source"], r["line"]): r for r in all_lines}.values())
    paths += ["manifest.json", "selected_filings.json", "documents.json", "10-K.txt", "earnings_release.txt"]
    if (folder / "10-Q.txt").exists():
        paths.append("10-Q.txt")
    return {"company": manifest["company"], "filings": filings,
            "citation_labels": sorted({r["source"] for r in all_lines}),
            "excerpt_policy": f"At most {excerpt_chars:,} characters per selected filing Item, on complete lines. Excerpts can omit later notes; never claim a full-document review.",
            **sections, "release": release_rows, "evidence_lines": all_lines,
            "financial_evidence": financial, "management_supplements": supplements,
            "availability": availability,
            "source_snapshot": [{"path": name, "sha256": evidence.digest(folder / name)} for name in dict.fromkeys(paths)]}


def model_context(context):
    """Send one copy of each source line, with compact metric references."""
    financial = context["financial_evidence"]
    def summary(bundle):
        return {column: {name: {"value": evidence.display(metric["value"], metric["unit"]), "unit": metric["unit"],
                                "citation": metric.get("citation"), **({"reason": metric["reason"]} if metric.get("reason") else {})}
                         for name, metric in metrics.items()}
                for column, metrics in bundle.get("metrics", {}).items()}
    signals = {**financial["signals"], "operating_margin_change_pp":
               evidence.display(financial["signals"]["operating_margin_change_pp"], "pp")}
    return {"company": context["company"], "filings": context["filings"],
            "citation_labels": context["citation_labels"], "excerpt_policy": context["excerpt_policy"],
            "availability": context["availability"],
            # Plain strings that start with the exact citation tag: smaller than JSON objects.
            "evidence_lines": [f"[{r['source']} L{r['line']}] {r['text']}" for r in context["evidence_lines"]
                               if r["text"].strip()],
            "financial_summary": summary(financial), "review_signals": signals,
            "peer_policy": financial["peer_policy"],
            "peers": {ticker: {"metrics": summary(peer), "periods_match_company": peer.get("periods_match_company"),
                                "missing": peer.get("missing")} for ticker, peer in financial["peers"].items()},
            "management_sources": [{k: v for k, v in source.items() if k != "text"}
                                   for source in context["management_supplements"]]}


def fit_context(folder, peers, supplements_manifest, personas):
    """Build the context with the longest excerpts that leave room for one send-back.

    personas: role key -> persona text. If even the shortest excerpts do not fit,
    the context is returned and check_size stops the run before a model call."""
    chars = EXCERPT_CHARS
    while True:
        context = build_research_context(folder, peers, supplements_manifest, chars)
        largest = max(estimated_tokens(build_message(context, personas.get(role.key, ""), rules=role.rules))
                      for role in ROLES)
        if largest + SEND_BACK_RESERVE_TOKENS <= MAX_INPUT_TOKENS or chars <= MIN_EXCERPT_CHARS:
            if chars < EXCERPT_CHARS:
                context["availability"]["excerpt_size"] = (
                    f"excerpts shortened from {EXCERPT_CHARS:,} to {chars:,} characters per Item so that one "
                    f"send-back fits the {MAX_INPUT_TOKENS:,}-token input limit; later lines are not sent")
            return context
        chars -= EXCERPT_STEP


def compact(value):
    return json.dumps(value, separators=(",", ":"))


def revision_text(previous, problems):
    if previous is None:
        return ""
    return ("\n\nSEND-BACK: the Strategy Manager's Python check rejected parts of your draft below. "
            "Return the full answer again. Keep the claims that passed. For each problem, "
            "copy the quote exactly from the cited line, choose the line that really holds "
            "the quote, or remove the claim. Problems:\n- " + "\n- ".join(problems or [])
            + "\n\nYour draft:\n" + compact(previous))


def build_message(context, persona, previous=None, problems=None, rules=RESEARCH_RULES):
    """The same rules and context every time; a send-back adds the draft and its problems."""
    return (rules + ("\nPersona (the rules above win):\n" + persona if persona else "")
            + revision_text(previous, problems) + "\n\nContext JSON:\n" + compact(model_context(context)))


def build_advisor_message(research, financial, persona, price_note, previous=None, problems=None):
    """The Investment Advisor sees only the two analysts' outputs and the price note."""
    context = {"research_analyst": research, "financial_analyst": financial, "price": price_note}
    return (ADVISOR_RULES + ("\nPersona (the rules above win):\n" + persona if persona else "")
            + revision_text(previous, problems) + "\n\nContext JSON:\n" + compact(context))


def estimated_tokens(message):
    return int(len(message) / CHARS_PER_TOKEN)


def check_size(message):
    tokens = estimated_tokens(message)
    if tokens > MAX_INPUT_TOKENS:
        raise data.DeskError(f"Model input is about {tokens:,} tokens; the limit is {MAX_INPUT_TOKENS:,}. "
                             "Reduce excerpts or peers. No model call was made.")
    return tokens


def save_context(folder, out, context):
    out.mkdir(parents=True, exist_ok=True)
    for source in context["source_snapshot"]:
        path = Path(folder) / source["path"]
        if evidence.digest(path) != source["sha256"]:
            raise data.DeskError("An input changed during the run: " + source["path"])
        target = out / "evidence" / source["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    # One context for both analysts; the file name is kept for older runs.
    data.save_json(out / "research_context.json", context)
    data.save_json(out / "research_model_input.json", model_context(context))
    data.save_json(out / "financial_evidence.json", context["financial_evidence"])
    data.save_json(out / "management_supplements.json", context["management_supplements"])


CITATION = re.compile(r"\[([^\[\]]+?) L(\d+)(?:\s*-\s*L?(\d+))?\]")
QUOTE = re.compile(r"[\"“]([^\"“”]{3,}?)[\"”]")
NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?%?")
MAX_RANGE = 5
# A year names a period; it is not a claimed amount (the Verifier skips years the same way).
# "2026", "FY2026" and "2025-2026" are skipped; "2,026", "$2026", "2026%" and "2026 million" are not.
YEAR = re.compile(r"(?:\bFY\s?)?(?<![\w$.,])(?:19|20)\d{2}(?![\d%]|[.,]\d|\s(?:million|billion|thousand)\b)")


def claimed_numbers(text):
    """The numbers a claim states: every number except years."""
    return NUMBER.findall(YEAR.sub(" ", text))
# Formatting characters only. Words, numbers and labels are never changed.
FORMAT_CHARS = str.maketrans({"【": "[", "】": "]", "‐": "-", "‑": "-", "‒": "-",
                              "–": "-", " ": " ", " ": " ", " ": " ", " ": " "})


def clean_format(text):
    return text.translate(FORMAT_CHARS)


def _norm(text):
    return re.sub(r"\s+", " ", text.replace("’", "'").replace("—", "-").replace("–", "-")).strip().lower()


def _digits(token):
    """Compare numbers by value, so 0.10 and 0.1 match. Text is never rewritten."""
    plain = token.replace("$", "").replace(",", "").rstrip("%")
    try:
        return str(Decimal(plain).normalize())
    except InvalidOperation:
        return plain


# A number written with "million" or "billion" may restate a line's number at another scale,
# for example "$196.7 billion" for "$ 196,721" in a table in millions. The check accepts it
# by the Verifier's own rule (verifier.on_lines: unit scaling, then rounding to the digits shown),
# so the check and the Verifier agree. A number without a scale word must match exactly.
SCALED = re.compile(r"(?<![\w.])\$?\s?(?P<num>\d[\d,]*(?:\.\d+)?)\s(?P<scale>million|billion)\b", re.I)


def scaled_numbers(text):
    """{number's value: scale word} for each number in text written with "million" or "billion"."""
    return {_digits(m["num"]): m["scale"].lower() for m in SCALED.finditer(text)}


def rescaled_on(token, scales, texts):
    """True when token has a scale word in scales and equals a number on texts after scaling and rounding."""
    scale = scales.get(_digits(token))
    if not scale or token.endswith("%"):
        return False
    plain = token.replace("$", "").replace(",", "")
    return verifier.on_lines(verifier.dec(plain), verifier.places(plain), verifier.SCALES[scale], texts)


def quote_on_line(quote, target):
    """Exact match; a quote shortened with ... or … matches when each part is on the line, in order."""
    parts = [_norm(p) for p in re.split(r"\.\.\.|…", quote) if _norm(p)]
    position = 0
    for part in parts:
        found = target.find(part, position)
        if found < 0:
            return False
        position = found + len(part)
    return bool(parts)


def line_map(context):
    """(source, line number) -> text, for every line the model was sent."""
    source_rows = context.get("evidence_lines")
    if source_rows is None:
        source_rows = [row for key in ("10-K_excerpts", "release") for row in context[key]]
    return {(row["source"], row["line"]): row["text"] for row in source_rows}


def check_research(sections, context):
    """Mark each citation, quote and number in the Research Analyst's text against its sources."""
    lines = line_map(context)
    all_numbers = {_digits(t) for text in lines.values() for t in NUMBER.findall(text)}
    marks, problems = [], []
    for name, text in sections.items():
        cites = list(CITATION.finditer(text))
        if not cites:
            problems.append(f"{name}: no citations")
        for bullet in text.splitlines():
            if bullet.startswith("- ") and not CITATION.search(bullet):
                problems.append(f"{name}: a claim has no line citation ({bullet[2:62].strip()}...)")
        previous_end = 0
        for cite in cites:
            # A quote belongs to the citation on its own bullet line, never to the next one.
            previous_end = max(previous_end, text.rfind("\n", 0, cite.start()) + 1)
            source, first = cite[1].strip(), int(cite[2])
            last = int(cite[3]) if cite[3] else first
            span = range(first, last + 1)
            row = {"section": name, "citation": cite[0]}
            if not 0 <= last - first < MAX_RANGE:
                row["result"] = f"line range longer than {MAX_RANGE} lines"
            elif any((source, n) not in lines for n in span):
                row["result"] = "unknown source line"
            else:
                quotes = QUOTE.findall(text[previous_end:cite.start()])
                target = _norm(" ".join(lines[(source, n)] for n in span))
                missing = [q for q in quotes if not quote_on_line(q, target)]
                if not quotes:
                    row["result"] = "no quote before citation"
                elif missing:
                    row["result"] = "quote not on cited line"
                    row["quote"] = missing[0]
                else:
                    local_numbers = {_digits(t) for t in NUMBER.findall(target)}
                    segment = text[previous_end:cite.start()]
                    scales = scaled_numbers(segment)
                    unmatched = [t for t in claimed_numbers(segment)
                                 if _digits(t) not in local_numbers and not rescaled_on(t, scales, [target])]
                    row["result"] = "number not on cited line" if unmatched else "ok"
            previous_end = cite.end()
            marks.append(row)
            if row["result"] != "ok":
                problems.append(f"{name}: {cite[0]} {row['result']}")
        if claimed_numbers(text[previous_end:]):
            problems.append(f"{name}: uncited number after the final citation")
        prose = CITATION.sub(" ", text)
        prose_scales = scaled_numbers(prose)
        for token in claimed_numbers(prose):
            if _digits(token) not in all_numbers and not rescaled_on(token, prose_scales, lines.values()):
                problems.append(f"{name}: number {token} not found in any source line sent")
    return {"status": "pass" if not problems else "fail",
            "citations": len(marks), "citations_ok": sum(m["result"] == "ok" for m in marks),
            "marks": marks, "problems": problems}


def check_insight(output, context):
    """Week 3: the Insight line states a number, and the Verifier checks it at its line.

    Each number in the sentence must be on a line that an insight_evidence claim
    cites. The tag of the line that holds the first number goes beside the
    sentence in the report. A tag written in the sentence itself is ignored."""
    sentence = (output.get("insight") or "").strip()
    if not sentence:
        return {"problems": ["Insight: the sentence is missing"], "insight_citation": None}
    lines, cited = line_map(context), []
    for claim in output.get("insight_evidence", []):
        tag = tidy_citation(claim.get("citation", ""))
        match = CITATION.fullmatch(f"[{tag}]")
        if not match:
            continue
        first = int(match[2]); last = int(match[3]) if match[3] else first
        span = [(match[1].strip(), n) for n in range(first, last + 1)]
        if 0 <= last - first < MAX_RANGE and all(key in lines for key in span):
            text = " ".join(lines[key] for key in span)
            cited.append((tag, {_digits(t) for t in NUMBER.findall(text)}, text))
    numbers = claimed_numbers(CITATION.sub(" ", sentence))
    scales = scaled_numbers(sentence)
    problems, tags = [], []
    if not numbers:
        problems.append("Insight: the sentence states no number; copy one from a line that an insight_evidence claim cites")
    for token in numbers:
        tag = next((tag for tag, values, _ in cited if _digits(token) in values), None)
        if tag is None:  # a rescaled number, by the Verifier's rule
            tag = next((tag for tag, _, text in cited if rescaled_on(token, scales, [text])), None)
        if tag is None:
            problems.append(f"Insight: number {token} is not on any line that an insight_evidence claim cites")
        elif tag not in tags:
            tags.append(tag)
    # insight_citation: the first line, kept for older runs; insight_citations: one per line that holds a number.
    return {"problems": problems, "insight_citation": tags[0] if tags else None, "insight_citations": tags}


def with_insight(result, output, context):
    insight = check_insight(output, context)
    problems = result["problems"] + insight["problems"]
    return {**result, "status": "pass" if not problems else "fail", "problems": problems,
            "insight_citation": insight["insight_citation"], "insight_citations": insight["insight_citations"]}


def signal_line(context):
    """Citation tag of the Python review-signal line, or None if it was not sent."""
    for row in context.get("evidence_lines", []):
        if row["source"] == "Python evidence" and row["text"].startswith(SIGNAL_LINE_START):
            return f"Python evidence L{row['line']}"
    return None


def check_financial(output, context):
    """The citation/quote/number check, plus two Financial Analyst rules that Python can test."""
    sections = render_sections(output, FINANCIAL_SECTIONS)
    peers_supplied = bool(context.get("financial_evidence", {}).get("peers"))
    if not output.get("peer_comparison") and not peers_supplied:
        del sections[FINANCIAL_SECTIONS["peer_comparison"]]  # nothing to compare; not a missing citation
    result = check_research(sections, context)
    problems = list(result["problems"])
    if peers_supplied and not output.get("peer_comparison"):
        problems.append("Peer Comparison: empty, but peer evidence was supplied")
    tag = signal_line(context)
    if tag and not any(tidy_citation(c["citation"]) == tag for c in output.get("review_flags", [])):
        problems.append(f"Review Flags: no flag quotes the review-signal line [{tag}]")
    return with_insight({**result, "problems": problems}, output, context)


def cited_keys(tag):
    """(source, line) keys of one citation tag, or [] when the tag is not a line citation."""
    match = CITATION.fullmatch(f"[{tidy_citation(tag)}]")
    if not match:
        return []
    first = int(match[2]); last = int(match[3]) if match[3] else first
    return [(match[1].strip(), n) for n in range(first, last + 1)] if 0 <= last - first < MAX_RANGE else []


def advisor_scope(upstream, context):
    """The citations the analysts used, and a context holding only those lines."""
    allowed = {tidy_citation(c["citation"]) for out in upstream for c in claims_of(out)}
    keys = {key for tag in allowed for key in cited_keys(tag)}
    restricted = {"evidence_lines": [{"source": source, "line": n, "text": text}
                                     for (source, n), text in line_map(context).items() if (source, n) in keys]}
    return allowed, restricted


# Change 1: a near-miss quote is replaced by the cited line's exact words, in code.
REPAIR_MIN_SIMILARITY = 0.9


def repair_quote(quote, text):
    """The cited line's exact words for a near-miss quote, or None.

    Used only when the quote is not on its line. The repair keeps every number
    the same, and the result must be at least REPAIR_MIN_SIMILARITY alike, so a
    changed number or a different statement is never "repaired"."""
    if not quote.strip():
        return None
    parts = [part.strip() for part in re.split(r"\.\.\.|\u2026", quote)]
    if len(parts) > 1:
        # Each part between "..." is repaired on its own; every part must pass, in order.
        fixed, scores = [], []
        for part in parts:
            if not part:
                fixed.append("")
            elif quote_on_line(part, _norm(text)):
                fixed.append(part); scores.append(1.0)
            else:
                result = repair_quote(part, text)
                if not result:
                    return None
                fixed.append(result[0]); scores.append(result[1])
        candidate = " ... ".join(fixed).strip()
        return (candidate, min(scores)) if scores and quote_on_line(candidate, _norm(text)) else None
    q, t = quote.strip().lower(), text.lower()
    match = difflib.SequenceMatcher(None, q, t, autojunk=False).find_longest_match(0, len(q), 0, len(t))
    if match.size < len(q) / 2:
        return None
    best, base = None, max(0, match.b - match.a)  # the quote may have extra words before the line's start
    for start in range(max(0, base - 8), max(1, min(len(t), base + 9))):
        for length in range(max(1, len(q) - 12), len(q) + 13):
            ratio = difflib.SequenceMatcher(None, q, t[start:start + length], autojunk=False).ratio()
            if best is None or ratio > best[0]:
                best = (ratio, start, start + length)
    if best is None:
        return None
    _, start, end = best
    while start > 0 and not t[start - 1].isspace():  # whole words only
        start -= 1
    while end < len(t) and not t[end].isspace():
        end += 1
    candidate = text[start:end].strip().lstrip("\u2022").strip()
    similarity = difflib.SequenceMatcher(None, q, candidate.lower(), autojunk=False).ratio()
    same_numbers = sorted(_digits(n) for n in NUMBER.findall(quote)) == sorted(_digits(n) for n in NUMBER.findall(candidate))
    if similarity < REPAIR_MIN_SIMILARITY or not same_numbers or not quote_on_line(candidate, _norm(text)):
        return None
    return candidate, round(similarity, 3)


# Citation repair: the quote is exact, but the tag points to the wrong line. Seen in runs:
# a sentence that wraps onto the next line, a heading cited in place of the line below it,
# and the wrong Python evidence line. Only an exact quote (quote_on_line) moves a citation.
CITATION_REACH = (2, 5)  # lines before and after the cited line(s) that are searched
CITATION_MAX_SPAN = 3  # a repaired citation covers at most 3 lines
GLOBAL_MIN_WORDS = 5  # a quote with fewer words is not searched outside the nearby lines


def span_tag(source, first, last):
    return f"{source} L{first}" if first == last else f"{source} L{first}-L{last}"


def repair_citation(quote, tag, lines):
    """The tag of the nearest line(s) that hold the exact quote, or None.

    First the lines near the cited line, as the shortest span; then, if the quote
    is long enough, the one line of the same source that holds it (only when one
    line does)."""
    keys = cited_keys(tag)
    if not keys or not quote.strip():
        return None
    source, first, last = keys[0][0], keys[0][1], keys[-1][1]
    best = None
    for start in range(first - CITATION_REACH[0], last + CITATION_REACH[1] + 1):
        for end in range(start, start + CITATION_MAX_SPAN):
            span = [(source, n) for n in range(start, end + 1)]
            if any(key not in lines for key in span):
                break
            if quote_on_line(quote, _norm(" ".join(lines[key] for key in span))):
                score = (end - start, abs(start - first))
                if best is None or score < best[0]:
                    best = (score, start, end)
                break  # a longer span from this start is never better
    if best:
        return span_tag(source, best[1], best[2])
    if len(_norm(quote.replace("...", " ").replace("…", " ")).split()) < GLOBAL_MIN_WORDS:
        return None
    hits = [n for (s, n), text in lines.items() if s == source and quote_on_line(quote, _norm(text))]
    return span_tag(source, hits[0], hits[0]) if len(hits) == 1 else None


def repair_claims(output, context):
    """Repair wrong citations and near-miss quotes in place; return the log of every repair."""
    lines, log = line_map(context), []
    for claim in claims_of(output):
        keys = cited_keys(claim.get("citation", ""))
        if not keys or any(key not in lines for key in keys):
            continue
        text = " ".join(lines[key] for key in keys)
        if quote_on_line(claim["quote"], _norm(text)):
            continue
        moved = repair_citation(claim["quote"], claim["citation"], lines)
        if moved:
            log.append({"citation": claim["citation"], "new_citation": moved, "quote": claim["quote"]})
            claim["citation"] = moved
            continue
        fixed = repair_quote(claim["quote"], text)
        if fixed:
            log.append({"citation": claim["citation"], "old": claim["quote"], "new": fixed[0], "similarity": fixed[1]})
            claim["quote"] = fixed[0]
    return log


def copy_analyst_quotes(output, upstream, context):
    """The Advisor must copy each analyst quote exactly. When its quote is not on the
    cited line, code copies the analysts' quote for that same citation (the one sharing
    the most numbers with the Advisor's claim). Returns the log of every copy."""
    lines, log = line_map(context), []
    by_tag = {}
    for out in upstream:
        for claim in claims_of(out):
            by_tag.setdefault(tidy_citation(claim["citation"]), []).append(claim["quote"])
    for claim in claims_of(output):
        tag = tidy_citation(claim.get("citation", ""))
        keys = cited_keys(tag)
        if not keys or any(key not in lines for key in keys) or tag not in by_tag:
            continue
        if quote_on_line(claim["quote"], _norm(" ".join(lines[key] for key in keys))):
            continue
        wanted = {_digits(n) for n in claimed_numbers(claim["claim"] + " " + claim["quote"])}
        best = max(by_tag[tag], key=lambda q: len(wanted & {_digits(n) for n in NUMBER.findall(q)}))
        log.append({"citation": tag, "old": claim["quote"], "new": best, "similarity": "copied from the analyst"})
        claim["quote"] = best
    return log


def claim_problems(claim, context, allowed=None):
    """The check's problems for one claim (empty when it passes)."""
    problems = [p.split(": ", 1)[1] if p.startswith("Claim: ") else p
                for p in check_research({"Claim": "- " + render_claim(claim)}, context)["problems"]]
    if allowed is not None and tidy_citation(claim["citation"]) not in allowed:
        problems.append("a line that no analyst cited (a new fact)")
    return problems


def split_claims(output, context, allowed=None):
    """Change 2: keep the claims that pass; return (kept output, removed claims with their problems)."""
    kept, removed = {}, []
    for key, value in output.items():
        if isinstance(value, dict) and "quote" in value:
            problems = claim_problems(value, context, allowed)
            kept[key] = None if problems else value
            if problems:
                removed.append((key, value, problems))
        elif isinstance(value, list) and any(isinstance(c, dict) and "quote" in c for c in value):
            kept[key] = []
            for claim in value:
                problems = claim_problems(claim, context, allowed)
                if problems:
                    removed.append((key, claim, problems))
                else:
                    kept[key].append(claim)
        else:
            kept[key] = value
    return kept, removed


def check_advisor(output, upstream, context):
    """Strategy Manager consistency check of the Investment Advisor: no new facts.

    upstream: the analysts' outputs. The Advisor may cite only lines that an
    analyst cited; its deciding number must be on its cited line; its thesis
    states no number except the deciding number."""
    allowed, restricted = advisor_scope(upstream, context)
    problems = []
    for claim in claims_of(output):
        tag = tidy_citation(claim["citation"])
        if tag not in allowed:
            problems.append(f"Investment Recommendation: [{tag}] is a line that no analyst cited (a new fact)")
    result = check_research(role_sections(ADVISOR, output), restricted)
    deciding = output.get("deciding_number") or {}
    numbers = {_digits(t) for t in claimed_numbers(deciding.get("claim", ""))}
    if not numbers:
        problems.append("Deciding number: the claim states no number")
    for token in claimed_numbers(output.get("thesis", "")):
        if _digits(token) not in numbers:
            problems.append(f"Thesis: number {token} is not the deciding number; write the thesis in words")
    if output.get("recommendation") not in {"Buy", "Hold", "Sell"}:
        problems.append("Recommendation: must be Buy, Hold or Sell")
    return with_insight({**result, "problems": result["problems"] + problems}, output, restricted)


def check_research_output(output, context):
    return with_insight(check_research(render_sections(output, SECTIONS), context), output, context)


CHECKS = {"research": check_research_output, "financial": check_financial}


def write_report(out, role, run, company, model):
    data.save_json(out / f"{role.persona_file[:-3]}.json",
                   {"model": model, "persona": run.persona, "attempts": run.attempts,
                    "output": run.output, "check": run.check, "history": run.history,
                    "quote_repairs": run.repairs})
    check, sections = run.check, role_sections(role, run.output)
    lines = [f"# {role.title} draft: {company.get('name')} ({company.get('ticker')})", "",
             f"Model: `{model}` via Purdue GenAI Studio. Persona: {run.persona}.",
             f"Citation check: **{check['status']}** ({check['citations_ok']} of {check['citations']} citations ok) "
             f"after {run.attempts} attempt(s); at most {MAX_ATTEMPTS} are allowed.",
             "This is quote/number matching, not a complete semantic Verifier or a human audit.",
             "Status: DRAFT. Human audit is pending.", ""]
    if role is ADVISOR:
        lines += [f"Recommendation: **{run.output.get('recommendation', 'MISSING')}**", "",
                  "Thesis: " + (run.output.get("thesis") or "MISSING"), "",
                  "What would change it: " + (run.output.get("what_would_change") or "MISSING"), ""]
    for title, body in sections.items():
        if title != "Insight":
            lines += [f"## {title}", "", body or "None supplied.", ""]
    lines += ["## Insight", "", insight_line(run), "",
              "Evidence:", "", sections["Insight"], ""]
    if check["problems"]:
        lines += ["## Check problems", ""] + [f"- {p}" for p in check["problems"]] + [""]
    lines += ["This is a learning exercise, not financial advice.",
              "AI assistance: Codex, Claude, Gemini, Purdue GenAI Studio (gpt-oss:120b). "
              "Human source verification and sign-off are pending.", ""]
    path = out / f"{role.persona_file[:-3]}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def insight_line(run):
    """'Insight: <sentence> [tag].' The tag goes before the full stop, so it stays in the sentence."""
    sentence = (run.output.get("insight") or "MISSING").strip()
    tags = run.check.get("insight_citations") or ([run.check["insight_citation"]] if run.check.get("insight_citation") else [])
    if not tags:
        return "Insight: " + sentence
    end = sentence[-1] if sentence[-1:] in ".!?" else "."
    return f"Insight: {sentence.rstrip('.!?')} " + " ".join(f"[{tag}]" for tag in tags) + end


def compile_report(state, folder, evidence_table):
    """The five parts in template order. Python evidence is added to Valuation Insights unchanged."""
    folder = Path(folder)
    selected = evidence.read_json(folder / "selected_filings.json")
    exhibit = evidence.read_json(folder / "documents.json")["earnings_release"].get("exhibit_label", "Exhibit 99.1")
    company = state.company
    first_line = f"{company.get('name')} ({company.get('ticker')}); filings read: " + "; ".join(
        f"{form} {row['accessionNumber']} ({'primary document and ' + exhibit if form == '8-K' else 'primary document'})"
        for form, row in selected.items())
    runs = {role.key: getattr(state, role.key) for role in ALL_ROLES}
    lines = [first_line, "Report run time: " + datetime.now().astimezone().isoformat(), "",
             f"Model: `{state.model}` via Purdue GenAI Studio. Graph: crewAI Flow (flow_desk.py).",
             "Personas: " + "; ".join(f"{role.title}: {runs[role.key].persona or 'not run'}" for role in ALL_ROLES) + ".",
             "Strategy Manager (code): " + "; ".join(
                 f"{role.title} {runs[role.key].check.get('status', 'not run')} after {runs[role.key].attempts} attempt(s)"
                 for role in ALL_ROLES) + ".",
             "Status: DRAFT. Human audit and partner checks are pending.", ""]
    if state.live and state.live_record:
        compiled = datetime.now(EASTERN)
        inside = compiled <= datetime.fromisoformat(state.live_record["window_ends_et"])
        state.live_record["report_compiled_et"] = compiled.isoformat()
        state.live_record["report_inside_window"] = inside
        lines.insert(-2, f"Live run: earnings 8-K {state.live_record['accession']} accepted "
                         f"{state.live_record['accepted_et']} (EDGAR); window ends {state.live_record['window_ends_et']}; "
                         f"report compiled {compiled.isoformat(timespec='seconds')}; inside the 24-hour window: "
                         f"{'yes' if inside else 'NO'}. The commit's time is the record.")

    research, financial, advisor = runs["research"], runs["financial"], runs["advisor"]
    # Change 2: only claims that pass the check go into the five parts. Removed claims are
    # listed under "Remaining review items" with their problems; nothing is dropped silently.
    context = state.research_context
    allowed, restricted = advisor_scope([research.output, financial.output], context)
    kept = {"research": split_claims(research.output, context),
            "financial": split_claims(financial.output, context),
            "advisor": split_claims(advisor.output, restricted, allowed)}
    titles = {**SECTIONS, **FINANCIAL_SECTIONS, **ADVISOR_SECTIONS,
              "deciding_number": "Deciding number", "insight_evidence": "Insight evidence"}
    repairs = sum(1 for role in ALL_ROLES for entry in runs[role.key].repairs if "new" in entry)
    moved = sum(1 for role in ALL_ROLES for entry in runs[role.key].repairs if "new_citation" in entry)
    lines.insert(-2, f"Quote repairs made in code: {repairs}; citation repairs made in code: {moved} "
                     "(each is listed in the role's JSON file). "
                     "Claims that failed the check are not in the five parts; see Remaining review items.")

    def bullets(claims):
        return "\n".join("- " + render_claim(c) for c in claims)

    def insight(role):
        run, out = runs[role.key], kept[role.key][0]
        failed = [p for p in run.check.get("problems", []) if p.startswith("Insight")]
        if failed or not out.get("insight_evidence"):
            return ["Insight: not shown, because it failed the Strategy Manager's check (see Remaining review items).", ""]
        return [insight_line(run), "", "Insight evidence:", "", bullets(out["insight_evidence"]), ""]

    def body(claims, removed_any):
        return bullets(claims) or ("None passed the Strategy Manager's check." if removed_any else "None supplied.")

    for part in PARTS:
        lines += [f"## {part}", ""]
        if OWNER[part] is RESEARCH:
            key = next(k for k, title in SECTIONS.items() if title == part)
            out, removed = kept["research"]
            lines += [body(out.get(key, []), any(k == key for k, _, _ in removed)), ""]
            if key == "future_developments":
                lines += insight(RESEARCH)
        elif OWNER[part] is FINANCIAL:
            out, removed = kept["financial"]
            for key, title in FINANCIAL_SECTIONS.items():
                lines += [f"### {title}", "", body(out.get(key, []), any(k == key for k, _, _ in removed)), ""]
            lines += insight(FINANCIAL)
            lines += ["### Python evidence (code-generated, unchanged)", "", evidence_table, ""]
        else:
            out, removed = kept["advisor"]
            deciding = out.get("deciding_number")
            lines += [f"Recommendation: **{out.get('recommendation', 'MISSING')}**", "",
                      "Thesis: " + (out.get("thesis") or "MISSING"), "",
                      "Deciding number: " + (render_claim(deciding) if deciding else
                                             "not shown, because it failed the Strategy Manager's check (see Remaining review items)."), "",
                      "Support:", "", body(out.get("support", []), any(k == "support" for k, _, _ in removed)), "",
                      "Risks:", "", body(out.get("risks", []), any(k == "risks" for k, _, _ in removed)), "",
                      "What would change it: " + (out.get("what_would_change") or "MISSING"), ""]
            lines += insight(ADVISOR)
    remaining = [f"{role.title}: {p}" for role in ALL_ROLES for p in runs[role.key].check.get("problems", [])]
    remaining += [f"{role.title} / {titles.get(key, key)}: removed from the report: {render_claim(claim)} "
                  f"Problem: {'; '.join(problems)}"
                  for role in ALL_ROLES for key, claim, problems in kept[role.key][1]]
    if remaining:
        lines += ["## Remaining review items", ""] + [f"- {p}" for p in remaining] + [""]
    lines += ["This is a learning exercise, not financial advice.",
              "AI assistance: Codex, Claude, Gemini, Purdue GenAI Studio (gpt-oss:120b). "
              "Human source verification and sign-off are pending.", ""]
    return "\n".join(lines)


class ResearchDeskFlow(Flow[DeskState]):
    llm_factory = staticmethod(make_llm)

    @start()
    def gather_filings(self):
        """Data node, no model: complete SEC data and sourced financial context."""
        print("Node: gather_filings", flush=True)
        price = Decimal(self.state.price) if self.state.price is not None else None
        if self.state.requested_run_folder:
            folder = Path(self.state.requested_run_folder).resolve()
            if evidence.read_json(folder / "manifest.json")["company"]["ticker"] != self.state.ticker:
                raise data.DeskError("Requested run folder belongs to another company.")
        elif self.state.reuse:
            folder = find_run(self.state.ticker, self.state.peers)
            print("Using saved filings:", folder, flush=True)
        else:
            run = data.Desk(data.SECClient(), self.state.ticker, self.state.peers or [], price, None)
            for step in range(1, 8):
                run.run_step(step)
            folder = run.folder
            price = None  # step 5 already used it
        if price is not None:
            # Recompute step 5 (calculations, P/E) on the selected saved run with the supplied price.
            run = data.Desk(data.SECClient(), self.state.ticker, self.state.peers or [], price, 5)
            run.folder, run.state = Path(folder), evidence.read_json(Path(folder) / "manifest.json")
            run.run_step(5)
        if self.state.price_date:
            calculations = evidence.read_json(Path(folder) / "calculations.json")
            calculations["price_reference"] = {"date": self.state.price_date, "source": self.state.price_source}
            data.save_json(Path(folder) / "calculations.json", calculations)
            data.save_json(Path(folder) / "price_reference.json", calculations["price_reference"])
        self.state.run_folder = str(folder)
        if self.state.live:
            eight_k = evidence.read_json(Path(folder) / "selected_filings.json")["8-K"]
            window = live_window(eight_k["accepted"])
            self.state.live_record = {"ticker": self.state.ticker, "accession": eight_k["accessionNumber"],
                                      "index_url": eight_k["index_url"], **window}
            if not window["open"]:
                raise data.DeskError(f"--live: the earnings 8-K {eight_k['accessionNumber']} was accepted "
                                     f"{eight_k['accepted']} Eastern; its 24-hour window ended {window['window_ends_et']}. "
                                     "No model call was made. Run without --live; that run would be a practice run.")
            print(f"Live window: 8-K {eight_k['accessionNumber']} accepted {eight_k['accepted']} Eastern; "
                  f"{window['hours_left']} hours left", flush=True)
        saved = evidence.read_json(Path(folder) / "calculations.json")
        reference = saved.get("price_reference") or {}
        self.state.price_note = ({"price_usd": saved["price_usd"], "date": reference.get("date") or "not confirmed",
                                  "source": reference.get("source") or "not confirmed"}
                                 if saved.get("price_usd") is not None else {"price_usd": None, "note": "no price supplied"})
        personas = {role.key: load_persona(PERSONA_DIR / role.persona_file) for role in ROLES}
        self.state.research_context = fit_context(folder, self.state.peers, self.state.supplements_manifest, personas)
        self.state.company = self.state.research_context["company"]

    def run_role(self, role):
        """Model node body: first draft, or one revision after the Strategy Manager's send-back."""
        run = getattr(self.state, role.key)
        revising = run.attempts > 0
        print(f"Node: {role.title.lower().replace(' ', '_')}" + (" (send-back)" if revising else ""), flush=True)
        persona = load_persona(PERSONA_DIR / role.persona_file)
        run.persona = "student persona" if persona else "neutral rules (persona file empty)"
        previous = run.output if revising else None
        problems = run.check.get("problems") if revising else None
        if role is ADVISOR:
            message = build_advisor_message(self.state.research.output, self.state.financial.output, persona,
                                            self.state.price_note, previous, problems)
        else:
            message = build_message(self.state.research_context, persona, previous, problems, rules=role.rules)
        run.attempts += 1
        print(f"{role.title} attempt {run.attempts}: model input about "
              f"{check_size(message):,} tokens (limit {MAX_INPUT_TOKENS:,})", flush=True)
        llm = self.llm_factory()
        self.state.model = getattr(llm, "model", "unknown")
        agent = Agent(role=role.title, goal=role.goal, backstory=persona or role.backstory,
                      llm=llm, max_iter=3, verbose=False)
        try:
            result = call_with_deadline(lambda: agent.kickoff(message, response_format=role.schema), ROLE_CALL_SECONDS)
            if result.pydantic is None:
                raise data.DeskError(f"{role.title} did not return the required fields.")
        except Exception as exc:  # noqa: BLE001 - a failed call is a failed draft, never a lost run
            if not revising:
                # For example the output-length limit. The draft is empty; the Manager sends it back once.
                run.output, run.call_error = {}, f"First attempt failed: {exc}"[:500]
                print(run.call_error, flush=True)
                return
            run.revision_error = f"Send-back attempt failed: {exc}"[:500]
            print(run.revision_error, flush=True)
            return
        run.call_error = ""
        output = result.pydantic.model_dump()
        for claim in claims_of(output):
            claim.update({k: clean_format(claim[k]) for k in ("claim", "quote")},
                         citation=tidy_citation(claim["citation"]))
        for key in ("insight", "thesis", "what_would_change"):
            if isinstance(output.get(key), str):
                output[key] = clean_format(output[key])
        try:
            repairs = []
            if role is ADVISOR:
                repairs = copy_analyst_quotes(output, [self.state.research.output, self.state.financial.output],
                                              self.state.research_context)
            repairs += repair_claims(output, self.state.research_context)
        except Exception as exc:  # noqa: BLE001 - a repair fault must never stop a run; the check still applies
            repairs = []
            run.repairs.append({"attempt": run.attempts, "error": f"quote repair skipped: {exc}"[:300]})
            print(f"{role.title}: quote repair skipped ({exc})", flush=True)
        for entry in repairs:
            run.repairs.append({"attempt": run.attempts, **entry})
            if "new_citation" in entry:
                print(f"{role.title}: citation repaired [{entry['citation']}] -> [{entry['new_citation']}]", flush=True)
            else:
                print(f"{role.title}: quote repaired at [{entry['citation']}] (similarity {entry['similarity']})", flush=True)
        run.output = output

    def check_role(self, role):
        """One role's Strategy Manager checks, in code."""
        run = getattr(self.state, role.key)
        if role is ADVISOR:
            return check_advisor(run.output, [self.state.research.output, self.state.financial.output],
                                 self.state.research_context)
        return CHECKS[role.key](run.output, self.state.research_context)

    @router(or_(gather_filings, "revise_research"))
    def research_analyst(self):
        self.run_role(RESEARCH)
        return "manager_review" if self.state.research.attempts > 1 else "research_ready"

    @router(or_("research_ready", "revise_financial"))
    def financial_analyst(self):
        self.run_role(FINANCIAL)
        return "manager_review" if self.state.financial.attempts > 1 else "financial_ready"

    @router(or_("financial_ready", "revise_advisor"))
    def investment_advisor(self):
        self.run_role(ADVISOR)
        return "manager_review"

    @router("manager_review")
    def strategy_manager(self) -> Literal["revise_research", "revise_financial", "revise_advisor", "report_ready"]:
        """Code, not a model: check the five parts; send one failed part back to its owner, once."""
        print("Node: strategy_manager", flush=True)
        for role in ALL_ROLES:
            run = getattr(self.state, role.key)
            if run.revision_error:
                problems = [p for p in run.check.get("problems", []) if run.revision_error not in p]
                run.check = {**run.check, "status": "fail",
                             "problems": problems + [run.revision_error + " The report keeps the previous draft."]}
                if len(run.history) < run.attempts:
                    run.history.append({"attempt": run.attempts, "error": run.revision_error})
                continue
            if run.call_error:
                run.check = {"status": "fail", "citations": 0, "citations_ok": 0, "marks": [], "insight_citation": None,
                             "problems": [run.call_error + " Return a shorter answer: write only the claims the rules ask for."]}
            else:
                run.check = self.check_role(role)
            if len(run.history) < run.attempts:
                run.history.append({"attempt": run.attempts, "output": run.output, "check": run.check})
        statuses = {role.title: getattr(self.state, role.key).check["status"] for role in ALL_ROLES}
        missing = [part for part in PARTS if not self.part_present(part)]
        for part in missing:
            run = getattr(self.state, OWNER[part].key)
            note = f"{part}: missing required part"
            if note not in run.check["problems"]:
                run.check = {**run.check, "status": "fail", "problems": run.check["problems"] + [note]}
        next_node = "report_ready"
        for role in ALL_ROLES:
            run = getattr(self.state, role.key)
            if run.check["status"] == "fail" and run.attempts < MAX_ATTEMPTS and not run.revision_error:
                next_node = f"revise_{role.key}"
                break
        self.state.manager.append({"statuses": statuses, "missing_parts": missing, "next": next_node})
        print("Strategy Manager: " + "; ".join(f"{k} {v}" for k, v in statuses.items()) + f" -> {next_node}", flush=True)
        return next_node

    def part_present(self, part):
        role = OWNER[part]
        output = getattr(self.state, role.key).output
        if role is RESEARCH:
            key = next(k for k, title in SECTIONS.items() if title == part)
            return bool(output.get(key))
        if role is FINANCIAL:
            return any(output.get(key) for key in FINANCIAL_SECTIONS)
        return (output.get("recommendation") in {"Buy", "Hold", "Sell"} and bool(output.get("thesis"))
                and bool(output.get("deciding_number")))

    @listen("report_ready")
    def compile_report(self):
        """Save every node's input and output, then the compiled report. No model."""
        print("Node: compile_report", flush=True)
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S-%f")
        folder = Path(self.state.run_folder)
        out = folder / "flow" / stamp
        out.mkdir(parents=True, exist_ok=False)
        save_context(folder, out, self.state.research_context)
        for role in ALL_ROLES:
            run = getattr(self.state, role.key)
            path = write_report(out, role, run, self.state.company, self.state.model)
            print("Saved:", path, flush=True)
            print(f"{role.title} check: {run.check['status']} ({run.check['citations_ok']}/{run.check['citations']} ok, "
                  f"{len(run.check['problems'])} problems, {run.attempts} attempt(s))", flush=True)
        data.save_json(out / "advisor_input.json", {"research_analyst": self.state.research.output,
                                                    "financial_analyst": self.state.financial.output,
                                                    "price": self.state.price_note})
        data.save_json(out / "strategy_manager.json", {"reviews": self.state.manager, "parts": list(PARTS)})
        # Verifier inputs: the same evidence snapshot, plus the quarter facts and the price reference.
        selected = evidence.read_json(folder / "selected_filings.json")
        exhibit = evidence.read_json(folder / "documents.json")["earnings_release"].get("exhibit_label", "Exhibit 99.1")
        release = (folder / "earnings_release.txt").read_text(encoding="utf-8")
        quarter = quarterly_facts(release, selected["8-K"]["accessionNumber"], exhibit)
        data.save_json(out / "evidence" / "quarter_facts.json", quarter)
        if (folder / "price_reference.json").exists():
            shutil.copyfile(folder / "price_reference.json", out / "evidence" / "price_reference.json")
        table = evidence_markdown(evidence.read_json(folder / "facts.json"),
                                  evidence.read_json(folder / "calculations.json"), quarter,
                                  evidence.read_json(folder / "peers.json"))
        report = out / "report.md"
        report.write_text(compile_report(self.state, folder, table), encoding="utf-8")
        print("Report:", report, flush=True)
        self.state.output_folder, self.state.report_path = str(out), str(report)

    @listen(compile_report)
    def verifier(self):
        """Runs on every compiled report. No option turns it off."""
        print("Node: verifier", flush=True)
        out = Path(self.state.output_folder)
        verified, marks = verifier.verify_run(out, report_name="report.md", evidence=out / "evidence")
        self.state.verified_folder = str(verified)
        self.state.verified_summary = verifier.summary(marks)
        print("Verified report:", verified / "verified_report.md", "-", self.state.verified_summary, flush=True)


def save_live(state, root=None):
    """Copy the live run's report, verified report and marks into runs/live/, ready to commit.

    Only small result files are copied: the filing texts and facts stay in the ignored data run."""
    record = state.live_record
    out, verified = Path(state.output_folder), Path(state.verified_folder)
    target = Path(root or LIVE_DIR) / f"{state.ticker}_{record['accepted_et'][:10]}" / out.name
    target.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(out / "report.md", target / "report.md")
    shutil.copyfile(verified / "verified_report.md", target / "verified_report.md")
    shutil.copyfile(verified / "marks.json", target / "marks.json")
    roles = {role.title: {"status": getattr(state, role.key).check.get("status"),
                          "attempts": getattr(state, role.key).attempts} for role in ALL_ROLES}
    data.save_json(target / "live.json", {**record, "verified_summary": state.verified_summary, "roles": roles,
                                          "recommendation": state.advisor.output.get("recommendation"),
                                          "source_run": str(out)})
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", type=data.normalize_ticker, nargs="?")
    parser.add_argument("--verify-only", metavar="RUN_FOLDER", help="Run only the Verifier on a saved run folder")
    parser.add_argument("--reuse", action="store_true", help="Use a complete saved data run; no SEC requests")
    parser.add_argument("--peers", nargs="*", default=None, help="Peer tickers separated by spaces or commas")
    parser.add_argument("--run-folder", help="Explicit complete saved run instead of selecting the newest")
    parser.add_argument("--supplements", help="JSON manifest of local management presentation text with source URLs")
    parser.add_argument("--prepare-only", action="store_true", help="Save inputs for review without a model call or report")
    parser.add_argument("--price", type=data.positive_price, help="USD share price for fiscal-year P/E")
    parser.add_argument("--price-date", help="Market date of the supplied price, YYYY-MM-DD")
    parser.add_argument("--price-source", help="HTTPS source URL of the supplied price")
    parser.add_argument("--live", action="store_true",
                        help="Live record run: fresh SEC data; stops before any model call if the earnings 8-K's "
                             "24-hour window has closed; saves the result in runs/live/")
    args = parser.parse_args(argv)
    if args.verify_only:
        return verifier.main([args.verify_only])
    if not args.ticker:
        parser.error("a ticker is required unless --verify-only is used")
    try:
        if bool(args.price_date) != bool(args.price_source) or (args.price_date and args.price is None):
            raise data.DeskError("Use --price-date and --price-source together, with --price.")
        if args.live and (args.reuse or args.run_folder or args.prepare_only):
            raise data.DeskError("--live fetches fresh SEC data; do not combine it with --reuse, --run-folder or --prepare-only.")
        if args.price_date:
            date.fromisoformat(args.price_date)
            if not args.price_source.startswith("https://"):
                raise data.DeskError("Price source must be an HTTPS URL.")
        flow = ResearchDeskFlow()
        peers = None if args.peers is None else list(dict.fromkeys(data.normalize_ticker(t) for group in args.peers for t in group.split(",") if t))
        inputs = {"ticker": args.ticker, "reuse": args.reuse, "peers": peers,
                  "requested_run_folder": args.run_folder, "supplements_manifest": args.supplements,
                  "price": None if args.price is None else str(args.price),
                  "price_date": args.price_date, "price_source": args.price_source, "live": args.live}
        if args.prepare_only:
            for name, value in inputs.items():
                setattr(flow.state, name, value)
            flow.gather_filings()
            out = Path(flow.state.run_folder) / "prepared_inputs" / datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S-%f")
            save_context(flow.state.run_folder, out, flow.state.research_context)
            print("Prepared inputs only (no report or verification result):", out)
            for role in ROLES:
                message = build_message(flow.state.research_context, load_persona(PERSONA_DIR / role.persona_file),
                                        rules=role.rules)
                tokens = estimated_tokens(message)
                print(f"{role.title} model input: about {tokens:,} tokens (limit {MAX_INPUT_TOKENS:,}); "
                      f"with the {SEND_BACK_RESERVE_TOKENS:,}-token send-back reserve: {tokens + SEND_BACK_RESERVE_TOKENS:,}"
                      + ("" if tokens <= MAX_INPUT_TOKENS else " - TOO LARGE; a model run would stop"))
            print("Excerpt policy:", flow.state.research_context.get("excerpt_policy", "not stated"))
            return 0
        flow.kickoff(inputs=inputs)
        print("Verified report:", Path(flow.state.verified_folder) / "verified_report.md")
        print(flow.state.verified_summary)
        if args.live:
            target = save_live(flow.state)
            inside = flow.state.live_record.get("report_inside_window")
            print(f"Live record saved: {target} (inside the 24-hour window: {'yes' if inside else 'NO'}). "
                  "Commit and push it now: the commit's time is the record.")
        passed = all(getattr(flow.state, role.key).check.get("status") == "pass" for role in ALL_ROLES)
        return 0 if passed else 2
    except (data.DeskError, OSError, ValueError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
