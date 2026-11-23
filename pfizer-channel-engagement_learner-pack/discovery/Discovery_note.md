Project Sankalp: Discovery Note & Operational Diagnosis

> **Discussion update (23 November 2026):** The FDE Academy forum discussion is useful role-play input for the hypothetical case, not independently verified evidence about real Pfizer. It clarifies intended operating assumptions for claims, allocation, scheme handling, and warehouse review. Keep these statements separate from extract-backed findings and verify policy wording against the PDFs before operational use. See [business problem validation](business_problem_validation.md) for reconciled data counts and assumptions.

Domestic Trade Channel · General Medicines Portfolio
Forward Deployed Engineering Engagement · Executive Discovery Brief
Target Reviewers: Rohan Mehta (Chief Financial Officer), Kavita Rao (Head of Supply Chain), Arjun Sethi (National Sales Manager)

1. Executive Context & Channel Architecture

Pfizer Limited’s General Medicines (GM) trade portfolio generates approximately ₹200 crore in annual primary sales across 36 oral solid and liquid SKUs spanning seven core therapy areas. Physical distribution originates at manufacturing sites and 18 contract loan-licence partners, consolidates at the Central Distribution Centre (CDC) in Bhiwandi, and moves via monthly allocation across six regional Carrying & Forwarding Agent (CFA) warehouses: Gurugram (CF-N01), Lucknow (CF-N02), Kolkata (CF-E01), Bhiwandi (CF-W01), Chennai (CF-S01), and Hyderabad (CF-S02). These six CFAs invoice and supply 156 authorized stockists, who in turn service retail chemists, dispensaries, hospitals, and an estimated 500,000 downstream dispensing points across India.

Physical Distribution and Information Flow

Understanding the path of product and claims through the domestic network exposes the structural vulnerability that underpins the current operating crisis:

1. Manufacturing & Primary Sourcing: Finished goods are released from plants (Goa, Visakhapatnam, Ahmedabad JV) and 18 loan-licence partner facilities, moving into the Central Distribution Centre (CDC) at Bhiwandi under Goods Transfer Notes.
2. Central Planning & Allocation: Demand Planning generates a national forecast, while Supply Chain allocates inventory across the six regional CFAs using pre-set percentage shares. Stock moves on Stock Transfer Orders (STOs).
3. CFA Warehousing & Invoicing: CFAs receive stock, post Goods Receipt Notes (GRNs) into local warehouse management systems, pick stock under First-Expiry, First-Out (FEFO) rules, and invoice stockists in SAP SD. Policy mandates that products must have at least 60% residual shelf life at dispatch.
4. Primary Sales vs. Secondary Visibility Blind Spot: Invoicing from CFAs to stockists represents primary sales, which Pfizer tracks in real time. However, onward sales from stockists to retail chemists (secondary sales) and chemist dispensing to patients (tertiary demand) are completely invisible to Pfizer. Following the cancellation of the Distributor Management System (DMS) pilot and the formal cessation of Stockist Sales Statements (SSS) under Trade Policy CO-POL-014 Clause 4.5, commercial operations has zero real-time visibility into downstream channel stock.
5. Reverse Claims Flow: Expired, near-expiry, or damaged stock flows back in reverse—from retailers to stockists, who then lodge claims with regional CFAs. CFAs physically inspect returns and log claims in monthly registers sent to Commercial Finance, where a two-person team manually validates claims against billing history before posting credit notes in SAP FI.

Primary shipments are sell-in and may be influenced by schemes. Without stockist sell-through and stock-on-hand, they are not a direct measure of downstream demand.

2. Evidence-backed Business Problem Areas

Review of the primary-sales and claims extracts, CFA stock snapshot, inbox correspondence, and supplied voice-note transcripts supports several signals for follow-up: quarter-end sales concentration, free-goods spend above the stated cap, regional availability concerns, short-shelf-life invoice flags, and claims-processing delays. The supplied records do not establish a single root cause or quantify avoidable financial loss; see the evidence limits in [business_problem_validation.md](business_problem_validation.md).

