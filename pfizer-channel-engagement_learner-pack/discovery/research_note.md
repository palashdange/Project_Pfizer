# Project Sankalp: industry and regulatory research

**Working note · 24 November 2026 · Fictional training case; the laws cited are real and were read at source**

This note explains *why* the problems in the [discovery note](Discovery_note.md) happen, using how the Indian pharma trade channel works and the laws the case pack cites by number. Each law was read on the official site; the version and date are in §4. Where a source could not be reached from this environment, §5 says so.

## 1. How the channel works

| Term | Meaning in this case | Source |
|---|---|---|
| C&F / CFA | Carrying and Forwarding agent: holds company stock for a territory, bills stockists for the company, receives and verifies returns. Six are in scope. | Doc 3 (C&F agreement); policy §5.1, §5.6 |
| Stockist | Licensed wholesaler buying from the company (primary sale) and selling to chemists (secondary sale, not visible to the company). Needs wholesale licences in Form 20B/21B. | Policy §8.2; Drugs Rules 1945 |
| MRP → PTR → PTS | MRP includes all taxes. PTR = MRP ex-GST less the chemist's 20%. PTS = PTR less the stockist's 10%. **PTS is the taxable value on the invoice** and values free goods, returns and credit notes. | Policy §2.1–2.3, Annexure A |
| Scheme / FOC | Quantity-linked free packs on a minimum order. Quarter-end schemes run in the last 7–10 days of a quarter; the free-goods cap is 3% of the quarter's sales (§4.4). | Policy §4.1–4.4 |
| NE / expired / BED / LBE | Near-expiry, expired, breakage-in-transit returns; LBE = claims raised by AIOCD members (the national chemists' association), settled on NE terms. | Policy §5.1–5.2 |
| CN | Credit note: the document that reverses value to the stockist. Under GST it must relate to the original tax invoice (§2 below). | Policy §5.7; CGST Act §34 |
| RSL | Residual shelf life at dispatch; must be at least 60% of total shelf life on the invoice date. SKUs here have 18, 24 or 36 months' life (5, 19 and 12 SKUs). | Policy §7.1; `sku_master.csv` |
| Scheduled formulation / NLEM | A medicine on the National List of Essential Medicines, so price-controlled under DPCO 2013 Schedule I. | Policy §2.1; DPCO 2013 |

## 2. What the laws say, and what that means for our findings

| Law (version read) | What it says | Why it matters here |
|---|---|---|
| **Drugs and Cosmetics Act 1940**, §18(a)(i) and §33(2)(h) | No one may sell, stock or distribute a drug that is not of standard quality. §33(2)(h) lets rules prohibit sale, stocking or distribution of a drug "after the expiry of the date of potency". | Expired stock cannot be sold, so every pack that a stockist cannot sell before expiry **must come back**. Over-supply turns directly into expiry claims, not into slow-moving stock. |
| **Drugs and Cosmetics Rules 1945**, Rule 65(5)(1)–(3), 65(6) | A wholesale supply must be made against a cash or credit memo showing the drug, **quantity and batch number**. A wholesaler's purchase records must show the supplier, drug, quantity and batch. Memos are kept 3 years and are open to an Inspector. | The stockist is legally required to hold **batch-wise purchase records**. The §5.4 fallback ("verify against the stockist's purchase ledger for that batch") is therefore always possible, and a claim with no invoice reference is a choice, not a data limit. It supports sending these to a person rather than crediting them. |
| **CGST Act 2017**, §34(1)–(2) | A supplier may issue a credit note "where the goods supplied are returned by the recipient", against the tax invoice for that supply. It must be declared by a time limit after the end of the financial year of the supply; after that, output tax cannot be reduced. | A credit note with **no invoice reference cannot be tied to the supply it reverses**: the brief's "tax document" risk, which is behind the ₹43.08 L/yr no-invoice exposure. It also creates a timing cost (below). |
| **DPCO 2013**, paras 14, 16, 20 (NPPA consolidated text plus the 30 Jun 2026 amendment) | Para 16: ceiling prices of scheduled formulations are revised by the annual WPI on 1 April; MRP may rise once a year, in April. Para 20: a non-scheduled MRP may not rise more than 10% in 12 months. | One reason stockists might buy before 31 March is an April price rise. **The data does not support that as the driver.** FY25 Q4's last-10-day share (34.63%) is no higher than FY25 Q3's (35.35%) or FY26 Q1's (34.69%), so it is the quarter-end schemes, at every quarter end, that load the channel ([discovery note §5](Discovery_note.md#5-why-it-may-be-happening-observed-signals)). |

**GST timing finding (from the extract, code in §6):** of 2,391 credited claims whose invoice reference matches a sales row (₹4.87 cr credited over 30 months), **1,120 credit notes (₹2.83 cr, 58%) were dated after 30 November following the end of the invoice's financial year**. That is **₹1.13 cr a year** of credited value on which the output GST may not be reversible under §34(2). By claim type: expired 537/816 (74% of value), near expiry 583/1,311 (50%), breakage and short supply 0. This follows from shelf life: an 18–36-month pack shipped with ≥60% RSL reaches its expiry window well after the §34 deadline. **The rupee GST cost is not sized**: GST rates per SKU are not in the pack, and how the company treats these notes (financial credit notes without GST) is an open question for Finance.

## 3. Why the problems happen

1. **Quarter-end schemes push stock past what stockists sell.** After the v4.1 change (15 Nov 2024), quarter-end packs went from about 20% to 35% of each quarter and free goods from 1.2% to 5.0% of sales, against a 3% cap. The policy's own stock norm (§4.5: no more than 2.5 months' average secondary stock) cannot be checked, because secondary sales are not received. Stock beyond sell-through ages in the stockist's warehouse.
2. **The law forces that stock back as claims.** Under D&C Act §18 and §33(2)(h), expired stock cannot be sold, so ageing stock returns 1–2 years later as NE or expiry claims. That is the lag seen between scheme loading (FY25 Q3) and rising expiry claims (FY26–FY27).
3. **Each late claim costs more than its PTS.** Most expiry credit notes are issued after the CGST §34(2) window, so the GST on them may not be recoverable (§2).
4. **Claim checks are weaker than the records allow.** Rule 65 requires batch-wise records at every licensed wholesaler, and CGST §34 ties every credit note to an invoice. Yet ₹43.08 L/yr is credited without an invoice reference, and duplicate and out-of-window claims are credited. A two-person team cannot check 4,000 lines against billing history (interviews p. 2); code can.
5. **None of these is a forecasting error.** The national forecast feeds a fixed allocation split (interviews p. 3). The research supports the discovery verdict: fix scheme loading, allocation and claim checks, not the forecast.

