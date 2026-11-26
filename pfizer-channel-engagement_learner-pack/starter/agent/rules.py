"""Deterministic business rules used by the agent tools."""

from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
from typing import Optional

from config import (
    BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS,
    CFA_TOPUP_MONTHS,
    DAYS_PER_MONTH,
    DUPLICATE_NEAR_QTY_MIN_PACKS,
    DUPLICATE_NEAR_QTY_TOLERANCE_PCT,
    SCHEME_LOOKBACK_MONTHS,
    SCHEME_MIN_ORDER_MULTIPLE,
    SCHEME_REGISTER,
    SCHEME_TIER_A_SKUS,
    SCHEME_TIER_B_SKUS,
    SCHEME_VALID_FROM_DAY,
    EXPIRY_CLAIM_WINDOW_DAYS as CLAIM_SUBMISSION_WINDOW_DAYS,
    FOC_CAP_PCT,
    MIN_REMAINING_SHELF_LIFE_DAYS,
    MIN_REMAINING_SHELF_LIFE_PCT,
)


def assess_expiry_claim_window(
    claim_type: str, claim_date: str | date, expiry_date: str | date,
    limit_days: int = CLAIM_SUBMISSION_WINDOW_DAYS,
) -> dict:
    """Assess the case-discussion 90-day window using the batch-master expiry.

    Dates determine whether the claim is near-expiry or expired; the supplied
    claim label is only reported as a mismatch signal, never trusted as truth.
    """
    if not isinstance(limit_days, int) or isinstance(limit_days, bool) or limit_days < 0:
        raise ValueError("limit_days must be a non-negative integer")
    normalized_label = (claim_type or "").strip().casefold().replace(" ", "_")
    # Other claim classes, such as short supply or breakage, do not use this expiry window.
    if normalized_label not in {"near_expiry", "expired"}:
        return {"status": "not_applicable", "reason": "Claim is not an expiry claim"}

    claim_day = parse_date(claim_date)
    expiry_day = parse_date(expiry_date)
    elapsed_days = (claim_day - expiry_day).days
    derived_type = "near_expiry" if elapsed_days < 0 else "expired"
    label_aliases = {"near_expiry": "near_expiry", "expired": "expired"}
    label_mismatch = (
        elapsed_days != 0
        and normalized_label in label_aliases
        and label_aliases[normalized_label] != derived_type
    )
    within_window = -limit_days <= elapsed_days <= limit_days
    return {
        "status": "within_window" if within_window else "outside_window",
        "derived_claim_type": derived_type,
        "claim_type_label_mismatch": label_mismatch,
        "elapsed_days": elapsed_days,
        "limit_days": limit_days,
        "reason": (
            "Within the configured window based on the batch-master expiry date"
            if within_window
            else "Outside the configured window based on the batch-master expiry date"
        ),
    }


def assess_transit_claim_window(
    claim_date: str | date,
    invoice_date: str | date,
    limit_days: int = BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS,
) -> dict:
    """Check that a transit breakage or short-supply claim is filed within 7 days."""
    if not isinstance(limit_days, int) or isinstance(limit_days, bool) or limit_days < 0:
        raise ValueError("limit_days must be a non-negative integer")
    claim_day = parse_date(claim_date)
    invoice_day = parse_date(invoice_date)
    elapsed_days = (claim_day - invoice_day).days
    within_window = 0 <= elapsed_days <= limit_days
    return {
        "status": "within_window" if within_window else "outside_window",
        "elapsed_days": elapsed_days,
        "limit_days": limit_days,
        "reason": (
            "Filed within the configured number of days after invoice"
            if within_window
            else "Filed before invoice or after the configured filing window"
        ),
    }


def is_below_min_days_to_expiry(
    invoice_date: str | date,
    expiry_date: str | date,
) -> bool:
    """Return True when fewer than the configured 60 days remain on invoice date."""
    remaining_days = (parse_date(expiry_date) - parse_date(invoice_date)).days
    return remaining_days < MIN_REMAINING_SHELF_LIFE_DAYS


def _parse_nonnegative_amount(value: str | int | float | Decimal, label: str) -> Decimal:
    """Parse money inputs without binary float arithmetic or negative values."""
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"{label} must be a valid amount") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return amount


