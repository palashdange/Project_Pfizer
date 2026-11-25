# Pfizer domestic channel: what we found and what we built

**Discovery note · 25 November 2026 · Fictional training case.** Data: invoice, claims and stock extracts, Apr 2024–Sep 2026. Figures are checks on past data, not proven savings, and they overlap, so do not add them up.

## The answer in brief

- **A new forecasting tool would not fix this.** The national forecast is fine. The money is lost after it, in three places.
- **Three problems:** quarter-end schemes push more stock than stockists can sell; stock is split across the C&Fs (regional warehouses) on last year's shares; and invalid claims are credited without proper checks.
- **What we built:** one read-only tool. It checks every claim before credit (**₹19.94 lakh a year stopped**, **₹86.26 lakh a year sent to a person**), checks each quarter's schemes against the policy, and shows where C&F stock is short or ageing. A named person makes every decision.

## 1. The three problems, ranked by money

Ranked by the money involved each year. Rank 1 is money already spent; ranks 2 and 3 are mostly money at risk.

### Rank 1. Quarter-end schemes push more stock than stockists can sell

**What happens.** In the last 7–10 days of each quarter, stockists get FOC (free-of-charge) packs for ordering at least 1.5× their normal month. Policy v4.1 extended this to more products on 15 Nov 2024 (policy p.1). Extra stock ages on the shelf and returns as expiry claims 1–2 years later; expired stock cannot legally be sold.

**Evidence.** The share of a quarter's packs shipped in its last 10 days rose from about 20% to 35%, and free goods from 1.2% to 5.0% of sales against a 3% cap (policy §4.4; table A). Free goods above the cap cost **₹1.58 crore a year**. The CFO approved every exception (QBR p.2); on 25 Aug 2026 he wrote "Approved, last time. I want to see the expiry impact before December" (inbox p.4). Expiry claims run **₹1.46 crore a year** above his 1% target, and ₹1.99 crore in Apr–Sep 2026 alone, about **₹4 crore a year** at that rate (interviews p.1). A Ludhiana stockist's voice note describes overbuying one product on a 10+2 offer while short of another ([voice-note log](voice_note_evidence_log.md)).

- **Owners:** Arjun Sethi, National Sales Manager (approves schemes); Rohan Mehta, CFO (approves cap exceptions).
- **Built:** scheme check per quarter. **₹50.2 lakh–₹2.63 crore a year** of free goods went to orders below the 1.5× minimum; the range depends on how the policy is read (question 5). Example: invoice INV/S01/2406/007225 (primary_sales.csv row 7850).
- **Ask:** keep to the 3% cap and the 1.5× rule; check the 2.5-month stock limit (§4.5) properly, not by phone call.

### Rank 2. Stock is split on last year's shares: short in one place, ageing in another

**What happens.** Each month the national forecast is split across the six C&Fs by fixed shares. The FY26 review was missed and the shares rolled forward (Kavita Rao, interviews p.1). Demand moved; the shares did not. A planning voice note also mentions the missed review ([voice-note log](voice_note_evidence_log.md)).

**Evidence.** Lucknow's (CF-N02) share of orders rose from 15.3% to 20.9% and its fill rate fell to 80.6%; Kolkata's (CF-E01) fell from 17.9% to 13.3% (table B). On 30 Sep 2026 Lucknow was out of stock on **23 of 36 products**, while **₹2.06 crore** of stock at PTS (price to stockist) will reach stockists with under 60% of its shelf life left, which they may refuse (policy §7.1); **₹1.22 crore** of it is at Kolkata (cnf_stock_snapshot.csv, e.g. row 4783). After Kolkata's warehouse system changed in Feb 2026, 83% of its dispatches shipped a newer batch while an older one was on hand, against 28–35% elsewhere: a sign its first-expiry-first-out picking is broken. Unfilled orders reach **₹15.33 crore a year** at PTS, an upper limit, not lost sales.

- **Owners:** Kavita Rao, Head of Supply Chain; Vaishali Kapoor, Demand Planning (shares).
- **Built:** stock view per month-end.
- **Ask:** reset the C&F shares; check Kolkata's picking rules.

### Rank 3. Claims are credited without proper checks

**What happens.** C&Fs log and verify expiry, breakage and short-supply claims; Commercial Finance then raises the CN (credit note). Two people settle about 4,000 claims a year and "do not have time to check each claim against the billing history" (Neha Bansal, interviews p.2). Only 31 claims were rejected in 30 months.

