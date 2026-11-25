# Project Sankalp: the money, on one page

**Working note · 25 November 2026 · Fictional training case.** Every figure below is reproduced by code: `python discovery/sizing.py` (writes [sizing_results.csv](sizing_results.csv)) or the pilot's own functions in `starter/agent/` (batch, scheme and stock reviews). Data: Apr 2024–Sep 2026 extracts; "per year" = observed total ÷ 30 months × 12.

**How to read the labels.** **Stopped:** the pilot rejects it under a policy rule before credit. **At risk:** money credited without the checks passing; the pilot sends it to a person; **not counted as saved**. **May be refused:** stock that will ship below the 60% shelf-life norm; not a write-off. **Context:** sizes a problem; not recoverable money.

## Problem 3: claims credited without proper checks (built: claim review + batch mode)

| Figure | ₹ per year | Label | Method | Source |
|---|---:|---|---|---|
| Invalid credits the rules stop | **19.94 L** | **Stopped** | Credited claims the pilot rejects; whole credit for window (§5.2) or repeat (§5.6), excess packs only for over-quantity (§5.5) | `agent/batch.py` `leakage` |
| Same, sized in discovery | 20.25 L | Stopped (check) | Window 15.74 L + repeat 4.45 L + over-quantity 0.07 L | sizing_results.csv |
| Whole value of the credited claims the rules reject | 42.00 L | Context | Over-quantity counted at full claim value, so larger than the invalid part | `batch.py` `caught` |
| Credited without the checks passing | **86.26 L** | **At risk** | To a person: no invoice, batch not in master, near repeats | `batch.py` `at_risk` |
| … of which no invoice reference | 43.08 L | At risk | §5.4 allows ledger check with written approval, not proof of invalidity | sizing_results.csv |
| Pending claims the rules would block | 6.58 L | Stopped (future) | Not yet credited | `batch.py` `would_block` |
| Credited with no recorded C&F verification | 36.14 L | Context (overlaps) | Blank remarks although SOP 2.6 requires the result | sizing `calculate_register_controls` |
| Credit notes after the CGST §34(2) window | 1.13 cr | Context | Credited value; the GST effect is not sized (rates per SKU not in the pack) | sizing `calculate_gst_credit_note_timing` |

## Problem 1: quarter-end scheme loading (built: scheme check)

| Figure | ₹ per year | Label | Method | Source |
|---|---:|---|---|---|
| Free goods above the 3% cap | **1.58 cr** | Context; needs CFO approval each quarter | Σ max(0, FOC at PTS − 3% of quarter sales) over 10 quarters | `agent/schemes.py`; matches sizing |
| Free goods on orders below the 1.5× minimum | **50.2 L – 2.63 cr** | Context; range | Annexure B; lower = non-scheme purchases only, upper = policy wording (all purchases). Client to confirm. | `schemes.py` |
| All free goods | 6.99 cr | Context | Free packs × PTS | `schemes.py` |
| Expiry claims above the CFO's 1% target | 1.46 cr (avg); FY27 H1 1.99 cr → ~3.97 cr run-rate | Context | FY excess over 1% of primary sales | sizing_results.csv |

## Problem 2: stale allocation and ageing stock (built: stock view; point in time, not per year)

| Figure at 30 Sep 2026 | ₹ | Label | Method | Source |
|---|---:|---|---|---|
| Stock that will ship below the 60% shelf-life norm | **2.06 cr** (Kolkata 1.22 cr) | **May be refused** | FEFO at each C&F's current outward rate; §7.1 | `agent/stock.py` |
| Stock that will hit the 60-day block (write-off) | 0 now; 11.84 L at 31 Dec 2025 | At risk when non-zero | §7.1–7.2 | `stock.py` |
| Lucknow (CF-N02) out of stock | 23 of 36 SKUs | Context | Snapshot marker: blank batch, zero packs | `stock.py` |
| Order gap after free goods | 15.33 cr / yr | Context: upper bound, **not lost sales** | Ordered − invoiced − free, at PTS; no order status in the data | sizing_results.csv |

## Rules for the deck

1. **Headline "stopped": ₹19.94 L a year** (matches discovery's ₹20.25 L). **Headline "at risk": ₹86.26 L a year**, always labelled "to a person, not saved".
2. **Never add across rows.** Claims, the expiry gap, schemes and the GST figure overlap: the same expired stock can appear in several.
3. **Problems 1 and 2 are sized, not saved.** The pilot makes them visible and owned; recovering them needs Sales (cap and 1.5× rule) and Planning (C&F shares).
4. **A forecast recovers 0% of the quantified rupees** (discovery §2). **Running cost:** ~$0.00016 a claim, **~$0.65 a year** (architecture §6).
