from datetime import date

import pytest

from agent.rules import (
    assess_expiry_claim_window,
    compare_claim_quantity,
    is_below_minimum_shelf_life,
    normalize_cfa_code,
    parse_pack_quantity,
    remaining_shelf_life_percent,
    shift_month,
)


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
