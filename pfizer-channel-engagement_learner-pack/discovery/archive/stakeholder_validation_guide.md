# Stakeholder validation guide

**Purpose:** Test the discovery hypotheses with the people who run the process, request the evidence needed to quantify value, and agree whether a pilot is worth doing.  
**Suggested format:** 60-minute working session per function, followed by a 30-minute cross-functional decision meeting.  
**Preparation:** Share the discovery findings brief and relevant exhibits in advance. Ask participants to bring the source reports or system views behind their answers.

## Outcomes to leave with

By the end of discovery, the team should be able to answer:

1. How does Pfizer define and calculate expiry/near-expiry returns, short supply, fill rate, and scheme economics?
2. At what point does the stock imbalance arise: forecast, allocation, CFA picking/dispatch, stockist ordering, or secondary demand?
3. Which part of the problem is both material and controllable within a short pilot?
4. Who owns the decision, who runs the process, and who must approve any resulting action?
5. What baseline and comparison will be used to judge whether a pilot helped?

## Opening: confirm the problem before proposing a solution

Start with the participant’s own view, not the pilot idea:

- What is the most important channel problem you are trying to solve this quarter?
- How does it affect your team, customers, or financial results?
- What makes this a priority now?
- Which part of the diagnosis in the discovery brief fits your experience? Which part does not?
- What evidence would change your mind?

Then establish the current process:

- Walk us through one recent example from demand signal to allocation, dispatch, stockist receipt, and eventual sale or return.
- Where are decisions made manually? What information is available at each step?
- What exceptions are common, and who handles them?
- What changes at quarter end or during a scheme?

## Questions by stakeholder

Use the questions as prompts. Follow concrete examples with “How do you know?”, “Can we see the record?”, and “What happened next?”

### CFO / Finance

- How is the reported expiry and near-expiry rate calculated? Which claim types, credit dates, primary-sales measure, and cutoff are included?
- Can we reconcile FY27 Q1’s reported ₹1.41 crore and 2.75% to the claim and sales ledgers? What explains the difference from the extracts?
- What does the 1% ambition mean in financial terms: provision, credited claims, write-offs, or a specific combination?
- What share of claims is recoverable, avoidable, or disputed? What evidence supports that split?
- How are duplicate claims checked today? Can we match claims to credit notes, payments, recoveries, and reversals?
- What is the claims backlog by age, value, and reason? How much staff time does verification take?
- What level of evidence and control is required before Finance would rely on an exception recommendation?

**Request:** monthly KPI definitions and workings; claim register; CN/payment/recovery ledger with stable IDs; provision and write-off history; backlog aging; team capacity or time-study data; scheme and FOC approvals.

### Supply Chain / Demand Planning

- How is the national SKU forecast built, and how are scheme volumes incorporated?
- How are allocation shares set and reviewed? When was the last review, and what triggers an in-cycle change?
- What explains the September snapshot pattern between Kolkata and Lucknow? Which SKUs and dates are most important?
- How do CFA constraints, transit time, service levels, and demand differences affect allocations?
- How is short supply recorded when the balance of an order is cancelled? Can we distinguish demand, allocation, and physical availability?
- How are near-expiry batches identified before allocation and dispatch? Who can override FEFO or shelf-life rules?
- What evidence would show that a reallocation or forecast change would have prevented an expiry or stockout?

**Request:** forecast versions and accuracy by SKU/region/month; allocation rules and change logs; replenishment and order history; short-supply/cancellation data; batch allocation and dispatch history; FEFO picks and override logs; approved exceptions; lead times and capacity constraints.

### Sales / National Sales Manager / Regional Sales Managers

- What is the role of quarter-end schemes in meeting targets and serving customers?
- Which scheme mechanics changed, when, and for which products or stockists?
- How do teams assess stockist inventory before recommending a scheme or placing orders?
- Do stockists report unsold scheme stock, expiry concerns, or requests to exclude products? How is that captured?
- Where are stockouts affecting customers or new accounts? Can you point to specific order lines or lost sales?
- How are secondary sales or stockist inventory obtained today? If they are unavailable centrally, what evidence do field teams use?
- What would make a risk alert useful to an RSM, and what would cause them to ignore it?

**Request:** scheme circulars and approvals; scheme participation by stockist/SKU/date; stockist secondary sales and inventory if available; order and lost-sales examples; field stock reports; target/incentive definitions; relevant territory feedback.

### CFA / Distribution Operations

- Please walk through receipt, storage, batch selection, picking, dispatch, and returns for one recent order.
- How does the WMS enforce FEFO? How are overrides captured and reviewed?
- How is remaining shelf life checked before dispatch? Who approves exceptions?
- What explains stock accuracy, storage capacity, and claim-verification differences across CFAs?
- How quickly can stock be returned to CDC or reallocated under current approvals? What makes that difficult?
- Which data fields or system events are unreliable or entered manually?

**Request:** batch/bin inventory and movement logs; pick/pack/dispatch records; FEFO override audit; expiry blocks and exception approvals; claim verification timestamps; storage capacity and utilization; CDC return requests and disposition; WMS change notices and known data-quality issues.