def free_goods_cap_check(
    free_value: str | int | float | Decimal,
    invoiced_value: str | int | float | Decimal,
) -> dict:
    """Compare free-goods value with the configured 3% of invoiced value cap."""
    free_amount = _parse_nonnegative_amount(free_value, "free_value")
    invoice_amount = _parse_nonnegative_amount(invoiced_value, "invoiced_value")
    cap_amount = invoice_amount * Decimal(str(FOC_CAP_PCT)) / Decimal("100")
    excess = max(Decimal("0"), free_amount - cap_amount)
    return {
        "status": "above_cap" if excess > 0 else "within_cap",
        "free_value": free_amount,
        "invoiced_value": invoice_amount,
        "cap_pct": FOC_CAP_PCT,
        "cap_value": cap_amount,
        "excess_value": excess,
    }


def claim_value_at_pts(
    qty: str | int | float | Decimal,
    pts: str | int | float | Decimal,
) -> Decimal:
    """Calculate claim value at PTS using exact decimal pack and price values."""
    quantity = _parse_nonnegative_amount(qty, "qty")
    price = _parse_nonnegative_amount(pts, "pts")
    return quantity * price


def compare_claim_value_at_pts(
    qty: str | int | float | Decimal,
    pts: str | int | float | Decimal,
    claim_value: str | int | float | Decimal,
) -> dict:
    """Flag PTS-value mismatches for human review; never decide claim entitlement."""
    calculated = claim_value_at_pts(qty, pts)
    claimed = _parse_nonnegative_amount(claim_value, "claim_value")
    return {
        "status": "match" if claimed == calculated else "mismatch_needs_person",
        "calculated_value_inr": calculated,
        "claim_value_inr": claimed,
        "variance_inr": claimed - calculated,
        "policy_reference": "CO-POL-014 §5.7",
    }


def compare_claim_quantity(claimed_qty: str, recorded_qty: str) -> dict:
    """Compare a claimed quantity with a recorded quantity without rounding."""
    claimed = parse_pack_quantity(claimed_qty)
    recorded = parse_pack_quantity(recorded_qty)
    return {
        "status": "within_recorded_quantity" if claimed <= recorded else "exceeds_recorded_quantity",
        "claimed_quantity": int(claimed) if claimed == claimed.to_integral_value() else str(claimed),
        "recorded_quantity": int(recorded) if recorded == recorded.to_integral_value() else str(recorded),
    }


def classify_prior_claim(current_qty: Decimal, prior_qty: Decimal, prior_status: str,
                         prior_has_credit_note: bool = True) -> Optional[str]:
    """Classify an earlier claim on the same stockist and batch (CO-POL-014 §5.6).

    Returns "repeat_of_credited" (same packs already credited), "repeat_of_pending" (same packs,
    earlier claim not yet settled), "near_repeat" (within the configured tolerance), or None.
    Rejected earlier claims moved no money and are ignored.
    """
    status = (prior_status or "").strip().casefold()
    if status not in {"credited", "pending"}:
        return None
    difference = abs(current_qty - prior_qty)
    if difference == 0:
        if status == "credited" and prior_has_credit_note:
            return "repeat_of_credited"
        return "repeat_of_pending"
    tolerance = max(
        Decimal(str(DUPLICATE_NEAR_QTY_MIN_PACKS)),
        current_qty * Decimal(str(DUPLICATE_NEAR_QTY_TOLERANCE_PCT)) / Decimal("100"),
    )
    return "near_repeat" if difference <= tolerance else None


_QUARTER = re.compile(r"^FY(\d{2})\s*Q([1-4])$", re.IGNORECASE)
_SCHEME = re.compile(r"^QS-FY(\d{2})Q([1-4])-([AB])$", re.IGNORECASE)


def fiscal_quarter_of(day: date) -> tuple[int, int]:
    """(two-digit FY, quarter) for an Indian April-March year: 15 Nov 2024 -> (25, 3)."""
    fy = day.year + 1 if day.month >= 4 else day.year
    quarter = (day.month - 4) % 12 // 3 + 1
    return fy % 100, quarter


