# Two-workflow weekly copilot: claims triage and supply-chain risk

**Status:** Two-workflow proposal for the hypothetical case; not validated with real process owners.

**First user:** Commercial Finance Controller Neha Bansal and the two-person claims team described in the case materials.

**Second user:** Head of Supply Chain Kavita Rao; planning partner: Lead Demand Planning Vaishali Kapoor.

**Mode:** Read-only decision support; decisions remain in existing operating processes

## Purpose

The first workflow helps Commercial Finance review register claims and decide which are supported for further processing, which appear to fail a documented check, and which need a human decision. The copilot may present a screening recommendation with evidence; a Finance-authorized person retains the decision and credit-note action. The second workflow helps Supply Chain investigate CFA–SKU availability and batch-aging signals before its next planning cycle. Keep decisions, screens, evidence, and performance measures separate for the two user groups.

For claims, the intended weekly disposition is **candidate to proceed for authorized review**, **exception indicated**, or **needs human review**. These labels are triage outcomes, not automatic credit or rejection. CO-POL-014 §§5.2, 5.4, 5.5, and 5.6 must be verified against the source policy and matched to actual approval authority before those checks are used operationally.

The largest measured Supply Chain signal is ₹15.33 crore/year after subtracting invoiced and free packs from ordered packs, valued at PTS. This is not confirmed lost sales or forecast savings: order status, downstream demand, and contribution margin are unavailable. The ₹22.32 crore invoiced-only gap is a separate overlapping diagnostic and is not additive. Claims screen values likewise indicate records to review, not proven avoidable losses.

This is a proposed weekly job-to-be-done, not proof that the case company already has this process or that a weekly review is the right cadence. Confirm the user, cadence, and actions as part of the hypothetical pilot review.

## Workflow 1: Commercial Finance claims triage (primary)

The case materials and role-play discussion make Commercial Finance the first user workflow. Neha Bansal is identified as Controller and the claims team is described as two people. Confirm those responsibilities, the weekly cadence, intake/register format, and final credit authority against the case files. This proposed workflow is not validated with real process owners. Keep its results separate from the Supply Chain review.

1. Load a pasted claim or register row from the case extract; retain its claim ID and source row. Do not imply a live mailbox connection.
2. Resolve the batch against `batch_master.csv`; use the master expiry date and derive `near_expiry` or `expired` from claim date. Show a label mismatch rather than trusting the claimant’s category.
3. Screen the inclusive window from 90 days before expiry through 90 days after expiry. The case discussion attributes this to CO-POL-014 §5.2; verify the PDF clause before treating it as approved policy.
4. Compare stockist, SKU, batch, and claimed quantity with billing records; search prior credited claims for a repeat. For a missing invoice reference, the discussion requires ledger evidence, quantity within invoiced volume, and written Area Manager approval that names the claim. The supplied CSV does not contain that approval evidence.
5. Show each check with source file/row, matched values, and calculation. Use cautious screening states such as **evidence supports further processing**, **exception indicated**, and **needs human review**. Do not present an automated credit/reject decision. A failed check or unavailable evidence is routed to an authorized person; the tool does not post a credit, send a reply, or change SAP.
6. A human records the disposition in the existing process. The pilot may draft a response, but the Finance team sends it.

**Count caveat:** the role-play discussion reports 804 no-invoice claims and approximate amounts that do not reconcile to this extract. Exact deduplication gives 879 of 4,503 claims with a blank invoice reference (884 of 4,526 raw rows). Use the calculation in [business problem validation](business_problem_validation.md) until a forum filter/data cut is provided. The annualized claim screens do not establish the amount this pilot would block or recover.

### Claims workflow acceptance checks

1. Each screened claim and matched billing/credit record can be traced to its source file and row or stable ID.
2. Policy checks use the approved source wording and documented boundary rules; uncertain or missing evidence routes to a person.
3. A repeat-credit signal is shown as a possible duplicate until Finance verifies its transaction history.
4. The interface never issues a credit, rejects a claim, posts a credit note, or treats a message's claimed approval as authority.
5. Pilot evaluation compares screening outcomes with an authorized human disposition and records reviewer effort; it does not count every flagged rupee as prevented loss.

## Workflow 2: Supply Chain availability and aging-risk review (secondary)

1. **Confirm the data cut.** The reviewer sees when each file was extracted, the period it covers, and the date of the latest CFA stock snapshot. If inputs are stale, missing, or outside the agreed review window, the screen says so and marks the review as historical or incomplete.
2. **Run the deterministic checks.** The system joins sales lines to batch and SKU masters, applies the 60% RSL rule at invoice date as required by CO-POL-014 §7.1, and checks the latest stock snapshot for cross-CFA availability signals. It reports records that cannot be evaluated separately.
3. **Triage the exceptions.** The reviewer filters by check type, CFA, SKU, and date, then opens a row to see its source values, calculation, and limitations. Results are ordered by date and identifier; no unapproved financial-risk score is implied.
4. **Verify in the source process.** The reviewer checks the cited record in the source system and chooses a disposition in the existing process: confirmed, not an issue, needs data correction, or escalated. The prototype does not store decisions or send updates to ERP, WMS, claims, or allocation systems.
5. **Close the review.** The reviewer records the review date, scope, unresolved items, and follow-up owner using the team's existing method. For pilot evaluation, collect reviewer dispositions and time spent through an approved mechanism; do not add persistence until an owner and retention rules are agreed.

## Proposed screen

### Header and data status

- Page title: **Weekly channel risk review**.
- Show source file names, extraction/effective dates, reviewed period, latest snapshot date, and refresh status.
- Distinguish a current weekly review from a retrospective run on the supplied case data.
- Show a warning when a required file is missing, the data is stale, dates cannot be parsed, or the stock snapshot has ambiguous keys.

