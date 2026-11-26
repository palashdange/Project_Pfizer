// Batch mode: route a month (or every month) of register claims in code and show rupees by route.
// Pure rendering lives in BatchView so Node tests can check it without a browser.
(function (root) {
  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // Indian convention: 1 lakh = 100,000 and 1 crore = 100 lakh.
  function formatLakh(value) {
    const amount = Number(value);
    if (!Number.isFinite(amount)) return "—";
    if (Math.abs(amount) >= 1e7) return `₹${(amount / 1e7).toFixed(2)} cr`;
    return `₹${(amount / 1e5).toFixed(2)} L`;
  }

  function formatInr(value) {
    const amount = Number(value);
    if (value === null || value === undefined || !Number.isFinite(amount)) return "not known";
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(amount);
  }

  const ROUTE_LABEL = { RECOMMEND_CREDIT: "Credit recommended", REJECT: "Reject", NEEDS_PERSON: "Needs a person" };
  const ROUTE_TONE = { RECOMMEND_CREDIT: "recommend", REJECT: "reject", NEEDS_PERSON: "review" };

  function renderBatch(result) {
    const annual = result.annualised_inr || {};
    const period = result.period_inr || {};
    const counts = result.route_counts || {};
    const perYear = result.months === 1 ? "× 12 (one month)" : `÷ ${result.months} months × 12`;
    const cards = [
      ["Leakage stopped / year", annual.leakage, `${formatInr(period.leakage)} in the period. Already credited; invalid under §5.2 window, §5.6 repeat, or excess packs under §5.5.`],
      ["Credited claims the rules reject / year", annual.caught, `${formatInr(period.caught)} in the period. Whole credit value of those claims.`],
      ["At risk: needs a person / year", annual.at_risk, `${formatInr(period.at_risk)} in the period. Already credited without the check passing. At risk, not saved.`],
      ["Pending claims it would block / year", annual.would_block, `${formatInr(period.would_block)} in the period. Not yet credited.`],
    ];
    const claims = Array.isArray(result.claims) ? result.claims : null;
    const head = '<thead><tr><th scope="col">Claim</th><th scope="col">Register status</th><th scope="col">Pilot route</th><th scope="col">₹ at stake</th><th scope="col">First problem (clause)</th><th scope="col">Source</th></tr></thead>';
    const rowsHtml = (list) => list.map((c) => `<tr>
          <td>${escapeHtml(c.claim_no)}<br><span class="muted">${escapeHtml(c.claim_date)} · ${escapeHtml(c.claim_type)}</span></td>
          <td>${escapeHtml(c.register_status)}</td>
          <td><span class="decision-badge ${ROUTE_TONE[c.route] || "review"}">${escapeHtml(ROUTE_LABEL[c.route] || c.route)}</span></td>
          <td>${escapeHtml(formatInr(c.at_stake_inr))}</td>
          <td>${escapeHtml(c.first_problem || "All checks pass")}</td>
          <td>${escapeHtml(c.source)}</td>
        </tr>`).join("");
    // Rejects and needs-a-person come first from the API; show those up front, the rest on request.
    const SHOWN = 15;
    const table = !claims ? '<p class="muted">Pick a quarter or a month to list its claims.</p>' : `
      <div class="table-wrap"><table>${head}<tbody>${rowsHtml(claims.slice(0, SHOWN))}</tbody></table></div>
      ${claims.length > SHOWN ? `<details class="more-claims"><summary>Show the other ${claims.length - SHOWN} claims</summary>
        <div class="table-wrap"><table>${head}<tbody>${rowsHtml(claims.slice(SHOWN))}</tbody></table></div></details>` : ""}`;
    return `
      <p class="card-subtitle">${escapeHtml(result.claims_reviewed)} claims · ${escapeHtml(result.period)} · annualised ${escapeHtml(perYear)}</p>
      <div class="metric-grid">${cards.map(([label, value, note]) => `
        <div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(formatLakh(value))}</strong><span>${escapeHtml(note)}</span></div>`).join("")}
      </div>
      <p class="hint">Routes: ${escapeHtml(counts.RECOMMEND_CREDIT ?? 0)} recommend credit (${escapeHtml(formatLakh(annual.recommend_credit))}/year) · ${escapeHtml(counts.REJECT ?? 0)} reject · ${escapeHtml(counts.NEEDS_PERSON ?? 0)} needs a person.${result.missing_value_claims ? ` ${escapeHtml(result.missing_value_claims)} claim(s) have no value and are left out of the sums.` : ""}</p>
      ${table}
      <p class="citation">Source: ${escapeHtml(result.source || "expiry_claims.csv")} Same checks as a single review; no model calls. A person decides every claim.</p>`;
  }

  // Picker options from /api/batch/periods: all months, then years, quarters and months, newest first.
  function periodOptions(periods) {
    const count = (n) => `${Number(n || 0).toLocaleString("en-IN")} claims`;
    const option = (p, label) => `<option value="${escapeHtml(p.value)}">${escapeHtml(label)} · ${escapeHtml(count(p.claims))}</option>`;
    const all = periods.all ? option(periods.all, `All months · ${periods.all.span}`) : '<option value="">All months in the register</option>';
    const group = (label, list, text) => (list && list.length
      ? `<optgroup label="${escapeHtml(label)}">${list.map((p) => option(p, text(p))).join("")}</optgroup>` : "");
    return all
      + group("Financial years", periods.years, (p) => `${p.value} · ${p.span}`)
      + group("Quarters", periods.quarters, (p) => `${p.value} · ${p.span}`)
      + group("Months", periods.months, (p) => p.span);
  }

  const api = { formatLakh, periodOptions, renderBatch };
  root.BatchView = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;

  // Wire the page only in a browser.
  if (typeof document === "undefined") return;
  const select = document.getElementById("batch-month");
  const button = document.getElementById("batch-run");
  const status = document.getElementById("batch-status");
  const out = document.getElementById("batch-out");
  if (!select || !button) return;

  async function run() {
    button.disabled = true;
    select.disabled = true;
    status.textContent = select.value ? "Checking the claims in this period…" : "Checking every claim in the register (first run takes about half a minute)…";
    try {
      const res = await fetch("/api/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(select.value ? { month: select.value } : {}),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `Server returned ${res.status}`);
      out.innerHTML = renderBatch(data);
      out.hidden = false;
      status.textContent = "";
    } catch (err) {
      status.textContent = `Something went wrong: ${err.message}.`;
    } finally {
      button.disabled = false;
      select.disabled = false;
    }
  }
  button.addEventListener("click", run);

  // Fill the picker as soon as the page opens; counting claims per period needs no routing.
  fetch("/api/batch/periods")
    .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`Server returned ${res.status}`))))
    .then((periods) => { select.innerHTML = periodOptions(periods); })
    .catch(() => { /* Keep "All months"; the batch still runs. */ });
}(typeof window !== "undefined" ? window : globalThis));
