/* Cycle one in-place status message while a question is being processed. */
(function (root) {
  "use strict";

  function clearPreviousOutput(elements) {
    elements.output.hidden = true;
    elements.answer.textContent = "";
    // Clear the previous result state with the answer to avoid a stale verdict badge.
    if (elements.decisionBadge) {
      elements.decisionBadge.textContent = "";
      elements.decisionBadge.hidden = true;
    }
    if (elements.decisionOwner) {
      elements.decisionOwner.textContent = "";
      elements.decisionOwner.hidden = true;
    }
    if (elements.flow) {
      elements.flow.replaceChildren();
      elements.flow.hidden = true;
    }
    elements.evidence.replaceChildren();
    elements.rawEvidence.textContent = "";
    elements.rawDetails.open = false;
  }

  function startStatusCycle(element, messages, intervalMs = 1500, timerApi = globalThis) {
    const steps = messages.length ? messages : ["Working…"];
    let index = 0;
    element.textContent = steps[index];
    const timer = timerApi.setInterval(() => {
      index = (index + 1) % steps.length;
      // textContent replaces the existing message instead of adding another line.
      element.textContent = steps[index];
    }, intervalMs);
    return () => timerApi.clearInterval(timer);
  }

  const api = { clearPreviousOutput, startStatusCycle };
  root.ProgressMessages = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : globalThis));
