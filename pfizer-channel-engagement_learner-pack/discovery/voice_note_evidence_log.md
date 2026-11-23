# Voice note evidence log

**Status:** Working discovery log · updated 15 November 2026
**Purpose:** Capture what callers and colleagues report in the six supplied voice notes, identify what those reports might mean for the channel, and list the records needed to verify them.

## How to read this log

The summaries below are based on transcripts/dictation provided in the working conversation; the recordings have not been independently transcribed or checked word-for-word. They are **reported claims, not verified Pfizer facts**. Product names, dates, quantities, acronyms, and places may have been misheard, especially in multilingual clips. Confirm against the original recording and source systems before using a claim in a business case or making an operational decision.

“Data needed” means evidence that could test the report. A file in the project pack may provide only a partial check; a point-in-time snapshot, for example, cannot confirm an outage over several weeks.

## Recording summaries and validation leads

### CALL_REC_9935xxxx_20260930 — stock availability in Gorakhpur

**Language / transcript basis:** Hindi; user-provided dictation.
**What the caller reports:** Gupta of Royal Pharma in Gorakhpur says Amoxiclav and Azithro have been unavailable for almost three weeks, and that Lucknow CNF repeatedly cancels their orders due to lack of stock. A new 200-bed hospital has placed an order with six items short. The caller says a September anti-infective order went to another company because Pfizer product was unavailable, and that newer parties in Prayagraj and Varanasi have raised similar concerns. He asks for someone to coordinate with Lucknow or the Mumbai decision-maker.
**Potential business issue:** Lost or at-risk orders due to product unavailability; possible pattern across multiple territories.
**Evidence to request/check:** Order-line history with ordered, supplied, cancelled quantities and reason codes; daily SKU-by-CNF stock and stockout dates; hospital order and fulfilment record; customer/field confirmation of competitor substitution; SKU mapping for the dictated product names.
**What the current pack can establish:** The CNF stock snapshot can show stock at its extraction date and primary sales can show shipments. Neither alone verifies three weeks of historical stockouts, cancelled demand, or competitor sales.
**Confidence / status:** Medium confidence in the broad stockout report; exact product/SKU mapping and scale unverified.

### CALL_REC_8662xxxx_20261007 — delayed claim and payment hold

**Language / transcript basis:** Telugu; user-provided dictation translated into English.
**What the caller reports:** Neelu Srinivas of Accounts at Matrix Medicos in Vijayawada calls about a Pantoprazole 40 claim. The dictated claim number sounds like “CLM 2607 0 26 27”; the caller says 689 strips worth ₹68,004 were submitted on July 29 and no credit note has arrived. The caller refers to a 30-day policy, says their MD has asked them to hold payment on current invoices until the claim is resolved, and reports being told by a Hyderabad office to resubmit if the credit note does not arrive. They also describe emails saying claims without invoice copies were approved by an Area Manager over the phone and ask for a callback.
**Potential business issue:** Claim turnaround and inconsistent resubmission/documentation practices may create payment friction, rework, or duplicate-claim risk.
**Evidence to request/check:** Claim register and status timestamps; submitted documents; credit-note ledger; invoice/payment ledger; resubmission and duplicate checks; Area Manager approval evidence and policy requirements.
**What the current pack can establish:** The project claims extract and policy can provide context on claim aging and rules, but this specific caller’s claim, payment hold, and approval trail must be matched to source records.
**Confidence / status:** Medium for the general complaint; low for the exact claim ID and amounts until verified. Do not treat the reported phone approval as valid approval without checking the required record.

### AUD-20261001-WA0004 — scheme stock and shortage in Ludhiana

