#!/usr/bin/env python3
"""Week 3 Verifier: marks every sourced number in a compiled report. Code only; no model.

Input: one saved run folder. The Verifier reads only:
  report.md (the compiled report), facts.json (XBRL facts), the saved filing
  texts (10-K.txt, 10-Q.txt, earnings_release.txt), and, if present,
  quarter_facts.json, peers.json and price_reference.json.
It never reads role instructions or role calls. From calculations.json it reads only
  the supplied price; it recomputes every calculation itself.

Rules (Lab 04):
- An XBRL-tagged number must equal the facts file exactly, for its tag and period.
- A line-sourced number must be on the cited line of that filing. Format may differ:
  41,954 in a "$ in millions" table equals "$41.954 billion".
- A ratio is recomputed from its stated inputs. Each input must be a sourced value.
- A named metric in prose (revenue growth, operating margin, ROE, debt to equity,
  P/E, free cash flow, diluted EPS) is recomputed from the facts file.
- A number with no source is Unsupported.
Marks: Correct, Wrong, Unsupported. Wrong and Unsupported numbers get the filing
value with its tag or line, where Python can find one.
Skipped: everything above the first "## " heading (run metadata and human
partner checks) and the Investment Advisor's thesis (## Investment Recommendation).

What code alone cannot catch: a number that is on the cited line but belongs to a
different year, segment or definition on that same line.
"""

import argparse
import ast
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
import operator
from pathlib import Path
import re
import sys

# The Investment Advisor's thesis, and the Manager's notes, which are not report claims.
SKIP_SECTIONS = {"Investment Recommendation", "Recommendation", "Remaining review items"}
METRIC_REACH = (80, 25)  # a metric phrase must end within 80 characters before, or start within 25 after, the number
HYPHENS = str.maketrans({"\u3010": "[", "\u3011": "]", "\u2011": "-", "\u2013": "-", "\u2014": "-", "\u2010": "-",
                         "\u2012": "-", "\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u2007": " "})
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
# Spans that hold no claimed number. Each is blanked (same length) before numbers are read.
NOT_CLAIMS = [r"https?://\S+", r"\]\([^)]*\)", r"`[^`]*`", r"\[[^\[\]]*\]", r"\d{10}-\d{2}-\d{6}",
              r"\d{4}-\d{2}-\d{2}", rf"\b(?:{MONTHS})\s+\d{{1,2}}(?:,\s+\d{{4}})?", r"\b(?:19|20)\d{2}\b",
              r"\bQ[1-4]\b", r"\bFY\s?\d{4}\b", r"\b(?:printed page|page|slide|Item|Schedule)\s+\d+",
              r"\bL\d+\b", r"\bline\s+\d+", r"\(\d\)", r"[A-Za-z]-\d+", r"\b\d{1,2}-[KQ]\b", r"\bExhibit\s+\d+(?:\.\d+)?",
              r"\d+:\d+", r"table header:.*$", r"column dates:.*$"]
NUMBER = re.compile(r"(?<![\w.,/])(?P<dollar>\$\s?)?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
                    r"(?P<pct>\s?(?:%|percent\b))?(?P<scale>\s(?:billion|million)\b)?(?P<times>\s?(?:x\b|×|times\b))?")
LINE_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
BRACKET_CITE = re.compile(r"\[([^\[\]]*?\bL\d+[^\[\]]*)\]")
PLAIN_CITE = re.compile(r"(?<!\[)\b(10-K|10-Q|Exhibit 99(?:\.1)?)\s+(L\d+(?:\s*-\s*L?\d+)?)")
RANGE = re.compile(r"L(\d+)(?:\s*-\s*L?(\d+))?")
TABLE_CELL = re.compile(r"^\s*(?P<num>[\d,]+(?:\.\d+)?) (?P<unit>[A-Za-z/]+); (?P<accn>\d{10}-\d{2}-\d{6}), "
                        r"`(?P<tag>[\w-]+:\w+)`, (?P<start>\d{4}-\d{2}-\d{2})(?: to (?P<end>\d{4}-\d{2}-\d{2}))?")