def quarter_bounds(fy: int, quarter: int) -> tuple[date, date]:
    """First and last day of a fiscal quarter."""
    start_month = (3 + 3 * (quarter - 1)) % 12 + 1
    start_year = 2000 + fy - 1 if quarter < 4 else 2000 + fy
    end_month = start_month + 2
    end = date(start_year, end_month, monthrange(start_year, end_month)[1])
    return date(start_year, start_month, 1), end


def parse_quarter(text: str) -> tuple[int, int]:
    """Parse "FY27 Q1" or a scheme code "QS-FY27Q1-A" into (fy, quarter)."""
    value = (text or "").strip().upper()
    match = _QUARTER.match(value) or _SCHEME.match(value)
    if not match:
        raise ValueError(f"Not a quarter or scheme code: {text!r}")
    return int(match.group(1)), int(match.group(2))


def scheme_validity(code: str) -> tuple[date, date]:
    """Annexure B: valid from the 22nd of the quarter's last month to that month's last day."""
    fy, quarter = parse_quarter(code)
    _, end = quarter_bounds(fy, quarter)
    return date(end.year, end.month, SCHEME_VALID_FROM_DAY), end


def scheme_skus(code: str) -> tuple[str, ...]:
    """The SKUs a scheme code covers: Tier A or Tier B list from Annexure B."""
    match = _SCHEME.match((code or "").strip().upper())
    if not match:
        raise ValueError(f"Not a scheme code: {code!r}")
    return SCHEME_TIER_A_SKUS if match.group(3) == "A" else SCHEME_TIER_B_SKUS


def expected_free_packs(code: str, invoiced_packs: Decimal) -> Decimal:
    """Free packs the scheme terms allow: invoiced x (free per 10) / 10, rounded half up."""
    key = (code or "").strip().upper()
    if key not in SCHEME_REGISTER:
        raise ValueError(f"Scheme code not in the Annexure B register: {code!r}")
    free_per_ten = SCHEME_REGISTER[key][1]
    return (Decimal(invoiced_packs) * free_per_ten / 10).quantize(Decimal("1"), rounding="ROUND_HALF_UP")


def scheme_order_eligibility(order_packs: Decimal, previous_months_packs: list[Decimal]) -> dict:
    """Annexure B: an order qualifies at >= 1.5 x the average monthly purchase of the previous 3 months.

    `previous_months_packs` holds the stockist's purchases of the SKU in each of the previous
    months (zero for a month with none). No purchase history at all cannot be judged.
    """
    if len(previous_months_packs) != SCHEME_LOOKBACK_MONTHS:
        raise ValueError(f"Expected {SCHEME_LOOKBACK_MONTHS} months of purchases")
    average = sum(previous_months_packs, Decimal("0")) / SCHEME_LOOKBACK_MONTHS
    if average == 0:
        return {"status": "no_history", "average": average, "threshold": Decimal("0"), "multiple": None}
    threshold = average * Decimal(str(SCHEME_MIN_ORDER_MULTIPLE))
    return {
        "status": "eligible" if Decimal(order_packs) >= threshold else "below_threshold",
        "average": average,
        "threshold": threshold,
        "multiple": Decimal(order_packs) / average,
    }


def dispatch_deadlines(expiry: date, total_shelf_life_days: int) -> dict:
    """Last dates a batch can leave the C&F (CO-POL-014 §7.1-7.2).

    - block: under 60 days to expiry it cannot be dispatched and is written off (§7.1-7.2).
    - short_shelf_life: below 60% of total shelf life a stockist may refuse it (§7.1).
    """
    if total_shelf_life_days <= 0:
        raise ValueError("Total shelf life must be positive")
    keep_days = round(total_shelf_life_days * MIN_REMAINING_SHELF_LIFE_PCT / 100)
    return {
        "block": expiry - timedelta(days=MIN_REMAINING_SHELF_LIFE_DAYS),
        "short_shelf_life": expiry - timedelta(days=keep_days),
    }


