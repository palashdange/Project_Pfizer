# Pfizer domestic channel: ranked sizing and pilot recommendation

**Working note · 23 November 2026 · Fictional training case**

## 1. Context

The case describes a domestic pharmaceutical channel with rising expiry claims, uneven availability, quarter-end dispatch concentration, and a request from CFO Rohan Mehta for a demand forecast. The supplied extracts support several operational and control signals, but they do not establish a single root cause or confirmed annual loss. The rupee estimates below are reproducible screening values from the case data, not savings commitments. In particular, an order gap valued at PTS is not automatically lost sales: the pack has no order status, stockist sell-through, contribution margin, or proof that unfilled units were not supplied later. The case data is fictional and should not be represented as actual Pfizer performance.

## 2. Ranked evidence and annualized screening values

Amounts are annualized from observed data by dividing by the number of months represented and multiplying by 12. They rank the size of the measured signal, not confidence that the amount can be recovered. Claims categories use mutually exclusive priority: duplicate, policy-window failure, over-quantity, then missing invoice reference. The shelf-life claim cross-check overlaps other categories and is not added. See [`sizing_results.csv`](sizing_results.csv) for quarter-level results, calculation methods, sample source rows, and policy references.

| Rank | Problem / annual value | Method and evidence | Owner to involve |
|---:|---|---|---|
| 1 | Uncovered-order pack value after free goods — **₹15.33 cr/year** | Positive `(ordered_qty − invoiced_qty − free_qty) × PTS`, after grouping split-batch invoice lines so order quantity is counted once and shipped/free packs are summed. `primary_sales.csv`; source rows by CFA are in `sizing_results.csv`. It is still only a screening proxy, not confirmed lost sales. | Kavita Rao; Vaishali Kapoor |
| 2 | Free goods above the 3% quarterly cap — **₹1.58 cr/year** | Sum of positive quarterly excess: free quantity × PTS less 3% of net invoiced value. Q1 FY27 computes to 3.69%, matching the QBR; QBR says the exception was CFO-approved. Sample rows are in `sizing_results.csv`. CO-POL-014 §4.4. | Arjun Sethi; Rohan Mehta |
| 3 | Credited claims without invoice reference — **₹43.08 lakh/year at risk** | Credited claims with blank reference remaining after higher-priority checks; value is the recorded credit amount. Blank reference is not proof of invalidity: CO-POL-014 §5.4 permits an alternate ledger and written approval route. Examples and rows are in `sizing_results.csv`. | Neha Bansal; Rohan Mehta |
| 4 | Credited claims outside policy window — **₹15.74 lakh/year screen** | Credited claim value outside type-specific §5.2 timing, using batch-master expiry for expiry claims and original invoice date for breakage/short supply. This is a rule-screened amount pending source-document review. Examples and linked rows are in `sizing_results.csv`. | Neha Bansal |
| 5 | Potential duplicate credits — **₹4.45 lakh/year candidate screen** | Later credited claim with same stockist, batch, and claimed quantity. There are candidates, not a confirmed full population of duplicates. One hand-checkable pair is CLM-2603-01616 / CLM-2605-04488, `expiry_claims.csv` rows 3269 and 3596; both record ₹26,846.40. CO-POL-014 §5.6. | Neha Bansal; Rohan Mehta |
| 6 | Expiry claims on stockist/batches with a below-60% RSL invoice — **₹96.37 lakh/year cross-check** | Claims on a stockist/batch for which at least one sales line had RSL below 60% on invoice date. It is a cross-cutting association, not evidence that the dispatch caused or qualifies the claim; do not add it to the ranked exposure total. CO-POL-014 §7.1. | Kavita Rao; Neha Bansal |
| 7 | Over-quantity claims — **₹6,642/year screen** | Excess claimed packs over summed invoiced plus free packs for stockist/batch, valued at PTS. Rule screen only; examples and source rows are in `sizing_results.csv`. CO-POL-014 §5.5. | Neha Bansal |
| — | Claim processing time — **42-day median; 3,115 of 4,112 over 30 days** | Claim-date to credit-note-date on rows with both dates; claim date is the available field, not a receipt timestamp. Q1 FY27 median is 43 days (406/548 over 30), versus QBR 46 days. No rupee value assigned. CO-POL-014 §5.6. | Neha Bansal; Rohan Mehta |