**Language / transcript basis:** Punjabi; user-provided Punjabi transcript, summarized in English.
**What the caller reports:** A caller associated with Grace Pharma Traders in Ludhiana says a 10+2 offer led them to buy a large quantity of Monte LC; they normally sell about 500–600 strips monthly and now have roughly two to three months of stock. They also say Amox-Clav is unavailable, orders placed around the 22nd and 30th were cancelled by the Gurugram CF due to no stock, and they have supplied a competing brand instead. They mention monsoon demand and the possibility of another Monte LC offer. Some dates, quantities, and phrases in the transcript are unclear.
**Potential business issue:** Promotional loading may leave excess stock of one product while a different demanded product is unavailable; possible competitor substitution.
**Evidence to request/check:** Scheme circular and participation by customer/SKU; customer stock-on-hand and secondary sales; order/cancellation records and CNF stock by date; substitution confirmation; returns/expiry outcomes for scheme stock.
**What the current pack can establish:** Primary sales and the CNF snapshot can give partial shipment and stock context. Without stockist inventory, sell-through, order cancellations, and scheme participation linked by customer/SKU/date, the alleged mismatch and its financial impact remain unproven.
**Confidence / status:** Medium for the reported pattern; low for exact quantities/dates.

### AUD-20261013-WA0003 — planning, allocation, and forecast discussion

**Language / transcript basis:** English transcript provided by the user. The user first introduced it as `AUD-20261003-WA0003`, but the voice-notes README lists the recording as `AUD-20261013-WA0003`; confirm the identifier against the file.
**What the speaker reports:** A colleague says a forecast-accuracy review is due, with a usual chart at SKU-month level and a metric sounding like “MAPS” around 14; both the acronym and meaning need confirmation (possibly MAPE, but do not assume). A Lucknow buffer top-up for Amox/Clav/Azithro is awaiting STO sign-off, reportedly the third such top-up that quarter. Hooghly wants to hold August and September. The allocation sheet is said to still use an FY25 split, with the FY26 review unfinished. A September sales overlay was late and described as a single number that would be spread manually. A vendor demo is also mentioned.
**Potential business issue:** Forecast and allocation inputs may be stale or manually adjusted; repeated buffer requests could indicate a mismatch between plan and local demand/availability.
**Evidence to request/check:** Forecast versions and metric definition; allocation versions, review approvals and change logs; buffer top-up/STO records; local demand and stock by SKU/CFA; the September overlay and its source; any agreed rules for spreading a national number.
**What the current pack can establish:** Primary sales can support a historical SKU-month shipment series, but cannot by itself confirm forecast accuracy, the FY25/FY26 allocation state, the reported top-ups, or downstream demand.
**Confidence / status:** Medium for the process concerns as reported; low for the “14” figure and metric until the original chart and definition are reviewed.

### AUD-20261014-WA0007 — aging lots and warehouse picking in Hooghly

**Language / transcript basis:** Bengali; user-provided Bengali transcript summarized in English. Some warehouse/software terms are uncertain.
**What the caller reports:** A caller from the Hooghly warehouse says that since a software change in February, pickers mostly take stock from front racks while older lots remain at the back around aisle 14. Some lots may not have moved since February or March and could enter a 50–60-day remaining-shelf-life range soon. The caller says batch/lot functionality is expected in a later software phase, the warehouse is about 95–96% full, and CDC deliveries continue. They worry the older lots may ultimately need to be destroyed.
**Potential business issue:** Picking and replenishment practices may allow older stock to age while newer stock is picked, increasing expiry exposure and congestion.
**Evidence to request/check:** Batch-by-bin inventory and movement history; WMS pick events and FEFO configuration/overrides; goods receipts and dispatches; expiry dates and blocked-stock rules; warehouse capacity/utilization record; software release notes and batch/lot feature status; destruction/write-off outcomes.
**What the current pack can establish:** Batch master and the CFA snapshot may identify stock and expiry exposure at a point in time. They cannot show which bin pickers selected, whether older lots were bypassed, or whether those lots were destroyed.
**Confidence / status:** Medium for the reported warehouse concern; exact dates, system capability, and projected destruction unverified.

### AUD-20261003-WA0011 — transcript not reliable enough to use

**Language / transcript basis:** The user-provided dictation sounded mixed/unclear; the user later said it might be Tamil or Telugu and did not understand it.
**What we can conclude:** No dependable summary has been established. Do not use the earlier attempted interpretation as evidence or combine it with the other notes. Revisit only with a reliable transcript or translation checked against the recording.
**Confidence / status:** Unusable for business conclusions in its current transcript form.