def fefo_packs_at_risk(batches: list[tuple[date, Decimal]], monthly_outward: Decimal,
                       as_of: date, deadline_key: str, deadlines: list[dict]) -> list[Decimal]:
    """Packs of each batch that cannot ship before its deadline if the C&F picks first-expiry-first-out.

    `batches` and `deadlines` are in the same order, sorted by expiry. Stock leaves at the current
    rolling outward rate; earlier-expiry batches go first (C&F clause 6.3), and only packs that can still
    ship use capacity. Returns whole packs at risk per batch.
    """
    if monthly_outward < 0:
        raise ValueError("Outward rate cannot be negative")
    per_day = Decimal(monthly_outward) / Decimal(str(DAYS_PER_MONTH))
    ahead = Decimal("0")
    at_risk = []
    for (expiry, packs), deadline in zip(batches, deadlines):
        days = max((deadline[deadline_key] - as_of).days, 0)
        can_ship = min(max(per_day * days - ahead, Decimal("0")), Decimal(packs))
        at_risk.append((Decimal(packs) - can_ship).quantize(Decimal("1"), rounding="ROUND_HALF_UP"))
        # Only packs that actually ship use outward capacity; blocked or refused stock does not.
        ahead += can_ship
    return at_risk


def months_of_cover(packs: Decimal, monthly_outward: Decimal) -> dict:
    """Months of stock at the current outward rate, against the 2-month top-up norm (§2.2)."""
    if packs <= 0:
        return {"status": "out_of_stock", "months": Decimal("0")}
    if monthly_outward <= 0:
        return {"status": "no_outward", "months": None}
    months = Decimal(packs) / Decimal(monthly_outward)
    return {"status": "above_norm" if months > Decimal(str(CFA_TOPUP_MONTHS)) else "within_norm", "months": months}


def shift_month(month: date, offset: int) -> date:
    """Return the first day of a month shifted by offset calendar months."""
    if not isinstance(month, date):
        raise ValueError("month must be a date")
    if isinstance(offset, bool) or not isinstance(offset, int):
        raise ValueError("offset must be an integer number of months")

    month_index = month.year * 12 + (month.month - 1) + offset
    year, zero_based_month = divmod(month_index, 12)
    if not 1 <= year <= 9999:
        raise ValueError("shifted month is outside the supported date range")
    return date(year, zero_based_month + 1, 1)