The claims figures above are annualized historical run rates, not a forecast of future leakage. The duplicate screen includes false positives until claim context is reviewed. The missing-reference amount is value at risk, not proven loss. The below-60% RSL cross-check is non-additive. The separate invoice-only gap before free goods is ₹22.32 crore/year; it is retained as a non-additive diagnostic because free packs may fulfill part of the ordered quantity. Exact deduplication, raw and clean row counts, date ranges, overlap counts, and QBR comparisons are printed by the sizing script.

## 3. CFO forecast ask: what could a forecast address?

The sizing script attributes **87.4% of the additive annualized screening total** to the after-free-packs order-gap proxy, the only item a forecast could plausibly influence, and labels that relationship “partly.” This is a share of screened rupee indicators, **not** 87.4% of recoverable loss or forecast-driven savings. The pack cannot establish a validated financial amount a forecast would recover. A forecast can inform planning and allocation, but cannot enforce scheme caps, verify claim windows, stop duplicate credits, validate invoice references, or gate short-RSL dispatches. Those require deterministic workflow controls and accountable review.

The primary-sales history can support a shipment baseline, but does not measure downstream demand. The case has 30 months of primary sales and no stockist sell-through or on-hand inventory. Therefore the pilot should show a transparent shipment baseline only as supporting context and must not call it a downstream-demand forecast or promise financial recovery. Before sizing forecast benefit, reconcile order status and cancellations, define the target, link allocation decisions to subsequent fill and sell-through, and agree contribution margin with Finance.

## 4. Recommended problem and user

Freeze the pilot around the weekly Supply Chain decision: **which CFA–SKU availability gaps or aging-batch signals need investigation before the next planning cycle?** The primary user is **Head of Supply Chain Kavita Rao**, with **Lead Demand Planning Vaishali Kapoor** as the planning partner. These roles and names are from `04_stakeholder_interview_notes.pdf`; they are case stakeholders, not real client validation. This choice follows the largest actionable signal (unfilled-order value) while avoiding the unsupported claim that forecasting alone solves it. The tool should show stock and shipment evidence, data cut, rule calculation, and source rows; the owner decides what to investigate through existing processes.

The pilot remains read-only and retrospective on the supplied extracts until refreshed dated data, order status, clear stock grain, and reviewer dispositions exist. Claims controls are a separate high-value opportunity, but combining Finance adjudication and Supply Chain planning into one first workflow would dilute the user, decision, and acceptance criteria. The weekly workflow and proposed architecture should use this scope; archived plans are retained as history, not current commitments.

## 5. Open questions for the case client

1. Which order-line field distinguishes accepted demand, cancellation, backorder, and partial fulfillment? Can repeat unfilled orders be linked to one demand event?
2. What is the official fill-rate numerator and denominator? The extract gives 88.02% invoiced-only and 90.85% including free packs, while the QBR gives 90.9%. Should free packs count as fulfillment for the official KPI and financial sizing?
3. Can the conflicting CFA/SKU/batch snapshot keys be reconciled, and what is the correct stock grain and timestamp?
4. What downstream sell-through and stock-on-hand data can be provided by stockist/SKU/week? Without these, how should the CFO’s request for a demand forecast be scoped?
5. What is the Finance-approved definition and cutoff for expiry claims as a percentage of primary sales, and can the ₹1.415 crore QBR numerator be reconciled to the claims ledger?
6. Which human roles own alert disposition, escalation, and recording outcomes? What response time and baseline effort should the pilot measure?
7. Can Finance verify claim receipt dates, approvals for missing-invoice claims, duplicate-credit matches, and the amounts actually recovered?

## Reproducibility

Run `python discovery/sizing.py` from the learner-pack root in an environment with pandas installed. The script writes [`sizing_results.csv`](sizing_results.csv). Its unit tests are in [`test_sizing.py`](test_sizing.py). For evidence interpretation, see [`voice_note_evidence_log.md`](voice_note_evidence_log.md) and [`business_problem_validation.md`](business_problem_validation.md). Earlier overlapping planning drafts are preserved under [`archive/`](archive/).