## Analysis — stock availability and short-shipment signal

**Question checked:** Do the sales and CFA stock extracts support the stockout reports for Amoxiclav and Azithromycin in the North region? This check tests the reported products and locations; it does not establish the callers’ explanations or estimate lost revenue.

### Product and location mapping

- The SKU master maps **Azithromycin 500 mg tablets** to **PFL1001** and **Amoxicillin + Clavulanic acid tablets (Amox-Clav)** to **PFL1002**.
- The stockist master maps Gorakhpur customers to **CF-N02 (Lucknow)** and Ludhiana customers to **CF-N01 (Gurugram)**. Prayagraj and Varanasi customers in the master are also mapped to CF-N02.

### CFA stock at month end

The September 30, 2026 snapshot has one row for each of CF-N02 / Lucknow’s 36 SKUs; 23 are recorded at zero stock. This is a clear month-end signal for Lucknow. It does not establish the exact dates of stockouts or verify the callers’ reported three-week duration.

The broader snapshot needs a data-quality caveat. Across all CFAs, normalizing code formatting yields 355 CFA/SKU/batch keys in 425 rows. Sixty-seven keys repeat, with 70 extra rows and conflicting quantities. Stock totals, cover, and batch-level exposure for CFAs with duplicate keys cannot be treated as reconciled until the source owner explains the records. In particular, the earlier Kolkata comparison and stock-cover totals should not be used as confirmed figures.

### September order and invoice records

The September 2026 primary-sales extract contains order-like records with positive `ordered_qty` but lower or zero `invoiced_qty`. For this summary, exact duplicate rows were removed; records were grouped by invoice number, stockist code (trimmed for whitespace), and SKU. Ordered quantity was counted once per group; invoiced quantity was summed within the group. These are quantities as recorded in the CSV, not a lost-sales or financial estimate.

| Stockist city / supplying CFA | SKU | Order groups | Ordered quantity | Invoiced quantity | Groups with zero invoiced quantity |
|---|---|---:|---:|---:|---:|
| Gorakhpur / CF-N02 | PFL1001 Azithromycin | 4 | 6,265 | 0 | 4 |
| Gorakhpur / CF-N02 | PFL1002 Amox-Clav | 6 | 12,654 | 2,876 | 3 |
| Prayagraj / CF-N02 | PFL1001 Azithromycin | 2 | 7,187 | 0 | 2 |
| Prayagraj / CF-N02 | PFL1002 Amox-Clav | 4 | 3,793 | 1,959 | 1 |
| Varanasi / CF-N02 | PFL1001 Azithromycin | 6 | 8,008 | 0 | 6 |
| Varanasi / CF-N02 | PFL1002 Amox-Clav | 4 | 3,765 | 2,310 | 1 |
| Ludhiana / CF-N01 | PFL1001 Azithromycin | 2 | 1,593 | 362 | 1 |
| Ludhiana / CF-N01 | PFL1002 Amox-Clav | 2 | 4,613 | 0 | 2 |

Several of the zero-invoiced rows have a blank batch number and zero net value. The extract does not include an order status or cancellation reason, so these rows are consistent with unfilled order lines but do not prove that the orders were cancelled or lost. The Ludhiana figures cover stockists listed in the master, not a confirmed match to the caller’s named Grace Pharma Traders.

### Match to the callers and data limitations

- **Gorakhpur:** Royal Pharma Traders appears in the stockist master as STK0152 under CF-N02. There are no FY27 September sales rows for PFL1001 or PFL1002 at this account, although other Gorakhpur stockists have order-like records for those products. The extract does not match the caller’s specific reported orders.
- **Ludhiana:** The stockist master has Sai Healthcare and Krishna Distributors in Ludhiana, but no Grace Pharma Traders. The city-level short-shipment records therefore cannot confirm the named caller’s experience.
- **Metric consistency:** The September CFA snapshot reports zero average monthly outward for CF-N02/PFL1001, while the sales extract records 13,542 invoiced units for that SKU at CF-N02 in August and 40,037 ordered units in September. These fields may use different definitions or grains; reconcile them with the data owner before using the outward field as a demand or stock-cover measure.
- The sales extract contains 93,809 rows, including 745 exact duplicate rows; after exact deduplication, 93,064 remain. Invoice dates appear as `DD-MM-YYYY`, `YYYY-MM-DD`, and `DD-Mmm-YYYY`; all dates parse after normalization.

