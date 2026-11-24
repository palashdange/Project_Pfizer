"""Focused coverage for sizing data normalization and policy arithmetic."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from sizing import _clean_file, calculate_sizing, fiscal_quarter, normalize_code, parse_mixed_dates


def _dates(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Apply the same date parser used by the CSV loader to a fixture frame."""
    for column in columns:
        frame[column] = parse_mixed_dates(frame[column])
    return frame


class SizingHelpersTest(unittest.TestCase):
    def test_normalizes_identifiers_and_cfa_hyphens(self):
        self.assertEqual(normalize_code(" cf-n02 ", cfa=True), "CFN02")
        self.assertEqual(normalize_code(" stK 02 "), "STK 02")

    def test_parses_the_three_supported_date_formats(self):
        parsed = parse_mixed_dates(pd.Series(["31-03-2025", "2025-03-31", "31-Mar-2025"]))
        self.assertTrue((parsed == pd.Timestamp("2025-03-31")).all())

    def test_fiscal_quarter_starts_in_april(self):
        dates = pd.Series(pd.to_datetime(["2024-04-01", "2024-06-30", "2024-07-01", "2025-03-31"]))
        self.assertEqual(fiscal_quarter(dates).tolist(), ["FY25 Q1", "FY25 Q1", "FY25 Q2", "FY25 Q4"])

    def test_exact_dedup_keeps_first_physical_source_row(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "small.csv"
            path.write_text("sku_code,value\n PFL1 ,1\n PFL1 ,1\n", encoding="utf-8")
            cleaned, raw_count, duplicates = _clean_file(path)
        self.assertEqual(raw_count, 2)
        self.assertEqual(duplicates, 1)
        self.assertEqual(int(cleaned.loc[0, "_source_row"]), 2)
        self.assertEqual(cleaned.loc[0, "sku_code"], "PFL1")


class SizingCalculationsTest(unittest.TestCase):
    def setUp(self):
        # Fixtures isolate one example for each policy and financial screen.
        self.frames = {}
        sales_rows = [
            ["INV1", "10-04-2024", "CFN01", "STK1", "SKU1", "B1", "100", "100", "0", "10", "1000", "NA"],
            ["INV4", "10-04-2024", "CFN02", "STK4", "SKU1", "B4", "100", "100", "0", "10", "1000", "NA"],
            ["INV5", "10-04-2024", "CFN02", "STK5", "SKU1", "B5", "100", "80", "20", "10", "800", "NA"],
            ["INV6", "10-04-2024", "CFN02", "STK6", "SKU1", "B6", "100", "30", "0", "10", "300", "NA"],
            ["INVB", "10-04-2024", "CFN02", "STK2", "SKU1", "B2", "100", "50", "0", "10", "500", "NA"],
        ]
        self.frames["primary_sales.csv"] = _dates(pd.DataFrame(sales_rows, columns=[
            "invoice_no", "invoice_date", "cnf_code", "stockist_code", "sku_code", "batch_no",
            "ordered_qty", "invoiced_qty", "free_qty", "pts_inr", "net_value_inr", "scheme_code",
        ]).assign(_source_row=range(2, 7)), ["invoice_date"])

        claim_rows = [
            ["C1", "11-04-2024", "STK1", "CF-N01", "SKU1", "B1", "", "10", "100", "Breakage in transit", "INV1", "Credited", "CN1", "20-04-2024", "1000"],
            ["C2", "12-04-2024", "STK1", "CF-N01", "SKU1", "B1", "", "10", "100", "Breakage in transit", "INV1", "Credited", "CN2", "20-05-2024", "1000"],
            ["C3", "02-10-2024", "STK4", "CFN02", "SKU1", "B4", "", "5", "50", "Near expiry", "INV4", "Credited", "CN3", "20-10-2024", "50"],
            ["C4", "15-04-2024", "STK5", "CFN02", "SKU1", "B5", "", "120", "1200", "Breakage in transit", "INV5", "Credited", "CN4", "20-04-2024", "1200"],
            ["C5", "15-04-2024", "STK6", "CFN02", "SKU1", "B6", "", "10", "100", "Near expiry", "", "Credited", "CN5", "20-04-2024", "300"],
            ["C6", "15-09-2024", "STK2", "CFN02", "SKU1", "B2", "", "5", "50", "Near expiry", "INVB", "Credited", "CN6", "20-09-2024", "50"],
            ["C7", "30-11-2024", "STK4", "CFN02", "SKU1", "B4", "", "3", "30", "Expired", "INV4", "Credited", "CN7", "05-12-2024", "30"],
        ]
        self.frames["expiry_claims.csv"] = _dates(pd.DataFrame(claim_rows, columns=[
            "claim_no", "claim_date", "stockist_code", "cnf_code", "sku_code", "batch_no",
            "expiry_date_as_claimed", "qty_claimed", "claim_value_inr", "claim_type",
            "original_invoice_ref", "status", "credit_note_no", "credit_note_date", "credit_value_inr",
        ]).assign(_source_row=range(2, 9)), ["claim_date", "expiry_date_as_claimed", "credit_note_date"])
        self.frames["batch_master.csv"] = _dates(pd.DataFrame([
            ["B1", "SKU1", "2023-10-10", "2025-10-10"],
            ["B2", "SKU1", "2023-10-10", "2024-10-10"],
            ["B4", "SKU1", "2023-09-01", "2024-09-01"],
            ["B5", "SKU1", "2023-10-10", "2025-10-10"],
            ["B6", "SKU1", "2024-03-01", "2024-07-10"],
        ], columns=["batch_no", "sku_code", "mfg_date", "expiry_date"]).assign(_source_row=range(2, 7)), ["mfg_date", "expiry_date"])
        self.frames["sku_master.csv"] = pd.DataFrame([["SKU1", "10", 2]], columns=["sku_code", "pts_inr", "_source_row"])
        self.frames["cnf_stock_snapshot.csv"] = pd.DataFrame(columns=["cnf_code", "snapshot_date"])
        self.frames["stockist_master.csv"] = pd.DataFrame(columns=["stockist_code", "cnf_code"])
        self.frames["claim_emails.csv"] = pd.DataFrame(columns=["email_id", "received_date"])

    def test_claim_buckets_priority_and_examples_are_traceable(self):
        result, summary = calculate_sizing(self.frames)
        q1 = result[result["period"] == "FY25 Q1"]
        duplicate = q1[q1["problem"].str.startswith("Potential duplicate credits")].iloc[0]
        self.assertEqual(float(duplicate["inr_value"]), 1000.0)
        self.assertIn("C1", duplicate["source_rows_example"])
        self.assertIn("C2", duplicate["source_rows_example"])

        q3 = result[result["period"] == "FY25 Q3"]
        window = q3[q3["problem"] == "Credited claims outside policy window"].iloc[0]
        self.assertEqual(float(window["inr_value"]), 50.0)
        over = q1[q1["problem"].str.startswith("Over-quantity")].iloc[0]
        self.assertEqual(float(over["inr_value"]), 200.0)
        no_invoice = q1[q1["problem"].str.startswith("Credited claims without")].iloc[0]
        self.assertEqual(float(no_invoice["inr_value"]), 300.0)
        rsl = result[(result["problem"].str.startswith("Expiry claims on stockist-batches"))
                     & (result["period"] == "FY25 Q2")].iloc[0]
        self.assertEqual(float(rsl["inr_value"]), 50.0)
        self.assertEqual(summary["overlaps"]["duplicate_credit_later_records"], 1)

    def test_short_rsl_claim_is_non_additive_diagnostic_and_gap_is_not_called_saved(self):
        result, summary = calculate_sizing(self.frames)
        q1 = result[result["period"] == "FY25 Q1"]
        gap = q1[q1["problem"].str.startswith("Unfilled-order pack value after free goods — CFN02")].iloc[0]
        invoice_only = q1[q1["problem"].str.startswith("Invoiced-only gap before free goods — CFN02")].iloc[0]
        # STK5's 20 free packs cover its 20-pack invoice gap; the separate
        # diagnostic retains that billable gap but the primary signal removes it.
        self.assertEqual(float(gap["inr_value"]), 1200.0)
        self.assertEqual(float(invoice_only["inr_value"]), 1400.0)
        self.assertIn("free packs treated as shipped fulfillment", gap["method"])
        self.assertIn("non-additive", invoice_only["problem"])
        self.assertGreater(summary["availability_problem_size_annualized_inr"], 0)
        self.assertGreater(summary["invoice_only_gap_annualized_diagnostic_inr"], summary["availability_problem_size_annualized_inr"])
        self.assertEqual(summary["forecast_share_of_quantified_recoverable_inr_pct"], 0.0)
        self.assertIn("no forecast-linked", summary["forecast_share_status"])

    def test_expiry_claim_gap_uses_fy_sales_and_annualizes_observed_months(self):
        result, summary = calculate_sizing(self.frames)
        fy25 = result[
            result["problem"].str.startswith("Expiry claims above 1% target")
            & result["period"].eq("FY25")
        ].iloc[0]
        annual = result[
            result["problem"].str.startswith("Expiry claims above 1% target")
            & result["period"].str.startswith("Annualized")
        ].iloc[0]
        # Near-expiry/expired claims total ₹230; 1% of FY25 net sales is ₹36.
        self.assertEqual(float(fy25["inr_value"]), 194.0)
        self.assertEqual(float(annual["inr_value"]), 582.0)
        self.assertEqual(summary["expiry_claims_above_1pct_target_annualized_inr"], 582.0)
        self.assertEqual(summary["forecast_share_of_quantified_recoverable_inr_pct"], 0.0)

    def test_driver_tables_show_quarter_end_packs_and_cfa_order_mix(self):
        result, summary = calculate_sizing(self.frames)
        quarter = summary["quarter_end_concentration"].iloc[0]
        self.assertEqual(quarter["period"], "FY25 Q1")
        self.assertEqual(quarter["primary_packs"], 380)
        self.assertEqual(quarter["last_10_day_packs"], 0)
        self.assertEqual(quarter["foc_pct_of_primary_net_value"], 5.56)

        cfa = summary["cfa_order_mix_and_fill"].set_index("cfa_code")
        self.assertEqual(cfa.loc["CFN01", "share_of_fy_ordered_qty_pct"], 20.0)
        self.assertEqual(cfa.loc["CFN02", "share_of_fy_ordered_qty_pct"], 80.0)
        self.assertEqual(cfa.loc["CFN02", "fill_rate_including_free_pct"], 70.0)


if __name__ == "__main__":
    unittest.main()
