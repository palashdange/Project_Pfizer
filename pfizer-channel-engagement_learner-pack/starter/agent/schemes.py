"""Quarter-end scheme review (CO-POL-014 §4.2-4.5, Annexure B), all in code.

Unit of review: a fiscal quarter ("FY27 Q1") or one scheme code ("QS-FY27Q1-A").
- Cap (§4.4): free goods at PTS issued in the quarter vs 3% of the quarter's primary sales value.
- Eligibility (Annexure B): each order line with free goods vs 1.5 x the stockist's average monthly
  purchase of that SKU over the previous 3 calendar months. Policy wording: all purchases. The
  non-scheme-only reading is reported as a range because the policy does not define it.
- Validity window, SKU list and free ratio (§4.2, Annexure B).
- Stock norm (§4.5): cannot be checked (no secondary sales data); always needs a person.
Order lines group split-batch rows by invoice and SKU (ordered_qty is on the first row only).
"""

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Optional

from agent import data
from agent.rules import (
    expected_free_packs, fiscal_quarter_of, free_goods_cap_check, parse_date, parse_quarter,
    quarter_bounds, scheme_order_eligibility, scheme_skus, scheme_validity,
)
from config import (
    SCHEME_CAP_POLICY_CLAUSE, SCHEME_LOOKBACK_MONTHS, SCHEME_REGISTER,
    SCHEME_STOCK_NORM_POLICY_CLAUSE, SCHEME_TERMS_POLICY_CLAUSE,
)

EXAMPLES = 5


def _d(value) -> Decimal:
    try:
        return Decimal(str(value or "0").replace(",", "") or "0")
    except InvalidOperation:
        return Decimal("0")


@lru_cache(maxsize=1)
def _order_lines() -> tuple[dict, ...]:
    """Group sales rows into order lines (invoice + SKU), once per process."""
    lines: dict[tuple, dict] = {}
    for row in data.rows_for("sales") or []:
        try:
            day = parse_date(row.get("invoice_date", ""))
        except ValueError:
            continue
        key = (row.get("invoice_no"), row.get("sku_code"))
        line = lines.setdefault(key, {
            "invoice_no": row.get("invoice_no"), "sku_code": row.get("sku_code"),
            "stockist_code": row.get("stockist_code"), "date": day, "ordered": Decimal("0"),
            "invoiced": Decimal("0"), "free": Decimal("0"), "free_value": Decimal("0"),
            "net_value": Decimal("0"), "scheme_code": None, "rows": [],
        })
        line["ordered"] = max(line["ordered"], _d(row.get("ordered_qty")))
        line["invoiced"] += _d(row.get("invoiced_qty"))
        line["free"] += _d(row.get("free_qty"))
        line["free_value"] += _d(row.get("free_qty")) * _d(row.get("pts_inr"))
        line["net_value"] += _d(row.get("net_value_inr"))
        code = (row.get("scheme_code") or "").strip().upper()
        if code and code != "NA":
            line["scheme_code"] = code
        line["rows"].append(row.get("source_row"))
    return tuple(lines.values())


@lru_cache(maxsize=1)
def _monthly_purchases() -> tuple[dict, dict]:
    """Invoiced packs by (stockist, SKU, year, month): all lines, and lines without free goods."""
    every, plain = defaultdict(Decimal), defaultdict(Decimal)
    for line in _order_lines():
        key = (line["stockist_code"], line["sku_code"], line["date"].year, line["date"].month)
        every[key] += line["invoiced"]
        if line["free"] == 0:
            plain[key] += line["invoiced"]
    return dict(every), dict(plain)


def _previous_months(table: dict, line: dict) -> list[Decimal]:
    months = []
    year, month = line["date"].year, line["date"].month
    for _ in range(SCHEME_LOOKBACK_MONTHS):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        months.append(table.get((line["stockist_code"], line["sku_code"], year, month), Decimal("0")))
    return months


def available_quarters() -> list[str]:
    return sorted({"FY%02d Q%d" % fiscal_quarter_of(line["date"]) for line in _order_lines()})


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _cite(lines: list[dict]) -> list[dict]:
    return [{"file": "primary_sales.csv", "source_row": line["rows"][0], "record_id": line["invoice_no"]}
            for line in lines[:EXAMPLES]]


def _check(status: str, reason: str, clause: str, lines: list[dict], **extra) -> dict:
    return {"status": status, "reason": reason, "policy_clause": clause, "evidence_rows": _cite(lines), **extra}


