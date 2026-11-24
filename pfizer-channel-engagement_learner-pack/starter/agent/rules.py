"""Deterministic business rules used by the agent tools."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re

from config import (
    BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS,
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
