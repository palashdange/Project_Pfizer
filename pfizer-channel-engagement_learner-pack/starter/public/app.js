// Calls the FastAPI backend. Same origin, so no CORS setup is needed.
const form = document.getElementById("ask");
const status = document.getElementById("status");
const questionInput = document.getElementById("q");
const askButton = form.querySelector("button");

// Presets and historical scenario replays share the same evidence-backed API flow.
document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question || "";
    form.requestSubmit();
  });
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  // Start each question with a clean result area so the prior answer is not mistaken for this one.
  const output = document.getElementById("out");
  ProgressMessages.clearPreviousOutput({
    output,
    answer: document.getElementById("answer"),
    decisionBadge: document.getElementById("decision-badge"),
    decisionOwner: document.getElementById("decision-owner"),
    evidence: document.getElementById("evidence"),
    rawEvidence: document.getElementById("raw-evidence"),
    rawDetails: document.querySelector(".raw-details"),
  });
  questionInput.disabled = true;
  askButton.disabled = true;
  const stopStatusCycle = ProgressMessages.startStatusCycle(status, [
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
    document.getElementById("answer").textContent = EvidenceFormatter.answerSummary(data.answer, evidence);
    // Show a carefully named result state; this pilot never turns screening into an approval.
    const decisionBadge = document.getElementById("decision-badge");
    const badge = EvidenceFormatter.resultBadge(evidence, data.route);
    decisionBadge.hidden = !badge;
    decisionBadge.textContent = badge ? badge.label : "";
    decisionBadge.className = badge ? `decision-badge ${badge.tone}` : "decision-badge";
    const owner = document.getElementById("decision-owner");
    owner.textContent = EvidenceFormatter.decisionOwner(data.route);
    owner.hidden = !owner.textContent;
    const evidencePanel = document.getElementById("evidence");
    evidencePanel.innerHTML = evidence.length
      ? evidence.map((item) => EvidenceFormatter.renderEvidence(item)).join("")
      : '<p class="muted">No source evidence was returned for this answer.</p>';
    // Bind the stock filters after evidence cards have been rendered into the page.
    EvidenceFormatter.attachStockFilters(evidencePanel);
    document.getElementById("raw-evidence").textContent = evidence.length
      ? JSON.stringify(evidence, null, 2)
      : "No tool was called.";
    output.hidden = false;
    status.textContent = `${data.model_calls} model call(s) · ${data.elapsed_seconds ?? "—"} seconds`;
  } catch (err) {
    status.textContent = `Something went wrong: ${err.message}. Check /api/health and the logs.`;
  } finally {
    stopStatusCycle();
    questionInput.disabled = false;
    askButton.disabled = false;
  }
});

// Scheme check: send the chosen quarter through the same graph and show it in the result card.
const schemeButton = document.getElementById("scheme-run");
if (schemeButton) {
  schemeButton.addEventListener("click", () => {
    const target = document.getElementById("scheme-target").value;
    questionInput.value = `Review quarter-end scheme ${target} against the policy.`;
    form.requestSubmit();
    status.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}
