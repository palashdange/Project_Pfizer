from datetime import date, timedelta
from decimal import Decimal

import pytest

from config import (
    BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS,
    CFA_VERIFICATION_WINDOW_WORKING_DAYS,
    CREDIT_NOTE_SLA_DAYS,
    EXPIRY_CLAIM_WINDOW_DAYS,
    FOC_CAP_PCT,
    MIN_REMAINING_SHELF_LIFE_DAYS,
    MIN_REMAINING_SHELF_LIFE_PCT,
)
from agent.rules import (
    classify_prior_claim,
    assess_transit_claim_window,
    assess_expiry_claim_window,
    claim_value_at_pts,
    compare_claim_value_at_pts,
    compare_claim_quantity,
    free_goods_cap_check,
    is_below_min_days_to_expiry,
    is_below_minimum_shelf_life,
    normalize_cfa_code,
    parse_pack_quantity,
    remaining_shelf_life_percent,
    shift_month,
)


def test_central_policy_values_match_the_case_rules():
    assert MIN_REMAINING_SHELF_LIFE_PCT == 60.0
    assert MIN_REMAINING_SHELF_LIFE_DAYS == 60
    assert EXPIRY_CLAIM_WINDOW_DAYS == 90
    assert BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS == 7
    assert CREDIT_NOTE_SLA_DAYS == 30
    assert FOC_CAP_PCT == 3.0
    assert CFA_VERIFICATION_WINDOW_WORKING_DAYS == 10


def test_exactly_sixty_percent_is_not_below_threshold():
    invoice = "10-02-2025"
    manufactured = "01-01-2025"
    expiry = "11-04-2025"

    assert remaining_shelf_life_percent(invoice, manufactured, expiry) == 60.0
    assert is_below_minimum_shelf_life(invoice, manufactured, expiry) is False


def test_one_day_below_sixty_percent_is_flagged():
    assert is_below_minimum_shelf_life(
        "11-02-2025", "01-01-2025", "11-04-2025"
    ) is True


def test_supported_mixed_date_formats_are_parsed():
    assert remaining_shelf_life_percent(
        "2025-02-10", "01-01-2025", "11-Apr-2025"
    ) == 60.0


def test_missing_date_is_rejected():
    with pytest.raises(ValueError, match="Date is missing"):
        remaining_shelf_life_percent("", "01-01-2025", "11-04-2025")


def test_expiry_must_be_after_manufacture_date():
    with pytest.raises(ValueError, match="Expiry date must be after"):
        remaining_shelf_life_percent(
            "10-02-2025", "11-04-2025", "01-01-2025"
        )


def test_shift_month_handles_year_rollover_and_negative_offsets():
    assert shift_month(date(2026, 9, 30), 1) == date(2026, 10, 1)
    assert shift_month(date(2026, 1, 1), -1) == date(2025, 12, 1)
    assert shift_month(date(2026, 9, 1), -12) == date(2025, 9, 1)


@pytest.mark.parametrize("offset", [True, 1.5, "1"])
def test_shift_month_requires_integer_offset(offset):
    with pytest.raises(ValueError, match="offset must be an integer"):
        shift_month(date(2026, 9, 1), offset)


def test_invoice_cannot_precede_manufacture_date():
    with pytest.raises(ValueError, match="Invoice date is before"):
        remaining_shelf_life_percent(
            "31-12-2024", "01-01-2025", "11-04-2025"
        )


def test_cfa_code_normalization_handles_format_variants():
    assert normalize_cfa_code("CF-E01") == "CFE01"
    assert normalize_cfa_code(" cfe01 ") == "CFE01"


def test_cfa_code_normalization_rejects_missing_code():
    with pytest.raises(ValueError, match="CFA code is missing"):
        normalize_cfa_code(" ")


def test_pack_quantity_accepts_thousands_separator():
    assert parse_pack_quantity("1,234") == 1234


@pytest.mark.parametrize("value", ["", "NaN", "-1", "abc"])
def test_pack_quantity_rejects_missing_invalid_or_negative_values(value):
    with pytest.raises(ValueError):
        parse_pack_quantity(value)


def test_expiry_claim_window_checks_the_inclusive_ninety_day_boundary():
    assert assess_expiry_claim_window("Expired", "29-08-2026", "31-05-2026")["status"] == "within_window"
    assert assess_expiry_claim_window("Expired", "30-08-2026", "31-05-2026")["status"] == "outside_window"


def test_near_expiry_window_starts_at_inclusive_ninety_days_before_expiry():
    assert assess_expiry_claim_window("Near expiry", "02-03-2026", "31-05-2026")["status"] == "within_window"
    assert assess_expiry_claim_window("Near expiry", "01-03-2026", "31-05-2026")["status"] == "outside_window"