def parse_date(value: str | date) -> date:
    """Parse a date object or a project CSV date in DD-MM-YYYY format."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Date is missing")

    # The data pack mixes these date formats across its CSV extracts.
    supported_formats = ("%d-%m-%Y", "%Y-%m-%d", "%d-%b-%Y")
    for date_format in supported_formats:
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except ValueError:
            continue
    raise ValueError(
        "Date must use DD-MM-YYYY, YYYY-MM-DD, or DD-Mon-YYYY format: "
        f"{value!r}"
    )


_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def parse_expiry_month(value: str) -> tuple[int, int]:
    """Return (year, month) from a full date or a month-only expiry such as "Sep 2026", "09/2026" or "Oct-26".

    Pharma packs print expiry as a month; batch-master expiry is the month end, so month-level
    comparison is the exact test.
    """
    text = (value or "").strip()
    try:
        full = parse_date(text)
        return full.year, full.month
    except ValueError:
        pass
    named = re.fullmatch(r"([A-Za-z]{3})[A-Za-z]*[\s\-/.,']*(\d{2}|\d{4})", text)
    numeric = re.fullmatch(r"(\d{1,2})\s*[/\-.]\s*(\d{2}|\d{4})", text)
    if named and named.group(1).casefold() in _MONTHS:
        month, year = _MONTHS[named.group(1).casefold()], int(named.group(2))
    elif numeric and 1 <= int(numeric.group(1)) <= 12:
        month, year = int(numeric.group(1)), int(numeric.group(2))
    else:
        raise ValueError(f"Expiry is not a recognisable date or month: {value!r}")
    return (year + 2000 if year < 100 else year), month


def parse_amount(value: str) -> Decimal:
    """Parse a rupee amount such as "Rs 64,400", "₹57,477.00" or "57477"."""
    cleaned = re.sub(r"(?i)(rs\.?|inr|₹|/-)", "", str(value or "")).replace(",", "").strip()
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Amount is not a number: {value!r}") from exc
    if amount < 0:
        raise ValueError(f"Amount cannot be negative: {value!r}")
    return amount


_PASTED_QTY = re.compile(r"^\s*([\d,]+(?:\.\d+)?)\s*(?:strips?|packs?|pcs|pieces|bottles?|tubes?|tabs?|tablets?|caps?|capsules?|units?|nos\.?|boxes?)?\s*$", re.IGNORECASE)
_CODE_SHAPES = {"sku_code": re.compile(r"^PFL-?\d{4}$", re.IGNORECASE), "stockist_code": re.compile(r"^STK-?\d{4}$", re.IGNORECASE)}


def parse_pasted_quantity(value: str) -> Decimal:
    """A pasted quantity may carry its unit ("80 strips", "612 bottles"); register quantities never do."""
    match = _PASTED_QTY.match(value or "")
    if not match:
        raise ValueError(f"Pasted quantity is not a number of packs: {value!r}")
    return parse_pack_quantity(match.group(1))


def compare_pasted_fields(pasted: dict, register: dict) -> list[dict]:
    """Compare fields read from pasted text with the register values; return one row per compared field.

    `register` holds claim_no context values: stockist_code, sku_code, batch_no, qty, claim_value_inr,
    invoice_ref, expiry. Each row is {field, pasted, register, match}; unparseable pasted values give
    match=None so a person sees them.
    """
    rows = []
    for field in ("stockist_code", "sku_code", "batch_no", "invoice_ref"):
        if pasted.get(field) and register.get(field):
            shape = _CODE_SHAPES.get(field)
            if shape and not shape.match(pasted[field].strip()):
                # A product or stockist *name* ("Sitagliptin 100") is not a code; it can't be compared exactly.
                continue
            same = pasted[field].strip().upper().replace("-", "") == register[field].strip().upper().replace("-", "")
            rows.append({"field": field, "pasted": pasted[field], "register": register[field], "match": same})
    comparisons = (
        ("qty", parse_pasted_quantity, parse_pack_quantity),
        ("claim_value", parse_amount, parse_amount),
        ("expiry_claimed", parse_expiry_month, parse_expiry_month),
    )
    register_keys = {"qty": "qty", "claim_value": "claim_value_inr", "expiry_claimed": "expiry"}
    for field, parse_pasted, parse_register in comparisons:
        pasted_value, register_value = pasted.get(field), register.get(register_keys[field])
        if not pasted_value or not register_value:
            continue
        try:
            same = parse_pasted(pasted_value) == parse_register(register_value)
        except ValueError:
            same = None
        rows.append({"field": field, "pasted": pasted_value, "register": register_value, "match": same})
    return rows


def remaining_shelf_life_percent(
    invoice_date: str | date,
    mfg_date: str | date,
    expiry_date: str | date,
) -> float:
    """Return the percentage of total shelf life remaining on invoice date.

    CO-POL-014 §7.1 defines the RSL measurement date as invoice date.
    """
    invoice = parse_date(invoice_date)
    manufactured = parse_date(mfg_date)
    expiry = parse_date(expiry_date)

    total_life_days = (expiry - manufactured).days
    if total_life_days <= 0:
        raise ValueError("Expiry date must be after manufacture date")
    if invoice < manufactured:
        raise ValueError("Invoice date is before manufacture date")

    remaining_days = (expiry - invoice).days
    return (remaining_days / total_life_days) * 100


def is_below_minimum_shelf_life(
    invoice_date: str | date,
    mfg_date: str | date,
    expiry_date: str | date,
) -> bool:
    """Return True when remaining shelf life is strictly below the 60% rule."""
    return (
        remaining_shelf_life_percent(invoice_date, mfg_date, expiry_date)
        < MIN_REMAINING_SHELF_LIFE_PCT
    )


def normalize_cfa_code(value: str) -> str:
    """Normalize CFA codes so formatting variants compare as the same location."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("CFA code is missing")
    # Some rows spell the same CFA with and without punctuation, e.g. CF-E01/CFE01.
    normalized = re.sub(r"[^A-Z0-9]", "", value.strip().upper())
    if not normalized:
        raise ValueError("CFA code is invalid")
    return normalized


def parse_pack_quantity(value: str) -> Decimal:
    """Parse a non-negative pack quantity, allowing thousands separators."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Pack quantity is missing")
    try:
        # Decimal avoids rounding stock quantities during validation.
        quantity = Decimal(value.strip().replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError(f"Pack quantity is invalid: {value!r}") from exc
    if not quantity.is_finite() or quantity < 0:
        raise ValueError(f"Pack quantity must be finite and non-negative: {value!r}")
    return quantity
