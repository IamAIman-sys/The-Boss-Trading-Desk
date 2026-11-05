"""Optional market prices and statement comparisons; SEC remains authoritative."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from dotenv import dotenv_values
import requests

ROOT = Path(__file__).resolve().parent
BASE = "https://api.financialdatasets.ai"
FIELDS = {
    "revenue": ("income_statements", "revenue"),
    "operating_income": ("income_statements", "operating_income"),
    "net_income": ("income_statements", "net_income"),
    "diluted_eps": ("income_statements", "earnings_per_share_diluted"),
    "equity": ("balance_sheets", "shareholders_equity"),
    "long_term_debt": ("balance_sheets", "non_current_debt"),
    "current_debt": ("balance_sheets", "current_debt"),
    "cfo": ("cash_flow_statements", "net_cash_flow_from_operations"),
    "capex": ("cash_flow_statements", "capital_expenditure"),
}
DEFINITION_NOTES = {
    "long_term_debt": "Check debt and lease scope against the selected SEC tag.",
    "current_debt": "Vendor current debt can include short-term borrowing beyond the current portion of long-term debt.",
    "capex": "Check cash-flow sign and asset scope against additions to property and equipment; no sign conversion is applied.",
}


class FinancialDatasetsError(ValueError):
    """A safe error that contains no key or provider response body."""


def number(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise FinancialDatasetsError("Missing or invalid numeric value.") from None
    if not result.is_finite():
        raise FinancialDatasetsError("Non-finite numeric value.")
    return result


def historical_date(value):
    try:
        day = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise FinancialDatasetsError("Price date must use YYYY-MM-DD.") from None
    if day.isoformat() != value:
        raise FinancialDatasetsError("Price date must use YYYY-MM-DD.")
    if day >= datetime.now(ZoneInfo("America/New_York")).date():
        raise FinancialDatasetsError("Choose a completed historical date before today in New York.")
    return day


def add_arguments(parser):
    parser.add_argument("--fetch-price-date", help="Fetch the closing price for this exact date (YYYY-MM-DD)")
    parser.add_argument("--compare-financial-datasets", action="store_true",
                        help="Compare main-company and peer annual SEC facts with Financial Datasets")


def options(args):
    if args.fetch_price_date:
        historical_date(args.fetch_price_date)
        if any(getattr(args, name, None) is not None for name in ("price", "price_date", "price_source")):
            raise FinancialDatasetsError("Use --fetch-price-date or manual --price inputs, not both.")
    if getattr(args, "step", None) and args.fetch_price_date and args.step != 5:
        raise FinancialDatasetsError("Use --fetch-price-date with a full run or --step 5.")
    if getattr(args, "step", None) and args.compare_financial_datasets and args.step not in (4, 7):
        raise FinancialDatasetsError("Use --compare-financial-datasets with a full run, --step 4, or --step 7.")
    return {"fd_client": FinancialDatasetsClient() if args.fetch_price_date or args.compare_financial_datasets else None,
            "fetch_price_date": args.fetch_price_date, "compare_financial_datasets": args.compare_financial_datasets}


class FinancialDatasetsClient:
    def __init__(self, env_path=ROOT / ".env", session=None):
        env = dotenv_values(env_path, interpolate=False)
        key, ua = env.get("FINANCIAL_DATASETS_API_KEY", ""), env.get("SEC_USER_AGENT", "")
        for name, value in (("FINANCIAL_DATASETS_API_KEY", key), ("SEC_USER_AGENT", ua)):
            if not value or not value.strip() or value == "paste-here" or any(c in value for c in "\r\n"):
                raise FinancialDatasetsError(f"Set {name} in .env beside the scripts.")
        self._key, self._ua = key, ua
        self.session = session or requests.Session()
        self.cache = {}

    def get(self, path, params):
        if path not in ("/prices", "/financials"):
            raise FinancialDatasetsError("Unsupported Financial Datasets endpoint.")
        url = BASE + path + "?" + urlencode(params)
        if url in self.cache:
            return self.cache[url], url
        try:
            response = self.session.get(BASE + path, params=params,
                                        headers={"X-API-KEY": self._key, "User-Agent": self._ua},
                                        timeout=(10, 30), allow_redirects=False)
        except requests.RequestException:
            raise FinancialDatasetsError("Financial Datasets connection failed; retry the requested step.") from None
        if response.status_code != 200:
            hints = {401: "Check the API key.", 402: "Check the account plan or credits.",
                     403: "Check endpoint permissions.", 429: "Rate limit reached; retry later."}
            raise FinancialDatasetsError(f"Financial Datasets HTTP {response.status_code}. " +
                                         hints.get(response.status_code, "Request failed; no substitute data was used."))
        try:
            payload = response.json(parse_float=Decimal)
        except ValueError:
            raise FinancialDatasetsError("Financial Datasets returned invalid JSON.") from None
        if not isinstance(payload, dict) or payload.get("error"):
            raise FinancialDatasetsError("Financial Datasets returned an invalid response.")
        if payload.get("next_page_url"):
            raise FinancialDatasetsError("Unexpected paginated response; narrow the query before using these data.")
        self.cache[url] = payload
        return payload, url

    def closing_price(self, ticker, requested_date):
        day = historical_date(requested_date)
        # Include the next boundary to support either inclusive or exclusive end dates.
        # Selection below always requires the exact requested day.
        payload, url = self.get("/prices", {"ticker": ticker, "interval": "day",
                                            "start_date": day.isoformat(),
                                            "end_date": (day + timedelta(days=1)).isoformat()})
        rows = payload.get("prices")
        if not isinstance(rows, list):
            raise FinancialDatasetsError("Missing prices list in Financial Datasets response.")
        matches = []
        for row in rows:
            if not isinstance(row, dict):
                raise FinancialDatasetsError("Invalid price record.")
            if str(row.get("time", ""))[:10] == requested_date:
                matches.append(row)
        if len(matches) != 1:
            raise FinancialDatasetsError("No unique closing price for the requested date. Check the trading calendar; no other date was substituted.")
        row = matches[0]
        for symbol in (payload.get("ticker"), row.get("ticker")):
            if symbol and symbol != ticker:
                raise FinancialDatasetsError("Price response ticker differs from the requested ticker.")
        if row.get("currency", "USD") != "USD":
            raise FinancialDatasetsError("The P/E calculator requires a USD price.")
        price = number(row.get("close"))
        if price <= 0:
            raise FinancialDatasetsError("Closing price must be positive.")
        return price, {"provider": "Financial Datasets", "ticker": ticker, "date": requested_date,
                       "source": url, "field": "close", "price_usd": str(price),
                       "retrieved_at": datetime.now(timezone.utc).isoformat(),
                       "adjustment": "Not specified by this endpoint's documentation; verify split and dividend treatment before comparing sources.",
                       "currency_basis": "USD assumed for the requested US listing when the response omits currency."}

    def compare(self, report):
        ticker = report["company"]["ticker"]
        periods = {}
        sources = []
        for period in report["periods"].values():
            if period and period["end"] not in periods:
                payload, url = self.get("/financials", {"ticker": ticker, "period": "annual", "limit": 1,
                                                        "report_period": period["end"]})
                if not isinstance(payload.get("financials"), dict):
                    raise FinancialDatasetsError("Missing financials object in Financial Datasets response.")
                periods[period["end"]] = payload["financials"]
                sources.append(url)
        rows = []
        for concept, (statement, field) in FIELDS.items():
            item = report["facts"][concept]
            for column in ("current", "prior"):
                sec = item[column]
                row = {"concept": concept, "column": column, "vendor_field": field,
                       "sec": sec, "status": "missing", "vendor_value": None}
                if not sec:
                    row["reason"] = "SEC fact is missing."
                    rows.append(row)
                    continue
                candidates = periods.get(sec["end"], {}).get(statement, [])
                if not isinstance(candidates, list):
                    raise FinancialDatasetsError("Invalid financial statement list.")
                candidates = [r for r in candidates if isinstance(r, dict) and r.get("ticker") == ticker
                              and r.get("period") == "annual" and r.get("report_period") == sec["end"]]
                if len(candidates) != 1:
                    row["reason"] = "No unique annual statement for the same ticker and period end."
                else:
                    vendor = candidates[0]
                    row["vendor_source"] = {k: vendor.get(k) for k in (
                        "report_period", "currency", "accession_number", "form_type", "filing_url", "filing_date")}
                    if vendor.get("currency") != "USD":
                        row["reason"] = "Vendor currency is missing or is not USD."
                    else:
                        try:
                            value = number(vendor.get(field))
                            difference = value - number(sec["val"])
                        except FinancialDatasetsError:
                            row["reason"] = "Vendor or SEC value is missing or is not a finite number."
                        else:
                            row.update(vendor_value=str(value), difference_vendor_minus_sec=str(difference),
                                       numeric_match=difference == 0,
                                       status="numeric_match" if difference == 0 else "difference")
                            acc = vendor.get("accession_number")
                            row["same_filing"] = bool(acc and sec.get("accn")) and re.sub(r"\D", "", acc) == re.sub(r"\D", "", sec["accn"])
                            if concept in DEFINITION_NOTES:
                                row.update(status="definition_review", reason=DEFINITION_NOTES[concept])
                rows.append(row)
        return {"ticker": ticker, "provider": "Financial Datasets", "sources": sources,
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "rows": rows,
                "policy": "Exact numeric comparison, no tolerance or sign conversion. Annual period ends must match; vendor start dates are unavailable. Definitions and filing versions can differ. Numeric agreement is not a human audit. SEC facts and calculations remain unchanged."}
