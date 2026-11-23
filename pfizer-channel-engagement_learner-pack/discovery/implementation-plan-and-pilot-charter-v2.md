# Implementation Plan and Pilot Charter: Project Sankalp Operational Rollout

## 1. Executive Framing and Pilot Charter Foundations

Project Sankalp addresses a structural operating divergence within the domestic trade channel of Pfizer Limited’s General Medicines division. Over successive operating cycles, commercial policies and supply chain controls have operated in silos, generating a simultaneous paradox of severe localized stockouts and mounting near-expiry inventory write-offs. While executive leadership initially diagnosed this friction as a failure of primary demand forecasting, diagnostic analysis of channel transactions reveals that the true vulnerabilities stem from quarter-end trade loading, rigid inter-depot replenishment mechanisms, warehouse dispatch non-compliance, and manual claims adjudication backlogs.

The primary objective of this pilot implementation is to deploy a dedicated, stateful decision-support engine—the Supply-Risk and Claims Verification Assistant—designed to operate strictly alongside existing enterprise systems. Rather than attempting to introduce ungrounded downstream forecasting models into a channel devoid of stockist-level secondary sales visibility, the pilot focuses on intercepting operational non-compliance, eliminating financial claim leakages, and highlighting regional distribution imbalances before inventory reaches clinical expiry.

To maintain organizational integrity and statutory compliance, the pilot adheres to a foundational operating principle:

> The pilot system operates as a non-invasive, read-only decision-support platform. It possesses zero direct write-back privileges into enterprise resource planning (SAP S/4HANA), warehouse management systems, or banking interfaces. It neither approves financial credits nor triggers physical inventory transfers automatically; every operational determination remains strictly vested in designated business owners.

The operational boundaries separating system capabilities from human authority are structured across three distinct operational layers:

| Operational Dimension | System Responsibilities (Read-Only Pilot) | Human Governance & Decision Authority |
| :--- | :--- | :--- |
| **Input Ingestion** | Ingests flat CSV snapshots of master registries, primary sales ledgers, regional stock balances, and incoming dealer correspondence. | Authorizes data cutoffs, validates extract freshness, and reconciles system inputs against audited schedules. |
| **Verification Logic** | Executes deterministic mathematical and policy checks: duplicate claim detection, 60% shelf-life screening, and 90-day expiry ceilings. | Evaluates flagged exceptions, investigates physical stock anomalies, and reviews disputed distributor documentation. |
| **Operational Action** | Outputs prioritized exception rosters, auditable evidence packages, and calculated financial variances. | Executes statutory credit note approvals in SAP FI, initiates stock rebalancing, and enforces warehouse picking compliance. |

---

## 2. Solution Positioning and Architectural Dimensions

A critical success factor for Project Sankalp is establishing exactly where the solution sits—both organizationally within the company's operating workflows and technically within the enterprise IT landscape. To prevent operational friction, avoid lengthy ERP customization cycles, and maintain absolute statutory compliance, the solution is designed with a two-fold architectural positioning.

### 2.1 In the Business Flow: Operational Decision Support (Alongside Existing Teams)

The system does not sit inside the physical distribution path, nor does it alter commercial hierarchy or delegation of authority. Physical goods continue to move through established channel nodes: from the Bhiwandi Central Distribution Center (CDC) to the 6 Carrying and Forwarding Agent (CFA) regional depots, onward to 156 authorized stockists, and down to retail chemists and hospitals.

Instead, the solution sits **alongside existing operational teams as an out-of-band audit copilot**, functioning as an intelligent pre-screening filter during routine review cadences:

```
[Bhiwandi CDC] ───> [6 Regional CFAs] ───> [156 Stockists] ───> [Retailers & Hospitals]
       │                    │                     │
       ▼                    ▼                     ▼
[Physical Inventory]  [WMS Picking]         [Claims & Orders]
       │                    │                     │
       └────────────────────┼─────────────────────┘
                            │ (Read-Only Periodic Data Extracts)
                            ▼
           ┌──────────────────────────────────┐
           │   Project Sankalp Assistant      │
           │  (LangGraph + Rule Engine)       │
           └──────────────────────────────────┘
                            │
              (Pre-Screened Audit Dossiers)
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    [Commercial Finance]           [Supply Chain & CFA]
    Tuesday Claims Audit           Thursday Rebalancing
    (Human Approves/Rejects)       (Human Reallocates)
```

