// Smoke-test forecast rendering with Node's built-in assertions; no browser packages needed.
const assert = require("node:assert/strict");
const { answerSummary, renderEvidence } = require("../public/evidence.js");

const forecast = {
  forecast_type: "primary shipments into the channel; not downstream demand",
  latest_data_month: "2026-09",
  forecast_start_month: "2026-10",
  forecast_end_month: "2026-12",
  forecastable_record_count: 1,
  returned_record_count: 1,
  exact_duplicate_rows_removed: 745,
  interpretation: "A shipment baseline, not a demand forecast.",
  data_freshness_note: "Confirm the latest source file before use.",
  forecasts: [{
    cfa_code: "CF-N02",
    sku_code: "PFL1001",
    forecast_month: "2026-10",
    forecast_quantity_packs: 3967,
    baseline_month: "2025-10",
    baseline_source_file: "primary_sales.csv",
    invoiced_quantity_packs_in_baseline: 3967,
    free_quantity_packs_in_baseline: 0,
    baseline_source_row_count: 9,
    baseline_source_rows: [55617, 55698],
  }],
  not_forecastable: [],
  order_fulfillment_screen: {
    status: "available",
    source_file: "primary_sales.csv",
    data_period_start: "2024-04",
    data_period_end: "2026-09",
    observed_months: 30,
    annualization_method: "Observed value ÷ 30 months × 12; run-rate illustration, not savings.",
    cfa_filter: "CFN02",
    sku_filter: "PFL1001",
    after_free_packs: {
      label: "Ordered packs not covered by invoiced or free packs",
      observed_uncovered_packs: 5,
      observed_value_inr: 10,
      annualized_value_inr: 120,
      formula: "max(ordered_qty − invoiced_qty − free_qty, 0) × PTS",
      source_examples: [{
        invoice_no: "INV-SPLIT", invoice_date: "2026-09-30", cfa_code: "CF-N02",
        stockist_code: "STK0001", sku_code: "PFL1001", ordered_qty: 20,
        invoiced_qty: 10, free_qty: 5, shortfall_packs: 5, pts_inr: 2,
        screened_value_inr: 10, source_file: "primary_sales.csv", source_rows: [2, 3],
      }],
    },
    invoiced_only_gap: {
      label: "Invoiced-only gap before free packs",
      observed_value_inr: 20,
      annualized_value_inr: 240,
      formula: "max(ordered_qty − invoiced_qty, 0) × PTS",
      additive: false,
      source_examples: [{
        invoice_no: "INV-SPLIT", invoice_date: "2026-09-30", cfa_code: "CF-N02",
        stockist_code: "STK0001", sku_code: "PFL1001", ordered_qty: 20,
        invoiced_qty: 10, free_qty: 5, shortfall_packs: 5, invoiced_only_gap_packs: 10,
        pts_inr: 2, screened_value_inr: 20, source_file: "primary_sales.csv", source_rows: [2, 3],
      }],
    },
    interpretation: "Gross screening proxies only; not confirmed lost sales or savings.",
  },
};

const html = renderEvidence(forecast);
assert.match(html, /Primary shipment forecast/);
assert.match(html, /Forecast packs/);
assert.match(html, /Source file/);
assert.match(html, /3967/);
assert.match(html, /2025-10/);
assert.match(html, /55617, 55698/);
assert.match(html, /Order fulfillment screen/);
assert.match(html, /Ordered packs not covered by invoiced or free packs/);
assert.match(html, /Invoiced-only gap before free packs/);
assert.match(html, /OVERLAPPING DIAGNOSTIC · DO NOT ADD TO PRIMARY VALUE/);
assert.match(html, /₹120/);
assert.match(html, /₹240/);
assert.match(html, /max\(ordered_qty − invoiced_qty − free_qty, 0\) × PTS/);
assert.match(html, /INV-SPLIT/);
assert.match(html, /primary_sales\.csv/);
assert.match(html, /2, 3/);
assert.match(answerSummary("", [forecast]), /not a downstream-demand forecast/);
