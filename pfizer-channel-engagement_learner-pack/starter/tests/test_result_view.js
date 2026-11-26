const test = require("node:test");
const assert = require("node:assert/strict");

const E = require("../public/evidence.js");
const ClaimSearch = require("../public/claim-search.js");

const duplicateChecks = {
  window: { status: "pass", reason: "-19 days from batch expiry.", policy_clause: "CO-POL-014 §5.2" },
  duplicate: { status: "fail", reason: "Earlier credited claim with the same quantity: CLM-2603-01616 (272 packs, Credited).", policy_clause: "CO-POL-014 §5.6", evidence_rows: [{ file: "expiry_claims.csv", source_row: 3269 }] },
  invoice_ref: { status: "missing", reason: "Original invoice reference is blank.", policy_clause: "CO-POL-014 §5.4" },
  value: { status: "pass", reason: "Claim value is 26846.4; quantity × PTS is 26846.4.", policy_clause: "CO-POL-014 §5.7" },
};

test("long numbers in findings get Indian grouping; identifiers, rows and dates do not", () => {
  assert.equal(E.formatNumbersInText("Claim value is 26846.4; above cap 11026604.20."), "Claim value is 26,846.40; above cap 1,10,26,604.20.");
  const untouched = "CLM-2603-01616 (272 packs), 2457 packs, 30-09-2025, expiry_claims.csv:3596, -19 days";
  assert.equal(E.formatNumbersInText(untouched), untouched);
});

test("why lists only the checks that did not pass, in plain words with their rule", () => {
  const why = E.reasons(duplicateChecks);
  assert.deepEqual(why.map((r) => [r.name, r.status]), [["Not claimed before", "fail"], ["Has a matching invoice", "missing"]]);
  assert.equal(why[0].clause, "CO-POL-014 §5.6");
});

test("next step is written by code for each route and never says the tool posted anything", () => {
  const reject = E.nextSteps("REJECT", duplicateChecks, []);
  assert.match(reject[0], /Do not raise a credit note/);
  assert.match(reject[0], /§5\.6/);
  assert.doesNotMatch(reject[0], /§5\.4/);  // a missing invoice is not a reason to reject
  const credit = E.nextSteps("RECOMMEND_CREDIT", {}, [{ at_stake_inr: "3936.80" }]);
  assert.match(credit[0], /₹3,936\.8/);
  assert.match(credit[0], /does not post it/);
  const person = E.nextSteps("NEEDS_PERSON", { invoice_ref: duplicateChecks.invoice_ref }, [], { email: true });
  assert.match(person[0], /email as unverified/);
  assert.match(person[1], /Area Manager's written approval/);
  assert.deepEqual(E.nextSteps("SCHEME_WITHIN_POLICY", {}, []), ["No action needed."]);
  assert.match(E.nextSteps("SCHEME_NEEDS_REVIEW", { cap: { status: "fail" } }, [])[0], /CFO's approval/);
});

test("plain route labels, headlines and the code-vs-AI label", () => {
  assert.deepEqual(E.resultBadge([], "RECOMMEND_CREDIT"), { label: "Credit recommended", tone: "recommend" });
  assert.deepEqual(E.resultBadge([], "NEEDS_PERSON"), { label: "Needs a person", tone: "review" });
  assert.match(E.headline("NOT_FOUND", [{ result_type: "claim_review" }]), /no AI was used/);
  assert.match(E.aiLabel("model"), /written by AI, then checked by code/);
  assert.match(E.aiLabel("code"), /written by code/);
  assert.equal(E.aiLabel(""), "");
  assert.equal(E.usageText(0, 0.4), "No AI used: code only · 0.4 s");
  assert.match(E.usageText(2, 3.1), /AI used 2× \(to read your text and write the explanation\)/);
});

test("check tables use plain names and coloured results, with source rows behind a toggle", () => {
  const html = E.renderEvidence({ result_type: "claim_review", claim_no: "CLM-2605-04488", checks: duplicateChecks, at_stake_inr: "26846.40" });
  assert.match(html, /Not claimed before/);
  assert.match(html, /<span class="status-badge fail">Failed<\/span>/);
  assert.match(html, /<span class="status-badge missing">Can&#39;t check<\/span>/);
  assert.match(html, /26,846\.40/);
  assert.match(html, /class="src">Source &amp; row: expiry_claims\.csv:3269/);
  assert.match(html, /data-source-toggle/);
});

test("claim search rows show stockist, type, date, product, batch, status and ₹, escaped", () => {
  const html = ClaimSearch.renderOption({
    kind: "claim", id: "CLM-2605-04488", status: "Credited", value_inr: "26846.4", stockist_name: "Sharma <b>Medical</b>",
    city: "Ludhiana", claim_type: "Expired", claim_date: "2026-05-12", product: "Azithromycin 500 mg tablets", sku_code: "PFL1001", batch_no: "K2310408",
  }, 0);
  assert.match(html, /CLM-2605-04488/);
  assert.match(html, /Credited/);
  assert.match(html, /₹26,846/);
  assert.match(html, /Sharma &lt;b&gt;Medical&lt;\/b&gt;, Ludhiana · Expired · 12 May 2026/);
  assert.match(html, /Azithromycin 500 mg tablets · PFL1001 · batch K2310408/);
  assert.match(ClaimSearch.renderOption({ kind: "email", id: "EML-017", from_name: "X", subject: "S", claim_date: "2026-10-01" }, 1), /Claim email/);
  assert.equal(ClaimSearch.summaryText({ total_claims: 328, pending_only: false }, 20), "Showing 20 of 328 claims. Type more to narrow.");
});

test("batch picker groups financial years, quarters and months with claim counts", () => {
  const { periodOptions } = require("../public/batch.js");
  const html = periodOptions({
    all: { value: "", span: "Apr 2024–Sep 2026", claims: 4503 },
    years: [{ value: "FY27", span: "Apr–Sep 2026 so far", claims: 1189 }],
    quarters: [{ value: "FY27 Q2", span: "Jul–Sep 2026", claims: 631 }],
    months: [{ value: "2026-09", span: "Sep 2026", claims: 229 }],
  });
  assert.match(html, /^<option value="">All months · Apr 2024–Sep 2026 · 4,503 claims<\/option>/);
  assert.match(html, /<optgroup label="Financial years"><option value="FY27">FY27 · Apr–Sep 2026 so far · 1,189 claims<\/option>/);
  assert.match(html, /<optgroup label="Quarters"><option value="FY27 Q2">FY27 Q2 · Jul–Sep 2026 · 631 claims/);
  assert.match(html, /<optgroup label="Months"><option value="2026-09">Sep 2026 · 229 claims/);
});