CALC = re.compile(r"^- (?P<name>[^:]+): (?P<expr>[\d,.\s()+\-*/]+?) = (?P<result>[\d,]+(?:\.\d+)?)\s*(?P<unit>%|x|USD)?")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z*(\[])")
CONSTANTS = {Decimal(100), Decimal(2)}
# Ten-K row labels used to show "the real line" beside a fact.
TEN_K_LABELS = {"revenue": ("Total sales", "Sales", "Total revenue", "Net sales"), "operating_income": ("Operating income",),
                "net_income": ("Net earnings", "Net income"), "diluted_eps": ("Diluted earnings per share",),
                "equity": ("Total shareholders", "Total stockholders", "Total equity"),
                "long_term_debt": ("Long-term debt",), "current_debt": ("Current portion of long-term debt",),
                "cfo": ("Net cash provided by operating activities",), "capex": ("Capital expenditures",)}
SCALES = {"": Decimal(1), "million": Decimal(10) ** 6, "billion": Decimal(10) ** 9}
# Lab 03 report template: the eleven core claims and where the report states them.
CORE_CLAIMS = [(1, "Total revenue (current)"), (2, "Revenue growth"), (3, "Operating income (current)"),
               (3, "Operating margin"), (4, "Net income (current)"), (5, "Diluted EPS (current)"),
               (6, "Return on average equity"), (7, "Debt to equity"), (8, "Free cash flow"),
               (9, "Latest reported quarter: Total revenue"), (10, "Quarterly revenue growth"),
               (11, "Latest reported quarter: GAAP diluted EPS")]


def dec(text):
    return Decimal(text.replace(",", ""))


def places(text):
    return len(text.split(".", 1)[1]) if "." in text else 0


def same(value, stated, decimals):
    """True when value, rounded the way the report rounded it, equals the stated number."""
    try:
        return value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP) == stated
    except InvalidOperation:
        return False


def fmt(value, decimals=2):
    if value is None:
        return "unavailable"
    value = Decimal(value)
    return f"{value:,.0f}" if value == value.to_integral() and abs(value) >= 1000 else f"{value:,.{decimals}f}"


def blank(text, pattern, flags=0):
    return re.sub(pattern, lambda m: " " * len(m[0]), text, flags=flags)


