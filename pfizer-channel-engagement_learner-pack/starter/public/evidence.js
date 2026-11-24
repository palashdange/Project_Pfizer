/* Format tool results as readable evidence cards; keep every value escaped. */
(function (root) {
  "use strict";

  const LABEL_OVERRIDES = {
    cnf: "CFA",
    cfas: "CFAs",
    sku: "SKU",
    skus: "SKUs",
    inr: "INR",
    pts: "PTS",
    mfg: "Manufacturing",
    source: "Source",
  };

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[character]));
  }

  function labelFor(key) {
    return key.split("_").map((part) => LABEL_OVERRIDES[part] || part)
      .join(" ").replace(/\b[a-z]/g, (letter) => letter.toUpperCase());
  }

  function scalar(value) {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    return String(value);
  }

  function renderValue(value) {
    if (Array.isArray(value)) {
      if (!value.length) return '<span class="muted">None</span>';
      return `<ul class="nested-list">${value.map((item) => `<li>${renderValue(item)}</li>`).join("")}</ul>`;
    }
    if (value && typeof value === "object") return renderFields(value);
    return escapeHtml(scalar(value));
  }

  function renderFields(record, excluded = []) {
    const entries = Object.entries(record).filter(([key, value]) => !excluded.includes(key) && value !== undefined);
    if (!entries.length) return '<p class="muted">No detail available.</p>';
    return `<dl class="evidence-fields">${entries.map(([key, value]) =>
      `<div><dt>${escapeHtml(labelFor(key))}</dt><dd>${renderValue(value)}</dd></div>`
    ).join("")}</dl>`;
  }

  function displayDate(value) {
    // Normalize common source formats for the table only; raw evidence stays untouched.
    const text = scalar(value);
    if (text === "—") return text;
    let match = text.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (match) return `${match[3].padStart(2, "0")}-${match[2].padStart(2, "0")}-${match[1]}`;

    match = text.match(/^(\d{1,2})[-/ ]([A-Za-z]{3}|\d{1,2})[-/ ](\d{4})$/);
    if (!match) return text;
    const monthNames = { jan: "01", feb: "02", mar: "03", apr: "04", may: "05", jun: "06", jul: "07", aug: "08", sep: "09", oct: "10", nov: "11", dec: "12" };
    const month = /^\d+$/.test(match[2]) ? match[2].padStart(2, "0") : monthNames[match[2].toLowerCase()];
    if (!month) return text;
    return `${match[1].padStart(2, "0")}-${month}-${match[3]}`;
  }

  function cellValue(value, key) {
    if (["invoice_date", "mfg_date", "expiry_date"].includes(key)) return displayDate(value);
    if (Array.isArray(value)) return value.length ? value.map(scalar).join(", ") : "—";
    if (value && typeof value === "object") return JSON.stringify(value);
    return scalar(value);
  }

  function renderTable(rows, columns, emptyMessage) {
    if (!rows.length) return `<p class="muted">${escapeHtml(emptyMessage)}</p>`;
    return `<div class="table-wrap"><table><thead><tr>${columns.map(([, label]) => `<th scope="col">${escapeHtml(label)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) =>
      `<tr>${columns.map(([key]) => `<td>${escapeHtml(cellValue(row[key], key))}</td>`).join("")}</tr>`
    ).join("")}</tbody></table></div>`;
  }

  function formatInr(value) {
    const amount = Number(value);
    if (!Number.isFinite(amount)) return escapeHtml(scalar(value));
    return new Intl.NumberFormat("en-IN", {
      style: "currency", currency: "INR", maximumFractionDigits: 2,
    }).format(amount);
  }

  function renderFulfillmentScreen(screen) {
    if (!screen || screen.status !== "available") {
      return `<section class="fulfillment-screen"><h4>Order fulfillment screen</h4><p class="muted">${escapeHtml(screen && screen.reason || "No order fulfillment measure is available.")}</p></section>`;
    }

    const primary = screen.after_free_packs || {};
    const diagnostic = screen.invoiced_only_gap || {};
    const exampleColumns = [
      ["invoice_no", "Invoice"], ["invoice_date", "Invoice date"], ["cfa_code", "CFA"],
      ["stockist_code", "Stockist"], ["sku_code", "SKU"], ["ordered_qty", "Ordered packs"],
      ["invoiced_qty", "Invoiced"], ["free_qty", "Free packs"], ["shortfall_packs", "After-free shortfall"],
      ["pts_inr", "PTS (INR)"], ["screened_value_inr", "Screened value (INR)"],
      ["source_file", "Source file"], ["source_rows", "Source row(s)"],
    ];
    const diagnosticColumns = exampleColumns.map(([key, label]) => [
      key === "shortfall_packs" ? "invoiced_only_gap_packs" : key,
      key === "shortfall_packs" ? "Invoiced-only gap" : label,
    ]);

    // Keep the invoiced-only diagnostic visually secondary because it overlaps the primary measure.
    return `<section class="fulfillment-screen">
      <h4>Order fulfillment screen</h4>
      <p class="muted">Source: ${escapeHtml(screen.source_file || "primary_sales.csv")} · ${escapeHtml(screen.data_period_start || "—")} to ${escapeHtml(screen.data_period_end || "—")} · ${escapeHtml(scalar(screen.observed_months))} observed months · CFA: ${escapeHtml(screen.cfa_filter || "All")} · SKU: ${escapeHtml(screen.sku_filter || "All")}</p>
      <div class="fulfillment-metrics">
        <article class="fulfillment-metric primary">
          <span class="metric-label">${escapeHtml(primary.label || "After-free-packs shortfall")}</span>
          <strong>${formatInr(primary.annualized_value_inr)}</strong>
          <span>Annualized run-rate illustration · ${formatInr(primary.observed_value_inr)} observed · ${escapeHtml(scalar(primary.observed_uncovered_packs))} uncovered packs</span>
          <code>${escapeHtml(primary.formula || "")}</code>
        </article>
        <article class="fulfillment-metric diagnostic">
          <span class="metric-label">${escapeHtml(diagnostic.label || "Invoiced-only diagnostic")}</span>
          <strong>${formatInr(diagnostic.annualized_value_inr)}</strong>
          <span>Annualized run-rate illustration · ${formatInr(diagnostic.observed_value_inr)}</span>
          <span class="non-additive">OVERLAPPING DIAGNOSTIC · DO NOT ADD TO PRIMARY VALUE</span>
          <code>${escapeHtml(diagnostic.formula || "")}</code>
        </article>
      </div>
      <p class="interpretation">${escapeHtml(screen.interpretation || "These are screening proxies, not confirmed lost sales or savings.")} ${escapeHtml(screen.annualization_method || "")}</p>
      <h5>Largest after-free-packs examples</h5>${renderTable(primary.source_examples || [], exampleColumns, "No positive after-free-packs shortfall examples in this selection.")}
      <h5>Largest invoiced-only examples</h5>${renderTable(diagnostic.source_examples || [], diagnosticColumns, "No positive invoiced-only gap examples in this selection.")}
    </section>`;
  }

  function stockRowMatches(row, filters) {
    // Filters only search fields and rows present in this source-backed result.
    const searchText = `${row.sku_code || ""} ${row.product_description || ""}`.toLocaleLowerCase();
    return searchText.includes(String(filters.search || "").toLocaleLowerCase())
      && (!filters.sku || row.sku_code === filters.sku)
      && (!filters.status || row.status === filters.status)
      && (!filters.cfa || row.cfa === filters.cfa)
      && (!filters.city || row.city === filters.city);
  }

  function renderStockTable(rows) {
    if (!rows.length) return '<p class="muted">No cross-CFA signals found.</p>';
    const options = (field) => [...new Set(rows.map((row) => row[field]).filter(Boolean))].sort();
    const select = (field, label, values) => `<label>${escapeHtml(label)}<select data-stock-filter="${field}"><option value="">All</option>${values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("")}</select></label>`;
    const columns = [
      ["sku_code", "SKU"], ["product_description", "Medicine / product"], ["therapy_area", "Therapy area"],
      ["status", "Stock status"], ["cfa", "CFA"], ["city", "City"], ["batch_no", "Batch"],
      ["qty_packs", "Reported packs"], ["source_rows", "Stock source row(s)"], ["product_source", "Product source"],
    ];
    return `<div class="stock-filter-panel" data-stock-filter-panel>
      <div class="stock-filters" aria-label="Filter stock signals">
        ${select("sku", "SKU", options("sku_code"))}
        <label>Medicine name<input type="search" data-stock-filter="search" placeholder="Search product name"></label>
        ${select("status", "Stock status", ["Zero-stock marker", "Positive batch stock"])}
        ${select("cfa", "CFA", options("cfa"))}
        ${select("city", "City", options("city"))}
        <button type="button" class="clear-stock-filters">Clear filters</button>
      </div>
      <p class="stock-result-count" aria-live="polite" data-stock-result-count></p>
      <div class="table-wrap"><table data-stock-table><thead><tr>${columns.map(([, label]) => `<th scope="col">${escapeHtml(label)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => {
        const attributes = `data-stock-row data-sku="${escapeHtml(row.sku_code)}" data-product="${escapeHtml(row.product_description || "")}" data-status="${escapeHtml(row.status)}" data-cfa="${escapeHtml(row.cfa)}" data-city="${escapeHtml(row.city)}"`;
        const values = [row.sku_code, row.product_description || "Product name not found in SKU master", row.therapy_area || "—", row.status, row.cfa, row.city, row.batch_no, row.qty_packs, row.source_rows, row.product_source || "—"];
        return `<tr ${attributes}>${values.map((value, index) => {
          // Highlight the zero-stock status cell so it stands out during review.
          const statusClass = index === 3 && row.status === "Zero-stock marker" ? ' class="stock-zero-cell"' : "";
          return `<td${statusClass}>${escapeHtml(cellValue(value, ""))}</td>`;
        }).join("")}</tr>`;
      }).join("")}</tbody></table></div>
    </div>`;
  }

  function attachStockFilters(container) {
    // Bind the controls after the result HTML has been added to the page.
    container.querySelectorAll("[data-stock-filter-panel]").forEach((panel) => {
      const controls = [...panel.querySelectorAll("[data-stock-filter]")];
      const rows = [...panel.querySelectorAll("[data-stock-row]")];
      const count = panel.querySelector("[data-stock-result-count]");
      const applyFilters = () => {
        const filters = Object.fromEntries(controls.map((control) => [control.dataset.stockFilter, control.value]));
        let visible = 0;
        rows.forEach((row) => {
          const matches = stockRowMatches({
            sku_code: row.dataset.sku,
            product_description: row.dataset.product,
            status: row.dataset.status,
            cfa: row.dataset.cfa,
            city: row.dataset.city,
          }, filters);
          row.hidden = !matches;
          if (matches) visible += 1;
        });
        count.textContent = `Showing ${visible} of ${rows.length} stock rows`;
      };
      controls.forEach((control) => {
        control.addEventListener("input", applyFilters);
        control.addEventListener("change", applyFilters);
      });
      panel.querySelector(".clear-stock-filters").addEventListener("click", () => {
        controls.forEach((control) => { control.value = ""; });
        applyFilters();
      });
      applyFilters();
    });
  }

  function renderBatch(item) {
    if (!item.found) {
      return `<article class="evidence-card"><h4>Batch not found</h4><p>No matching batch record for ${escapeHtml(item.batch_no || "the requested batch")}.</p></article>`;
    }
    const fields = Object.entries(item).filter(([key]) => !["found", "batch_no"].includes(key))
      .map(([field, value]) => ({ field: labelFor(field), value }));
    return `<article class="evidence-card"><h4>Batch ${escapeHtml(item.batch_no || "details")}</h4>${renderTable(fields, [["field", "Field"], ["value", "Value"]], "No batch fields returned.")}</article>`;
  }

  function renderShelfLife(item) {
    const metrics = [
      ["Flagged lines", item.flagged_count],
      ["Evaluated", item.evaluated_count],
      ["Could not evaluate", item.unevaluable_count],
      ["Batch not supplied", item.not_supplied_count],
    ];
    const flagged = item.flagged_shipments || [];
    const unevaluable = item.unevaluable_rows || [];
    const shipmentColumns = [
      ["invoice_no", "Invoice"], ["source_file", "Source file"], ["source_row", "Source row"],
      ["invoice_date", "Invoice date"], ["stockist_code", "Stockist"],
      ["sku_code", "SKU"], ["batch_no", "Batch"], ["invoiced_qty", "Qty invoiced"],
      ["mfg_date", "Mfg date"], ["expiry_date", "Expiry date"],
      ["remaining_shelf_life_pct", "Shelf life %"],
    ];
    const reviewColumns = [
      ["invoice_no", "Invoice"], ["invoice_date", "Invoice date"], ["sku_code", "SKU"],
      ["batch_no", "Batch"], ["reason", "Why not evaluated"], ["source_file", "Source file"], ["source_row", "Source row"],
    ];
    return `<div class="metric-grid">${metrics.map(([label, value]) => `<div class="metric"><strong>${escapeHtml(scalar(value))}</strong><span>${escapeHtml(label)}</span></div>`).join("")}</div>
      <p class="interpretation">Policy threshold: ${escapeHtml(scalar(item.threshold_pct))}% remaining shelf life. CO-POL-014 §7.1 defines RSL on the invoice date.</p>
      <h4>Flagged invoice lines</h4>${renderTable(flagged, shipmentColumns, "No invoice lines were flagged.")}
      ${unevaluable.length ? `<h4>Rows needing review</h4>${renderTable(unevaluable, reviewColumns, "No rows need review.")}` : ""}
      ${item.flagged_results_truncated || item.unevaluable_results_truncated ? '<p class="muted">Some rows are omitted from this result because of the display limit.</p>' : ""}`;
  }

  function renderStock(item) {
    const metrics = [
      ["SKUs with cross-CFA signals", item.cross_cfa_imbalance_sku_count],
      ["Zero-stock CFA/SKUs", item.zero_stock_cfa_sku_count],
      ["Positive-stock CFA/SKUs", item.positive_stock_cfa_sku_count],
      ["Data-quality issues", item.data_quality_issue_count],
    ];
    const signals = item.signals || [];
    const stockRows = [];
    signals.forEach((signal) => {
      (signal.zero_stock_cfas || []).forEach((cfa) => stockRows.push({
        sku_code: signal.sku_code, product_description: signal.product_description, therapy_area: signal.therapy_area,
        product_source: signal.product_source_file ? `${signal.product_source_file} row ${signal.product_source_row}` : "",
        status: "Zero-stock marker", cfa: cfa.cnf_code, city: cfa.cnf_city,
        batch_no: "—", qty_packs: "0", source_rows: cfa.source_rows,
      }));
      (signal.cfas_with_positive_stock || []).forEach((cfa) => {
        (cfa.positive_batches || []).forEach((batch) => (batch.reported_quantities_packs || []).forEach((qty, index) => stockRows.push({
          sku_code: signal.sku_code, product_description: signal.product_description, therapy_area: signal.therapy_area,
          product_source: signal.product_source_file ? `${signal.product_source_file} row ${signal.product_source_row}` : "",
          status: "Positive batch stock", cfa: cfa.cnf_code, city: cfa.cnf_city,
          batch_no: batch.batch_no, qty_packs: qty, source_rows: [(batch.source_rows || [])[index] || "—"],
        })));
      });
    });
    return `<p class="interpretation">Latest snapshot: ${escapeHtml(scalar(item.latest_snapshot_date))}. These are review signals, not proof of excess stock or transfer feasibility.</p>
      <div class="metric-grid">${metrics.map(([label, value]) => `<div class="metric"><strong>${escapeHtml(scalar(value))}</strong><span>${escapeHtml(label)}</span></div>`).join("")}</div>
      <h4>Stock signals by product and CFA</h4>${renderStockTable(stockRows)}
      ${item.data_quality_issues && item.data_quality_issues.length ? `<h4>Data-quality notes</h4>${renderTable(item.data_quality_issues, [["cnf_code", "CFA"], ["sku_code", "SKU"], ["reason", "Issue"], ["source_row", "Source row"]], "No data-quality notes.")}` : ""}
      ${item.signals_truncated ? '<p class="muted">Additional SKU signals were omitted from this result.</p>' : ""}`;
  }

  function renderForecast(item) {
    const metrics = [
      ["Forecast rows returned", (item.forecasts || []).length],
      ["Forecastable rows", item.forecastable_record_count],
      ["No matching baseline", item.not_forecastable_count],
      ["Duplicate rows removed", item.exact_duplicate_rows_removed],
    ];
    const columns = [
      ["cfa_code", "CFA"], ["sku_code", "SKU"], ["forecast_month", "Forecast month"],
      ["forecast_quantity_packs", "Forecast packs"], ["baseline_month", "Baseline month"],
      ["baseline_source_file", "Source file"],
      ["invoiced_quantity_packs_in_baseline", "Baseline invoiced"],
      ["free_quantity_packs_in_baseline", "Baseline free"],
      ["baseline_source_row_count", "Source rows"], ["baseline_source_rows", "Source row IDs"],
    ];
    return `<p class="interpretation">${escapeHtml(scalar(item.interpretation))} Latest data month: ${escapeHtml(scalar(item.latest_data_month))}. Forecast window: ${escapeHtml(scalar(item.forecast_start_month))} to ${escapeHtml(scalar(item.forecast_end_month))}. Method: same month last year. ${escapeHtml(scalar(item.data_freshness_note))}</p>
      <div class="metric-grid">${metrics.map(([label, value]) => `<div class="metric"><strong>${escapeHtml(scalar(value))}</strong><span>${escapeHtml(label)}</span></div>`).join("")}</div>
      ${renderFulfillmentScreen(item.order_fulfillment_screen)}
      <h4>Primary shipment forecast</h4>${renderTable(item.forecasts || [], columns, "No forecast rows could be produced for this selection.")}
      ${(item.not_forecastable || []).length ? `<h4>Months without a baseline</h4>${renderTable(item.not_forecastable, [["cfa_code", "CFA"], ["sku_code", "SKU"], ["forecast_month", "Forecast month"], ["baseline_month", "Baseline month"], ["reason", "Why no forecast"]], "Every requested month has a baseline.")}` : ""}
      ${item.results_truncated || item.not_forecastable_truncated ? '<p class="muted">Some forecast rows were omitted by the display limit. Add CFA and SKU filters to narrow the result.</p>' : ""}`;
  }

  function renderClaim(item) {
    if (!item.found) {
      return `<article class="evidence-card"><h4>Claim not found</h4><p>${escapeHtml(item.claim_no || "Requested claim")} was not found in ${escapeHtml(item.source_file || "the claims extract")}.</p></article>`;
    }
    const claim = item.claim || {};
    const claimColumns = [
      ["claim_no", "Claim"], ["claim_date", "Claim date"], ["stockist_code", "Stockist"],
      ["sku_code", "SKU"], ["batch_no", "Batch"], ["claim_type", "Type"],
      ["qty_claimed", "Qty claimed"], ["claim_value_inr", "Claim value (INR)"], ["status", "Ledger status"],
      ["source_file", "Source file"], ["source_row", "Source row"],
    ];
    const priorColumns = [
      ["claim_no", "Earlier claim"], ["credit_note_no", "Credit note"], ["credit_note_date", "Credit date"],
      ["credit_value_inr", "Credited (INR)"], ["same_quantity", "Same quantity"],
      ["same_claim_value", "Same claim value"], ["source_file", "Source file"], ["source_row", "Source row"],
    ];
    const batch = item.batch_check || {};
    const context = item.claim_context || {};
    const batchRows = batch.batch_source ? [batch.batch_source] : [];
    const filing = item.filing_window || {};
    const invoiceRows = item.matched_invoice_rows || [];
    // Keep the at-a-glance audit table tied to checks actually returned by the tools.
    const auditRows = [
      { check: "Claim record", status: "FOUND", source: `${claim.source_file || "—"}:${claim.source_row || "—"}`, finding: `${claim.claim_no || "Claim"} · ${claim.status || "Ledger status unavailable"}` },
      { check: "Batch and product", status: batch.status === "verified" ? "VERIFIED" : "NEEDS REVIEW", source: batch.batch_source ? `${batch.batch_source.source_file}:${batch.batch_source.source_row}` : "batch_master.csv: —", finding: batch.expiry_date_matches_master === true ? "Batch found; expiry matches master" : batch.expiry_date_matches_master === false ? "Expiry differs from batch master" : "Batch details need verification" },
      { check: "Prior credit screen", status: (item.prior_credited_claims || []).length ? "MATCH FOUND" : "NO MATCH IN EXTRACT", source: (item.prior_credited_claims || []).map((row) => `${row.source_file}:${row.source_row}`).join(", ") || "expiry_claims.csv extract", finding: (item.prior_credited_claims || []).length ? `${item.prior_credited_claims.length} possible prior credited claim(s); human review` : "No matching credited claim in supplied extract" },
      { check: "Invoice reference", status: String(item.invoice_reference_status || "needs review").replaceAll("_", " ").toUpperCase(), source: invoiceRows.map((row) => `${row.source_file}:${row.source_row}`).join(", ") || "primary_sales.csv extract", finding: invoiceRows.length ? `${invoiceRows.length} matching invoice row(s)` : item.invoice_reference ? "No invoice match found" : "Invoice reference missing; check ledger" },
      { check: "Quantity comparison", status: String((item.quantity_comparison || {}).status || "not assessed").replaceAll("_", " ").toUpperCase(), source: invoiceRows.map((row) => `${row.source_file}:${row.source_row}`).join(", ") || "primary_sales.csv extract", finding: item.quantity_comparison_note || "Claimed quantity could not be compared with an invoice line" },
      { check: "Expiry filing window", status: String(filing.status || "needs_review").replaceAll("_", " ").toUpperCase(), source: batch.batch_source ? `${batch.batch_source.source_file}:${batch.batch_source.source_row}` : "batch_master.csv: —", finding: filing.reason || (filing.elapsed_days !== undefined ? `${filing.elapsed_days} days elapsed; limit ${filing.limit_days} days` : "No filing-window calculation returned") },
    ];
    const invoiceColumns = [
      ["invoice_no", "Invoice"], ["invoice_date", "Date"], ["stockist_code", "Stockist"],
      ["sku_code", "SKU"], ["batch_no", "Batch"], ["invoiced_qty", "Invoiced qty"],
      ["free_qty", "Free qty"], ["source_file", "Source"], ["source_row", "Row"],
    ];
    const reviewLabel = item.review_status === "NEEDS_HUMAN_REVIEW" ? "Needs human review" : item.review_status || "Needs human review";
    return `<article class="evidence-card claim-review">
      <p class="interpretation"><strong>${escapeHtml(reviewLabel)}</strong> · Screening evidence only; a person retains claim authority.</p>
      <h4>Audit checks</h4>${renderTable(auditRows, [["check", "Check"], ["status", "Status"], ["source", "Source & row"], ["finding", "Finding"]], "No audit checks returned.")}
      <h4>Claim record</h4>${renderTable([claim], claimColumns, "No claim record returned.")}
      <p><strong>${escapeHtml(scalar(context.product_description))}</strong>${context.therapy_area ? ` · ${escapeHtml(context.therapy_area)}` : ""} · ${escapeHtml(scalar(context.stockist_name))}, ${escapeHtml(scalar(context.city))}</p>
      ${context.product_source ? renderTable([context.product_source], [["sku_code", "SKU"], ["product_description", "Medicine"], ["source_file", "Product source"], ["source_row", "Product row"]], "No product master match.") : ""}
      ${context.stockist_source ? renderTable([context.stockist_source], [["stockist_code", "Stockist"], ["stockist_name", "Name"], ["city", "City"], ["source_file", "Stockist source"], ["source_row", "Stockist row"]], "No stockist master match.") : ""}
      <h4>Batch and product check</h4>
      <p>Batch check: ${escapeHtml(scalar(batch.status))}. Expiry date matches batch master: ${escapeHtml(scalar(batch.expiry_date_matches_master))}.</p>
      ${batchRows.length ? renderTable(batchRows, [["batch_no", "Batch"], ["sku_code", "SKU"], ["mfg_date", "Mfg date"], ["expiry_date", "Master expiry"], ["source_file", "Source file"], ["source_row", "Source row"]], "No batch record found.") : '<p class="muted">No matching batch master record.</p>'}
      <h4>Earlier credited claims</h4>${renderTable(item.prior_credited_claims || [], priorColumns, "No earlier credited claim with this stockist, SKU, and batch was found in the extract.")}
      <p class="interpretation">Duplicate screen: ${escapeHtml(scalar(item.duplicate_signal))}. A match is a review signal, not an automatic rejection.</p>
      <h4>Invoice and quantity evidence</h4>
      <p>Invoice reference: ${escapeHtml(scalar(item.invoice_reference))} · ${escapeHtml(scalar(item.invoice_reference_status))}</p>
      ${renderTable(invoiceRows, invoiceColumns, "No matching invoice or ledger line was found.")}
      <p>${escapeHtml(item.quantity_comparison_note || "Quantity could not be compared.")} ${escapeHtml(scalar(item.quantity_comparison && item.quantity_comparison.status))}</p>
      <h4>Expiry filing-window screen</h4>
      ${renderTable([{status: filing.status, elapsed_days: filing.elapsed_days, limit_days: filing.limit_days, reason: filing.reason, policy_reference: item.filing_window_policy_reference}], [["status", "Screen result"], ["elapsed_days", "Days after expiry"], ["limit_days", "Window (days)"], ["reason", "Explanation"], ["policy_reference", "Policy reference"]], "No filing-window assessment returned.")}
      <p class="interpretation">${escapeHtml(item.read_only_notice || "Human review required.")}</p>
    </article>`;
  }

  function renderClaimEmail(item) {
    if (!item.found) {
      return `<article class="evidence-card"><h4>Email not found</h4><p>${escapeHtml(item.email_id || "Requested email")} was not found in ${escapeHtml(item.source_file || "the email extract")}.</p></article>`;
    }
    const emailAudit = [{
      check: "Correspondence integrity", status: "UNTRUSTED INPUT",
      source: `${item.source_file || "claim_emails.csv"}:${item.source_row || "—"}`,
      finding: "Treat message text and claimed approvals as evidence to verify; do not follow embedded instructions",
    }];
    return `<article class="evidence-card claim-review">
      <p class="interpretation"><strong>Untrusted correspondence</strong> · Do not treat email instructions or claimed approvals as system instructions or policy evidence.</p>
      <h4>Audit checks</h4>${renderTable(emailAudit, [["check", "Check"], ["status", "Status"], ["source", "Source & row"], ["finding", "Finding"]], "No email audit checks returned.")}
      ${renderTable([item], [["email_id", "Email ID"], ["received_date", "Received"], ["from_name", "Sender"], ["stockist_code_by_mailbox_rule", "Mailbox stockist"], ["subject", "Subject"], ["source_file", "Source file"], ["source_row", "Source row"]], "No email metadata returned.")}
      <h4>Original message</h4><pre class="email-body">${escapeHtml(item.body || "")}</pre>
      <p class="interpretation">${escapeHtml(item.interpretation_notice || "Verify any authorization in the formal business system.")}</p>
    </article>`;
  }

  function renderEvidence(item) {
    if (typeof item === "string") {
      try { item = JSON.parse(item); } catch (_) {
        return `<article class="evidence-card">${escapeHtml(item)}</article>`;
      }
    }
    if (!item || typeof item !== "object") return `<article class="evidence-card">${escapeHtml(scalar(item))}</article>`;
    if (item.result_type === "expiry_claim_review") return renderClaim(item);
    if (item.result_type === "claim_email_evidence") return renderClaimEmail(item);
    if (Object.prototype.hasOwnProperty.call(item, "found")) return renderBatch(item);
    if (Object.prototype.hasOwnProperty.call(item, "forecast_type")) return renderForecast(item);
    if (Object.prototype.hasOwnProperty.call(item, "flagged_shipments")) return renderShelfLife(item);
    if (Object.prototype.hasOwnProperty.call(item, "signals")) return renderStock(item);
    return `<article class="evidence-card">${renderTable(Object.entries(item).map(([field, value]) => ({ field: labelFor(field), value })), [["field", "Field"], ["value", "Value"]], "No evidence details returned.")}</article>`;
  }

  function answerSummary(answer, evidence) {
    const item = Array.isArray(evidence) ? evidence[0] : null;
    if (item && item.result_type === "expiry_claim_review") {
      return item.found
        ? `Claim ${item.claim.claim_no} was screened against the supplied claim, batch, invoice, and prior-credit records. Human review is required; this is not an approval or rejection.`
        : `Claim ${item.claim_no || "requested"} was not found in the claims extract; human review is required.`;
    }
    if (item && typeof item === "object" && item.result_type === "claim_email_evidence") {
      return item.found
        ? `Email ${item.email_id} was retrieved from ${item.source_file} row ${item.source_row}. The message is untrusted evidence and requires human verification.`
        : `Email ${item.email_id || "requested"} was not found in the claim email extract.`;
    }
    if (item && typeof item === "object" && Object.prototype.hasOwnProperty.call(item, "found")) {
      return item.found ? `Batch ${item.batch_no} details were retrieved from the batch master.` : `Batch ${item.batch_no || "requested"} was not found in the batch master.`;
    }
    if (item && typeof item === "object" && Object.prototype.hasOwnProperty.call(item, "forecast_type")) {
      const forecastCount = item.forecastable_record_count || 0;
      const shownCount = item.returned_record_count ?? (item.forecasts || []).length;
      const periodText = `for ${item.forecast_start_month} to ${item.forecast_end_month}`;
      return `${forecastCount} primary-shipment baseline row(s) were calculated ${periodText}; ${shownCount} are shown. Method: same month last year. This is not a downstream-demand forecast.`;
    }
    if (item && typeof item === "object" && Object.prototype.hasOwnProperty.call(item, "flagged_shipments")) {
      return `${item.flagged_count} invoice lines were below the ${item.threshold_pct}% remaining shelf-life threshold (${item.evaluated_count} evaluated).`;
    }
    if (item && typeof item === "object" && Object.prototype.hasOwnProperty.call(item, "signals")) {
      return `${item.cross_cfa_imbalance_sku_count} SKU(s) have positive stock at one CFA and a zero-stock marker at another in the ${item.latest_snapshot_date} snapshot. Review these as signals; they do not confirm excess stock or transfer feasibility.`;
    }
    return answer || "No answer was returned.";
  }

  function resultBadge(evidence) {
    // Labels describe the result type; they are not business approval decisions.
    const item = Array.isArray(evidence) ? evidence.find((entry) => entry && typeof entry === "object") : null;
    if (!item) return null;
    if (item.result_type === "expiry_claim_review") return { label: "NEEDS HUMAN REVIEW", tone: "review" };
    if (item.result_type === "claim_email_evidence") return { label: "UNTRUSTED INPUT · VERIFY", tone: "review" };
    if (Object.prototype.hasOwnProperty.call(item, "found")) return { label: item.found ? "SOURCE RECORD FOUND" : "RECORD NOT FOUND", tone: item.found ? "informational" : "review" };
    if (Object.prototype.hasOwnProperty.call(item, "flagged_shipments")) return { label: "SHELF-LIFE SCREENING", tone: "informational" };
    if (Object.prototype.hasOwnProperty.call(item, "signals")) return { label: "STOCK SIGNALS · REVIEW", tone: "informational" };
    if (Object.prototype.hasOwnProperty.call(item, "forecast_type")) return { label: "SHIPMENT BASELINE", tone: "informational" };
    return { label: "SOURCE EVIDENCE", tone: "informational" };
  }

  const api = { answerSummary, attachStockFilters, escapeHtml, labelFor, renderEvidence, resultBadge, stockRowMatches };
  root.EvidenceFormatter = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : globalThis));