def test_expiry_date_is_included_and_derived_as_expired():
    result = assess_expiry_claim_window("Near expiry", "31-05-2026", "31-05-2026")
    assert result["status"] == "within_window"
    assert result["derived_claim_type"] == "expired"
    # The case description includes expiry day in both adjacent windows.
    assert result["claim_type_label_mismatch"] is False


def test_non_expiry_claim_types_do_not_use_expiry_window():
    result = assess_expiry_claim_window("Short supply", "12-05-2026", "31-05-2026")
    assert result["status"] == "not_applicable"


def test_claim_category_is_derived_from_dates_not_trusted_label():
    result = assess_expiry_claim_window("Near expiry", "12-05-2026", "31-05-2026")
    assert result["status"] == "within_window"
    assert result["derived_claim_type"] == "near_expiry"
    assert result["claim_type_label_mismatch"] is False


def test_expired_label_before_expiry_is_flagged_as_mismatch_but_window_is_checked():
    result = assess_expiry_claim_window("Expired", "30-05-2026", "31-05-2026")
    assert result["status"] == "within_window"
    assert result["elapsed_days"] == -1
    assert result["derived_claim_type"] == "near_expiry"
    assert result["claim_type_label_mismatch"] is True


def test_claim_quantity_comparison_reports_overage_without_rounding():
    assert compare_claim_quantity("11", "10") == {
        "status": "exceeds_recorded_quantity",
        "claimed_quantity": 11,
        "recorded_quantity": 10,
    }


@pytest.mark.parametrize(
    ("elapsed", "expected"),
    [(6, "within_window"), (7, "within_window"), (8, "outside_window")],
)
def test_transit_claim_window_checks_below_at_and_above_seven_days(elapsed, expected):
    result = assess_transit_claim_window(
        date(2026, 4, 1) + timedelta(days=elapsed),
        date(2026, 4, 1),
    )

    assert result["status"] == expected
    assert result["limit_days"] == BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS
    assert result["elapsed_days"] == elapsed


@pytest.mark.parametrize(
    ("days_left", "expected"), [(59, True), (60, False), (61, False)]
)
def test_minimum_days_to_expiry_checks_below_at_and_above_sixty(days_left, expected):
    invoice_date = date(2026, 1, 1)

    assert is_below_min_days_to_expiry(
        invoice_date, invoice_date + timedelta(days=days_left)
    ) is expected


@pytest.mark.parametrize(
    ("free_value", "expected"), [("299", "within_cap"), ("300", "within_cap"), ("301", "above_cap")]
)
def test_free_goods_cap_checks_below_at_and_above_three_percent(free_value, expected):
    result = free_goods_cap_check(free_value, "10000")

    assert result["status"] == expected
    assert result["cap_value"] == 300


def test_claim_value_at_pts_uses_decimal_arithmetic():
    assert claim_value_at_pts("2", "10.25") == Decimal("20.50")


@pytest.mark.parametrize(
    ("claimed", "expected"),
    [("19.99", "mismatch_needs_person"), ("20", "match"), ("20.01", "mismatch_needs_person")],
)
def test_claim_amount_comparison_checks_below_at_and_above_pts_value(claimed, expected):
    result = compare_claim_value_at_pts("2", "10", claimed)

    assert result["status"] == expected
    assert result["policy_reference"] == "CO-POL-014 §5.7"


def test_prior_claim_exact_repeat_of_credited_vs_pending():
    assert classify_prior_claim(Decimal("272"), Decimal("272"), "Credited") == "repeat_of_credited"
    assert classify_prior_claim(Decimal("547"), Decimal("547"), "Pending") == "repeat_of_pending"
    # A credited row without a credit note number has not moved money yet: treat like pending.
    assert classify_prior_claim(Decimal("10"), Decimal("10"), "Credited", prior_has_credit_note=False) == "repeat_of_pending"
    assert classify_prior_claim(Decimal("10"), Decimal("10"), "Rejected") is None


def test_near_repeat_tolerance_is_one_percent_or_one_pack_whichever_is_larger():
    # 1 pack always counts (small claims): 50 vs 51 is 2% but only 1 pack.
    assert classify_prior_claim(Decimal("50"), Decimal("51"), "Credited") == "near_repeat"
    assert classify_prior_claim(Decimal("50"), Decimal("52"), "Credited") is None
    # 1% of 500 = 5 packs: at 5 it counts, at 6 it does not.
    assert classify_prior_claim(Decimal("500"), Decimal("495"), "Credited") == "near_repeat"
    assert classify_prior_claim(Decimal("500"), Decimal("494"), "Credited") is None
    assert classify_prior_claim(Decimal("370"), Decimal("371"), "Credited") == "near_repeat"
