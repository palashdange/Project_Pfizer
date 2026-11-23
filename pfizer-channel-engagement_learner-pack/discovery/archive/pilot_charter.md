# Pilot charter: batch and CFA stock risk review

**Status:** Proposed, based on desk research and unvalidated assumptions  
**Business owners:** Supply Chain / Demand Planning and CFA Operations (specific people to confirm)  
**Finance interviews:** Out of scope for this phase  
**Pilot mode:** Read-only decision support; no operational write-back

## Why this pilot

The supplied records give two concrete signals worth testing with Supply Chain and CFA Operations. First, a subset of FY27 Q1 invoice–batch groups appears below the policy’s 60% remaining-shelf-life threshold. Second, the September 2026 CFA snapshot shows high stock cover at Kolkata alongside many zero-stock SKUs at Lucknow, with Kolkata holding some of those same SKUs.

These signals suggest a useful operational question: **Can teams see and review batch and location risks early enough to prevent avoidable short-dated dispatches or missed availability?** The data does not yet prove that either signal caused returns or stockouts. The pilot should test whether alerts are accurate, actionable, and worth incorporating into the existing review process. [Trade terms and returns policy](../../data-pack/02_trade_terms_and_returns_policy.pdf) [CFA stock snapshot](../../data-pack/data/cnf_stock_snapshot.csv) [Primary sales extract](../../data-pack/data/primary_sales.csv) [Batch master](../../data-pack/data/batch_master.csv)

## Objective

Give Supply Chain and CFA operations a traceable view of potential batch and CFA/SKU risks using the supplied extracts, so a person can verify each alert and decide whether to investigate under current procedures.

The pilot is successful if users can reliably distinguish actionable exceptions from false alarms and review them more efficiently than the current approach. It is **not** a commitment to reduce returns by a specified amount; the available data and pilot duration are not sufficient to make that claim.

## Users and decisions supported

| User | Question the pilot should help answer | Decision remains with |
|---|---|---|
| Demand Planning / Supply Chain | Which CFA/SKU pairs may warrant an allocation or replenishment review? | Existing Supply Chain decision owner |
| CFA operations | Which batches or dispatch lines need a shelf-life or FEFO check? | Existing CFA supervisor / distribution owner |
| Regional Sales (limited supporting view) | Which reported availability signals should be checked with Supply Chain? | Existing Sales and Supply Chain owners |

Names and formal decision rights are assumptions; confirm them before any live operational use.

## Proposed workflow

1. **Load the agreed extracts.** Use primary sales, batch and SKU masters, and CFA stock snapshots. Record each file’s source, extraction date, date range, and grain.
2. **Run deterministic checks.** Calculate remaining shelf life at invoice date for invoice–batch lines; aggregate current CFA stock and outward at CFA/SKU grain; identify zero-stock markers and compare locations.
3. **Create a review queue.** Each potential exception shows the rule, source row identifiers, input dates and quantities, calculation, and data caveat. The queue ranks by rule-based severity; it does not claim an expected loss.
4. **Human review.** An assigned Supply Chain or CFA user checks the source records and records a disposition in the team’s existing process (for example: confirmed, not an issue, needs investigation). The pilot itself does not store operational decisions unless separately approved and designed.
5. **Review outcomes.** Compare alerts to user adjudication, measure review effort, and document data gaps and process changes needed for a broader pilot.

For the prototype, the supplied starter app is a FastAPI/LangGraph skeleton with a batch lookup tool. It currently demonstrates batch lookup, not a risk queue. Any future implementation should put calculations and thresholds in deterministic Python tools; the language model may explain returned evidence but must not invent dates, quantities, or risk flags. The current starter instructions also require tests for business rules. [Starter README](../../starter/README.md) [Starter tools](../../starter/agent/tools.py) [Starter graph](../../starter/agent/graph.py) [Starter agent instructions](../../starter/AGENTS.md)

## In-scope checks

### 1. Remaining-shelf-life check

- Compare remaining shelf life on invoice date with the policy threshold of 60% of total shelf life.
- Show invoice date, manufacture date, expiry date, remaining/total days, calculated percentage, CFA, SKU, batch, and source line.
- Treat a flag as a **candidate exception** until Distribution confirms date conventions, batch matching, and any approved exception.

### 2. CFA/SKU stock imbalance check