**Evidence, per year** (sizing_results.csv): **₹15.74 lakh** credited outside the filing window (§5.2); **₹4.45 lakh** repeat credits (§5.6), e.g. CLM-2603-01616 and CLM-2605-04488 (expiry_claims.csv rows 3269, 3596); ₹6,642 over-quantity (§5.5); **₹43.08 lakh** with no invoice reference (§5.4); ₹36.1 lakh with no recorded C&F check.

- **Owner:** Neha Bansal, Controller, Commercial Finance.
- **Built:** claim check before credit: **₹19.94 lakh a year stopped**; **₹86.26 lakh a year sent to a person** (at risk, not saved).
- **Ask:** run the check before every CN; C&Fs record their verification.

## 2. The CFO's forecasting request: our view

**A forecasting tool would recover none of the money we can size.** The forecast is national and "the allocation sheet splits it" (Vaishali Kapoor, interviews p.3). The quarter-end spike "is not demand" (Kavita Rao, p.1); she wants "not another forecast" (p.2). The losses come after the forecast: schemes, shares and claim checks. The [research note](research_note.md) explains why, with the laws behind each problem.

## 3. Who uses the tool, and the plan for the money

- **Weekly:** Neha Bansal's claims team. Credit, reject or send each claim to a person (rank 3).
- **Quarterly:** Commercial Finance with Arjun Sethi and Rohan Mehta. Scheme check (rank 1).
- **Monthly:** Kavita Rao. Stock view (rank 2).

We built the claim check first: its rules are exact, the money is provable, and its owner asked for it. Ranks 1 and 2 are larger, but recovering them needs Sales and Planning to change practice; the tool makes them visible and owned. Every figure and its source: [money summary](money_summary.md).

## 4. Open questions for the client

1. What exactly is the CFO's 1% target measured on? FY27 Q1 claims: QBR ₹1.41 crore / 2.75% (p.2) vs extract ₹1.354 crore / 2.64%.
2. Can Finance link claims to invoices, CNs, payments and reversals, to prove what was avoidable?
3. Can Planning share the allocation versions, approvals and the demand behind the C&F shares?
4. Can we get unbilled orders, order status, stockist sales and stock on hand?
5. Annexure B's "average monthly purchase over the previous three months": all purchases, or only non-scheme ones? It moves the ineligible free goods from ₹50.2 lakh to ₹2.63 crore a year.

## Appendix: the two tables

**A. Quarter-end loading** (primary_sales.csv via [sizing.py](sizing.py)). The QBR's free-goods figures for FY26 Q1 to FY27 Q1 match exactly.

| Quarter | FY25 Q1 | Q2 | **Q3** | Q4 | FY26 Q1 | Q2 | Q3 | Q4 | FY27 Q1 | Q2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Packs shipped in last 10 days | 20.4% | 21.2% | **35.4%** | 34.6% | 34.7% | 31.9% | 30.6% | 29.1% | 30.6% | 27.8% |
| FOC as % of sales (cap 3%) | 1.18% | 1.25% | **4.95%** | 4.69% | 4.68% | 3.75% | 3.47% | 3.19% | 3.69% | 2.82% |

**B. C&F share of orders and fill rate.** Fill rate counts free packs and matches the QBR to rounding (QBR p.1).

| C&F | FY25 share / fill | FY26 share / fill | FY27 H1 share / fill |
|---|---:|---:|---:|
| CF-E01 Kolkata | 17.9% / 100% | 16.7% / 94.9% | 13.3% / 94.7% |
| CF-N01 Gurugram | 16.9% / 100% | 17.2% / 91.8% | 18.2% / 86.6% |
| **CF-N02 Lucknow** | 15.3% / 100% | 16.8% / 92.7% | **20.9% / 80.6%** |
| CF-S01 Chennai | 18.6% / 100% | 18.3% / 95.9% | 17.7% / 87.6% |
| CF-S02 Hyderabad | 15.7% / 100% | 15.5% / 94.5% | 15.0% / 88.7% |
| CF-W01 Bhiwandi | 15.7% / 100% | 15.5% / 93.4% | 15.0% / 92.0% |

**Reproduce:** `python discovery/sizing.py` writes [sizing_results.csv](sizing_results.csv); tests: `pytest discovery/test_sizing.py`.