### Claims processing owners

- What checks happen before a claim reaches Finance? Which are system-enforced and which depend on a person?
- How do you verify claims without an invoice reference under the policy?
- How are repeat stockist/batch claims identified when quantities are split or claimed over time?
- Where does elapsed time accumulate: receipt, CFA verification, Area Manager approval, or Finance CN processing?
- What would a useful pre-check need to show so that it saves time without creating false rejections?

**Request:** claim intake and status timestamps; verification evidence; approval records; invoice and batch billing history; repeat-claim/CN matching logic; reason codes; rejected and pending claim samples.

## Evidence checklist

Ask for de-identified or appropriately access-controlled extracts with stable keys and clear definitions. No patient or HCP information is needed for this work.

| Evidence | Minimum useful grain | Why it matters |
|---|---|---|
| Stockist sell-through and inventory | Stockist × SKU × week/month, with stock on hand | Tests whether primary shipments match downstream demand and whether stock is accumulating |
| Orders and fulfillment | Order line × SKU × date, including ordered, supplied, cancelled quantities and reason | Separates demand from allocation/availability and clarifies fill-rate calculation |
| Scheme participation | Stockist × SKU × scheme × dates, with free and paid quantities | Links offers to subsequent sales, stock, claims, and margin |
| Batch movement and shelf-life | Batch × location × movement/dispatch date, quantity, expiry, and exception | Locates where aging stock entered the flow and validates shelf-life flags |
| Claims and financial settlement | Claim ID linked to invoice, batch, CN, payment/recovery, status dates, and approvals | Measures true claim value, duplicate exposure, leakage, and cycle time |
| Forecast and allocation history | Forecast/allocation version × SKU × CFA × period, with overrides and rationale | Tests forecast and allocation hypotheses rather than inferring from one snapshot |

For each file, record owner, extraction date, period, grain, key fields, exclusions, and known limitations. Reconcile totals to a trusted monthly report before using it in a business case.

## Decision rights (RAPID to validate)

Do not assume titles map cleanly to decision rights. Use this table in the cross-functional meeting and have the client name the individuals or roles:

| Decision | Recommend | Agree / provide input | Decide | Perform | Must be informed |
|---|---|---|---|---|---|
| Return KPI definition and value baseline | Finance analytics | Supply Chain, Sales | CFO / Finance owner (confirm) | Finance analytics | SteerCo |
| Forecast/allocation rule change | Demand Planning | Sales, CFA operations, Finance | Supply Chain leader (confirm) | Demand Planning / CFA teams | CFO and NSM |
| Scheme design or exception above FOC cap | Sales | Finance, Supply Chain | Existing scheme approver / CFO per policy | Sales operations | Relevant regions and CFAs |
| Credit note, recovery, or write-off | Claims / Finance operations | CFA and Sales as required | Existing Finance authority | Finance / claims team | CFO and process owner |
| Pilot alert disposition | Pilot/process owner | Relevant data and business owners | Current process decision-maker | Assigned business user | SteerCo |

The pilot should support existing decision-makers. It should not change approval or transaction authority.

## Cross-functional close: choose the pilot slice

Use the final session to compare candidate slices against four questions:

1. Is the issue material enough to matter to the CFO or customer service?
2. Can the team access the required data with stable identifiers and acceptable quality?
3. Is there a named business owner who can review alerts and act within current authority?
4. Can the pilot establish a baseline and a fair comparison within the available time?

The current proposed scope has two separate read-only workflows. **First:** Commercial Finance claims triage for Controller Neha Bansal and the two-person team described in the case, with an authorized human retaining credit-note decisions. **Second:** Supply Chain availability and aging-risk review for Kavita Rao. Confirm both owners and the weekly cadence before treating them as agreed. Do not combine the metrics or imply the same decision-maker owns both.

For claims, agree the register intake, disposition states, authoritative policy text for §§5.2/5.4/5.5/5.6, evidence needed for a match, reviewer effort, and how to measure correctly routed cases and actual credit/recovery outcomes. For Supply Chain, agree the stock/batch data cut, alert usefulness, and availability measures. Neither workflow should claim savings until Finance validates a baseline and actual outcomes.

## Interview notes template

Copy this block for each conversation:

- **Date / participants / roles:**
- **Their stated priority:**
- **Current process and systems:**
- **Specific example discussed:**
- **Evidence shown or promised:**
- **What supports our hypothesis:**
- **What challenges or changes it:**
- **Metric definition / baseline:**
- **Decision owner and process owner:**
- **Open question / action / owner / due date:**
- **Implication for pilot scope:**

## Reference

This guide is based on the current discovery synthesis and the project’s stated policy and operating constraints. See [business problem validation](business_problem_validation.md), [trade terms and returns policy](../data-pack/02_trade_terms_and_returns_policy.pdf), [C&F agreement and SOP](../data-pack/03_cnf_agreement_and_sop.pdf), and [company and channel overview](../data-pack/01_company_and_channel_overview.pdf).
