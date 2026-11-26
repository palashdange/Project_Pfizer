"""Batch mode: route every register claim in a period in code and total the rupees by route.

Definitions (all sums in Decimal, from expiry_claims.csv):
- at stake: claim_value_inr, or qty_claimed x SKU PTS when the claim value is blank (§5.7).
- caught: register status Credited, pilot route REJECT -> credit_value_inr the pilot would have stopped.
- leakage: the invalid part of "caught". Window (§5.2) or repeat (§5.6) failures make the whole credit
  invalid; a claim that only exceeds invoiced + free packs (§5.5) is invalid only for the excess
  packs x PTS. This is the like-for-like comparison with discovery/sizing.py.
- at risk: register status Credited, pilot route NEEDS_PERSON -> credit_value_inr a person should
  have checked first. Counted as at risk, never as saved.
- would block: register status Pending, pilot route REJECT -> claim value not yet credited.
Annualised = period total x 12 / months in the period.
"""

from collections import Counter
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Optional

from agent import data
from agent.graph import at_stake_inr, review_claim
import re
from calendar import month_abbr
from datetime import date

from agent.rules import fiscal_quarter_of, parse_date

ROUTES = ("RECOMMEND_CREDIT", "REJECT", "NEEDS_PERSON")


def _amount(value) -> Optional[Decimal]:
    text = str(value or "").replace(",", "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _month_key(claim: dict) -> Optional[str]:
    try:
        day = parse_date(claim.get("claim_date", ""))
    except ValueError:
        return None
    return f"{day.year:04d}-{day.month:02d}"


@lru_cache(maxsize=1)
def _all_reviews() -> tuple[dict, ...]:
    """Route every register claim once per process; the register is a static extract."""
    rows = []
    for claim in data.rows_for("claim") or []:
        review = review_claim(claim["claim_no"])
        # Failed checks first, so a rejected claim shows the rule that rejected it.
        not_passed = [(name, item) for name, item in review["checks"].items() if item.get("status") != "pass"]
        not_passed.sort(key=lambda pair: pair[1].get("status") != "fail")
        problems = [
            f"{name}: {item.get('reason', '')} ({item.get('policy_clause') or 'no clause'})"
            for name, item in not_passed
        ]
        stake = at_stake_inr(claim, data.get_sku(claim.get("sku_code", "")))
        credit = _amount(claim.get("credit_value_inr"))
        failed = {name for name, item in review["checks"].items() if item.get("status") == "fail"}
        leakage = None
        if review["route"] == "REJECT" and credit is not None:
            if failed & {"window", "duplicate"}:
                leakage = credit
            else:
                quantity = review["checks"].get("quantity", {})
                excess = _amount(quantity.get("claimed_quantity")) or Decimal("0")
                excess -= _amount(quantity.get("recorded_quantity")) or Decimal("0")
                pts = _amount((data.get_sku(claim.get("sku_code", "")) or {}).get("pts_inr")) or Decimal("0")
                leakage = min(credit, max(excess, Decimal("0")) * pts)
        rows.append({
            "claim_no": claim["claim_no"],
            "month": _month_key(claim),
            "claim_date": claim.get("claim_date"),
            "claim_type": claim.get("claim_type"),
            "register_status": claim.get("status"),
            "route": review["route"],
            "at_stake_inr": stake,
            "credit_value_inr": credit,
            "leakage_inr": leakage,
            "first_problem": problems[0] if problems else "",
            "problem_count": len(problems),
            "source": f"{claim.get('source_file')}:{claim.get('source_row')}",
        })
    return tuple(rows)


def available_months() -> list[str]:
    return sorted({row["month"] for row in _all_reviews() if row["month"]})


_FY = re.compile(r"^FY(\d{2})$")
_FYQ = re.compile(r"^FY(\d{2})\s*Q([1-4])$")


def _fiscal(month: str) -> tuple[int, int]:
    """(two-digit FY, quarter) of a "YYYY-MM" month, Indian April-March year."""
    year, mon = (int(part) for part in month.split("-"))
    return fiscal_quarter_of(date(year, mon, 1))


def _months_in(period: str, months: list[str]) -> list[str]:
    """Register months inside a period: "YYYY-MM", a financial year "FY26", or a quarter "FY26 Q3"."""
    text = (period or "").strip().upper()
    if text in months:
        return [text]
    if match := _FYQ.match(text):
        fy, quarter = int(match.group(1)), int(match.group(2))
        return [m for m in months if _fiscal(m) == (fy, quarter)]
    if match := _FY.match(text):
        return [m for m in months if _fiscal(m)[0] == int(match.group(1))]
    return []


def _span(months: list[str]) -> str:
    """"Apr 2025–Mar 2026" or "Apr–Sep 2026" for a run of "YYYY-MM" months."""
    first, last = months[0], months[-1]
    label = lambda m: f"{month_abbr[int(m[5:])]} {m[:4]}"  # noqa: E731
    if first == last:
        return label(first)
    if first[:4] == last[:4]:
        return f"{month_abbr[int(first[5:])]}–{label(last)}"
    return f"{label(first)}–{label(last)}"


@lru_cache(maxsize=1)
def available_periods() -> dict:
    """Years, quarters and months with claims, newest first, for the batch picker.

    Counted from the register's claim dates only, so the picker loads without routing any claim.
    """
    counts = Counter(_month_key(claim) for claim in data.rows_for("claim") or [])
    counts.pop(None, None)
    months = sorted(counts)
    groups = {"years": {}, "quarters": {}}
    for month in months:
        fy, quarter = _fiscal(month)
        groups["years"].setdefault(f"FY{fy:02d}", []).append(month)
        groups["quarters"].setdefault(f"FY{fy:02d} Q{quarter}", []).append(month)

    def entries(group: dict, full_length: int) -> list[dict]:
        out = []
        for value, members in sorted(group.items(), key=lambda kv: kv[1][0], reverse=True):
            partial = len(members) < full_length and members[-1] == months[-1]
            out.append({"value": value, "span": _span(members) + (" so far" if partial else ""),
                        "months": len(members), "claims": sum(counts[m] for m in members)})
        return out

    return {
        "all": {"value": "", "span": _span(months), "months": len(months), "claims": sum(counts.values())},
        "years": entries(groups["years"], 12),
        "quarters": entries(groups["quarters"], 3),
        "months": [{"value": m, "span": _span([m]), "months": 1, "claims": counts[m]} for m in reversed(months)],
    }


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def run_batch(month: Optional[str] = None, include_claims: Optional[bool] = None) -> dict:
    """Totals for a period, or for every month in the register when month is None.

    `month` may be one month ("YYYY-MM"), a financial year ("FY26") or a quarter ("FY26 Q3").
    Annualised figures divide by the register months inside the period, so a part year is not inflated.
    """
    months = available_months()
    selected = months if month is None else _months_in(month, months)
    if not selected:
        raise ValueError(f"No claims in the register for month {month!r}. Available: {months[0]} to {months[-1]}.")
    chosen = set(selected)
    rows = [row for row in _all_reviews() if row["month"] in chosen]
    period_months = len(selected)
    zero = Decimal("0")

    def total(predicate, field):
        return sum((row[field] for row in rows if predicate(row) and row[field] is not None), zero)

    credited = lambda row: (row["register_status"] or "").casefold() == "credited"
    pending = lambda row: (row["register_status"] or "").casefold() == "pending"
    figures = {
        "caught": total(lambda r: credited(r) and r["route"] == "REJECT", "credit_value_inr"),
        "leakage": total(lambda r: credited(r) and r["route"] == "REJECT", "leakage_inr"),
        "at_risk": total(lambda r: credited(r) and r["route"] == "NEEDS_PERSON", "credit_value_inr"),
        "would_block": total(lambda r: pending(r) and r["route"] == "REJECT", "at_stake_inr"),
        "recommend_credit": total(lambda r: r["route"] == "RECOMMEND_CREDIT", "at_stake_inr"),
    }
    annual = {key: value * 12 / period_months for key, value in figures.items()}
    counts = Counter(row["route"] for row in rows)
    result = {
        "period": (f"{month.strip().upper()} ({_span(selected)})" if month and month.strip().upper() not in months
                   else month or f"{months[0]} to {months[-1]}"),
        "months": period_months,
        "claims_reviewed": len(rows),
        "route_counts": {route: counts.get(route, 0) for route in ROUTES},
        "period_inr": {key: _money(value) for key, value in figures.items()},
        "annualised_inr": {key: _money(value) for key, value in annual.items()},
        "missing_value_claims": sum(1 for row in rows if row["at_stake_inr"] is None),
        "definitions": {
            "caught": "Already credited in the register; the pilot would reject (credit_value_inr).",
            "leakage": "The invalid part of caught: whole credit for window (§5.2) or repeat (§5.6) failures; only excess packs x PTS for over-quantity (§5.5).",
            "at_risk": "Already credited; the pilot sends it to a person first (credit_value_inr). At risk, not saved.",
            "would_block": "Still pending; the pilot would reject (claim value).",
            "recommend_credit": "The pilot recommends credit (claim value).",
        },
        "source": "expiry_claims.csv, routed by the same checks as /api/ask; annualised = period x 12 / months.",
        "available_months": months,
    }
    # Claim lists for a month or a quarter; a year or more is summarised only.
    if include_claims if include_claims is not None else (month is not None and period_months <= 3):
        result["claims"] = [
            {**row, "at_stake_inr": _money(row["at_stake_inr"]) if row["at_stake_inr"] is not None else None,
             "credit_value_inr": _money(row["credit_value_inr"]) if row["credit_value_inr"] is not None else None,
             "leakage_inr": _money(row["leakage_inr"]) if row["leakage_inr"] is not None else None}
            for row in sorted(rows, key=lambda r: (r["route"] != "REJECT", r["route"] != "NEEDS_PERSON",
                                                   -(r["at_stake_inr"] or 0)))
        ]
    return result
