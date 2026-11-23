# Pfizer domestic channel: data-backed diagnosis

**Working discovery note · updated 15 November 2026**

## Executive readout

This is a fictional teaching case, not evidence about Pfizer’s actual operations. Within the case pack, Finance reports a sharp rise in expiry claims and a fall in stockist fill rate. The records also show quarter-end sales concentration, free-goods spend above the stated cap, a matched duplicate credit, delayed claims, and repeated unfilled-order signals in the North. Together these support a real operating problem to investigate: the channel may be committing or holding stock without enough visibility into where demand is, while supply, allocation, schemes, picking, and claims controls are handled through separate processes.

The pack does not prove one root cause or quantify avoidable loss. Important measures do not fully reconcile, and the CFA stock snapshot contains conflicting duplicate records. There is no stockist sell-through or stock-on-hand data. Treat the diagnosis as a set of evidence-backed signals and testable explanations, not a causal finding or savings commitment.

## What is supported by the case evidence

### Expiry claims rose, but Finance’s total does not tie to the claims extract

The QBR reports ₹1.415 crore of expiry claims in FY27 Q1, equal to 2.75% of ₹51.36 crore primary sales. It reports 0.64% in FY25 Q2. After parsing all supplied date formats and removing exact duplicate rows, the sales extract totals ₹51.357 crore for April–June 2026, which reconciles to the QBR denominator after rounding. The claims extract has 518 near-expiry or expired claims dated in that quarter. The sum of their populated claim values is ₹1.354 crore, or 2.64% of extracted sales, about ₹6.06 lakh below the QBR numerator. Eighteen of the 518 rows have no claim value, so the difference may partly reflect missing values; it is not reconciled. For FY25 Q2, the equivalent claims-extract rate is 0.61%, directionally close to the QBR’s 0.64%.

The rise is supported, but the official rate’s numerator and cutoff remain unreconciled. The extract supports an arithmetic difference of about ₹84.1 lakh between its recorded Q1 claims and 1% of QBR primary sales. Using the QBR figures, the corresponding gap is about ₹90.1 lakh. Neither amount is proven avoidable or recoverable. Finance must reconcile which claims, dates, and values the official KPI includes before either becomes a business-case estimate. [QBR finance and MIS pack](../data-pack/06_qbr_finance_and_mis_pack.pdf) [Primary sales extract](../data-pack/data/primary_sales.csv) [Expiry claims extract](../data-pack/data/expiry_claims.csv)

### Sales and free goods are concentrated around quarter end

For FY27 Q1, June accounts for 45.7% of extracted primary sales value, and June 22–30 accounts for 29.2%. The QBR’s FY26 quarterly average is 46% for the final month and 30% for its final nine days. These are similar patterns from different periods, not a same-period reconciliation. The sales extract also values Q1 free goods at 3.69% of invoiced primary sales, matching the QBR and exceeding the policy’s 3% cap. The QBR says the exception was approved by the CFO.

Interview notes and the inbox describe schemes, sales targets, and quarter-end loading. This supports examining scheme timing and economics. It does not establish that schemes caused expiry claims: the pack lacks scheme-linked stockist sell-through, stock-on-hand, and later returns by customer and SKU. The policy’s scheme stock norm depends on secondary sales, which are unavailable. [Trade terms and returns policy](../data-pack/02_trade_terms_and_returns_policy.pdf) [Stakeholder interview notes](../data-pack/04_stakeholder_interview_notes.pdf) [Inbox export](../data-pack/05_inbox_export.pdf)

### North availability and unfilled-order signals recur

At the September 30 snapshot, Lucknow (CF-N02) has 23 of 36 SKUs at zero stock. This CFA has one record per SKU in that snapshot, so the count is not affected by the duplicate-key issue described below. In September sales records, several listed stockists in Gorakhpur, Prayagraj, Varanasi, and Ludhiana have order-like lines with zero invoiced quantity for Amox-Clav or Azithromycin. The extract lacks order status and cancellation reason, so these are unfilled-order signals, not confirmed cancellations or lost sales.

