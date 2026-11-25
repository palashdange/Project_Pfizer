/* Search-as-you-type for the claim-review box.
   Suggests register claims (pending first) and claim emails from /api/claims/search. Picking one
   reviews it at once; anything else typed or pasted still goes to the review as free text. */
(function (root) {
  "use strict";

  const STATUS_TONE = { Pending: "review", Credited: "recommend", Rejected: "reject" };

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function formatDate(iso) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(iso || "")) return "";
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
  }

  function formatRupees(value) {
    const amount = Number(value);
    if (value === "" || !Number.isFinite(amount)) return "";
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);
  }

  // One option row: claim number, status and ₹ on top; stockist, type and date; product and batch.
  function renderOption(row, index) {
    const id = `claim-option-${index}`;
    if (row.kind === "email") {
      return `<li id="${id}" role="option" class="combo-option" data-value="${escapeHtml(row.id)}" data-kind="email" aria-selected="false">
        <div class="opt-top"><strong>${escapeHtml(row.id)}</strong><span class="decision-badge informational">Claim email</span></div>
        <div class="opt-line">From ${escapeHtml(row.from_name)} · ${escapeHtml(formatDate(row.claim_date))}</div>
        <div class="opt-line muted">${escapeHtml(row.subject)}</div></li>`;
    }
    return `<li id="${id}" role="option" class="combo-option" data-value="${escapeHtml(row.id)}" data-kind="claim" aria-selected="false">
      <div class="opt-top"><strong>${escapeHtml(row.id)}</strong>
        <span class="decision-badge ${STATUS_TONE[row.status] || "informational"}">${escapeHtml(row.status)}</span>
        <span class="opt-value">${escapeHtml(formatRupees(row.value_inr))}</span></div>
      <div class="opt-line">${escapeHtml(row.stockist_name)}, ${escapeHtml(row.city)} · ${escapeHtml(row.claim_type)} · ${escapeHtml(formatDate(row.claim_date))}</div>
      <div class="opt-line muted">${escapeHtml(row.product)} · ${escapeHtml(row.sku_code)} · batch ${escapeHtml(row.batch_no)}</div></li>`;
  }

  function summaryText(data, shown) {
    const total = data.total_claims || 0;
    if (!total && !shown) return "";
    const scope = data.pending_only ? "pending claims" : "claims";
    return total > shown ? `Showing ${shown} of ${total.toLocaleString("en-IN")} ${scope}. Type more to narrow.` : `${total.toLocaleString("en-IN")} matching ${scope}.`;
  }

  const api = { formatDate, formatRupees, renderOption, summaryText };
  root.ClaimSearch = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;

  // Wire the page only in a browser that has the search box.
  if (typeof document === "undefined") return;
  const input = document.getElementById("q");
  const list = document.getElementById("claim-options");
  const form = document.getElementById("ask");
  const pendingOnly = document.getElementById("pending-only");
  const count = document.getElementById("combo-count");
  if (!input || !list || !form) return;

  let options = [];
  let active = -1;
  let timer = null;
  let requestId = 0;

  function close() {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    active = -1;
  }

  function setActive(index) {
    options.forEach((el, i) => el.setAttribute("aria-selected", String(i === index)));
    active = index;
    if (index >= 0 && options[index]) {
      input.setAttribute("aria-activedescendant", options[index].id);
      options[index].scrollIntoView({ block: "nearest" });
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  function choose(el) {
    input.value = el.dataset.value;
    close();
    form.requestSubmit();
  }

  async function search() {
    const query = input.value.trim();
    // Long pasted text is a claim email or details, not a search: leave it for the review.
    if (query.length > 60 || query.includes("\n")) { close(); return; }
    const mine = ++requestId;
    try {
      const params = new URLSearchParams({ q: query, pending_only: pendingOnly && pendingOnly.checked ? "true" : "false", limit: "20" });
      const res = await fetch(`/api/claims/search?${params}`);
      if (!res.ok || mine !== requestId) return;
      const data = await res.json();
      const rows = data.results || [];
      const shown = rows.filter((row) => row.kind === "claim").length;
      if (count) count.textContent = query ? summaryText(data, shown) : `${(data.pending_in_register || 0).toLocaleString("en-IN")} pending claims to review · ${data.pending_only ? "" : "pending shown first"}`.replace(/ · $/, "");
      list.innerHTML = rows.length
        ? rows.map(renderOption).join("") + (shown < (data.total_claims || 0) ? `<li class="combo-footer" role="presentation">${escapeHtml(summaryText(data, shown))}</li>` : "")
        : `<li class="combo-footer" role="presentation">No claim matches “${escapeHtml(query)}”. Press Review to read this text with AI instead.</li>`;
      options = [...list.querySelectorAll(".combo-option")];
      options.forEach((el) => el.addEventListener("mousedown", (event) => { event.preventDefault(); choose(el); }));
      list.hidden = document.activeElement !== input;
      input.setAttribute("aria-expanded", String(!list.hidden));
      setActive(-1);
    } catch (_) {
      close();  // Search is a convenience; typing a claim number still works without it.
    }
  }

  function scheduleSearch() {
    clearTimeout(timer);
    timer = setTimeout(search, 180);
  }

  input.addEventListener("input", scheduleSearch);
  input.addEventListener("focus", scheduleSearch);
  input.addEventListener("blur", () => setTimeout(close, 120));
  if (pendingOnly) pendingOnly.addEventListener("change", () => { input.focus(); scheduleSearch(); });
  input.addEventListener("keydown", (event) => {
    if (list.hidden && event.key === "ArrowDown") { scheduleSearch(); return; }
    if (event.key === "ArrowDown" && options.length) { event.preventDefault(); setActive((active + 1) % options.length); }
    else if (event.key === "ArrowUp" && options.length) { event.preventDefault(); setActive(active <= 0 ? options.length - 1 : active - 1); }
    else if (event.key === "Enter" && !list.hidden && active >= 0) { event.preventDefault(); choose(options[active]); }
    else if (event.key === "Escape") { close(); }
  });
  form.addEventListener("submit", close);
}(typeof window !== "undefined" ? window : globalThis));
