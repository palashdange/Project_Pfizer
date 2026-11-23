# Step 1: Business context and working hypothesis

**Status:** Working summary from the fictional case pack. Definitions and hypothesis should be revisited if the source material or sponsor interpretation changes.

## Channel in brief

Products move from the central distribution center (CDC) to carrying and forwarding agent (CFA) warehouses, then to stockists, and onward to retailers, pharmacies, and hospitals. Planning and allocation decisions move stock into the network. Returns and expiry claims move back through CFA checks to Finance for review and possible credit. The case pack provides primary shipment records and some CFA inventory, but not stockist sell-through or stock-on-hand. The map is in [channel_business_flow.md](channel_business_flow.md).

## Working vocabulary

| Term | Meaning in this case | Why it matters here |
|---|---|---|
| CDC | Central distribution center; the overview places it at Bhiwandi. | Origin point for product moving into the domestic channel. |
| CFA / C&F | Carrying and forwarding agent; a warehouse and distribution node serving stockists. The case materials use CFA and C&F terminology. | CFA inventory and replenishment are visible in some supplied records; stock at a CFA is not the same as stock available at every stockist. |
| Stockist | A wholesale channel customer supplied through a CFA and serving downstream trade customers. | The supplied pack does not include this level’s complete inventory or sell-through. |
| Primary sales / shipments | Pfizer’s invoiced product movement into the channel, represented by the supplied primary-sales extract. | This measures sell-in; it does not directly measure what pharmacies or patients consume. |
| Secondary sales / sell-through | Stockist sales onward to retailers, pharmacies, or other customers. | Needed, with stockist inventory, to measure downstream demand; absent from this data pack. |
| Allocation | The decision about how available supply is divided among CFAs or locations. | Poor alignment could contribute to stock imbalance, but the pack does not include allocation history to establish causation. |
| Trade scheme / FOC | A promotion offered to the channel; FOC means free-of-charge goods. | Scheme quantities can affect shipments and channel inventory. The policy cap and exceptions need to be read with the applicable approvals. |
| Expiry / near-expiry claim | A stockist claim concerning returned product that is expired or approaching expiry under the policy. | Claims can create credit-note costs; a flagged shipment or claim is not automatically an avoidable loss. |
| FEFO | First-expiry, first-out: pick the batch that expires first before later-expiring stock, subject to the SOP and any approved exception. | Warehouse picking practice can affect which batches age or reach customers. |
| Fill rate | A measure of how much ordered quantity was supplied. | The pack’s QBR and a straightforward calculation from the sales extract do not reconcile, so the official formula and population remain to be confirmed. |

## CFO hypothesis to test

**Working hypothesis:** Better forecasting and allocation, using reliable downstream demand signals, may help reduce expiry-related financial leakage while improving product availability; the case asks for an AI demand-forecasting capability and evidence of money recovered or protected, but the supplied records do not yet establish the root cause, a recoverable amount, or whether primary shipments are an acceptable forecast target.

Treat this as a hypothesis, not a confirmed diagnosis. In particular, stockist sell-through and inventory are missing; the reported 1% ambition also needs a precise Finance definition before it can be treated as a measurable target. See [business_problem_validation.md](business_problem_validation.md) and [implementation_plan.md](implementation_plan.md).

## Sources and interpretation notes

- [Company and channel overview](../data-pack/01_company_and_channel_overview.pdf) and [C&F agreement and SOP](../data-pack/03_cnf_agreement_and_sop.pdf) describe channel roles and warehouse practices.
- [Trade terms and returns policy](../data-pack/02_trade_terms_and_returns_policy.pdf) describes schemes, FOC limits, shelf-life requirements, and claim handling.
- [Business problem validation](business_problem_validation.md) documents the quantified evidence, mismatches, and data gaps.
- The table uses plain-language summaries for discovery. For any calculation or operational decision, use the exact policy definition and source record rather than this glossary.