The Gorakhpur caller is Royal Pharma Traders (STK0152). The customer is in the master under Lucknow, but the sales extract has no FY27 Amox-Clav or Azithromycin sales for that customer. Other Gorakhpur stockists have related September order-like lines. This supports a regional concern but does not verify the named caller’s transactions. The Varanasi inbox message separately reports repeated cancellations for the same products. [CFA stock snapshot](../data-pack/data/cnf_stock_snapshot.csv) [Primary sales extract](../data-pack/data/primary_sales.csv) [Stockist master](../data-pack/data/stockist_master.csv) [Inbox export](../data-pack/05_inbox_export.pdf)

### Short-shelf-life dispatch flags are a review queue, not a loss estimate

Policy requires at least 60% of total shelf life to remain at dispatch. Using invoice date as the available proxy for dispatch, and comparing remaining days with each batch’s manufacturing-to-expiry duration, 217 invoice/batch groups in FY27 Q1 fall below the threshold. Their associated invoice value is ₹1.115 crore. This amount is the value attached to flagged records, not the value of a confirmed breach or loss. The extract does not contain actual dispatch timestamps, approved exceptions, or WMS pick and override events.

One inbox complaint can be matched: invoice INV/E01/2606/076199, batch E2540483, SKU PFL1404, dated June 21, 2026, appears in sales with 358 packs invoiced. The batch master shows manufacture on May 11, 2025 and expiry on April 30, 2027; about 45% of its total shelf life remained at invoice. This supports a concrete short-dated-invoice concern. Distribution still needs to confirm the dispatch-date convention and any exception before calling it a policy breach. [Trade terms and returns policy](../data-pack/02_trade_terms_and_returns_policy.pdf) [Primary sales extract](../data-pack/data/primary_sales.csv) [Batch master](../data-pack/data/batch_master.csv) [Inbox export](../data-pack/05_inbox_export.pdf)

### Claims handling has delay and duplicate-credit evidence

The policy gives Commercial Finance 30 days from claim receipt to approve and raise a credit note. The claims extract has claim dates but no separate received timestamp, so claim date is used as a proxy. Among 548 credited FY27 Q1 claims with both dates recorded, median claim-to-credit time is 43 calendar days; 406 (74.1%) took more than 30 days. The QBR reports 46 days, close but not identical; the exact calculation and cutoff should be reconciled.

The Vijayawada audio complaint matches claim CLM-2607-02627 for Matrix Medicos (STK0143): PFL1401, 689 packs, ₹68,004.30, submitted July 29, 2026. It remains pending with no credit-note date in the September 30 claims extract, 63 days after the recorded claim date. The October 7 recording and September 10 inbox email both describe the delay. The caller’s reported payment hold is not independently visible in the supplied records.

The duplicate-credit example is also traceable. For STK0025, batch F2440122, PFL1401, quantity 272, the claims extract records credit CLM-2603-01616 for ₹26,846.40 and a second credit CLM-2605-04488 for the same quantity and amount. The inbox discusses the second credit and possible recovery. This establishes one duplicate-credit event in the case data, not its overall prevalence. Of 4,503 claims after exact-row deduplication, 879 (19.5%) have no invoice reference; the raw extract has 884 such rows among 4,526 (19.5%). Policy allows that only after ledger verification and written Area Manager approval; the extract does not contain the approval evidence needed to judge those rows. [Trade terms and returns policy](../data-pack/02_trade_terms_and_returns_policy.pdf) [Expiry claims extract](../data-pack/data/expiry_claims.csv) [Claim emails](../data-pack/data/claim_emails.csv)

## What the forum discussion adds—and what it does not prove

The FDE Academy forum is a role-play discussion for this fictional case. Treat its answers as additional case assumptions, not as independent transaction evidence or confirmation of real Pfizer practices.

