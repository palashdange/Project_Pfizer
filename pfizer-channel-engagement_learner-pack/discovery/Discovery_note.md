# Pfizer domestic channel: discovery and pilot recommendation

**Working note · 25 November 2026 · Fictional training case**

## 1. The three problems

The CFO sees expiry returns rising and fill rates falling, and asks for an AI forecast. The data points to three problems, none of them a forecast error. Extracts cover Apr 2024–Sep 2026; figures are screens, not proven savings, and sell-through, stock on hand and causal links are not in the pack.

| Problem | Evidence | Owner | Our response |
|---|---|---|---|
| **1. Quarter-end scheme loading** pushes stock past what stockists sell; it expires and returns as claims 1–2 years later | Last-10-day pack share 20%→35% and FOC 1.2%→5.0% after v4.1 (15 Nov 2024); FOC above the 3% cap ₹1.58 cr/yr; expiry claims ₹1.46 cr/yr above the CFO's 1% target, now ~₹4 cr/yr (§2, §5) | Arjun Sethi (NSM, approves schemes); Rohan Mehta (CFO, cap exceptions); Commercial Finance checks cost (§4.3) | **Built:** scheme check per quarter (cap, 1.5× minimum order, terms). Free goods on orders below the minimum: ₹50.2 L–₹2.63 cr/yr. **Recommend:** enforce the cap and §4.5 stock norm |
| **2. Stale C&F allocation** splits stock on last year's shares | CF-N02 Lucknow order share 15.3%→20.9%, fill 80.6%; CF-E01 Kolkata 17.9%→13.3% (§5) | Kavita Rao, Vaishali Kapoor | **Built:** stock view per snapshot. At 30 Sep 2026 Lucknow is out of stock on 23 of 36 SKUs; ₹2.06 cr will ship below the 60% shelf-life norm, ₹1.22 cr at Kolkata, which skipped older stock on 83% of dispatches after its Feb 2026 WMS change (vs 28–35% elsewhere). **Recommend:** allocation review; check Kolkata's WMS picking rules |
| **3. Weak claim checks** let invalid claims be credited | ₹20.25 L/yr outside window, repeat or over-quantity; ₹43.08 L/yr credited with no invoice reference; ₹36.1 L/yr credited with no recorded C&F verification (overlaps); 31 rejections in 30 months vs 532 the rules reject (§2; [research note §4](research_note.md)) | Neha Bansal | **Built:** the claims-check pilot |

## 2. Ranked recovery indicators (₹)

Rank 1 is the largest modeled expiry-target gap; it is not proven recoverable and overlaps claim-control screens.

| Rank | Indicator / value | Method and evidence | Owners |
|---:|---|---|---|
| 1 | **Expiry-claim gap:** 30-month run-rate **₹1.46 cr/year**; FY27 H1 observed **₹1.99 cr**, current run-rate **₹1.99 cr × 2 = ₹3.97 cr/year** | FY-specific excess over 1% of primary net value; sum positive gaps ÷ 30 months × 12. H1 = Apr–Sep 2026; claims are grouped by claim FY, not matched cohorts. [Sizing](sizing_results.csv); CFO target ([interviews, p. 1](../data-pack/04_stakeholder_interview_notes.pdf)). | Rohan Mehta, Arjun Sethi, Kavita Rao |
| 2 | **No-invoice-reference credited claims: ₹43.08 lakh/year at risk** | Residual credited value after higher-priority screens; blank reference is not proof of invalidity. CO-POL-014 §5.4 allows ledger verification and written Area Manager approval. [Sizing](sizing_results.csv). | Neha Bansal |
| 3 | **Outside-window credited claims: ₹15.74 lakh/year** | Type-specific CO-POL-014 §5.2 windows. [Sizing](sizing_results.csv). | Neha Bansal |
| 4 | **Potential duplicate credits: ₹4.45 lakh/year** | Later credit matching stockist + batch + quantity; candidates need payment/ledger review. Includes hand-checked CLM-2603-01616 / CLM-2605-04488. §5.6. [Sizing](sizing_results.csv). | Neha Bansal, Rohan Mehta |
| 5 | **Over-quantity screen: ₹6,642/year** | Excess claimed packs above invoiced + free packs, valued at PTS; higher-priority categories excluded. §5.5. [Sizing](sizing_results.csv). | Neha Bansal |

