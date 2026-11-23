# Implementation plan: Pfizer channel engagement pilot

**Status:** Working plan based on the project brief and current starter app  
**Updated:** 14 November 2026  
**Purpose:** Get from the current LangGraph prototype to a traceable, evaluated, deployed pilot without building past the evidence.

## Where we are

The starter app runs a LangGraph model/tool loop and now has four tools: batch lookup, a 60% remaining-shelf-life check, a CFA stock comparison, and a same-month-last-year primary-shipment baseline forecast. The forecast is a prototype for Pfizer shipments into the channel; it does not forecast downstream demand. The rules, tool, and API wiring have automated tests. This is a useful technical slice, but not yet a measured business case or a live weekly planning workflow.

The current `pilot_charter.md` proposes a read-only batch and CFA stock-risk review and puts Finance interviews out of scope. The project brief makes the CFO's forecast request, money recovered or protected, and evidence-based ranking central. The prototype now demonstrates the narrower primary-shipment forecast option; it does not resolve whether the case sponsor accepts shipments as a proxy for the requested downstream demand forecast or establish money recovered or protected.

## Priority 0 — Resolve the use case before adding features

**Why first:** The brief asks for an AI demand-forecasting tool before quarter end. The data pack has primary sales, but it does not include stockist sell-through or stockist on-hand inventory. Primary sales measure Pfizer's shipments into the channel; they are not the same as end-customer demand.

**Decision to get from the sponsor / reviewers:**

1. Is a forecast of future primary sales an acceptable first pilot, clearly labeled as a sell-in forecast?
2. Or must the pilot forecast downstream demand? If so, request stockist secondary sales and inventory at stockist × SKU × period grain before claiming that capability.
3. If neither can be resolved with available time and data, agree explicitly that the pilot is a retrospective operational-risk review, and document that it does not fulfill the forecast request.

**Done when:** The chosen outcome, target user, weekly decision, forecast target (if applicable), and data limitations are written in the pilot charter and architecture note.

## Priority 1 — Complete discovery and rank the business problems

Use the Reader's Guide workflow: connect the policies, stakeholder beliefs, and voice notes to data tests; then rank findings by rupee impact, evidence, and business owner.

| Work | Evidence or input needed | Output / acceptance check |
|---|---|---|
| Reconcile the official expiry/near-expiry KPI | QBR definition, claims extract, sales extract, cutoff dates, Finance owner | One reproducible rate with numerator, denominator, period, exclusions, and source references; document any remaining difference |
| Validate the forecast/availability hypothesis | Forecast versions, allocation history, order and cancellation lines, secondary sales and stockist inventory if available | Separate what data proves from what remains a hypothesis; name the owner of the forecast/allocation decision |
| Check expiry and claim leakage hypotheses | Claims, claim emails, batch/invoice joins, credit-note/payment/recovery identifiers and policy | Quantify confirmed cases separately from candidate flags; never treat flagged invoice value as savings |
| Complete stakeholder evidence | Interviews/notes and all six voice notes, with transcripts/translations where needed | Record each belief, speaker/role, evidence offered, and client-only follow-up question |
| Rank findings | Validated amounts, method, source rows/pages, controllability, and owner | Ranked problem list tied to the CFO ask; include confidence and data limitations |

**Important scope correction:** Finance validation cannot stay wholly out of scope if the submission claims a rupee business case or progress toward the CFO's 1% ambition. If Finance is unavailable, label the value estimate as provisional and do not represent it as recovered or recoverable money.

## Priority 2 — Freeze one workflow and document the LangGraph design

Choose one vertical slice based on Priority 0 and discovery findings. Do not add features just because the data exists.

The architecture note should include:

- the named user, their weekly job, and the decision the pilot supports;
- a LangGraph diagram showing model nodes, deterministic Python nodes/tools, edges, and the capped tool loop;
- which files each tool reads and the grain of its result;
- what happens when a record is missing, malformed, ambiguous, or outside policy;
- where each policy number is configured, with its source document and page;
- expected model calls and approximate cost per run;
- human decision rights and the explicit no-writeback boundary.