| Forum input | How it changes the working diagnosis | Evidence status / dependency |
|---|---|---|
| CFO and Demand Planning describe forecast accuracy as stable and allocation shares as unchanged since FY25. | Prioritize a check of allocation governance and regional deployment before adding a complex forecast model. | Stakeholder assertion in the discussion. The forecast extract and allocation workbook are absent, so this does not prove allocation is the cause. |
| Finance describes a 30-day claim processing limit, weekly register cadence, duplicate linkage, evidence checks, and a human decision for exceptions. | A deterministic claims screening and audit queue is a plausible pilot slice; the tool should recommend and explain, while the reviewer decides. | Process detail from role-play. Validate clause wording and decision rights against source PDFs. |
| Claims without an invoice reference require matching ledger evidence, an in-range quantity, and written Area Manager approval naming the claim. | Missing reference must not be treated as automatic rejection or automatic approval; missing evidence routes to a person. | The extract has no approval artifact, so the 879 deduplicated blank-reference rows cannot be classified as eligible or invalid from this CSV alone. |
| The forum gives a date-derived near-expiry and expired claim window: 90 days before expiry through expiry, then through 90 days after expiry; use batch-master expiry and ignore the submitted label. | `assess_expiry_claim_window` now derives the category from dates, returns label mismatch evidence, and screens the inclusive window. Other claim types remain not applicable. | Discussion interpretation of CO-POL-014 §5.2; confirm the policy PDF before operational use. Expiry day is included; the implementation classifies that boundary as expired without flagging either adjacent label as a mismatch. |
| Supply Chain says the monthly outward field is unreliable; use primary sales, deduplicate repeated unmet orders, and remove only scheme-period demand above a normal month. | Any allocation analysis should use an explicit, reproducible demand proxy and avoid treating scheme spikes or repeated unmet orders as recurring demand. | Assumptions supplied by the forum. Repeated-order linkage and scheme line coding require source fields and definitions to be checked. |
| Return/reallocation conditions include two-month cover, 10–14 day transit, and a ₹5 lakh per-SKU minimum. | These can be scenario parameters for a human-reviewed planning analysis. | They are not verified operational rules from the structured extracts. CDC stock availability is also assumed, not measured here. |

### Claims-without-invoice count reconciliation

The forum cites 804 claims with no invoice reference and approximate claim/credit amounts of ₹1.50 crore/₹1.30 crore. The supplied claims extract has 4,526 raw rows; 23 exact duplicate rows leave 4,503. Blank `original_invoice_ref` appears on 884 raw rows and 879 deduplicated rows. Of the deduplicated blank-reference rows, 798 are marked credited; their populated claim values total ₹1.273 crore and populated credit values total ₹1.327 crore. The forum’s count and amounts do not reproduce from this population. A different cutoff or filter may explain the difference; until it is supplied, report both sources separately and do not imply the forum amounts were computed from this CSV.

## Data checks that change what can be concluded

| Check | Evidence | Effect on diagnosis |
|---|---|---|
| Primary-sales period and duplicates | 93,809 raw rows; 745 exact duplicate rows removed, leaving 93,064. All dates parse after supporting `DD-MM-YYYY`, `YYYY-MM-DD`, and `DD-Mmm-YYYY` forms. Period: April 1, 2024–September 30, 2026. | Q1 sales reconcile to QBR at ₹51.357 crore. Reproducible calculations should state deduplication and date parsing. |
| Claims duplicates and coverage | 4,526 raw rows; 23 exact duplicate rows removed, leaving 4,503. Claim dates parse across the same mixed formats. | Counts and sums here use exact-row-deduplicated records. The populated Q1 claim values differ from the QBR by ₹6.06 lakh; 18 Q1 rows have no claim value. |
| CFA snapshot grain | September 30 has 425 rows. After normalizing CFA code formatting, these represent 355 CFA/SKU/batch keys; 67 keys repeat, with 70 excess rows and conflicting quantities. | Do not rely on total stock cover, Kolkata stock value, or total expiry exposure from this snapshot until conflicts are resolved. Lucknow’s 23/36 zero-SKU count is still usable because CF-N02 has 36 unique SKU rows. |
| Fill-rate reconciliation | Sum of `invoiced_qty` divided by `ordered_qty` in exact-row-deduplicated FY27 Q1 sales is 85.3%. The QBR reports 90.9%. | Do not present the raw calculation as the official fill-rate KPI. Agree the population, treatment of blank-batch unfilled lines, and formula with the metric owner. |
| Master joins | SKU and nonblank batch identifiers in sales match their masters. Some identifiers vary in case or CFA formatting and require normalization. | Normalize before joins. Keep customer-specific conclusions tied to matched stockist codes and do not infer from city totals alone. |

