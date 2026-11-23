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
};

const html = renderEvidence(forecast);
assert.match(html, /Primary shipment forecast/);
assert.match(html, /Forecast packs/);
assert.match(html, /Source file/);
assert.match(html, /3967/);
assert.match(html, /2025-10/);
assert.match(html, /55617, 55698/);
assert.match(answerSummary("", [forecast]), /not a downstream-demand forecast/);