### Assessment

**Finding:** The available extracts support a stock availability and short-shipment concern for Amox-Clav and Azithromycin in North-region records. The strongest usable stock snapshot fact is Lucknow’s 23 zero-stock SKUs. The primary-sales extract also has order-like records with zero invoiced quantities across Gorakhpur, Prayagraj, Varanasi, and listed Ludhiana customers. The evidence is stronger for a regional signal than for the specific experiences of the callers.

**Not established:** The extracts do not show the reason or final status of the unfilled quantities, the exact duration of each outage, whether customers switched to competitors, or the rupee value of lost sales. To confirm those points, request order status/cancellation history, daily CFA stock and dispatch records, and customer-linked order data for the named stockists.

**Sources:** [Primary sales extract](../data-pack/data/primary_sales.csv), [CFA stock snapshot](../data-pack/data/cnf_stock_snapshot.csv), [SKU master](../data-pack/data/sku_master.csv), and [stockist master](../data-pack/data/stockist_master.csv).

## Analysis — aging stock and warehouse-picking signal

**Question checked:** Do the batch master, CFA stock snapshots, and primary-sales extract support the Hooghly caller’s report of older cardio/pain lots nearing expiry and remaining unpicked?

### Location and product scope

The stockist master has no customer record with city `Hooghly`, and the CFA stock snapshot has no warehouse or bin field for Hooghly. The East CFA is recorded as **CF-E01 / Kolkata**. I used that CFA as a regional proxy only; it is not confirmed to be the caller’s warehouse. The SKU master’s relevant therapy areas are named **Cardio-metabolic** and **Pain and inflammation**.

### September 30, 2026 stock and expiry

The latest CFA snapshot is **September 30, 2026**, two weeks before the recording. It does not contain a Hooghly warehouse or bin location. Hooghly is identified as the East C&F in the company and channel documents, but the snapshot labels that CFA CF-E01 / Kolkata; this is only a possible location mapping for the caller.

The stock snapshot has repeated normalized CFA/SKU/batch keys with conflicting quantities. At the latest date, 67 keys repeat across 425 rows, with 70 extra rows. For that reason the previously calculated Kolkata cardio/pain stock total, 22,032-pack near-expiry quantity, and related PTS exposure are withdrawn as unverified. The expiry dates recorded for positive cardio/pain lines place the earliest listed expiry at **March 31, 2027**, 182 days after the snapshot. That does not show stock within 50–60 days of expiry in the September snapshot, but conflicting quantities mean the exact exposure cannot be sized. Neither the warehouse mapping nor the caller’s timeframe is confirmed.

### Batch movement check

Because the monthly snapshot contains repeated keys with conflicting quantities, comparing its March and September balances would give a misleading movement measure. Primary sales can show that invoices were recorded against a CFA/SKU/batch, but they cannot establish which bins were picked, whether older lots were bypassed, or the quantity physically remaining. WMS pick and movement events are required for that test.

### Assessment and evidence gap

**Finding:** The pack contains expiry-dated cardio/pain records, but the stock snapshot’s conflicting duplicate keys prevent a reliable location-level inventory or expiry-exposure total. The expiry dates on positive lines do not show a listed cardio/pain batch due within 180 days of September 30. That does not validate the reported 50–60-day risk, and it cannot rule out an issue in a specific bin.

**Not established:** The pack cannot verify the Hooghly caller’s bin/aisle account, whether the WMS selected newer lots over older ones, the reported 95–96% warehouse utilization, continued deliveries into that specific warehouse, or whether any lots were destroyed. We need the warehouse-to-CFA mapping, batch/bin inventory history, WMS pick and FEFO override events, receipts, capacity records, and write-off records to test those claims.