The September stock extract also contains many duplicate keys at the East, North, West, and South CFAs. Earlier calculations of Kolkata cover and expiry value therefore should not be used as verified totals. Batch/expiry dates can identify what may be at risk, but the duplicated quantities prevent a reliable stock valuation by location. [CFA stock snapshot](../data-pack/data/cnf_stock_snapshot.csv) [SKU master](../data-pack/data/sku_master.csv) [Stockist master](../data-pack/data/stockist_master.csv)

## Can the data support a primary-sales forecast?

Yes, as a historical CFA-by-SKU monthly shipment baseline. After exact-row deduplication, the extract covers 30 continuous months and all 216 CFA/SKU combinations (6 CFAs × 36 SKUs). The target tested was monthly invoiced quantity plus free quantity. A rolling-origin backtest made three-month predictions from 16 historical origins, for 10,368 predictions across the 216 series.

| Simple method | Three-month WAPE |
|---|---:|
| Last observed month | 44.0% |
| Trailing 3-month average | 35.3% |
| Trailing 12-month average | 35.1% |
| Same month in prior year | **21.6%** |
| Average of prior observations from the same calendar month | 22.1% |

The same-month-prior-year baseline had the lowest aggregate WAPE among these simple methods. Its WAPE ranged from 17.1% to 29.3% by CFA; the same-month average was slightly better for CFE01. This is retrospective evidence on primary shipments, not proof of downstream demand or a validated operational forecast. The planning audio’s “around 14” metric is unclear and is not used as a target. No pass/fail accuracy threshold is set in the case materials.

The data pack explicitly says secondary visibility is unavailable and the earlier DMS pilot was discontinued. It contains no stockist sell-through or stock-on-hand table. Therefore the downstream-demand forecast cannot be trained or evaluated from this pack. Do not silently use primary shipments as a proxy for downstream demand. [Company and channel overview](../data-pack/01_company_and_channel_overview.pdf) [Primary sales extract](../data-pack/data/primary_sales.csv)

## Diagnosis and next work

**Supported:** the case shows rising expiry claims, falling reported fill rate, high free-goods spend, repeated North zero-stock and unfilled-order signals, short-shelf-life invoices that need review, delayed claim handling, and one duplicate credit. Stakeholder notes and operational records point to several control and planning weaknesses worth testing. The CFA agreement calls for monthly allocation, defined top-up limits, FEFO picking, logged overrides, and no direct CFA-to-CFA transfer; the pack does not include the detailed allocation workbook or WMS events needed to see where execution diverged.

**Not established:** the records do not prove that schemes caused returns, that an inaccurate forecast caused the regional shortages, that excess CFA inventory was available to the affected stockists, or how much value was avoidable. The conflicting snapshot keys, QBR/extract differences, missing sales-order status, and lack of stockist sell-through prevent those conclusions.

For this hypothetical exercise, validate the case internally by obtaining and reconciling the missing artifacts rather than contacting real Pfizer personnel:

1. **Finance:** reconcile the QBR return numerator, cutoff, fill-rate formula, and claim-to-credit timing. Match claims to credit notes and invoice payments to estimate duplicate or delayed-claim exposure.
2. **Sales and channel:** obtain stockist sell-through and on-hand stock by stockist/SKU/month, plus scheme participation and stockist order status/cancellation reason.
3. **Supply Chain and CFA operations:** resolve duplicate snapshot keys; obtain dated allocation versions, demand inputs, order fill/cancel records, dispatch timestamps, WMS batch/bin pick events, FEFO overrides, and approved exceptions.
4. **Model review:** retain the seasonal-naïve method as a transparent primary-sales baseline, compare it with simple alternatives, and show WAPE overall, by CFA, and by forecast horizon. Gate downstream forecasting on receipt of sell-through and stockist inventory data.

If built as a pilot, keep it read-only and show each number’s source and calculation. It can flag items for human review; current owners retain authority for credits, write-offs, transfers, and scheme approvals. Measure alert accuracy and review time alongside returns, availability, aging stock, and claim turnaround. A short pilot should not be presented as proof that it caused a reduction in returns.

## Source scope

This review used the six case PDFs, seven supplied CSVs, and the user-provided voice-note transcripts recorded in [voice_note_evidence_log.md](voice_note_evidence_log.md). All source documents identify the material as fictional training content. Calculations use exact-row deduplication for primary sales and claims; the stock snapshot is not treated as additive where normalized keys conflict. No source data was changed.