class Run:
    """Everything the Verifier may read from one saved run, and nothing else."""

    def __init__(self, folder, report_name="report.md"):
        self.folder = Path(folder)
        read = lambda name: json.loads((self.folder / name).read_text(encoding="utf-8")) if (self.folder / name).exists() else None
        self.report = (self.folder / report_name).read_text(encoding="utf-8")
        self.facts = read("facts.json")
        if not self.facts:
            raise ValueError(f"{self.folder}: facts.json is required")
        self.quarter = read("quarter_facts.json") or {}
        self.peers = read("peers.json") or {}
        self.price = read("price_reference.json") or {}
        if not self.price.get("price_usd"):
            # The supplied price is an input, not a calculation; only that field is read.
            saved = read("calculations.json") or {}
            if saved.get("price_usd") is not None:
                self.price = {**self.price, "price_usd": saved["price_usd"], "price_date": self.price.get("date"),
                              "source_url": self.price.get("source")}
        self.texts = {}
        for label, name in (("10-K", "10-K.txt"), ("10-Q", "10-Q.txt"), ("Exhibit 99", "earnings_release.txt")):
            if (self.folder / name).exists():
                self.texts[label] = (self.folder / name).read_text(encoding="utf-8").splitlines()
        self.texts["Exhibit 99.1"] = self.texts.get("Exhibit 99", [])
        self.metrics = self._metrics()
        self.known = self._known_values()

    def fact(self, key, column="current"):
        entry = self.facts["facts"].get(key, {}).get(column)
        return Decimal(str(entry["val"])) if entry else None

    def ten_k_line(self, key, value):
        """The last 10-K line (statements come after MD&A) that has the row label and the value."""
        lines = self.texts.get("10-K", [])
        targets = {fmt(value / SCALES["million"], 0), fmt(value, 2)} if value is not None else set()
        found = None
        for number, line in enumerate(lines, 1):
            text = line.translate(HYPHENS).strip()
            if any(text.startswith(label) for label in TEN_K_LABELS.get(key, ())) and \
                    any(t in {m.group() for m in LINE_NUMBER.finditer(text)} for t in targets):
                found = (number, text[:160])
        return found

    def fact_source(self, key, column="current"):
        entry = self.facts["facts"][key][column]
        source = f"`{entry['tag']}`, {entry.get('start', 'instant')} to {entry['end']}, accession {entry['accn']}"
        line = self.ten_k_line(key, Decimal(str(entry["val"])))
        return source + (f"; 10-K L{line[0]}: \"{line[1]}\"" if line else "")

    def _metrics(self):
        """Named metrics, recomputed here from the facts file. Each: (value, unit, arithmetic, source)."""
        f, out = self.fact, {}
        def add(name, unit, function, arithmetic, source):
            try:
                value = function()
                if value is not None:
                    out[name] = (value, unit, arithmetic, source)
            except (TypeError, InvalidOperation, ZeroDivisionError):
                pass
        rc, rp, op, ni = f("revenue"), f("revenue", "prior"), f("operating_income"), f("net_income")
        eq, eqp, ltd, cd = f("equity"), f("equity", "prior"), f("long_term_debt"), f("current_debt")
        cfo, capex, eps = f("cfo"), f("capex"), f("diluted_eps")
        tags = "facts.json, annual current and prior periods"
        add("revenue growth", "%", lambda: (rc - rp) / rp * 100, f"({fmt(rc)} - {fmt(rp)}) / {fmt(rp)} × 100", tags)
        add("operating margin", "%", lambda: op / rc * 100, f"{fmt(op)} / {fmt(rc)} × 100", tags)
        add("net margin", "%", lambda: ni / rc * 100, f"{fmt(ni)} / {fmt(rc)} × 100", tags)
        add("return on equity", "%", lambda: ni / ((eq + eqp) / 2) * 100, f"{fmt(ni)} / (({fmt(eq)} + {fmt(eqp)}) / 2) × 100", tags)
        add("debt to equity", "x", lambda: (ltd + cd) / eq, f"({fmt(ltd)} + {fmt(cd)}) / {fmt(eq)}", tags)
        add("free cash flow", "USD", lambda: cfo - abs(capex), f"{fmt(cfo)} - {fmt(abs(capex) if capex is not None else None)}", tags)
        add("diluted eps", "USD", lambda: eps, f"facts.json diluted EPS {eps}", self.fact_source("diluted_eps") if eps else "")
        price = Decimal(str(self.price["price_usd"])) if self.price.get("price_usd") else None
        add("p/e", "x", lambda: price / eps, f"{price} / {eps}", "supplied price / facts.json annual diluted EPS")
        q = self.quarter
        if q.get("total_revenue"):
            qc, qp = dec(q["total_revenue"]["current"]), dec(q["total_revenue"]["prior"])
            line = q["total_revenue"]["source"]["line_number"]
            add("quarterly revenue growth", "%", lambda: (qc - qp) / qp * 100, f"({fmt(qc)} - {fmt(qp)}) / {fmt(qp)} × 100",
                f"Exhibit 99 L{line}")
        if q.get("diluted_eps"):
            line = q["diluted_eps"]["source"]["line_number"]
            add("quarterly diluted eps", "USD", lambda: dec(q["diluted_eps"]["current"]),
                f"release diluted EPS {q['diluted_eps']['current']}", f"Exhibit 99 L{line}")
        return out

    def _known_values(self):
        """Every sourced value a calculation may use as an input: value -> source."""
        known = {}
        def facts_of(report, who):
            for key, fact in report["facts"].items():
                for column in ("current", "prior"):
                    if fact.get(column):
                        known.setdefault(Decimal(str(fact[column]["val"])),
                                         f"{who} `{fact[column]['tag']}` {column}, accession {fact[column]['accn']}")
        facts_of(self.facts, self.facts["company"]["ticker"])
        for ticker, peer in self.peers.items():
            if "facts" in peer:
                facts_of(peer["facts"], ticker)
        for key in ("total_revenue", "diluted_eps"):
            if self.quarter.get(key):
                for column in ("current", "prior"):
                    known.setdefault(dec(self.quarter[key][column]),
                                     f"release {key} {column}, Exhibit 99 L{self.quarter[key]['source']['line_number']}")
        if self.price.get("price_usd"):
            known.setdefault(dec(self.price["price_usd"]), f"supplied price, {self.price.get('price_date')}, {self.price.get('source_url')}")
        return known