**Calculation notes:** The batch master contains 663 rows with unique batch numbers and parseable expiry dates. Stock quantities were not summed for this assessment where normalized September CFA/SKU/batch keys conflict. Exact duplicate primary-sales rows were removed before checking invoices. The self-assessed Q1 FY27 CFA scorecard reports FEFO compliance as “Yes” for all CFAs, including CF-E01; this is a reported control result, not a substitute for the absent bin-level picking evidence.

**Sources:** [Hooghly warehouse recording](../data-pack/voice-notes/AUD-20261014-WA0007.ogg), [CFA stock snapshot](../data-pack/data/cnf_stock_snapshot.csv), [batch master](../data-pack/data/batch_master.csv), [SKU master](../data-pack/data/sku_master.csv), [primary sales extract](../data-pack/data/primary_sales.csv), and [stockist master](../data-pack/data/stockist_master.csv).

## Analysis — claims and planning cross-checks

### Vijayawada claim is matched in the records

The Telugu call’s identifiers and amount match a claims record and an inbox message. Claim **CLM-2607-02627** is for Matrix Medicos (STK0143), SKU PFL1401, batch K2440124, 689 packs, and ₹68,004.30. The claim date is July 29, 2026; the claim remains Pending with no credit-note date in the September 30 extract. It was 63 days past its recorded claim date at that cutoff, beyond the policy’s 30-day target if claim date is a reasonable proxy for receipt. The extract has no separate received timestamp. This substantiates the delayed-claim example in the recording. The caller’s reported hold on current invoice payments is not recorded in the supplied claims or sales data.

The caller also describes advice to resubmit claims and phone approvals for missing invoice copies. The pack supports that invoice references are blank on 879 of 4,503 exact-row-deduplicated claims (19.5%; 884 of 4,526 raw rows), but policy permits these only after ledger verification and written Area Manager approval. The extract does not hold that approval trail. A blank invoice reference alone is not evidence of an invalid claim.

### Duplicate-credit report has one confirmed example

The inbox report and claims extract match a duplicate credit for STK0025, PFL1401, batch F2440122, and 272 packs. Claim CLM-2603-01616 and later claim CLM-2605-04488 each show a credit of ₹26,846.40. This supports the reported control gap and one duplicate-credit event. It does not size the full exposure or prove how much was recovered.

### Planning audio raises a testable issue, not a validated forecast metric

The English planning transcript mentions a national SKU-month forecast, a late sales overlay, a repeated North buffer top-up, an allocation sheet still on an FY25 split, and an unclear metric transcribed as “MAPS” around 14. Interview notes independently describe a national forecast, allocation shares, and a SKU-level scheme overlay. The supplied pack does not include forecast versions, actual forecast accuracy results, the allocation workbook, or its change history, so the stale-allocation claim and the “14” figure cannot be verified.

The sales extract can support a historical **primary shipment** baseline. After exact-row deduplication, all 216 CFA/SKU series have 30 consecutive monthly observations. A rolling-origin, three-month backtest over 16 origins gives 21.6% WAPE for same-month-prior-year seasonal naïve, compared with 22.1% for the mean of prior observations from the same calendar month. This is a retrospective comparison on shipments, not evidence of downstream demand or the accuracy of the planning team’s existing forecast. The unclear “around 14” figure is not treated as a target.

### Other cross-checks and limits

- The finance QBR and primary-sales extract agree on FY27 Q1 primary sales after rounding (₹51.36 crore). The populated values for near-expiry and expired claims total ₹1.354 crore, versus ₹1.415 crore in the QBR, a ₹6.06 lakh difference. Eighteen of the 518 Q1 expiry-claim rows have no claim value; this may explain part of the difference but does not reconcile it.
- The case records show free goods at 3.69% of Q1 primary sales, above the policy’s 3% cap. The QBR says the CFO approved the exception. This confirms the scheme-control context, not that schemes caused the calls’ stock or expiry problems.
- The North-region order-like lines and Lucknow’s 23/36 zero-stock SKUs support a regional availability concern. The named Gorakhpur account has no FY27 September lines for the two cited products; city-level records cannot prove that caller’s orders were cancelled.
- The latest stock snapshot has 67 repeated normalized CFA/SKU/batch keys with conflicting quantities. Do not use its summed stock, stock cover, or expiry-value estimates to corroborate callers until the conflicts are resolved.
- The warehouse agreement requires batch/bin records and FEFO picking, while the CFA self-assessment reports FEFO compliance as “Yes.” Neither establishes how picks occurred in the caller’s specific aisle. The reported system change, 95–96% capacity, and threatened destruction remain unverified.