- Aggregate stock once per CFA/SKU at the latest agreed snapshot date; do not sum a repeated monthly-outward value across batch rows.
- Use explicit zero-stock markers as zero, while distinguishing them from missing or unmatched data.
- Compare stock cover using the snapshot’s defined outward measure and show the underlying stock and outward values.
- Highlight other CFAs with the same SKU for review; do not recommend a transfer or assert demand without downstream evidence.

### 3. Near-expiry stock visibility

- List batches approaching expiry at CFA, with packs, PTS value, and expiry date.
- Present exposure as inventory at risk, not forecast write-off.
- If any projected depletion or demand ranking is later added, show the assumptions and do not treat CFA outward as stockist sell-through.

## Out of scope

- Finance interviews, reconciliation of the official return-rate KPI, or a committed financial-savings case.
- Claims adjudication, credit-note issuance, payments, recovery, or write-off decisions.
- Scheme approval or optimization.
- Automatic allocation changes, stock transfers, dispatch blocks, or ERP/WMS write-back.
- Patient or HCP data.
- A demand forecast presented as sell-through: stockist secondary sales and inventory are not in the supplied data pack.

## Data and controls

**Needed for the first prototype:** `primary_sales.csv`, `batch_master.csv`, `sku_master.csv`, and `cnf_stock_snapshot.csv`. The starter directory currently contains only the batch and SKU masters; the sales and stock files are in the data pack and must be made available to the prototype through the project’s approved local/deployment process.

Before relying on the output, confirm:

- consistent CFA identifiers (the stock extract includes formatting variants);
- date formats, fiscal periods, and the definition of “dispatch date” versus invoice date;
- batch-master join coverage and treatment of missing manufacture or expiry dates;
- that zero-stock rows are markers rather than missing positive quantities;
- stock and outward grain, especially repeated monthly outward across batch rows;
- whether the observed exception threshold is policy, warning, or informational.

All outputs should retain source traceability. No model-generated value should be treated as a fact unless returned by a deterministic tool. Follow access controls for the source data and the project’s read-only constraint. [Company and channel overview](../../data-pack/01_company_and_channel_overview.pdf) [Starter agent instructions](../../starter/AGENTS.md)

## Measures of success

Agree the baseline and review period with the pilot owners before running the pilot. Do not set arbitrary targets before seeing a baseline.

| Measure | Definition to agree |
|---|---|
| Alert precision | Share of reviewed alerts confirmed as actionable by the designated business reviewer |
| Review effort | Median time to verify and disposition an alert, compared with the current method where measurable |
| Shelf-life control | Confirmed below-threshold invoice–batch lines and approved exceptions, separately reported |
| Stock-risk usefulness | Share of CFA/SKU alerts judged useful for investigation; track false positives and missing-data cases |
| Traceability | Share of alerts with complete source rows, inputs, rule, and reproducible calculation |
| Operational follow-up | Number of alerts investigated and actions taken through existing processes; report actions, not assumed savings |

## Assumptions to test

1. CFA/SKU visibility at batch level is useful to Supply Chain and CFA operations in their regular review cadence.
2. The shipment and stock signals in the supplied extracts can be reproduced from operational source systems.
3. A named user can verify alerts and route confirmed issues through current processes.
4. Exception review can happen early enough to affect a dispatch or replenishment decision; historical flags alone may only support retrospective analysis.
5. Users prefer traceable rules and evidence over a model-generated recommendation.

If assumptions 2 or 3 fail, narrow the prototype to a retrospective data-quality and exception analysis rather than an operational queue.

## Decisions required before build

- Name the Supply Chain product owner and CFA review users.
- Confirm whether the first pilot is retrospective on the supplied data or prospective with refreshed extracts.
- Confirm the dispatch date field and policy interpretation for shelf-life checks.
- Agree which CFA/SKU cover threshold warrants an alert; the 2.5-month stock norm in the policy is based on stockist secondary sales and should not automatically be reused for CFA inventory.
- Agree where user dispositions will be recorded. Keep the prototype non-persistent unless the client approves a storage approach.
- Select a review period and establish a comparison method for alert precision and review effort.

## Recommendation

Proceed to a narrow, retrospective prototype using the existing files, starting with the remaining-shelf-life check and CFA/SKU stock visibility. Review its results with Supply Chain and CFA operations before adding prospective alerts or expanding scope. Keep Finance out of this phase and describe all financial value as unvalidated.