METRIC_WORDS = [("quarterly revenue growth", r"(?:quarter\w*).{0,60}(?:revenue|sales) (?:growth|grew|increase)|(?:revenue|sales) growth.{0,40}quarter"),
                ("revenue growth", r"(?<!comparable )(?<!comparable-)(?:revenue|sales) (?:growth|grew|increased|rose)|growth in (?:revenue|sales)"),
                ("operating margin", r"operating margin"), ("net margin", r"net (?:profit )?margin"),
                ("return on equity", r"return on (?:average )?equity|\bROE\b"),
                ("debt to equity", r"debt[- ]to[- ]equity|debt.{0,80}divided by.{0,30}equity"),
                ("p/e", r"\bP/E\b|price[- ]to[- ]earnings"), ("free cash flow", r"free cash flow"),
                ("quarterly diluted eps", r"quarter\w*.{0,60}diluted (?:EPS|earnings per share)"),
                ("diluted eps", r"diluted (?:EPS|earnings per share)")]


def number_tokens(text):
    clean = text
    for pattern in NOT_CLAIMS:
        clean = blank(clean, pattern, re.M)
    for match in NUMBER.finditer(clean):
        unit = "%" if match["pct"] else "x" if match["times"] else "USD"
        scale = (match["scale"] or "").strip()
        yield match.start("num"), match.end("num"), match["num"], unit, SCALES[scale]


def on_lines(stated, decimals, scale, lines):
    """A stated number is on a line if some number there equals it after unit scaling and rounding."""
    for line in lines:
        for found in LINE_NUMBER.findall(line):
            for s in (SCALES[""], Decimal(1000), SCALES["million"], SCALES["billion"]):
                if same(dec(found) * s / scale, stated, decimals):
                    return True
    return False


def safe_eval(expr):
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.Constant):
            return Decimal(str(node.value))
        raise ValueError("unsupported expression")
    return walk(ast.parse(expr.replace(",", ""), mode="eval"))