## 4. Sources read (accessed 24 Nov 2026)

| Document | Official source | Version read |
|---|---|---|
| Drugs and Cosmetics Act 1940 and Rules 1945 | India Code, `indiacode.gov.in`, handle 123456789/507619 (MoHFW consolidated PDF) | As amended up to 31 Dec 2016 |
| Central Goods and Services Tax Act 2017 | India Code, handle 123456789/550806 (Gazette of India, 12 Apr 2017) | As enacted |
| Drugs (Prices Control) Order 2013 | NPPA, `nppa.gov.in/en/drugspricescontrolorder2013`: consolidated text and amendment S.O. 3516(E) | As amended up to S.O. 2324(E), 25 May 2023, plus S.O. 3516(E), 30 Jun 2026 |
| CO-POL-014 v4.2, C&F agreement, interviews, QBR | Case data pack, docs 02, 03, 04, 06 | As supplied |

## 5. Not verified from here

- **CGST §34(2) time limit after 2022.** The as-enacted text says "September following the end of the financial year". The Finance Act 2022 changed this to 30 November; the amended text sits on CBIC's tax-information portal, which failed TLS checks from this environment. The figures in §2 use 30 November (the later date, so the smaller share); under the as-enacted text the share is 68%.
- **D&C Rules after 2016.** The India Code consolidation runs to 31 Dec 2016. Rule 65 should be checked for later amendments.
- **CDSCO Good Distribution Practices guidance** (returns and expired-stock handling, cited in doc 1 and doc 3). `cdsco.gov.in` refused connections from outside India.
- **NPPA's March 2026 WPI notification** (cited in doc 1) was not found on NPPA's 2026 pages.
- **AIOCD trade norms on expiry returns.** No official AIOCD source was located.

## 6. Reproduce

The GST timing numbers come from `starter/data/expiry_claims.csv` (status Credited, `credit_note_date`, `credit_value_inr`) joined on `original_invoice_ref` to `primary_sales.csv` (`invoice_date`). A credit note counts as late when its date is after 30 November following the 31 March that ends the invoice's financial year. Annualised over the 30 months of claims data.