These are checks against the fictional case files and user-provided transcripts. They are not interviews with real process owners, and they do not independently validate the recordings’ translations.

## Cross-note themes to test

| Working hypothesis | Voice-note signals | Records needed to confirm or reject it |
|---|---|---|
| Some products may be unavailable where orders are being placed | Gorakhpur reports repeated cancellations and a hospital shortfall; Ludhiana reports Amox-Clav shortage; planning note mentions repeated top-ups | Dated order lines, cancellations/reasons, SKU-by-CNF stock history, fill-rate definitions, customer demand and substitution evidence |
| Scheme activity and supply may be poorly matched by product or location | Ludhiana reports Monte LC scheme stock alongside an Amox-Clav shortage | Scheme participation, stockist on-hand and secondary sales by SKU, primary shipments, orders and later returns |
| Older stock may be aging in the warehouse | Hooghly caller reports back-rack lots remaining while front stock is picked | Batch/bin inventory movements, pick events, FEFO rules/overrides, expiry and write-off records |
| Planning and allocation inputs may be stale or manually patched | Planning note reports FY25 split, unfinished FY26 review, late overlay and buffer top-ups | Forecast and allocation versions, approval/change history, top-up records, local demand and stock; metric owner confirmation |
| Claim delays or informal resubmission may create friction or control risk | Vijayawada caller reports a delayed credit note and conflicting resubmission/documentation advice | Claim-to-credit-note/payment linkage, full status history, duplicate detection, required approval and invoice evidence |

## Overall readout

Taken together, the recordings point to a possible mismatch between what the channel needs, what is available at each location, what is promoted, and how warehouse stock is picked. One delayed claim and one duplicate credit are matched to structured records; North availability concerns have partial record support. Other caller reports remain unverified. This is a hypothetical case review, not real process-owner validation or a confirmed root-cause analysis. The pack lacks the stockist, warehouse-event, scheme, and claims-workflow evidence needed to size several issues.

The recordings do **not** yet establish the rupee value of lost sales, avoidable expiry, scheme impact, or claim leakage. Quantify those only after the relevant records and metric definitions are agreed with process owners and Finance.

## Suggested next validation steps

1. Confirm transcripts, especially product names, dates, quantities, acronyms, and the disputed `WA0003` recording date.
2. For the exercise, record the missing order/cancellation, stockist secondary-sales, stockist-inventory, allocation-version, and warehouse-event data as dependencies; do not imply that real owners were contacted.
3. Use the matched claim and duplicate-credit records as reproducible examples, then leave aggregate claims leakage and actual customer payment effects unquantified until the needed records are supplied.
4. Update each evidence item to **confirmed in supplied records**, **partly supported**, **not supported by this pack**, or **unusable transcript**. Keep transcription uncertainty and source cutoff visible.

## Source files

- [Voice notes README](../data-pack/voice-notes/README.md)
- [Gorakhpur call recording](../data-pack/voice-notes/CALL_REC_9935xxxx_20260930.m4a)
- [Vijayawada claims call recording](../data-pack/voice-notes/CALL_REC_8662xxxx_20261007.m4a)
- [Ludhiana stockist recording](../data-pack/voice-notes/AUD-20261001-WA0004.ogg)
- [Planning discussion recording](../data-pack/voice-notes/AUD-20261013-WA0003.ogg)
- [Hooghly warehouse recording](../data-pack/voice-notes/AUD-20261014-WA0007.ogg)
- [Unclear recording](../data-pack/voice-notes/AUD-20261003-WA0011.ogg)
- [Business problem validation](business_problem_validation.md)
- [Stakeholder validation guide](stakeholder_validation_guide.md)