class Verifier:
    def __init__(self, run):
        self.run, self.marks = run, []

    def mark(self, start, end, text, section, item, result, why, correct=None, source=""):
        self.marks.append({"id": f"V{len(self.marks) + 1}", "section": section, "item": item, "number": text,
                           "mark": result, "why": why, "correct": correct, "source": source,
                           "start": start, "end": end})

    def verify(self):
        report = self.run.report
        offset, section, sub = 0, None, ""
        for raw in report.splitlines(keepends=True):
            line = raw.translate(HYPHENS)
            if line.startswith("## "):
                section, sub = line[3:].strip(), ""
            elif line.startswith("### "):
                sub = line[4:].strip()
            elif section and section not in SKIP_SECTIONS and not line.lstrip().startswith("Source quote:"):
                where = f"{section}" + (f" / {sub}" if sub else "")
                if line.startswith("|") and "`" in line:
                    self.table_row(line, offset, where)
                elif CALC.match(line):
                    self.calculation(line, offset, where)
                else:
                    self.prose(line, offset, where, sub)
            offset += len(raw)
        return self.marks

    def table_row(self, line, offset, where):
        cells = line.split("|")
        label, position = cells[1].strip(), len(cells[0]) + 1 + len(cells[1]) + 1
        for column, cell in zip(("current", "prior"), cells[2:4]):
            match = TABLE_CELL.match(cell)
            if match:
                start, end = offset + position + match.start("num"), offset + position + match.end("num")
                self.tagged(match, start, end, where, f"{label} ({column})")
            position += len(cell) + 1

    def tagged(self, match, start, end, where, item):
        """XBRL rule: exact equality with facts.json for the same tag and period."""
        tag, period_end, period_start = match["tag"], match["end"] or match["start"], match["start"] if match["end"] else None
        for key, fact in self.run.facts["facts"].items():
            for column in ("current", "prior"):
                entry = fact.get(column)
                if entry and entry["tag"] == tag and entry["end"] == period_end and entry.get("start") in (period_start, None):
                    value = Decimal(str(entry["val"]))
                    if dec(match["num"]) == value:
                        return self.mark(start, end, match["num"], where, item, "Correct", "equals facts.json exactly",
                                         source=self.run.fact_source(key, column))
                    return self.mark(start, end, match["num"], where, item, "Wrong",
                                     f"facts.json has {fmt(value)} for this tag and period",
                                     correct=fmt(value), source=self.run.fact_source(key, column))
        self.mark(start, end, match["num"], where, item, "Unsupported", f"no fact for {tag} ending {period_end}")

    def calculation(self, line, offset, where):
        match = CALC.match(line)
        name, expr, stated = match["name"].strip(), match["expr"].strip(), match["result"]
        unsourced = []
        for token in LINE_NUMBER.finditer(match["expr"]):
            value = dec(token.group())
            if value not in CONSTANTS and value not in self.run.known:
                unsourced.append(token.group())
                start = offset + match.start("expr") + token.start()
                self.mark(start, start + len(token.group()), token.group(), where, f"{name} input", "Unsupported",
                          "input is not a sourced fact, release value or supplied price")
        start, end = offset + match.start("result"), offset + match.end("result")
        try:
            value = safe_eval(expr)
        except (ValueError, SyntaxError, ZeroDivisionError, InvalidOperation):
            return self.mark(start, end, stated, where, name, "Unsupported", "the arithmetic could not be recomputed")
        if unsourced:
            # The fault is the input, so the stated arithmetic cannot give the filing value.
            metric = next((self.run.metrics[n] for n, p in METRIC_WORDS if re.search(p, name, re.I) and n in self.run.metrics), None)
            why = f"input {', '.join(unsourced)} is not sourced; the stated arithmetic gives {value:.6f}"
            correct = None
            if metric and not same(metric[0], dec(stated), places(stated)):
                correct = fmt(metric[0], places(stated))
                why += f"; from the facts: {metric[2]} = {correct}"
            elif metric:
                why += f"; from the facts ({metric[2]}) the stated result is right"
            return self.mark(start, end, stated, where, name, "Unsupported", why, correct=correct,
                             source=metric[3] if metric else "")
        if same(value, dec(stated), places(stated)):
            self.mark(start, end, stated, where, name, "Correct", f"recomputed: {expr} = {value:.6f}",
                      source="arithmetic of the stated inputs")
        else:
            self.mark(start, end, stated, where, name, "Wrong", f"recomputed: {expr} = {value:.6f}",
                      correct=fmt(value, places(stated)), source="arithmetic of the stated inputs")

    def prose(self, line, offset, where, sub):
        position = 0
        for sentence in SENTENCE_END.split(line):
            position = line.index(sentence, position)
            cited = []
            for match in BRACKET_CITE.finditer(sentence):
                label = re.match(r"\s*([^,;]*?)\s*(?=L\d)", match[1])
                label = label[1].replace("saved ", "").replace(".txt", "").strip() if label else ""
                cited += [(label, int(a), int(b or a)) for a, b in RANGE.findall(match[1])]
            for match in PLAIN_CITE.finditer(sentence):
                cited += [(match[1], int(a), int(b or a)) for a, b in RANGE.findall(match[2])]
            lines = [text for label, a, b in cited for n, text in enumerate(self.run.texts.get(label, []), 1)
                     if a <= n <= b and b - a < 20]
            bullet = re.match(r"^- \**([^:*]+?)\**:", sentence.strip())
            item = (f"{sub}: " if sub else "") + bullet[1].strip() if bullet else where
            for start, end, text, unit, scale in number_tokens(sentence):
                window = sentence[max(0, start - METRIC_REACH[0]):end + METRIC_REACH[1]]
                self.prose_number(window, offset + position + start, offset + position + end, text, unit, scale,
                                  where, item, cited, lines)
            position += len(sentence)

    def prose_number(self, window, start, end, text, unit, scale, where, item, cited, lines):
        stated, decimals = dec(text), places(text)
        if lines and on_lines(stated, decimals, scale, lines):
            tags = ", ".join(f"{label} L{a}" + (f"-L{b}" if b != a else "") for label, a, b in cited)
            return self.mark(start, end, text, where, item, "Correct", "on the cited line", source=tags)
        # Named metric: recompute from the facts file.
        quarter = bool(re.search(r"\bQ[1-4]\b|quarter", window, re.I))
        metrics = [name for name, pattern in METRIC_WORDS if re.search(pattern, window, re.I)
                   and self.run.metrics.get(name) and self.run.metrics[name][1] == unit
                   and name.startswith("quarterly") == quarter]
        match = None  # (why, source) of a sourced value that equals the stated number
        for name in metrics:
            value, _, arithmetic, source = self.run.metrics[name]
            if same(value / scale, stated, decimals):
                match = (f"recomputed {name}: {arithmetic}", source)
                break
        if not match and unit == "USD":
            match = next((("equals a sourced value", source) for value, source in self.run.known.items()
                          if same(value / scale, stated, decimals)), None)
        if not match:
            match = next(((f"recomputed {name}: {arithmetic}", source)
                          for name, (value, metric_unit, arithmetic, source) in self.run.metrics.items()
                          if metric_unit == unit and same(value / scale, stated, decimals)), None)
        if not match and metrics:
            value, _, arithmetic, source = self.run.metrics[metrics[0]]
            correct = fmt(value / scale, max(decimals, 2))
            return self.mark(start, end, text, where, item, "Wrong",
                             f"recomputed {metrics[0]}: {arithmetic} = {correct}", correct=correct, source=source)
        if lines:
            # A line-sourced number must be on its line. A right number with a wrong line is Unsupported.
            near = self.nearby(stated, decimals, scale, cited)
            why = "not on the cited line"
            if near:
                why += f"; the number is on {near[0]} (citation off by {near[1]} line(s))"
            elif match:
                why += f"; it matches a sourced value: {match[0]}"
            return self.mark(start, end, text, where, item, "Unsupported", why,
                             correct=text if near or match else None, source=near[0] if near else match[1] if match else "")
        if match:
            return self.mark(start, end, text, where, item, "Correct", match[0], source=match[1])
        self.mark(start, end, text, where, item, "Unsupported", "no line citation, and no sourced value or metric matches")

    def nearby(self, stated, decimals, scale, cited, reach=5):
        """The closest line, within `reach` lines of a cited range in the same filing, that holds the number."""
        best = None
        for label, a, b in cited:
            lines = self.run.texts.get(label, [])
            for n in range(max(1, a - reach), min(len(lines), b + reach) + 1):
                distance = a - n if n < a else n - b if n > b else 0
                if distance and on_lines(stated, decimals, scale, [lines[n - 1]]) and (best is None or distance < best[1]):
                    best = (f"{label} L{n}", distance)
        return best


