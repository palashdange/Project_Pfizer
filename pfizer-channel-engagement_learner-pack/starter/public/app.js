// Calls the FastAPI backend. Same origin, so no CORS setup is needed.
const form = document.getElementById("ask");
const questionInput = document.getElementById("q");
const askButton = form.querySelector("button");

// Presets and historical scenario replays share the same evidence-backed API flow.
document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question || "";
    form.requestSubmit();
  });
});

// Each section owns a result panel; ids share a prefix ("" for claims, "scheme-" for schemes).
function panel(prefix) {
  const get = (id) => document.getElementById(prefix + id);
  return {
    status: get("status"), output: get("out"), answer: get("answer"), decisionBadge: get("decision-badge"),
    decisionOwner: get("decision-owner"), evidence: get("evidence"), rawEvidence: get("raw-evidence"),
    rawDetails: get("raw-details"),
  };
}

async function askAndRender(question, ui, controls) {
  // Start with a clean result area so the prior answer is not mistaken for this one.
  ProgressMessages.clearPreviousOutput(ui);
  controls.forEach((el) => { el.disabled = true; });
  const stopStatusCycle = ProgressMessages.startStatusCycle(ui.status, [
    "Thinking…",
    "Checking the sources…",
    "Validating the evidence…",
    "Preparing the answer…",
  ]);
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Server returned ${res.status}`);
    const evidence = Array.isArray(data.evidence) ? data.evidence : [];
    ui.answer.textContent = EvidenceFormatter.answerSummary(data.answer, evidence);
    // Show a carefully named result state; this pilot never turns screening into an approval.
    const badge = EvidenceFormatter.resultBadge(evidence, data.route);
    ui.decisionBadge.hidden = !badge;
    ui.decisionBadge.textContent = badge ? badge.label : "";
    ui.decisionBadge.className = badge ? `decision-badge ${badge.tone}` : "decision-badge";
    ui.decisionOwner.textContent = EvidenceFormatter.decisionOwner(data.route);
    ui.decisionOwner.hidden = !ui.decisionOwner.textContent;
    ui.evidence.innerHTML = evidence.length
      ? evidence.map((item) => EvidenceFormatter.renderEvidence(item)).join("")
      : '<p class="muted">No source evidence was returned for this answer.</p>';
    // Bind the stock filters after evidence cards have been rendered into the page.
    EvidenceFormatter.attachStockFilters(ui.evidence);
    ui.rawEvidence.textContent = evidence.length ? JSON.stringify(evidence, null, 2) : "No tool was called.";
    ui.output.hidden = false;
    ui.status.textContent = `${data.model_calls} model call(s) · ${data.elapsed_seconds ?? "—"} seconds`;
  } catch (err) {
    ui.status.textContent = `Something went wrong: ${err.message}. Check /api/health and the logs.`;
  } finally {
    stopStatusCycle();
    controls.forEach((el) => { el.disabled = false; });
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (question) askAndRender(question, panel(""), [questionInput, askButton]);
});

// Scheme check: same graph, result shown in the scheme section's own panel.
const schemeButton = document.getElementById("scheme-run");
if (schemeButton) {
  const schemeSelect = document.getElementById("scheme-target");
  schemeButton.addEventListener("click", () => {
    askAndRender(`Review quarter-end scheme ${schemeSelect.value} against the policy.`,
      panel("scheme-"), [schemeSelect, schemeButton]);
  });
}