Keep exact joins, calculations, thresholds, classifications with fixed rules, and source selection in code. Let the model choose tools when appropriate and explain tool results in plain language; it must not invent facts or make approval decisions.

**Done when:** A reviewer can follow every important result from the graph to its tool, rule, input file, source row, and owner.

## Priority 3 — Make the data and evaluation set trustworthy

Before adding another business rule:

1. Inventory the seven extracts and record owner/source, extraction date, date range, primary key, grain, duplicates, missing fields, code variants, and joins.
2. Reconcile key aggregates against the QBR or another trusted report. Explain differences before using them in the business case.
3. Load CSV data once per process as the build guide recommends; avoid repeated full-file reads during a user request.
4. Preserve `source_file` and source row identifiers through joins and into every result. A number shown in the UI must be traceable to its record or policy clause.
5. Create the brief's hand-checked set of 10–20 real records. A business reviewer should agree the expected result for each record before the pilot is scored.

**Done when:** The check set records the expected output, actual output, match/mismatch, and what the tool does when it cannot decide. Keep unit tests too; the check set complements them and does not replace them.

## Priority 4 — Build the smallest complete user workflow

Implement only after the first four priorities establish the target and evidence. The workflow should show:

The proposed weekly review and screen requirements are in [weekly_review_workflow.md](weekly_review_workflow.md). They describe the candidate read-only workflow; they do not resolve the forecast-scope decision in Priority 0.

- one clear input or agreed review period;
- the result or exception first, including the rule and responsible reviewer;
- the exact evidence: source file, row/key, values used, calculation, and policy reference;
- clear states for loading, not found, needs a person, and error;
- no invented values and no automatic claims, credit notes, transfers, dispatch blocks, scheme approvals, or system write-back.

For the current code, first close traceability gaps in batch lookup and CFA stock output. Then build the chosen forecast or review slice. Add near-expiry or claim checks only if discovery ranks them in scope and each one has source evidence and a hand-checked test.

## Priority 5 — Deploy early, evaluate, and present honestly

- Deploy a thin vertical slice as soon as it runs locally; do not wait until the final day.
- Test `/api/health` and a real question on the deployed URL, including on a phone or unfamiliar device.
- Run `pytest -q` after each code slice and run the 10–20-record hand-checked set before presenting.
- Report check-set accuracy, what failed, and what the system does with uncertain records.
- Measure alert precision, review effort, and operational follow-up. Claim money saved only when the method and evidence support that amount.
- Prepare the required deliverables: discovery note, architecture note, private repository with README/AGENTS/tests, deployed pilot URL, and a deck of at most 12 slides with a live demo.

The guide gives a submission deadline of **Sunday, 22 November 2026**. A practical sequence is: scope and evidence first; architecture and check set next; build and deploy the first slice early; then evaluate, prepare the demo, and finish the submission.

## Priority summary

| Order | Gate | Do not proceed to… until… |
|---|---|---|
| 0 | Sponsor scope decision | We know whether the target is primary-sales forecasting, downstream demand forecasting with added data, or an explicitly narrower retrospective pilot |
| 1 | Discovery and value validation | The important findings are ranked, sourced, and assigned to owners |
| 2 | Architecture | The user, decision, graph, data, rules, failure behavior, and cost are clear |
| 3 | Data and check set | The numbers reconcile sufficiently and 10–20 records have agreed expected outcomes |
| 4 | Complete user workflow | The chosen slice works end to end and shows traceable evidence |
| 5 | Submission | Deployment, check-set results, limitations, and demo are ready |

## Reference requirements

- **Reader's Guide, pages 2–3:** understand the channel and files, clean and join the data, size and rank findings, and finish discovery before design.
- **Project Brief, pages 2–7:** discover → design → build → deploy → present; a LangGraph graph is required; every number needs evidence; include a hand-checked 10–20-record set and all five deliverables.
- **Build and Deploy Guide, pages 1–6:** implement one testable slice at a time, keep code explainable, show decision and evidence in the UI, load CSVs once, deploy early, and verify the live URL.