The table below summarizes **signals supported by the supplied case records**. It does not establish root cause, confirmed avoidable loss, or client-owner agreement. Amounts attached to flagged records are not automatically savings or losses. The order is for discussion, not a ranking by verified financial impact. Detailed calculations and limitations are in [business_problem_validation.md](business_problem_validation.md) and [voice_note_evidence_log.md](voice_note_evidence_log.md).

| Problem area | Evidence and measured signal | What the evidence does not establish | Candidate pilot action |
| --- | --- | --- | --- |
| Quarter-end sales concentration and free-goods spend | FY27 Q1: June is 45.7% of extracted primary-sales value; June 22–30 is 29.2%. Free goods are 3.69% of invoiced primary sales, above the stated 3% cap. The QBR reports ₹1.415 crore of expiry claims (2.75%); populated claim values total ₹1.354 crore (2.64%), a ₹6.06 lakh difference. See [business_problem_validation.md](business_problem_validation.md), “Sales and free goods” and “Expiry claims.” | Timing does not prove schemes caused expiry claims. The QBR and extract do not reconcile; neither amount is an avoidable-loss estimate. | Review scheme approvals and volume alongside stockist sell-through, stock, and subsequent claims before proposing scheme controls. |
| Regional availability signals and stock-data quality | At September 30, CF-N02 has zero stock for 23 of 36 SKUs. September sales also contain zero-invoiced order-like lines for some products. Sources: [cnf_stock_snapshot.csv](../data-pack/data/cnf_stock_snapshot.csv) and [primary_sales.csv](../data-pack/data/primary_sales.csv). | Order-like lines do not confirm lost sales or cancellations. Conflicting duplicate keys prevent reliable Kolkata stock-value or capacity estimates. | Reconcile snapshot keys; review dated orders, cancellations, and CFA stock before recommending reallocation or transfers. |
| Claims turnaround and duplicate-credit controls | Of 548 credited FY27 Q1 claims with both dates, median claim-to-credit time is 43 days and 406 (74.1%) exceed 30 days. One duplicate-credit example is recorded at claims rows 3269 and 3596: two credits of ₹26,846.40 for the same stockist, batch, and quantity. 879 of 4,503 exact-row-deduplicated claims (19.5%) lack an invoice reference; the raw extract has 884 of 4,526 rows (19.5%). Source: [expiry_claims.csv](../data-pack/data/expiry_claims.csv). | Claim date is a receipt-date proxy; the QBR reports 46 days. The example does not establish aggregate leakage or recovery. A blank invoice reference alone does not prove a claim invalid. | Match claims to invoices, credit notes, and recovery records; route missing-reference claims for policy-required human verification. |
| Short-shelf-life invoice review | 217 FY27 Q1 invoice/batch groups calculate below 60% remaining shelf life using invoice date as a dispatch-date proxy; associated invoice value is ₹1.115 crore. Example: [primary-sales row 81945](../data-pack/data/primary_sales.csv), invoice `INV/E01/2606/076199`, batch `E2540483`; [batch-master row 472](../data-pack/data/batch_master.csv). | ₹1.115 crore is associated invoice value, not confirmed loss. Missing dispatch timestamps and exception evidence mean the records do not prove a policy breach or WMS/FEFO bypass. | Check flagged invoices against dispatch timestamps, exception approvals, and warehouse pick records before proposing a dispatch control. |

In-Depth Problem Analysis & Field Root Causes

1. Quarter-End Scheme Concentration & Expiry-Claim Signals

The case records support quarter-end sales concentration, FY27 Q1 free-goods value above the stated cap, and higher expiry-claim values than earlier periods. They do not show stockist sell-through or stock-on-hand, so they cannot establish that schemes caused stock accumulation or returns. QBR and claims-extract values also differ; neither the ₹84.1 lakh extract comparison nor the ₹90.1 lakh QBR comparison is a proven avoidable loss.