### Summary cards

Show separate counts for:

- invoice lines below the shelf-life threshold;
- invoice lines evaluated;
- lines not evaluated, split by missing batch and other data issues;
- SKUs with a cross-CFA stock signal;
- CFA/SKU groups excluded because stock rows conflict or are ambiguous.

Every count must state its period or snapshot date and result grain. Do not combine shipment counts with stock-group counts. Do not convert flagged invoice value into loss or savings.

### Exceptions table

Use separate tabs or filters for **Shelf-life review** and **CFA stock review** so each table has one clear grain.

**Shelf-life table** — one row per primary-sales invoice line:

| Field | Display requirement |
|---|---|
| Invoice and source reference | Invoice number, source file, and source row; keep the source reference visible without horizontal scrolling where practical |
| Invoice date | Show the invoice date used in the §7.1 RSL calculation |
| Customer and location | Stockist, CFA code, and city when present in the source |
| Product and batch | SKU, product name when joined, batch number |
| Quantities | Invoiced quantity and free quantity as separate values |
| Shelf-life calculation | Manufacture date, expiry date, remaining-shelf-life percentage, and the 60% threshold |
| Review state | Candidate flag, not a confirmed policy breach; show missing or mismatched join details as not evaluable |

**CFA stock table** — one row per SKU/CFA stock observation or comparison leg:

| Field | Display requirement |
|---|---|
| Snapshot and source reference | Snapshot date, source file, source row(s) |
| Product and location | SKU, CFA code, city |
| Stock evidence | Zero-stock marker or positive batch stock, batch number, reported pack quantity |
| Comparison | Show the zero-stock CFA and positive-stock CFA for the same SKU together |
| Review state | “Review signal”; explicitly state that it does not prove excess stock, demand, or transfer feasibility |

Tables need text search, filtering, and pagination so reviewers can inspect all results. Summary counts must describe the full result set, not just the visible page. Keep raw source payload available as a secondary detail, not as the main reading view.

### Row details

Opening a row should show:

- the source file and row number (or stable business key);
- source values used by the rule;
- the calculation in plain language, including date fields and threshold;
- join status and any data-quality caveat;
- a link or instruction for locating the record in the source process;
- an explicit note that the result needs human review.

## Rules and evidence boundaries

| Check | Rule for the pilot | What it supports | What it does not support |
|---|---|---|---|
| Shelf-life screen | Compare remaining shelf life on invoice date with 60% of total shelf life as specified by CO-POL-014 §7.1. | Finding candidate invoice lines for review | Confirming a return, destruction, loss, or avoidable value |
| CFA availability signal | For a SKU, compare explicit zero-stock markers with positive stock tied to a batch at other CFAs on the same snapshot date. Exclude conflicting/ambiguous CFA-SKU records. | Finding locations worth reviewing together | Inferring downstream demand, excess stock, safe/feasible transfer, or lost sales |

The tool must retain the exact source values and source row for each result. If a required value is missing, a join is ambiguous, or a record cannot be evaluated, show that state instead of filling a value by inference.

## What the current prototype can and cannot do

The current app can answer batch lookups, run a shelf-life screen, identify cross-CFA stock signals, review an individual claim, inspect a claim email, and show a primary-shipment baseline. It is not yet an operational weekly queue for either team: there are no review-period controls, data-freshness gate, saved dispositions, or complete register-processing workflow. The claims tool reviews an identified claim, but does not yet implement every §5.2/§5.4/§5.5/§5.6 route as a validated end-to-end decision workflow. The shelf-life tool scans the supplied primary-sales file and returns at most 25 detail rows, even when the summary count is larger. Its 3,434 flagged lines are a whole-file result for that loaded extract, not a latest-week count.

The case data ends on September 30, 2026 for the latest CFA snapshot and does not provide stockist sell-through or stock-on-hand. The diagnosis found conflicting duplicate keys in the snapshot; those groups should not be used to create stock alerts until resolved. Do not present this static data pack as a live operational feed.

## Pilot acceptance checks

Before calling the screen useful for a weekly review:

1. A user can identify the data period and freshness before interpreting a count.
2. Every displayed exception can be traced to its source file and row or key.
3. Counts reconcile to a saved, reproducible calculation over the same filters and period.
4. Shelf-life dates and percentages match hand-checked records; invoice date is displayed as the §7.1 calculation date.
5. Ambiguous stock records are excluded or marked for data correction, not silently summed.
6. The table can display, filter, and paginate the full result set while keeping summary counts stable.
7. A reviewer can distinguish a candidate signal from a confirmed issue and knows which existing process to use next.
8. The pilot records no business action or financial benefit as completed unless a human and source record confirm it.

Do not set alert-precision, time-saving, or financial targets until a baseline and reviewer method are agreed. Track confirmed, rejected, and data-correction dispositions; time to review; and follow-up taken. Treat any change in returns or availability as an observed outcome, not proof of pilot causality.

## Data needed before prospective weekly use

- refreshed, timestamped extracts and an agreed period/cutoff;
- actual dispatch date and approved shelf-life exception data;
- stable order status and cancellation reason if the workflow expands to unfilled demand;
- a reconciled stock snapshot with explicit grain and conflict resolution;
- downstream stockist inventory and sell-through before making demand or stock-transfer recommendations;
- named users, escalation routes, and an agreed place to record dispositions.

## Relationship to existing discovery work

This is the second workflow in the proposed scope described in [Discovery_note.md](Discovery_note.md). Evidence and limitations are detailed in [business_problem_validation.md](business_problem_validation.md); earlier planning drafts are retained under [archive/](archive/). The primary-sales baseline is supporting context only: absent stockist sell-through and inventory, it is not a downstream-demand forecast or a basis for a savings claim.