def core_summary(marks):
    rows = []
    for claim, item in CORE_CLAIMS:
        mark = next((m for m in marks if m["item"] == item or f"{m['section'].split(' / ')[-1]}: {m['item']}" == item), None)
        rows.append({"claim": claim, "item": item, "mark": mark["mark"] if mark else "Missing",
                     "id": mark["id"] if mark else ""})
    return rows


def render(report, marks, run_folder):
    """Verified report: first line kept, table of marks under it, wrong numbers corrected in place."""
    body = report
    for mark in sorted(marks, key=lambda m: m["start"], reverse=True):
        if mark["mark"] == "Correct":
            continue
        fix = f"~~{mark['number']}~~ **{mark['correct']}** [{mark['id']}]" if mark["correct"] else \
              f"{mark['number']} [{mark['id']}: unsupported]"
        body = body[:mark["start"]] + fix + body[mark["end"]:]
    first, rest = body.split("\n", 1)
    counts = {k: sum(m["mark"] == k for m in marks) for k in ("Correct", "Wrong", "Unsupported")}
    core = core_summary(marks)
    table = ["", "## Verifier marks", "",
             f"Run: `{run_folder}`. Verified {datetime.now().astimezone().isoformat(timespec='seconds')} by `verifier.py` "
             "(code only, no model). Skipped: run metadata above the first section and the Investment Advisor's thesis.", "",
             f"**{len(marks)} numbers: {counts['Correct']} Correct, {counts['Wrong']} Wrong, {counts['Unsupported']} Unsupported.**", ""]
    if any(row["mark"] != "Missing" for row in core):
        table += ["Core claims (Lab 03 template):", "", "| Core claim | Item | Mark | Mark id |", "| --- | --- | --- | --- |"]
        table += [f"| {r['claim']} | {r['item']} | {r['mark']} | {r['id']} |" for r in core] + [""]
    table += ["| Id | Section | Item | Number | Mark | Filing value | Why / arithmetic | Source (tag or line) |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    cell = lambda s: str(s or "").replace("|", "\\|").replace("\n", " ")
    table += [f"| {m['id']} | {cell(m['section'])} | {cell(m['item'])} | {cell(m['number'])} | **{m['mark']}** | "
              f"{cell(m['correct'])} | {cell(m['why'])} | {cell(m['source'])} |" for m in marks]
    table += ["", "A code check cannot tell whether a number on the cited line is for the period and definition the "
              "sentence claims. Human audit is still needed.", ""]
    return first + "\n" + "\n".join(table) + "\n" + rest


def summary(marks):
    counts = {k: sum(m["mark"] == k for m in marks) for k in ("Correct", "Wrong", "Unsupported")}
    return f"{len(marks)} numbers: {counts['Correct']} Correct, {counts['Wrong']} Wrong, {counts['Unsupported']} Unsupported"


def verify_run(folder, out_root=None, report_name="report.md"):
    """Verify one saved run. Writes a new timestamped folder; never overwrites an earlier result."""
    run = Run(folder, report_name)
    marks = Verifier(run).verify()
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S-%f")
    out = Path(out_root or Path(folder) / "verified") / stamp
    out.mkdir(parents=True, exist_ok=False)
    (out / "verified_report.md").write_text(render(run.report, marks, Path(folder).name), encoding="utf-8")
    (out / "marks.json").write_text(json.dumps({"run": str(folder), "marks": marks, "core_claims": core_summary(marks)},
                                               indent=2), encoding="utf-8")
    return out, marks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_folder", help="Saved run folder with report.md, facts.json and filing texts")
    args = parser.parse_args(argv)
    print("Node: verifier", flush=True)
    try:
        out, marks = verify_run(args.run_folder)
    except (OSError, ValueError, KeyError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1
    print(f"Verified report: {out / 'verified_report.md'}")
    print(summary(marks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
