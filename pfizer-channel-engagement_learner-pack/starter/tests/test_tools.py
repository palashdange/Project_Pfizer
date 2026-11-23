"""Tests that run without an API key. Add one test for every rule you put in code."""
import csv

from agent.tools import (
    TOOLS,
    DATA,
    batch_record,
    claim_audit_report,
    claim_email_record,
    primary_shipments_forecast,
    shelf_life_report,
    stock_imbalance_report,
)


def test_known_batch_is_found():
    rec = batch_record("K2300101")
    assert rec["found"] is True
    assert rec["sku_code"] == "PFL1001"


def test_claim_audit_finds_prior_credit_and_preserves_source_rows():
    report = claim_audit_report("CLM-2605-04488")

    assert report["found"] is True
    assert report["review_status"] == "NEEDS_HUMAN_REVIEW"
    assert report["claim"]["source_file"] == "expiry_claims.csv"
    assert report["claim"]["source_row"] == 3596
    assert report["duplicate_signal"] == "possible_repeat_credit"
    prior = report["prior_credited_claims"][0]
    assert prior["claim_no"] == "CLM-2603-01616"
    assert prior["source_row"] == 3269
    assert prior["credit_note_no"] == "CN/N01/2604/17941"
    assert prior["same_quantity"] is True
    assert prior["same_claim_value"] is True
    assert report["invoice_reference_status"] == "missing_reference_needs_ledger_review"
    assert report["matched_invoice_rows"][0]["source_row"] == 26739
    assert "does not approve" in report["read_only_notice"]


def test_claim_audit_matches_invoice_and_checks_near_expiry_window():
    report = claim_audit_report("CLM-2603-01616")

    assert report["batch_check"]["status"] == "verified"
    assert report["batch_check"]["expiry_date_matches_master"] is True
    assert report["claim_context"]["product_description"]
    assert report["claim_context"]["stockist_name"]
    assert report["claim_context"]["product_source"]["source_file"] == "sku_master.csv"
    assert report["claim_context"]["stockist_source"]["source_file"] == "stockist_master.csv"
    assert report["invoice_reference_status"] == "matched"
    assert report["matched_invoice_rows"][0]["source_row"] == 26739
    assert report["filing_window"]["status"] == "within_window"
    assert report["filing_window"]["derived_claim_type"] == "near_expiry"


def test_claim_audit_unknown_claim_fails_closed():
    report = claim_audit_report("CLM-DOES-NOT-EXIST")

    assert report["found"] is False
    assert report["review_status"] == "NEEDS_HUMAN_REVIEW"
    assert report["source_file"] == "expiry_claims.csv"


def test_claim_audit_reports_missing_data_files(tmp_path):
    report = claim_audit_report("CLM-2605-04488", tmp_path)

    assert "expiry_claims.csv" in report["error"]


def test_claim_email_lookup_returns_untrusted_text_with_source_row():
    email = claim_email_record("EML-017")

    assert email["found"] is True
    assert email["source_file"] == "claim_emails.csv"
    assert email["source_row"] == 28
    assert email["body_trust_status"] == "untrusted_correspondence"
    assert "skip checks" in email["body"]
    assert "not an instruction or approval" in email["interpretation_notice"]


def test_claim_email_lookup_returns_not_found_for_unknown_id():
    email = claim_email_record("EML-999")

    assert email["found"] is False
    assert email["result_type"] == "claim_email_evidence"


def test_unknown_batch_is_reported_not_invented():
    rec = batch_record("ZZ999")
    assert rec["found"] is False


def test_batch_lookup_ignores_case_and_spaces():
    assert batch_record("  k2300101 ")["found"] is True