**Other scale indicators:** The after-free-packs order gap is **₹15.33 cr/year** (availability upper bound, not lost sales). FOC above the quarterly cap screens at **₹1.58 cr/year**; QBR says the CFO approved each exception ([QBR, p. 2](../data-pack/06_qbr_finance_and_mis_pack.pdf)). The <60% RSL claim cross-check (₹96.37 lakh/year) overlaps the claims screens.

## 3. Forecast verdict

**A new forecast tool has no demonstrated direct recovery here; the intervention areas are scheme loading, CFA allocation, and claim controls.** Vaishali says the forecast is national and the allocation sheet splits it, so the ₹15.33 cr gap is not itself forecast error ([interviews, p. 3](../data-pack/04_stakeholder_interview_notes.pdf)). **0% of quantified recoverable rupees is demonstrated as forecast-addressable**; the expiry gap is a monitor, not a forecast benefit estimate. Why the problems happen, read against the D&C Act, Drugs Rules, CGST §34 and DPCO 2013: [research note](research_note.md).

## 4. Pilot user and plan for the money

**Primary user:** Commercial Finance claims executive; owner Neha Bansal (Controller). Weekly, review each claim and recommend credit, reject, or person review; Finance keeps decision authority. Her two-person team handles about 4,000 lines/year and cannot check every claim against billing history ([interviews, p. 2](../data-pack/04_stakeholder_interview_notes.pdf)).

**Secondary user:** Kavita Rao (Head of Supply Chain), reviewing expiry-risk batches and short CFAs ([interviews, p. 2](../data-pack/04_stakeholder_interview_notes.pdf)); served by the pilot's stock view.

**Plan for the money:** the pilot flags **₹20.25 L/yr** of invalid credits before the credit note (batch mode re-runs every register claim: ₹19.94 L/yr) and sends **₹86.26 L/yr** of credits that fail a check to a person, including ₹43.08 L/yr without an invoice reference for ledger and approval review; at risk, not saved. These are screens, not proven savings. For problem 1 the scheme check shows Commercial Finance, Arjun Sethi (NSM) and Rohan Mehta (CFO), each quarter, the free goods above the cap (₹1.58 cr/yr) and on orders below the 1.5× minimum; stopping them needs Sales to change practice. For problem 2 the stock view shows Kavita, per snapshot, where stock is short and where it will age; fixing shares is a Demand Planning change.

## 5. Why it may be happening: observed signals

Quarter-end share is invoiced + free packs in the final 10 days ÷ quarter packs; FOC is free quantity × PTS ÷ primary net value. Source: exact-deduplicated [primary sales](../data-pack/data/primary_sales.csv), calculated in [sizing.py](sizing.py). v4.1 extended quarter-end schemes to Tier B SKUs on 15 Nov 2024; FY25 Q3 includes pre- and post-change days (policy revision history, p. 1).

| FY quarter | Last-10-day pack share | FOC / primary net value |
|---|---:|---:|
| FY25 Q1 | 20.38% | 1.18% |
| FY25 Q2 | 21.17% | 1.25% |
| FY25 Q3 | **35.35%** | **4.95%** |
| FY25 Q4 | 34.63% | 4.69% |
| FY26 Q1 | 34.69% | 4.68% |
| FY26 Q2 | 31.89% | 3.75% |
| FY26 Q3 | 30.60% | 3.47% |
| FY26 Q4 | 29.14% | 3.19% |
| FY27 Q1 | 30.64% | 3.69% |
| FY27 Q2* | 27.84% | 2.82% |