* **Commercial Finance Workflow (Weekly Claims Audit)**:
  * *Operational Reality*: A two-person claims team currently spends 43 to 46 days manually cross-checking distributor expiry and damage claims across spreadsheets, creating severe backlogs, prompting stockist payment withholdings, and allowing duplicate credits to pass.
  * *Assistant Role*: The assistant pre-screens all incoming digital claims and correspondence. It verifies batch existence, calculates elapsed time against the 90-day post-expiry policy ceiling, executes relational joins against `primary_sales.csv` to detect quantity over-claims, and flags historical duplicate payouts on identical `(stockist, batch)` combinations. 
  * *Human Authority*: The assistant generates an auditable pass/fail verdict with row-level proof. The finance executive retains 100% discretion to sign off, reject, or request Area Manager validation.
* **Supply Chain Planning & CFA Operations Workflow (Weekly Rebalancing)**:
  * *Operational Reality*: CFA depots operate under rigid historical allocations, resulting in extreme regional asymmetry—Kolkata sits at 96% warehouse capacity with blocked aisles, dispatching batches below 60% residual shelf life (RSL), while Lucknow experiences severe stockouts on 23 of 36 vital SKUs.
  * *Assistant Role*: The assistant scans weekly billing extracts and stock snapshots. It surfaces batches dispatched below the mandatory 60% RSL threshold before orders leave depots and flags cross-CFA stock imbalances where one depot holds surplus inventory of an SKU that another depot lacks.
  * *Human Authority*: The central planner uses these alerts to evaluate freight economics and initiate formal Inter-Depot Transfers (IDTs) or adjust monthly production allocations through standard ERP processes.
* **Strict No-Writeback Boundary**: The assistant **never automatically creates a credit note in SAP FI, never moves inventory in SAP MM, and never blocks an invoice**. It functions strictly as an evidence-backed advisor.

### 2.2 In the Technical Architecture: Standalone Serverless Cloud Application

