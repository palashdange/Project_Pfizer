"""Batch totals: definitions of caught, leakage, at risk and would block, with exact Decimal sums."""

from decimal import Decimal

import pytest

import agent.batch as batch
from agent.graph import at_stake_inr


def _row(claim_no, month, status, route, stake, credit=None, leakage=None):
    return {
        "claim_no": claim_no, "month": month, "claim_date": "", "claim_type": "Expired",
        "register_status": status, "route": route,
        "at_stake_inr": Decimal(stake) if stake is not None else None,
        "credit_value_inr": Decimal(credit) if credit is not None else None,
        "leakage_inr": Decimal(leakage) if leakage is not None else None,
        "first_problem": "", "problem_count": 0, "source": f"expiry_claims.csv:{claim_no}",
    }


@pytest.fixture
def rows(monkeypatch):
    fixture = (
        _row("C1", "2025-01", "Credited", "REJECT", "1000.00", "1000.00", "1000.00"),   # window: whole credit
        _row("C2", "2025-01", "Credited", "REJECT", "500.00", "500.00", "20.00"),       # over-quantity: excess only
        _row("C3", "2025-01", "Credited", "NEEDS_PERSON", "300.00", "300.00"),          # at risk, not saved
        _row("C4", "2025-02", "Pending", "REJECT", "250.00"),                           # would block
        _row("C5", "2025-02", "Credited", "RECOMMEND_CREDIT", "100.00", "100.00"),
        _row("C6", "2025-02", "Pending", "RECOMMEND_CREDIT", None),                      # value unknown
    )
    monkeypatch.setattr(batch, "_all_reviews", lambda: fixture)
    return fixture


def test_all_months_totals_and_annualisation(rows):
    result = batch.run_batch()

    assert result["months"] == 2 and result["claims_reviewed"] == 6
    assert result["route_counts"] == {"RECOMMEND_CREDIT": 2, "REJECT": 3, "NEEDS_PERSON": 1}
    assert result["period_inr"] == {
        "caught": "1500.00", "leakage": "1020.00", "at_risk": "300.00",
        "would_block": "250.00", "recommend_credit": "100.00",
    }
    # 2 months observed -> x 12 / 2.
    assert result["annualised_inr"]["leakage"] == "6120.00"
    assert result["missing_value_claims"] == 1
    assert "claims" not in result


def test_single_month_lists_claims_rejects_first(rows):
    result = batch.run_batch("2025-01")

    assert result["months"] == 1
    assert [c["claim_no"] for c in result["claims"]] == ["C1", "C2", "C3"]
    assert result["annualised_inr"]["caught"] == "18000.00"


def test_unknown_month_is_an_error_not_a_guess(rows):
    with pytest.raises(ValueError, match="No claims in the register for month '2030-01'"):
        batch.run_batch("2030-01")


def test_at_stake_uses_claim_value_or_quantity_times_pts():
    assert at_stake_inr({"claim_value_inr": "3,936.80"}, None) == Decimal("3936.80")
    assert at_stake_inr({"claim_value_inr": "", "qty_claimed": "400"}, {"pts_inr": "98.7"}) == Decimal("39480.00")
    assert at_stake_inr({"claim_value_inr": "", "qty_claimed": "400"}, None) is None


def test_quarter_and_year_periods_select_their_months_and_annualise_by_them(rows):
    quarter = batch.run_batch("FY25 Q4")  # Jan-Mar 2025: both fixture months
    assert quarter["months"] == 2 and quarter["claims_reviewed"] == 6
    assert quarter["period"] == "FY25 Q4 (Jan–Feb 2025)"
    assert [c["claim_no"] for c in quarter["claims"]][:2] == ["C1", "C2"]  # a quarter lists its claims
    year = batch.run_batch("fy25")
    assert year["months"] == 2 and year["annualised_inr"] == batch.run_batch()["annualised_inr"]
    with pytest.raises(ValueError, match="No claims in the register"):
        batch.run_batch("FY24 Q1")


def test_periods_come_from_claim_dates_newest_first_with_counts():
    periods = batch.available_periods()
    assert periods["all"]["claims"] == 4503 and periods["all"]["months"] == 30
    assert [p["value"] for p in periods["years"]] == ["FY27", "FY26", "FY25"]
    assert periods["years"][0]["span"] == "Apr–Sep 2026 so far"
    assert periods["quarters"][0] == {"value": "FY27 Q2", "span": "Jul–Sep 2026", "months": 3, "claims": 631}
    assert periods["months"][0]["value"] == "2026-09" and len(periods["months"]) == 30
    assert sum(p["claims"] for p in periods["years"]) == sum(p["claims"] for p in periods["months"]) == 4503