2. Regional Availability and Allocation Hypothesis

The September 30 snapshot shows zero stock for 23 of 36 SKUs at CF-N02, and sales records contain order-like lines with zero invoiced quantity. The forum discussion says regional shares remain at FY25 levels and suggests testing allocation. This is a stakeholder hypothesis, not a data-confirmed root cause: the allocation workbook, dated national forecast, verified stock by location, and downstream demand are not supplied. The forum says inter-CFA movement must pass through Bhiwandi CDC; treat transit and freight as scenario constraints until verified in the agreement and source data.

3. Claims Processing and Duplicate-Credit Signals

The supplied claims extract shows 43-day median claim-to-credit time among the defined Q1 credited population, against the case’s stated 30-day processing limit; the QBR reports 46 days, so Finance reconciliation remains open. One duplicate credit is directly matched in the extract: the same stockist, batch, quantity, and value appear as two credited claims. This is evidence of one event, not an estimate of total leakage. The role-play discussion adds a proposed screening procedure and clarifies that a missing invoice reference must be checked against billing plus written Area Manager approval naming the claim. The extract contains no approval evidence, and a blank reference alone does not prove a claim invalid.

4. Short-Shelf-Life Invoice Candidates

Using invoice date as a proxy for dispatch, 217 FY27 Q1 invoice/batch groups calculate below the 60% remaining-shelf-life threshold. Their associated value is not a confirmed breach or loss. One reported case matches a sales row and batch-master dates at about 45% remaining. Warehouse congestion and FEFO issues are described in the voice note, but the pack has no WMS pick/override events to establish that congestion caused the candidate dispatches.

5. Forecast and Pilot Scope

The case data supports a retrospective primary-shipment baseline, but not a downstream-demand forecast because stockist sell-through and on-hand data are absent. The forum says the reported national forecast accuracy is stable and recommends checking allocation shares before building a new forecasting capability. That is a useful prioritization signal, not proof the forecast is sound or that allocation caused the shortages. A sensible pilot is deterministic exception screening with source evidence and human review; use the forecast only as a transparent baseline while the allocation and demand data gaps are addressed.

6. Proposed Pilot Scope and Users

The forum discussion supports testing an automation-first, read-only workflow rather than beginning with a new demand-sensing model. The pilot should return reproducible checks and row-level evidence; Finance and Supply Chain reviewers remain responsible for decisions. The forum’s cadence and business rules are scenario inputs until confirmed against the supplied policy and case files.

**Commercial Finance reviewer:** review claims from pasted text or register rows; see batch-master expiry, date-derived claim window, billing quantity, prior-credit match, and invoice-reference evidence. Missing or failed checks go to a person. The forum says a claim without an invoice reference needs a matching billing-ledger record, a quantity within invoiced volume, and written Area Manager approval naming the claim. The supplied data does not contain that approval. Replies may be drafted, but a Finance employee sends them. No credit note is posted by the prototype.

**Supply Chain reviewer:** review retrospective shelf-life candidates and regional stock signals. The forum suggests testing the existing allocation split, using non-scheme primary dispatch as a temporary demand proxy, and handling stock through the CDC. The pack lacks live dispatches, a verified allocation workbook, CDC inventory, and downstream stockist data. The prototype must not block dispatches, initiate transfers, or claim a financial saving.

No pilot success target for forecast accuracy, claim rejection, or financial recovery is adopted from the forum alone. Agree a hand-checked case set and review measures before treating the pilot as operationally effective.

7. Remaining Questions for the Hypothetical Pilot

For this fictional exercise, these remaining data questions should be reconciled within the case materials before presenting operational recommendations. The forum answered some process questions, but these evidence gaps remain:

1. Finance KPI Reconciliation:
  * Question to Rohan Mehta (CFO) & Neha Bansal (Controller): The Q1 FY27 QBR reports ₹1.415 crore in expiry claims (2.75% of sales), whereas summing the 518 deduplicated rows in expiry_claims.csv yields ₹1.354 crore (2.64% of sales), with 18 rows lacking populated values. What specific date cutoffs, transaction types, or manual journal provisions account for this ₹6.06 lakh variance? Furthermore, how is the target 1.0% return rate officially defined—as net credit notes issued, provisions accrued, or physical write-offs?
2. Fill-Rate Metric Definition:
  * Question to Kavita Rao (Head of Supply Chain): The QBR reports an operational fill rate of 90.9% for Q1 FY27. However, dividing total invoiced quantity by total ordered quantity across exact-row-deduplicated primary sales yields 85.3%. Does the official corporate fill-rate calculation exclude unsupplied lines with blank batch entries, apply order-line capping, or filter out specific scheme codes?
3. Policy Amendment v4.2 Governance:
  * Question to Arjun Sethi (NSM) & Neha Bansal (Controller): 879 of 4,503 exact-row-deduplicated claims (19.5%) lack an original invoice reference; the raw extract has 884 of 4,526 rows (19.5%). The forum says these claims require a matched ledger, quantity within invoiced volume, and written Area Manager approval naming the claim. Where is that evidence retained? The supplied extract does not contain it, so the pilot must route such rows for human review rather than infer eligibility.
4. CFA Snapshot Key Conflicts & WMS Audit Data:
  * Question to Kavita Rao (Head of Supply Chain): The September 30 cnf_stock_snapshot.csv contains 70 duplicate rows with conflicting quantities across identical CFA/SKU/batch keys. Can Supply Chain supply the definitive month-end physical stock reconciliation and provide CFA WMS batch-level pick/override audit logs to verify whether FEFO picking rules were bypassed?


## Forum discussion: useful assumptions, not source-data findings

The discussion narrows the pilot toward deterministic checks with human handling of exceptions. Finance’s described screening sequence is: use batch-master expiry dates; infer near-expiry versus expired from claim date; check the window, billing quantity, prior credit, and required written approval for claims without an invoice reference; send failures or missing evidence to a person. It also describes a weekly claims register as operationally acceptable and outbound replies as drafts only. These details are case-role-play answers and should be verified against the policy PDF and the case’s intended decision rights.

Supply Chain’s responses suggest a separate allocation and aging-stock analysis: use six months of ordered packs including free packs, count repeated unmet orders once, smooth scheme spikes, and compare against the agreement’s two-month top-up norm. Use primary sales rather than the known-unreliable `avg_monthly_outward_packs` field. The forum also describes CDC-mediated transfers, a 10–14 day transit assumption, and a proposed minimum return value. These are planning assumptions; the supplied pack does not provide the dated allocation workbook, current national forecast, verified CDC availability, or stockist sell-through needed to confirm the cause or expected benefit.

The same discussion says the national forecast’s reported accuracy is stable and that allocation shares remain at FY25 levels. This is a reason to investigate allocation before investing in a new forecasting model, not proof that forecast error is irrelevant or that allocation caused the observed shortages. Current data can test shipment patterns, but cannot measure downstream demand.

### Reconciliation required before citing the no-invoice claim total

The discussion cites 804 claims and approximately ₹1.50 crore, of which ₹1.30 crore was credited. In the supplied `expiry_claims.csv`, exact-row deduplication gives 4,503 records, of which 879 have blank `original_invoice_ref`; the raw file has 4,526 rows and 884 blanks. Among the deduplicated blank-reference rows, 798 are marked credited. Their populated `claim_value_inr` totals ₹1.273 crore and their populated `credit_value_inr` totals ₹1.327 crore. These are separate fields and neither reproduces the forum’s rounded figures. The forum may use a different filter or data cut; do not combine its totals with this extract or call the difference leakage until the populations are reconciled.