def review_scheme(target: str) -> Optional[dict]:
    """Review one quarter or scheme code; None when it is outside the extract or the register."""
    text = (target or "").strip().upper()
    fy, quarter = parse_quarter(text)
    label = "FY%02d Q%d" % (fy, quarter)
    if label not in available_quarters():
        return None
    is_code = text.startswith("QS-")
    if is_code and text not in SCHEME_REGISTER:
        return None
    start, end = quarter_bounds(fy, quarter)
    in_quarter = [line for line in _order_lines() if start <= line["date"] <= end]
    codes = [text] if is_code else sorted(c for c in SCHEME_REGISTER if parse_quarter(c) == (fy, quarter))
    scheme_lines = [l for l in _order_lines() if l["free"] > 0 and l["scheme_code"] in codes]
    every, plain = _monthly_purchases()

    # §4.4 cap: always the whole quarter (all schemes), by invoice date.
    foc = sum((l["free_value"] for l in in_quarter), Decimal("0"))
    sales = sum((l["net_value"] for l in in_quarter), Decimal("0"))
    cap = free_goods_cap_check(foc, sales)
    pct = (foc / sales * 100) if sales else Decimal("0")
    cap_check = _check(
        "fail" if cap["status"] == "above_cap" else "pass",
        f"{label}: free goods at PTS {_money(foc)} = {pct:.2f}% of primary sales {_money(sales)}; "
        f"cap 3% = {_money(cap['cap_value'])}; above cap {_money(cap['excess_value'])}.",
        SCHEME_CAP_POLICY_CLAUSE, sorted([l for l in in_quarter if l["free"] > 0], key=lambda l: -l["free_value"]),
        foc_value_inr=_money(foc), sales_value_inr=_money(sales), foc_pct=f"{pct:.2f}",
        above_cap_inr=_money(cap["excess_value"]),
    )

    # Annexure B eligibility: policy wording (all purchases), plus the non-scheme reading as a range.
    below, below_plain, no_history = [], [], []
    for line in scheme_lines:
        order = line["ordered"] or line["invoiced"]
        result = scheme_order_eligibility(order, _previous_months(every, line))
        if result["status"] == "no_history":
            no_history.append(line)
        elif result["status"] == "below_threshold":
            below.append(line)
        if scheme_order_eligibility(order, _previous_months(plain, line))["status"] == "below_threshold":
            below_plain.append(line)
    below_value = sum((l["free_value"] for l in below), Decimal("0"))
    plain_value = sum((l["free_value"] for l in below_plain), Decimal("0"))
    scheme_value = sum((l["free_value"] for l in scheme_lines), Decimal("0"))
    eligibility = _check(
        "fail" if below else ("missing" if no_history else "pass"),
        f"{len(below)} of {len(scheme_lines)} order lines with free goods were below 1.5 x the stockist's 3-month "
        f"average purchase; free goods on them {_money(below_value)} of {_money(scheme_value)}. "
        f"Counting only non-scheme purchases: {len(below_plain)} lines, {_money(plain_value)}. "
        f"{len(no_history)} line(s) had no purchase history to judge.",
        SCHEME_TERMS_POLICY_CLAUSE, sorted(below, key=lambda l: -l["free_value"]),
        lines_checked=len(scheme_lines), lines_below=len(below), free_value_below_inr=_money(below_value),
        lines_below_non_scheme_reading=len(below_plain), free_value_below_non_scheme_reading_inr=_money(plain_value),
        lines_without_history=len(no_history),
    )

    outside, wrong_sku, over_ratio = [], [], []
    over_value = Decimal("0")
    for line in scheme_lines:
        valid_from, valid_to = scheme_validity(line["scheme_code"])
        if not valid_from <= line["date"] <= valid_to:
            outside.append(line)
        if line["sku_code"] not in scheme_skus(line["scheme_code"]):
            wrong_sku.append(line)
        allowed = expected_free_packs(line["scheme_code"], line["invoiced"])
        if line["free"] > allowed:
            over_ratio.append(line)
            over_value += (line["free"] - allowed) * (line["free_value"] / line["free"])
    validity = _check(
        "fail" if outside else "pass",
        f"{len(outside)} of {len(scheme_lines)} free-goods lines fell outside the 22nd-to-month-end validity window.",
        SCHEME_TERMS_POLICY_CLAUSE, outside, lines_outside=len(outside))
    sku_list = _check(
        "fail" if wrong_sku else "pass",
        f"{len(wrong_sku)} of {len(scheme_lines)} free-goods lines were on SKUs outside the circular's list.",
        SCHEME_TERMS_POLICY_CLAUSE, wrong_sku, lines_wrong_sku=len(wrong_sku))
    ratio = _check(
        "fail" if over_ratio else "pass",
        f"{len(over_ratio)} of {len(scheme_lines)} lines got more free packs than the scheme ratio allows "
        f"(rounded); excess {_money(over_value)}.",
        SCHEME_TERMS_POLICY_CLAUSE, over_ratio, lines_over_ratio=len(over_ratio), excess_inr=_money(over_value))
    stock_norm = _check(
        "missing",
        "Cannot be checked: secondary sales are not received, so the 2.5-month stock norm is confirmed by the "
        "RSM in discussion only. A person must confirm before the scheme is offered.",
        SCHEME_STOCK_NORM_POLICY_CLAUSE, [])

    checks = {"cap": cap_check, "eligibility": eligibility, "validity_window": validity,
              "sku_list": sku_list, "free_ratio": ratio, "stock_norm": stock_norm}
    route = "SCHEME_NEEDS_REVIEW" if any(c["status"] == "fail" for c in checks.values()) else "SCHEME_WITHIN_POLICY"
    return {
        "target": text if is_code else label, "quarter": label, "scheme_codes": codes,
        "circulars": sorted({SCHEME_REGISTER[c][0] for c in codes}), "route": route, "checks": checks,
    }