To ensure rapid deployment without entangling the project in lengthy enterprise IT change-management approvals, database migrations, or single sign-on (SSO) integrations, the solution is built as a **fully decoupled, standalone web application**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                            │
│  - Single-screen responsive web console (FastAPI + HTML5/CSS3/Vanilla JS)│
│  - Accessible via any web browser (mobile & desktop) with zero login   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTPS REST Calls
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Serverless Application Layer (Vercel)                 │
│                                                                        │
│  ┌───────────────────────┐             ┌─────────────────────────────┐ │
│  │   Input Sanitizer     │             │    LangGraph State Machine  │ │
│  │ (Regex Injection Guard│ ──────────> │   (Cyclic Model/Tool Loop)  │ │
│  │   defuses EML-017)    │             │   (Max Trips Guard = 4)     │ │
│  └───────────────────────┘             └──────────────┬──────────────┘ │
│                                                       │                │
│                         ┌─────────────────────────────┴─────────────┐  │
│                         ▼                                           ▼  │
│              ┌────────────────────┐                   ┌──────────────┐ │
│              │ Probabilistic LLM  │                   │ Deterministic│ │
│              │ (Pydantic Parsing &│                   │ Python Rules │ │
│              │ Summary Generation)│                   │ (rules.py)   │ │
│              └────────────────────┘                   └──────┬───────┘ │
└──────────────────────────────────────────────────────────────┼─────────┘
                                                               │
                                  ┌────────────────────────────┘
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   In-Memory Data Layer (DuckDB / Pandas)               │
│  - Read-Only CSV Extracts loaded at application initialization          │
│  - `sku_master.csv`, `batch_master.csv`, `stockist_master.csv`         │
│  - `primary_sales.csv`, `cnf_stock_snapshot.csv`, `expiry_claims.csv`  │
│  - Zero ERP write-back permissions; zero external database dependencies│
└────────────────────────────────────────────────────────────────────────┘
```

* **Hosting & Runtime Topology**:
  * Deployed on **Vercel Hobby Tier** using a serverless FastAPI backend paired with a static HTML/JS frontend.
  * Operates with **zero local installations, no external database dependencies, and no login barriers**, ensuring any reviewer or panel member can interact with live test cases on a smartphone or laptop instantly.
* **Air-Gapped Data Layer (Read-Only CSV Ingestion)**:
  * Operates entirely on read-only snapshots of Pfizer's core data extracts (`sku_master.csv`, `batch_master.csv`, `stockist_master.csv`, `primary_sales.csv`, `cnf_stock_snapshot.csv`, `expiry_claims.csv`, and `claim_emails.csv`).
  * Ingests files into memory upon serverless startup using Pandas and DuckDB. This guarantees that the system cannot corrupt, alter, or write to master enterprise records.
* **Rigid Code vs. Model Partitioning**:
  * *Deterministic Python (`rules.py`)*: Executes 100% of arithmetic, date calculations (90-day expiry windows, 60% shelf-life durations), duplicate relational lookups, and pricing multiplications. Zero mathematical operations are delegated to generative AI.
  * *Language Model (`prompts.py`)*: Restricted strictly to converting messy distributor correspondence into structured Pydantic schemas and formatting deterministic rule outputs into clear, professional audit rationale.
* **Defensive Engineering & Injection Guardrails**:
  * Incorporates an input sanitization node that neutralizes adversarial prompt injection attempts (such as record `EML-017` in `claim_emails.csv` claiming verbal executive approval from the National Sales Manager) before text reaches the language model.
  * Encapsulates the LangGraph tool-calling loop with a hard ceiling (`trips < 4`), preventing infinite execution loops or cost runaway.

---

## 3. Governance, Ownership Matrix, and Decision Authority

A successful operational rollout requires precise demarcations of responsibility, establishing unambiguous lines between system-generated exception alerts and human adjudication authority. Because the pilot spans commercial finance, central supply planning, regional warehousing, and field sales, decision rights must be transparently codified across all participating functions.

The operational governance structure is anchored by an executive steering group that meets bi-weekly, supported by working-level business process owners who execute routine daily and weekly evaluations.

The table below delineates the distribution of authority, operational accountabilities, and review cadences across all internal stakeholder groups:

| Organizational Function | Responsible Business Owner | Primary Operational Decision Supported | Authority Retained by Human Owner | Escalation Trigger & Cadence |
| :--- | :--- | :--- | :--- | :--- |
| **Commercial Finance** | Commercial Finance Claims Lead | Verification of stockist expiry and breakages claims submitted via portal or email | Statutory approval and issuance of SAP FI credit notes; approving policy exception overrides | Disputed claims exceeding ₹50,000; duplicate claim attempts; weekly review every Tuesday |
| **Supply Chain Planning** | Central Demand and Replenishment Planner | Bi-weekly allocation adjustments and inter-depot inventory balancing across regional CFAs | Reallocating monthly production quotas; issuing formal Inter-Depot Transfer (IDT) orders | CFA stock cover variance exceeding 45 days; persistent hospital stockouts; review every Thursday |
| **CFA Operations** | Regional CFA Warehouse Supervisors (Bhiwandi, Kolkata, Lucknow, Gurugram, Chennai, Hyderabad) | Enforcement of First-Expiry, First-Out (FEFO) picking and pre-dispatch residual shelf life checks | Overriding warehouse management system picking bins; authorizing emergency short-dated dispatches | Pick lines failing the 60% residual shelf-life threshold; warehouse capacity exceeding 85% |
| **Sales & Channel Management** | National Sales Manager (NSM) and Regional Area Managers | Monitoring field availability, stockist fill rates, and secondary stock absorption | Negotiating commercial terms; authorizing non-standard promotional scheme allocations | Stockist order cancellations on life-saving anti-infectives; quarter-end allocation freezes |
| **Forward Deployed Engineering (FDE)** | Lead Systems Architect and Technical Delivery Team | Maintaining LangGraph pipeline integrity, rule determinism, and data pipeline freshness | System performance tuning, rule calibration, and guardrail enforcement; zero operational authority | System exception rate exceeding 5%; adversarial prompt injection detection; real-time monitoring |

Under no circumstances does the pilot bypass established commercial delegation of authority limits. Any recommendation to withhold a credit note, reject an out-of-policy batch return, or reallocate regional safety stock must be corroborated by physical documentation and signed off by the accountable corporate officer.

---

## 4. Phased Implementation Roadmap: Gates 0 Through 5

To prevent premature feature development and ensure complete evidentiary integrity, the rollout follows a rigorous six-stage gating mechanism. Progression across gates is strictly contingent upon meeting defined quantitative acceptance criteria, preventing the deployment of unverified capabilities into production environments.

The sequencing balances immediate risk containment with long-term institutional embedding over a structured four-week operational deployment schedule:

1. **Week 1 (Foundations & Alignment)**: Execution of Priority Gate 0 (Executive Scope Resolution) and Priority Gate 1 (Baseline Data Reconciliation).
2. **Week 2 (Core Build & Tool Lock)**: Execution of Priority Gate 2 (Core LangGraph Agent Freeze) and deterministic tool calibration.
3. **Week 3 (Verification & Shadow Operations)**: Execution of Priority Gate 3 (Automated Test Harness Execution) and Priority Gate 4 (Live Operational Shadow Running).
4. **Week 4 (Auditing & Organizational Hand-off)**: Execution of Priority Gate 5 (Steering Committee Review and Operational Transition).

### Priority Gate 0: Executive Scope Resolution and Boundary Alignment
Prior to technical development, formal alignment must be established with executive leadership—specifically Chief Financial Officer Rohan Mehta and Head of Supply Chain Kavita Rao—regarding the analytical boundaries of the system.
* **Core Determination**: Clarify whether the project mandate focuses on an operational-risk audit engine grounded in primary billing data, or if leadership mandates downstream patient-level demand forecasting.
* **Evidentiary Constraint**: Because the General Medicines division discontinued its Distributor Management System (DMS) pilot and does not capture stockist sell-through or pharmacy stock-on-hand, training an unconstrained artificial intelligence demand-sensing model on primary sales alone would institutionalize the very quarter-end stuffing distortions causing the crisis.
* **Exit Gate Requirement**: Executive sign-off confirming that the pilot deliverable is an auditable operational-risk and claims verification copilot, coupled with a seasonal-naïve primary shipment baseline, rather than an ungrounded secondary demand forecasting model.

### Priority Gate 1: Baseline Data Reconciliation and Anomaly Isolation
The technical delivery team must systematically ingest, sanitize, and reconcile all client data extracts to establish a mathematically defensible operational baseline.
* **Data Hygiene Mandates**: Execute exact-row deduplication across the primary sales extract (removing 745 duplicate rows to reconcile exactly with the ₹51.357 crore QBR baseline) and the expiry claims register (removing 23 duplicate entries).
* **Key Conflict Resolution**: Isolate the 67 repeating composite keys across 70 rows in the regional CFA stock snapshot (`cnf_stock_snapshot.csv`). Establish a defensive policy that excludes unresolved multi-record CFA/SKU/batch combinations from automatic aggregation, routing them instead to a data-quality review queue.
* **Exit Gate Requirement**: Formal reconciliation sign-off from Commercial Finance confirming that primary sales totals, promotional free-goods percentages (3.69%), and historical claim counts tie directly to audited financial schedules.

### Priority Gate 2: Core LangGraph Agent and Deterministic Tool Freeze
Freeze the core technical architecture, enforcing the rigid separation between probabilistic language modeling and deterministic Python business rules.
* **Deterministic Code Lock**: Implement exact mathematical evaluation modules for Residual Shelf Life (`(Expiry - Invoice) / (Expiry - Mfg) < 60%`), temporal submission eligibility (`Claim Date - Expiry Date <= 90 days`), relational invoice joins, duplicate key set lookups, and the seasonal-naïve ($t - 12$) shipment projection.
* **Probabilistic Node Constraints**: Confine language model execution strictly to semantic extraction of incoming dealer correspondence (`claim_emails.csv`) using strict Pydantic schemas, supplemented by deterministic pre-sanitization regex to neutralize adversarial prompt injections (such as record `EML-017`).
* **Exit Gate Requirement**: Code freeze of `rules.py`, `tools.py`, and `graph.py` with zero hardcoded business logic embedded inside prompt templates.

### Priority Gate 3: Automated Test Harness and Evaluation Set Execution
Subject the compiled state graph to an automated evaluation harness incorporating the full ground-truth test suite.
* **Check Set Verification**: Execute the 15 hand-verified test cases documented in the operational evaluation register across batch authentication, boundary shelf-life calculations, cross-CFA stock signals, unknown batch rejection (`ZZ999`), and baseline projections.
* **Defensive Edge Testing**: Validate that the system correctly fails closed—emitting `"unevaluable"` or `"requires_human_review"` statuses—when encountering missing invoice numbers (Policy v4.2 loophole), unlisted batch codes, or blank batch fields (2,654 primary sales rows).
* **Exit Gate Requirement**: 100% pass rate on all deterministic business rule assertions and automated `pytest` suites before proceeding to end-user interface integration.

### Priority Gate 4: User Interface Deployment and Operational Shadow Running
Deploy the complete application package to a secure, serverless cloud environment (Vercel Hobby tier) and initiate a two-week operational shadow-running period.
* **Deployment Topology**: Host the FastAPI backend and vanilla HTML/JavaScript frontend, ensuring complete mobile responsiveness and zero-friction access without enterprise single sign-on bottlenecks.
* **Shadow Operations**: Run the tool parallel to existing manual workflows. Commercial Finance inputs live weekly claim batches into the tool while continuing their standard spreadsheet checks, comparing system recommendations against manual determinations.
* **Exit Gate Requirement**: Successful execution of live shadow reviews across two consecutive weekly cycles, achieving an alert precision rate exceeding 90% and demonstrating zero system-induced processing delays.

### Priority Gate 5: Steering Review, Performance Auditing, and Transition Hand-off
Present the synthesized operational outcomes to the executive steering committee and formalize ongoing system ownership.
* **Deliverables Presentation**: Deliver the 20-minute executive presentation and live software demonstration to CFO Rohan Mehta, Kavita Rao, and Arjun Sethi, detailing confirmed leakage interceptions, operational time savings, and policy compliance rates.
* **Transition Roadmap**: Deliver the final repository, technical runbooks (`README.md`, `AGENTS.md`), and automated test harnesses to the internal IT and supply chain analytics teams for permanent operational maintenance.
* **Exit Gate Requirement**: Formal acceptance of the pilot evaluation report and executive approval to transition the tool from pilot status into permanent operational policy.

---

## 5. Operational Cadence: The Dual Weekly Review Workflow

To ensure seamless integration into existing corporate routines without overwhelming operating personnel, the pilot establishes two dedicated weekly operational workflows: the Tuesday Commercial Finance Claims Audit and the Thursday Supply Chain Rebalancing Review.

### 5.1 The Tuesday Commercial Finance Claims Audit
Conducted every Tuesday at 10:00 AM, this workflow supports the two-person commercial finance claims team in systematically clearing the 4,000-claim annual backlog and preventing unauthorized payouts.
1. **Data Ingestion and Parsing**: The claims clerk uploads the weekly batch of digital claim submissions or unstructured dealer correspondence (`claim_emails.csv`). The Pydantic parsing node extracts distributor codes, batch numbers, claimed quantities, and returned stock values.
2. **Automated Deterministic Verification**: The system executes a sequential audit cascade:
   * *Duplicate Screening*: Matches `(stockist_code, batch_no)` against historical credits in `expiry_claims.csv`. Any repeat claim is instantly flagged with the original credit note number, payment date, and amount.
   * *Policy Window Validation*: Calculates the elapsed duration between batch expiry and claim receipt. The pilot screens the 90-day window before or after batch expiry using the forum interpretation of CO-POL-014 §5.2; verify the PDF wording. Exceptions are presented for human review, not automatically rejected.
   * *Purchase Reconciliation*: Cross-references the stockist’s primary purchasing history in `primary_sales.csv`. If the claimed quantity exceeds the total invoiced quantity for that batch, an over-claim exception is generated.
   * *Valuation Check*: Multiplies verified physical units by the official Price to Stockist (PTS) rate in `sku_master.csv`, recalculating claimed totals to eliminate unauthorized dealer markups.
3. **Exception Triage and Adjudication**: The screen presents an audited claims roster. Verified claims meeting all policy criteria are routed for batch credit note generation. Non-compliant claims display exact row citations and policy failure codes, enabling the clerk to issue formal rejection letters immediately.
4. **Adjudication Closeout**: The claims lead reviews flagged exceptions, applies manual overrides where authorized written Area Manager approvals exist (under Policy Amendment v4.2), and exports the sanitized credit approval file for batch upload into SAP FI.

### 5.2 The Thursday Supply Chain and CFA Rebalancing Review
Conducted every Thursday at 2:00 PM, this workflow brings together the Central Demand Planner and Regional Warehouse Supervisors to maintain physical inventory health and prevent avoidable near-expiry write-offs.
1. **CFA Snapshot Refresh**: The central replenishment planner ingests the latest synchronized stock extract across all six regional distribution nodes (`cnf_stock_snapshot.csv`).
2. **Deterministic Risk Screening**: The engine applies two independent operational filters:
   * *Residual Shelf Life (RSL) Gatekeeper*: Scans pending warehouse dispatch orders and recent billing lines against `batch_master.csv`. Any shipment where remaining shelf life falls below 60% of total manufactured duration is flagged as a candidate dispatch breach under SOP §5.3.
   * *Cross-CFA Imbalance Detection*: Evaluates stock cover at SKU level across all depots. The engine identifies instances where a critical SKU sits at an explicit zero-stock marker at one CFA (e.g., Lucknow CF-N02) while another regional depot concurrently holds surplus physical inventory of that identical SKU (e.g., Kolkata CF-E01).
3. **Operational Review and Investigation**: The planning team reviews the exception dashboard. For shelf-life alerts, the relevant CFA supervisor verifies picking bin logs to determine whether older stock was picked out of FEFO rotation due to warehouse congestion (such as the blocked aisles documented at Hooghly C&F). For regional stock imbalances, the central planner evaluates whether freight economics and residual shelf life warrant initiating an emergency Inter-Depot Transfer (IDT).
4. **Action Logging and Execution**: Reviewers log dispositions directly within their operational tracking sheets. While the pilot does not trigger ERP stock movements directly, confirmed imbalances form the empirical basis for the central planner’s weekly stock allocation adjustments.

---

## 6. Success Metrics, Evaluation KPIs, and Value Attribution Rules

To ensure objective evaluation, the pilot establishes rigorous performance metrics paired with strict financial accounting rules. A common failure in operational pilots is conflating total flagged inventory value with realized cost savings; Project Sankalp enforces clear boundaries between theoretical exposure and verifiable financial recovery.

The table below outlines the core evaluation metrics, baseline operating levels, pilot targets, and measurement protocols:

| Performance Metric | Operational Definition | Current Baseline Level | 4-Week Pilot Target | Measurement Protocol & Source Ledger |
| :--- | :--- | :--- | :--- | :--- |
| **Claim-to-Credit Turnaround (TAT)** | Elapsed calendar days from stockist claim receipt to formal credit note issuance | 43 to 46 calendar days (74.1% breach rate) | Less than 7 calendar days | Timestamps recorded in `expiry_claims.csv` and weekly portal logs; Policy SLA: 30 days |
| **Duplicate Credit Note Leakage** | Number and gross INR value of duplicate credits issued on identical batch/stockist records | Multiple confirmed occurrences; ₹26,846.40 in single matched case | Absolute zero (100% duplicate interception) | Relational check on `(stockist_code, batch_no)` in the settled claims register |
| **Alert Precision Rate** | Percentage of system-generated exception alerts confirmed as actionable by human reviewers | Not applicable (manual ad-hoc process) | Greater than 85% actionable precision | Human review disposition logs recorded during Tuesday and Thursday sessions |
| **Unreferenced Claim Interception** | Percentage of claims lacking original invoice numbers audited against primary ledgers | 19.5% of deduplicated claims (879 rows) lack invoice references; approval evidence is absent from this extract | 100% audited; zero unverified settlements | Null checks on `original_invoice_ref` validated against primary billing ledgers |
| **Short-Dated Dispatch Compliance** | Volume and value of outward dispatches violating the 60% residual shelf-life threshold | 217 invoice lines in Q1 FY27 valued at ₹1.115 Cr | 50% reduction in unapproved short-dated dispatches | Pre-dispatch audit matching `primary_sales.csv` against `batch_master.csv` |
| **Regional Stockout Mitigation** | Reduction in zero-stock SKU instances at high-demand regional depots (e.g., Lucknow) | 23 of 36 SKUs at zero physical stock | Minimum 30% reduction in persistent stockouts | Cross-depot snapshot tracking in `cnf_stock_snapshot.csv` |

### Strict Value Attribution and Financial Recovery Accounting
To maintain absolute credibility with Chief Financial Officer Rohan Mehta and the audit committee, financial savings must be categorized across three distinct accounting tiers:

1. **Tier 1: Confirmed Avoided Payouts (Direct Hard-Rupee Recovery)**:
   * *Scope*: Represents duplicate claim attempts intercepted before credit note generation, calculated over-claims where claimed units exceeded primary purchase history, and math errors where dealer claim amounts exceeded official PTS rates.
   * *Accounting Treatment*: Counted as direct, 100% verified cash leakage prevention. Every reported rupee must cite the specific stockist code, batch number, historical credit note reference, and intercepted claim row.
2. **Tier 2: Avoided Expiry Exposure (Working Capital Protection)**:
   * *Scope*: Represents inventory at regional CFAs flagged for short residual shelf life or regional over-stocking that is successfully reallocated or prioritized for commercial liquidation before reaching the 90-day near-expiry window.
   * *Accounting Treatment*: Reported as protected working capital rather than realized cash savings. Valued at manufacturing cost (or PTS minus gross distribution margin), explicitly excluding speculative lost-sales projections.
3. **Tier 3: Process Efficiency Gains (Operational Capacity Creation)**:
   * *Scope*: Measures the reduction in manual spreadsheet reconciliation hours achieved by the two-person commercial finance claims desk (reducing claim processing duration from 45 minutes per claim to under 3 minutes).
   * *Accounting Treatment*: Reported strictly as human capacity reclaimed and compliance SLA adherence; never converted into speculative headcount cost reductions.

---

## 7. Risk Management, Edge Handling, and Rollback Protocols

Deploying an analytical copilot into a high-volume pharmaceutical supply chain entails operational, technical, and behavioural risks. To prevent system failures from disrupting live trade flows, the pilot incorporates comprehensive risk mitigation controls and formal fallback protocols.

The table below outlines critical operational failure modes and their corresponding technical and organizational countermeasures:

| Failure Mode & Vulnerability | Root Cause & Operational Manifestation | Technical Detection & Safeguard | Rollback & Fallback Protocol |
| :--- | :--- | :--- | :--- |
| **Data Ingestion Stale-State** | Automated daily ETL pipeline fails or client ERP exports are delayed beyond agreed cutoffs | Automated timestamp header validation; flags any extract older than 7 calendar days | System displays prominent amber warning banner; halts automated scoring and falls back to manual review |
| **Adversarial Prompt Manipulation** | Distributor embeds deceptive instructions in email text claiming executive approvals (e.g., `EML-017`) | Deterministic regex pre-sanitizer strips system commands; LLM prompt isolates untrusted dealer text | Immediate isolation of correspondence; marks claim as `SECURITY_REVIEW_REQUIRED`; alerts system admin |
| **Composite Key Collisions** | Regional stock snapshot contains conflicting duplicate entries (67 repeating keys across 70 rows) | Composite key validator on `(cnf_code, sku_code, batch_no)` detects non-unique records | Automatically suppresses stock quantity summation; emits `DATA_QUALITY_CONFLICT` and routes to inventory auditor |
| **Missing Primary Transaction Data** | Unrecorded invoice references (884 claims) or missing batch codes (2,654 primary sales lines) | Explicit null-handler marks record as `not_supplied`; prevents false-positive violation flags | System prompts clerk for secondary documentation; enforces physical Area Manager sign-off |
| **Language Model Service Degradation** | Upstream API timeout, latency spike, or token exhaustion during peak weekly audit cycles | Graph state loop capped at `trips < 4`; asynchronous retry wrapper with 5-second timeout | Graceful degradation to standalone deterministic Python rule engine; bypasses LLM text parsing |
| **User Operational Disengagement** | Field sales or warehouse personnel bypass system alerts due to alert fatigue or skepticism | Alert precision threshold monitoring; continuous calibration of operational trigger levels | Weekly steering review triages false positives; temporarily suppresses noisy alert categories |

### Formal Rollback Protocols and Operational Containment
Because the pilot platform is architecturally decoupled from enterprise execution systems, system containment requires zero complex rollback scripts or database rollbacks:
* **Instant Operational Decoupling**: If the system generates erroneous recommendations or encounters critical software bugs, operating personnel immediately revert to standard spreadsheet reconciliation workflows. Because the pilot maintains zero write privileges into SAP, disabling the web application has zero adverse impact on live invoicing, warehouse picking, or banking settlements.
* **Audit Trail Preservation**: All system states, user inputs, parsed structures, and rule execution logs are continuously persisted in lightweight local log stores. If a business decision is contested by a stockist or audit partner, the complete decision lineage—including exact source row references, policy timestamps, and user disposition notes—can be exported as an immutable audit dossier.

Through this disciplined implementation plan and charter, Project Sankalp establishes a robust, auditable, and non-disruptive operational bridge that directly resolves channel friction, protects commercial margins, and restores balance to Pfizer’s domestic distribution network.
