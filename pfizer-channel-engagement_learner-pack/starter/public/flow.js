// LangGraph flow: the whole graph as inline SVG, then a replay of the route one request took.
// Yellow = node that called the model, white = plain code. Check nodes take their result colour.
(function (root) {
  "use strict";

  // Fixed layout, drawn to fit a phone (viewBox 360 x 500).
  const NODES = {
    parse_input: { x: 180, y: 28, w: 150, label: "parse_input", sub: "regex; model for free text" },
    lookup: { x: 66, y: 92, w: 104, label: "lookup", sub: "claim + records" },
    scheme_review: { x: 180, y: 92, w: 108, label: "scheme_review", sub: "§4.4, Annex B" },
    stock_review: { x: 294, y: 92, w: 104, label: "stock_review", sub: "§7.1, C&F §2.2" },
    dispatch_checks: { x: 66, y: 152, w: 106, label: "dispatch_checks" },
    NOT_FOUND: { x: 200, y: 152, w: 100, label: "NOT_FOUND", end: true },
    check_window: { x: 54, y: 210, w: 76, label: "window", sub: "§5.2" },
    check_quantity: { x: 138, y: 210, w: 76, label: "quantity", sub: "§5.5" },
    check_duplicate: { x: 222, y: 210, w: 76, label: "duplicate", sub: "§5.6" },
    check_invoice_ref: { x: 306, y: 210, w: 76, label: "invoice", sub: "§5.4" },
    check_batch_expiry: { x: 96, y: 260, w: 76, label: "expiry", sub: "batch" },
    check_value: { x: 180, y: 260, w: 76, label: "value", sub: "§5.7" },
    check_pasted_fields: { x: 264, y: 260, w: 76, label: "pasted", sub: "§5.3" },
    decide: { x: 180, y: 322, w: 110, label: "decide", sub: "route priority" },
    explain: { x: 180, y: 390, w: 120, label: "explain", sub: "model, guarded" },
    END: { x: 180, y: 458, w: 90, label: "END", end: true },
  };
  const H = 34;
  const CHECKS = ["check_window", "check_quantity", "check_duplicate", "check_invoice_ref",
    "check_batch_expiry", "check_value", "check_pasted_fields"];
  const CHECK_KEY = {
    check_window: "window", check_quantity: "quantity", check_duplicate: "duplicate",
    check_invoice_ref: "invoice_ref", check_batch_expiry: "batch_expiry", check_value: "value",
    check_pasted_fields: "pasted_fields",
  };

  const pt = (name, side) => {
    const n = NODES[name];
    if (side === "top") return [n.x, n.y - H / 2];
    if (side === "left") return [n.x - n.w / 2, n.y];
    if (side === "right") return [n.x + n.w / 2, n.y];
    return [n.x, n.y + H / 2];
  };
  const line = (a, b) => [pt(a, "bottom"), pt(b, "top")];
  // Edges as point lists; long branches run down the left and right margins.
  // Edges as point lists. The free-text path runs down the left margin (x=7); the scheme and stock
  // paths share one channel down the right margin (x=353) into explain.
  const EDGES = {
    "parse_input>lookup": line("parse_input", "lookup"),
    "parse_input>scheme_review": line("parse_input", "scheme_review"),
    "parse_input>stock_review": line("parse_input", "stock_review"),
    "parse_input>explain": [pt("parse_input", "left"), [7, 28], [7, 390], pt("explain", "left")],
    "lookup>dispatch_checks": line("lookup", "dispatch_checks"),
    "lookup>NOT_FOUND": [pt("lookup", "right"), [134, 92], [134, 152], pt("NOT_FOUND", "left")],
    ...Object.fromEntries(CHECKS.map((c) => [`dispatch_checks>${c}`, line("dispatch_checks", c)])),
    ...Object.fromEntries(CHECKS.map((c) => [`${c}>decide`, line(c, "decide")])),
    "decide>explain": line("decide", "explain"),
    "scheme_review>NOT_FOUND": [pt("scheme_review", "bottom"), [180, 122], [200, 122], pt("NOT_FOUND", "top")],
    "stock_review>NOT_FOUND": [pt("stock_review", "bottom"), [294, 152], pt("NOT_FOUND", "right")],
    "scheme_review>explain": [pt("scheme_review", "right"), [244, 92], [244, 122], [353, 122], [353, 390], pt("explain", "right")],
    "stock_review>explain": [pt("stock_review", "right"), [353, 92], [353, 390], pt("explain", "right")],
    "explain>END": line("explain", "END"),
  };

  function svgMarkup() {
    const edges = Object.entries(EDGES).map(([id, points]) =>
      `<polyline class="flow-edge" data-edge="${id}" points="${points.map((p) => p.join(",")).join(" ")}"/>`).join("");
    const nodes = Object.entries(NODES).map(([id, n]) => {
      const shape = n.end
        ? `<rect x="${n.x - n.w / 2}" y="${n.y - H / 2}" width="${n.w}" height="${H}" rx="17"/>`
        : `<rect x="${n.x - n.w / 2}" y="${n.y - H / 2}" width="${n.w}" height="${H}" rx="7"/>`;
      const text = n.sub
        ? `<text x="${n.x}" y="${n.y - 2}">${n.label}</text><text class="flow-sub" x="${n.x}" y="${n.y + 10}">${n.sub}</text>`
        : `<text x="${n.x}" y="${n.y + 4}">${n.label}</text>`;
      return `<g class="flow-node${id === "explain" ? " model" : ""}" data-node="${id}">${shape}${text}</g>`;
    }).join("");
    return `<svg class="flow-svg" viewBox="0 0 360 480" role="img" aria-label="LangGraph route for this request">${edges}${nodes}</svg>`;
  }

  // Group the recorded trace into steps; the parallel checks form one step.
  function stepsFor(trace) {
    const steps = [];
    for (const node of trace || []) {
      const last = steps[steps.length - 1];
      if (CHECKS.includes(node) && last && last.every((n) => CHECKS.includes(n))) last.push(node);
      else steps.push([node]);
    }
    return steps;
  }

  function statusClass(status) {
    if (status === "pass") return "pass";
    if (status === "fail") return "fail";
    if (status === "review" || status === "missing") return "review";
    return "";
  }

  // parse_input used the model when there are more model calls than the explain node accounts for.
  function parseUsedModel(result) {
    const explained = (result.trace || []).includes("explain") ? 1 : 0;
    return (result.model_calls || 0) > explained;
  }

  function render(container, result, delayMs = 160) {
    if (!container) return;
    container.innerHTML = `<p class="flow-title">How the graph decided <span class="flow-legend"><i class="lg model"></i>model <i class="lg code"></i>code <i class="lg pass"></i>pass <i class="lg fail"></i>fail <i class="lg review"></i>person</span></p>${svgMarkup()}`;
    container.hidden = false;
    const svg = container.querySelector("svg");
    const node = (id) => svg.querySelector(`[data-node="${id}"]`);
    if (parseUsedModel(result)) node("parse_input").classList.add("model");
    const steps = stepsFor(result.trace);
    const ending = result.route === "NOT_FOUND" ? "NOT_FOUND" : ((result.trace || []).includes("explain") ? "END" : null);
    if (ending) steps.push([ending]);
    let previous = [];
    steps.forEach((step, index) => {
      const light = () => {
        for (const id of step) {
          const el = node(id);
          if (!el) continue;
          el.classList.add("lit");
          if (CHECKS.includes(id)) {
            const check = (result.checks || {})[CHECK_KEY[id]];
            // A check that ran but had nothing to compare (e.g. no pasted details) stays plain.
            const cls = check ? statusClass(check.status) : "";
            if (cls) el.classList.add(cls);
          }
          for (const from of previous) {
            const edge = svg.querySelector(`[data-edge="${from}>${id}"]`);
            if (edge) edge.classList.add("lit");
          }
        }
        previous = step;
      };
      if (delayMs > 0) setTimeout(light, index * delayMs); else light();
    });
  }

  const api = { render, stepsFor, statusClass, parseUsedModel, svgMarkup, NODES, EDGES };
  root.FlowView = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : globalThis));