**For Rohan’s “show me if schemes hurt us”:** FY25 Q2→Q3 late-quarter packs rose 21.17%→35.35% and FOC 1.25%→4.95%; FOC stayed above 3% in later full quarters, while the QBR says exceptions were CFO-approved—evidence of scheme-loading risk, not causation (QBR, pp. 1–2). Approving the Q2 FY27 exception on 25 Aug 2026, Rohan wrote: "Approved, last time. I want to see the expiry impact before December" ([inbox, p. 4](../data-pack/05_inbox_export.pdf)). Ludhiana voice notes also report Monte-LC excess after a 10+2 offer alongside Amox-Clav shortages, qualitative only ([voice-note log](voice_note_evidence_log.md#aud-20261001-wa0004--scheme-stock-and-shortage-in-ludhiana)).

CFA share is share of FY ordered packs. First group split-batch rows by invoice/date/CFA/stockist/SKU. [sizing.py](sizing.py) reports uncapped fill: `sum(invoiced + free) / sum(ordered)`; the comparison caps each grouped order at 100%: `sum(min(invoiced + free, ordered)) / sum(ordered)`. FY25 is **100.00% under both methods**: all 33,916 recorded groups match ordered quantity. The billed extract omits orders with no invoice.

| CFA | FY25 share; capped / uncapped fill | FY26 share / fill | FY27 H1 share / fill |
|---|---:|---:|---:|
| CF-E01 | 17.85%; 100.00% / 100.00% | 16.71% / 94.90% | 13.25% / 94.66% |
| CF-N01 | 16.86%; 100.00% / 100.00% | 17.23% / 91.75% | 18.24% / 86.56% |
| CF-N02 | 15.33%; 100.00% / 100.00% | 16.80% / 92.73% | **20.85% / 80.60%** |
| CF-S01 | 18.59%; 100.00% / 100.00% | 18.31% / 95.89% | 17.67% / 87.63% |
| CF-S02 | 15.72%; 100.00% / 100.00% | 15.46% / 94.49% | 15.00% / 88.69% |
| CF-W01 | 15.65%; 100.00% / 100.00% | 15.50% / 93.39% | 14.99% / 91.96% |

Uncapped fill including free packs matches QBR FY26 Q1–Q4 and FY27 Q1 to rounding: 99.52%, 94.58%, 91.52%, 90.25%, 90.85% vs 99.5%, 94.6%, 91.5%, 90.3%, 90.9%. Capping yields 100% and fails to reconcile; QBR does not state its formula (p. 1). Kavita says FY26 shares may have rolled forward after a missed review; Vaishali confirms forecast/allocation are separate ([interviews, pp. 1, 3](../data-pack/04_stakeholder_interview_notes.pdf)). A planning voice note also flags the FY26 review gap ([voice-note log](voice_note_evidence_log.md#aud-20261013-wa0003--planning-allocation-and-forecast-discussion)); these support review, not causation.

## 6. Open questions

1. What is the CFO’s 1% numerator/denominator, and how should FY27 Q1 claims reconcile: QBR ₹1.41 cr / 2.75% (p. 2) vs extract ₹1.354 cr / 2.64%?
2. Can Finance link claims to invoices, credit notes, payments, recoveries, and reversals to establish avoidable leakage?
3. Can Planning provide allocation versions/approvals and the demand evidence used for CFA shares?
4. Can the case provide non-invoiced orders, order status, sell-through, stock on hand, and final human-review ownership?
5. Annexure B's "average monthly purchase over the previous three months": all purchases, or only non-scheme purchases? It moves free goods on ineligible orders from ₹50.2 L to ₹2.63 cr a year.

**Reproduce:** from the learner-pack root run `python discovery/sizing.py` and `pytest discovery/test_sizing.py`; script writes [sizing_results.csv](sizing_results.csv) and prints driver tables. `*` = FY27 H1 through 30 Sep 2026.
