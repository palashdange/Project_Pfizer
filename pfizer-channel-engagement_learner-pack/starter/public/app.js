// Calls the FastAPI backend. Same origin, so no CORS setup is needed.
// Used by the pilot page (/) and the demo page (/demos); each element is optional.
const form = document.getElementById("ask");
const questionInput = document.getElementById("q");
const askButton = form ? form.querySelector("button") : null;

// Each section owns a result panel; ids share a prefix ("" for claims, "scheme-" for schemes).
function panel(prefix) {
  const get = (id) => document.getElementById(prefix + id);
  return {
    status: get("status"), output: get("out"), answer: get("answer"), decisionBadge: get("decision-badge"),
    decisionOwner: get("decision-owner"), evidence: get("evidence"), rawEvidence: get("raw-evidence"),
    rawDetails: get("raw-details"), flow: get("flow"),
    headline: get("headline"), why: get("why"), next: get("next"), aiLabel: get("ai-label"),
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
    const E = EvidenceFormatter;
    ui.answer.textContent = E.answerSummary(data.answer, evidence);
    // Show a carefully named result state; this pilot never turns screening into an approval.
    const badge = E.resultBadge(evidence, data.route);
    ui.decisionBadge.hidden = !badge;
    ui.decisionBadge.textContent = badge ? badge.label : "";
    ui.decisionBadge.className = badge ? `decision-badge ${badge.tone}` : "decision-badge";
    if (ui.headline) ui.headline.textContent = E.headline(data.route, evidence) || "Result";
    // Why and next step are written by code from the checks, not by the model.
    const checks = data.checks || {};
    const why = E.reasons(checks);
    if (ui.why) {
      const total = Object.keys(checks).length;
      ui.why.innerHTML = why.length
        ? `<h4>Why</h4><ul class="why-list">${why.map((r) => `<li>${E.statusBadge(r.status)} <strong>${E.escapeHtml(r.name)}</strong>: ${E.escapeHtml(r.text)}${r.clause ? ` <span class="clause">${E.escapeHtml(r.clause)}</span>` : ""}</li>`).join("")}</ul>`
        : total ? `<h4>Why</h4><p>All ${total} checks passed.</p>` : "";
      ui.why.hidden = !ui.why.innerHTML;
    }
    if (ui.next) {
      const steps = E.nextSteps(data.route, checks, evidence, { email: /\bEML-\d+/i.test(question) });
      ui.next.innerHTML = steps.length ? `<h4>Next step</h4><ul>${steps.map((step) => `<li>${E.escapeHtml(step)}</li>`).join("")}</ul>` : "";
      ui.next.hidden = !steps.length;
    }
    ui.decisionOwner.textContent = E.decisionOwner(data.route);
    ui.decisionOwner.hidden = !ui.decisionOwner.textContent;
    if (ui.aiLabel) {
      ui.aiLabel.textContent = E.aiLabel(data.explanation_source) || "Summary · written by code";
      ui.aiLabel.className = `ai-label ${data.explanation_source === "model" ? "model" : "code"}`;
      ui.aiLabel.hidden = false;
    }
    ui.evidence.innerHTML = evidence.length
      ? evidence.map((item) => E.renderEvidence(item)).join("")
      : '<p class="muted">No source evidence was returned for this answer.</p>';
    // Bind the stock filters and source toggles after evidence cards are in the page.
    E.attachStockFilters(ui.evidence);
    E.attachSourceToggles(ui.evidence);
    ui.rawEvidence.textContent = evidence.length ? JSON.stringify(evidence, null, 2) : "No tool was called.";
    ui.output.hidden = false;
    // Replay the route the request took through the LangGraph graph.
    if (ui.flow && window.FlowView) FlowView.render(ui.flow, data);
    ui.status.textContent = EvidenceFormatter.usageText(data.model_calls, data.elapsed_seconds);
  } catch (err) {
    ui.status.textContent = `Something went wrong: ${err.message}. Check /api/health and the logs.`;
  } finally {
    stopStatusCycle();
    controls.forEach((el) => { el.disabled = false; });
  }
}

if (form) {
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (question) askAndRender(question, panel(""), [questionInput, askButton]);
  });
}

// Demo page: each case runs its check-set input into the single result panel.
const demoButtons = [...document.querySelectorAll("[data-demo]")];
demoButtons.forEach((button) => {
  button.addEventListener("click", () => {
    askAndRender(button.dataset.demo, panel(""), demoButtons);
    document.getElementById("status").scrollIntoView({ behavior: "smooth", block: "start" });
  });
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

// Stock review for the Head of Supply Chain: same graph, result in section 4's own panel.
const stockButton = document.getElementById("stock-run");
if (stockButton) {
  const stockSelect = document.getElementById("stock-target");
  stockButton.addEventListener("click", () => {
    askAndRender(`Stock review ${stockSelect.value} for every C&F.`, panel("stock-"), [stockSelect, stockButton]);
  });
}