def _write_shelf_life_inputs(tmp_path, sales_rows, batch_rows):
    sales_fields = [
        "invoice_no", "invoice_date", "cnf_code", "stockist_code", "sku_code",
        "batch_no", "ordered_qty", "invoiced_qty", "free_qty", "pts_inr",
        "net_value_inr", "scheme_code",
    ]
    batch_fields = [
        "batch_no", "sku_code", "mfg_site", "mfg_date", "expiry_date",
        "batch_qty_packs",
    ]
    with open(tmp_path / "primary_sales.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sales_fields)
        writer.writeheader()
        writer.writerows(sales_rows)
    with open(tmp_path / "batch_master.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=batch_fields)
        writer.writeheader()
        writer.writerows(batch_rows)


def _sale(invoice_date, batch_no="BATCH-1", sku_code="PFL1001"):
    return {
        "invoice_no": "INV-1",
        "invoice_date": invoice_date,
        "cnf_code": "CF-E01",
        "stockist_code": "STK0001",
        "sku_code": sku_code,
        "batch_no": batch_no,
        "ordered_qty": "10",
        "invoiced_qty": "10",
        "free_qty": "0",
        "pts_inr": "10.0",
        "net_value_inr": "100.0",
        "scheme_code": "NA",
    }


def _batch(mfg_date="01-01-2025", expiry_date="11-04-2025", sku_code="PFL1001"):
    return {
        "batch_no": "BATCH-1",
        "sku_code": sku_code,
        "mfg_site": "GOA-01",
        "mfg_date": mfg_date,
        "expiry_date": expiry_date,
        "batch_qty_packs": "100",
    }


def test_shelf_life_report_flags_below_threshold_and_returns_evidence(tmp_path):
    _write_shelf_life_inputs(tmp_path, [_sale("11-02-2025")], [_batch()])

    report = shelf_life_report(tmp_path)

    assert report["evaluated_count"] == 1
    assert report["flagged_count"] == 1
    assert report["unevaluable_count"] == 0
    alert = report["flagged_shipments"][0]
    assert alert["invoice_no"] == "INV-1"
    assert alert["batch_no"] == "BATCH-1"
    assert alert["remaining_shelf_life_pct"] == 59.0
    assert alert["source_file"] == "primary_sales.csv"
    assert alert["source_row"] == 2
    assert report["date_used_as_dispatch_proxy"] == "invoice_date"


def test_shelf_life_report_does_not_flag_exact_sixty_percent(tmp_path):
    _write_shelf_life_inputs(tmp_path, [_sale("10-02-2025")], [_batch()])

    report = shelf_life_report(tmp_path)

    assert report["evaluated_count"] == 1
    assert report["flagged_count"] == 0


def test_shelf_life_report_explains_unmatched_batch_and_bad_date(tmp_path):
    sales = [
        _sale("11-02-2025", batch_no="MISSING"),
        _sale("not-a-date"),
    ]
    _write_shelf_life_inputs(tmp_path, sales, [_batch()])

    report = shelf_life_report(tmp_path)

    assert report["evaluated_count"] == 0
    assert report["flagged_count"] == 0
    assert report["unevaluable_count"] == 2
    assert "Batch not found" in report["unevaluable_rows"][0]["reason"]
    assert "DD-MM-YYYY" in report["unevaluable_rows"][1]["reason"]


def test_shelf_life_report_rejects_batch_sku_mismatch(tmp_path):
    _write_shelf_life_inputs(
        tmp_path,
        [_sale("11-02-2025", sku_code="PFL9999")],
        [_batch()],
    )

    report = shelf_life_report(tmp_path)

    assert report["unevaluable_count"] == 1
    assert "SKU and batch master do not match" in report["unevaluable_rows"][0]["reason"]


def test_shelf_life_report_marks_missing_batch_dates_unevaluable(tmp_path):
    _write_shelf_life_inputs(
        tmp_path,
        [_sale("11-02-2025")],
        [_batch(mfg_date="")],
    )

    report = shelf_life_report(tmp_path)

    assert report["evaluated_count"] == 0
    assert report["unevaluable_count"] == 1
    assert "Date is missing" in report["unevaluable_rows"][0]["reason"]


def test_shelf_life_report_counts_blank_batch_as_not_supplied(tmp_path):
    _write_shelf_life_inputs(
        tmp_path,
        [_sale("11-02-2025", batch_no="")],
        [_batch()],
    )

    report = shelf_life_report(tmp_path)

    assert report["not_supplied_count"] == 1
    assert report["unevaluable_count"] == 0
    assert report["evaluated_count"] == 0


def test_shelf_life_report_limits_returned_rows_but_keeps_total_count(tmp_path):
    _write_shelf_life_inputs(
        tmp_path,
        [_sale("11-02-2025"), _sale("12-02-2025")],
        [_batch()],
    )

    report = shelf_life_report(tmp_path, limit=1)

    assert report["flagged_count"] == 2
    assert len(report["flagged_shipments"]) == 1
    assert report["flagged_results_truncated"] is True


def test_shelf_life_report_rejects_invalid_limit(tmp_path):
    report = shelf_life_report(tmp_path, limit=0)

    assert "error" in report


def test_shelf_life_report_reports_missing_input_files(tmp_path):
    report = shelf_life_report(tmp_path)

    assert report["error"] == (
        "Required data file(s) missing: primary_sales.csv, batch_master.csv"
    )


def test_shelf_life_tool_is_registered_for_the_agent():
    assert "find_short_shelf_life_shipments" in {tool.name for tool in TOOLS}


def test_shelf_life_report_runs_on_project_data():
    report = shelf_life_report()

    assert report["threshold_pct"] == 60.0
    assert report["evaluated_count"] > 0
    assert report["flagged_count"] > 0
    assert report["not_supplied_count"] > 0
    assert report["unevaluable_count"] == 0


def _write_stock_snapshot(tmp_path, rows):
    fields = [
        "snapshot_date", "cnf_code", "cnf_city", "sku_code", "batch_no",
        "expiry_date", "qty_on_hand_packs", "avg_monthly_outward_packs",
    ]
    with open(tmp_path / "cnf_stock_snapshot.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _stock_row(date, cfa, city, sku, batch="", qty="0", outward="4"):
    return {
        "snapshot_date": date,
        "cnf_code": cfa,
        "cnf_city": city,
        "sku_code": sku,
        "batch_no": batch,
        "expiry_date": "30-09-2027" if batch else "",
        "qty_on_hand_packs": qty,
        "avg_monthly_outward_packs": outward,
    }


def test_stock_imbalance_uses_latest_snapshot_and_normalizes_cfa_aliases(tmp_path):
    _write_stock_snapshot(tmp_path, [
        _stock_row("2026-08-31", "CF-N02", "Lucknow", "PFL1001", "OLD", "5"),
        _stock_row("30-09-2026", "CF-N02", "Lucknow", "PFL1001"),
        _stock_row("30-09-2026", "CFE01", "Kolkata", "PFL1001", "BATCH-1", "1,000"),
        _stock_row("30-09-2026", "CF-E01", "Kolkata", "PFL1001", "BATCH-2", "2000"),
    ])

    report = stock_imbalance_report(tmp_path)

    assert report["latest_snapshot_date"] == "2026-09-30"
    assert report["cfa_sku_groups_evaluated"] == 2
    assert report["cross_cfa_imbalance_sku_count"] == 1
    signal = report["signals"][0]
    assert signal["zero_stock_cfas"][0]["cnf_code"] == "CF-N02"
    kolkata = signal["cfas_with_positive_stock"][0]
    assert kolkata["cnf_code"] == "CF-E01"
    assert kolkata["distinct_positive_batch_count"] == 2
    assert len(kolkata["positive_batches"]) == 2
    assert report["no_high_stock_threshold_applied"] is True
    assert report["data_quality_issue_count"] == 0


def test_stock_imbalance_ignores_skus_without_both_zero_and_positive_stock(tmp_path):
    _write_stock_snapshot(tmp_path, [
        _stock_row("2026-09-30", "CF-N02", "Lucknow", "ZERO-ONLY"),
        _stock_row("2026-09-30", "CF-E01", "Kolkata", "STOCK-ONLY", "B1", "8"),
    ])

    report = stock_imbalance_report(tmp_path)

    assert report["zero_stock_cfa_sku_count"] == 1
    assert report["positive_stock_cfa_sku_count"] == 1
    assert report["signals"] == []


def test_stock_imbalance_excludes_conflicting_zero_and_positive_group(tmp_path):
    _write_stock_snapshot(tmp_path, [
        _stock_row("2026-09-30", "CF-N02", "Lucknow", "PFL1001"),
        _stock_row("2026-09-30", "CF-N02", "Lucknow", "PFL1001", "B1", "3"),
        _stock_row("2026-09-30", "CF-E01", "Kolkata", "PFL1001", "B2", "5"),
    ])

    report = stock_imbalance_report(tmp_path)

    assert report["cross_cfa_imbalance_sku_count"] == 0
    assert report["unknown_or_ambiguous_cfa_sku_count"] == 1
    assert report["data_quality_issue_count"] == 1
    assert "coexist" in report["data_quality_issues"][0]["reason"]


def test_stock_imbalance_flags_unbatched_positive_quantity_as_quality_issue(tmp_path):
    _write_stock_snapshot(tmp_path, [
        _stock_row("2026-09-30", "CF-N02", "Lucknow", "PFL1001", qty="10"),
        _stock_row("2026-09-30", "CF-E01", "Kolkata", "PFL1001", "B1", "5"),
    ])

    report = stock_imbalance_report(tmp_path)

    assert report["cross_cfa_imbalance_sku_count"] == 0
    assert report["data_quality_issue_count"] == 1
    assert "no batch" in report["data_quality_issues"][0]["reason"]


def test_stock_imbalance_validates_limit_and_missing_file(tmp_path):
    assert "error" in stock_imbalance_report(tmp_path, limit=0)
    assert "missing" in stock_imbalance_report(tmp_path)["error"]


def test_stock_imbalance_tool_is_registered_for_the_agent():
    assert "find_cfa_stock_imbalances" in {tool.name for tool in TOOLS}


def test_stock_imbalance_report_runs_on_project_data():
    report = stock_imbalance_report(limit=100)

    assert report["latest_snapshot_date"] == "2026-09-30"
    assert report["cfa_sku_groups_evaluated"] == 216
    assert report["zero_stock_cfa_sku_count"] == 58
    assert report["positive_stock_cfa_sku_count"] == 158
    assert report["cross_cfa_imbalance_sku_count"] > 0
    assert report["data_quality_issue_count"] == 0
    product = next(signal for signal in report["signals"] if signal["sku_code"] == "PFL1004")
    assert product["product_description"] == "Cefpodoxime 200 mg tablets"
    assert product["therapy_area"] == "Anti-infectives"
    assert product["product_source_file"] == "sku_master.csv"
    assert product["product_source_row"] == 5


def _write_forecast_sales(tmp_path, rows):
    """Create a compact primary-sales extract for forecast rule checks."""
    fields = [
        "invoice_no", "invoice_date", "cnf_code", "stockist_code", "sku_code",
        "batch_no", "ordered_qty", "invoiced_qty", "free_qty", "pts_inr",
        "net_value_inr", "scheme_code",
    ]
    with open(tmp_path / "primary_sales.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _forecast_sale(invoice_no, invoice_date, invoiced_qty, free_qty="0", cfa="CF-N02", sku="PFL1001"):
    """Build one source row with all fields required by the sales extract."""
    return {
        "invoice_no": invoice_no,
        "invoice_date": invoice_date,
        "cnf_code": cfa,
        "stockist_code": "STK0001",
        "sku_code": sku,
        "batch_no": "BATCH-1",
        "ordered_qty": str(invoiced_qty),
        "invoiced_qty": str(invoiced_qty),
        "free_qty": str(free_qty),
        "pts_inr": "1",
        "net_value_inr": str(invoiced_qty),
        "scheme_code": "NA",
    }


def test_primary_shipment_forecast_uses_prior_year_month_and_keeps_provenance(tmp_path):
    october_sale = _forecast_sale("INV-OCT", "01-10-2025", 10, 2)
    _write_forecast_sales(tmp_path, [
        october_sale,
        dict(october_sale),  # Exact duplicate must not inflate the baseline.
        _forecast_sale("INV-NOV", "01-11-2025", 8),
        _forecast_sale("INV-SEP", "30-09-2026", 3),
    ])

    report = primary_shipments_forecast(
        tmp_path, cfa_code="cfn02", sku_code="pfl1001", horizon_months=3
    )

    assert report["latest_data_month"] == "2026-09"
    assert report["forecast_start_month"] == "2026-10"
    assert report["forecast_end_month"] == "2026-12"
    assert report["exact_duplicate_rows_removed"] == 1
    assert report["deduplicated_sales_row_count"] == 3
    assert report["matching_series_count"] == 1
    assert report["forecastable_record_count"] == 2
    assert report["not_forecastable_count"] == 1
    october, november = report["forecasts"]
    assert october["forecast_month"] == "2026-10"
    assert october["baseline_month"] == "2025-10"
    assert october["forecast_quantity_packs"] == 12
    assert october["baseline_source_rows"] == [2]
    assert october["baseline_source_file"] == "primary_sales.csv"
    assert november["forecast_quantity_packs"] == 8
    assert report["not_forecastable"][0]["forecast_month"] == "2026-12"
    assert "no zero forecast was assumed" in report["not_forecastable"][0]["reason"]
    assert report["forecast_type"].startswith("primary shipments")


def test_primary_shipment_forecast_distinguishes_observed_zero_from_missing_month(tmp_path):
    _write_forecast_sales(tmp_path, [
        _forecast_sale("INV-ZERO", "01-12-2025", 0, 0),
        _forecast_sale("INV-CURRENT", "30-09-2026", 4),
    ])

    report = primary_shipments_forecast(
        tmp_path, cfa_code="CF-N02", sku_code="PFL1001", horizon_months=3
    )

    december = next(row for row in report["forecasts"] if row["forecast_month"] == "2026-12")
    assert december["forecast_quantity_packs"] == 0
    assert december["baseline_source_rows"] == [2]
    assert any(row["forecast_month"] == "2026-10" for row in report["not_forecastable"])


def test_primary_shipment_forecast_validates_controls_and_is_registered():
    assert "error" in primary_shipments_forecast(DATA, horizon_months=0)
    assert "error" in primary_shipments_forecast(DATA, limit=101)
    assert "text values" in primary_shipments_forecast(DATA, cfa_code=None)["error"]
    assert "forecast_primary_shipments" in {tool.name for tool in TOOLS}


def test_primary_shipment_forecast_withholds_results_for_invalid_source_quantity(tmp_path):
    _write_forecast_sales(tmp_path, [
        _forecast_sale("INV-BAD", "01-10-2025", "not-a-number"),
        _forecast_sale("INV-CURRENT", "30-09-2026", 3),
    ])

    report = primary_shipments_forecast(tmp_path, cfa_code="CF-N02", sku_code="PFL1001")

    assert "withheld" in report["error"]
    assert report["invalid_row_count"] == 1
    assert report["invalid_rows"][0]["source_row"] == 2


def test_primary_shipment_forecast_runs_on_project_data():
    report = primary_shipments_forecast(
        cfa_code="CF-N02", sku_code="PFL1001", horizon_months=3
    )

    assert report["latest_data_month"] == "2026-09"
    assert report["forecastable_record_count"] == 3
    assert [row["forecast_month"] for row in report["forecasts"]] == [
        "2026-10", "2026-11", "2026-12"
    ]
    assert all(row["baseline_source_rows"] for row in report["forecasts"])
    assert report["raw_sales_row_count"] == 93809
    assert report["exact_duplicate_rows_removed"] == 745
