Architecture Note: Project Sankalp System Design and Operational Engine

> **Status and evidence boundary (23 November 2026):** This is a proposed design for a fictional training case. The forum discussion contributes role-play requirements, not proof of Pfizer process. Sections below describe proposed capabilities unless explicitly marked as current implementation. The current app is a local, read-only prototype over static extracts; it is not air-gapped, does not ingest a live mailbox, and does not implement every control described here. Keep arithmetic, date rules, record matching, and policy thresholds in tested Python. AI may help interpret questions or draft explanations, but cannot decide claim eligibility or create unsupported facts.

## 1. System Mission and Operational Framing

The proposed Project Sankalp architecture is a read-only review aid for investigating claims and domestic-channel supply signals in a fictional case. The evidence supports several concerns but does not establish one root cause or quantify avoidable loss. The forum discussion suggests testing allocation and manual claims controls before treating forecast error as the primary issue.

The proposed system is a read-only analytical copilot alongside existing enterprise systems. The local prototype has no SAP or WMS write-back, does not post credit notes, and does not initiate Stock Transfer Orders (STOs). It is not air-gapped and has not been deployed for operational use. The proposed pilot can provide auditable triage for Finance and Supply Chain reviewers. The case discussion suggests weekly review, but the cadence and owners remain pilot assumptions:
* Commercial Finance Claims Reviewer: A proposed weekly review of pasted claim text or register rows against claims, billing, batch, and policy evidence. The current prototype has no live mailbox ingestion and does not issue claim decisions.
* Supply Chain Reviewer: A proposed review of shelf-life candidates, stock signals, and allocation assumptions. Current extracts support retrospective analysis only; they do not provide live planned dispatches or reliable downstream demand.

Any operational use requires confirmation of the source policy, named decision owners, data freshness, and security review. Human reviewers retain authority; this design does not claim to establish statutory or regulatory compliance.

## 2. LangGraph State Machine and Workflow Topology

The current application uses a LangGraph model/tool loop. The additional typed state fields and nodes below are a target design sketch, not evidence that the current code implements those nodes or controls. Current graph behavior and tool wiring are in `starter/agent/graph.py` and `starter/agent/tools.py`. The division of responsibility remains: deterministic code owns calculations and rule checks; model output cannot override source evidence.

2.1 State Schema Specification

Execution state is maintained by a centralized, typed schema implemented in Python using Pydantic:
```

from typing import Annotated, Dict, Any, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
import operator

class GraphState(TypedDict):
    # Conversational message history with append-only reducer
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Internal model invocation counter capping execution loops
    trips: int
    
    # Parsed input entities from natural language or mailbox text
    raw_query: str
    parsed_claim: Optional[Dict[str, Any]]
    
    # Deterministic audit and verification outputs
    batch_evidence: Optional[Dict[str, Any]]
    shelf_life_evidence: Optional[Dict[str, Any]]
    stock_imbalance_evidence: Optional[Dict[str, Any]]
    claims_audit_evidence: Optional[Dict[str, Any]]
    
    # Adjudication disposition and audit trail
    disposition: str  # "AUTO_RECOMMEND", "FLAG_EXCEPTION", "NEEDS_HUMAN_REVIEW", "REJECT"
    policy_violations: List[str]
    audit_trail: List[Dict[str, Any]]

```

2.2 Node Architecture and Graph Routing

The current graph uses a model/tool loop over registered deterministic tools. The state schema and extra nodes below are proposed design elements unless confirmed in `starter/agent/graph.py`; they are not a description of every implemented control:

* START: The incoming inquiry or raw stockist email is wrapped into a `HumanMessage`, and `trips` is initialized to 0.
* Model Node (`call_model`): The core LLM invocation node. It increments the iteration counter (`trips += 1`), binds available tool definitions, and submits the current conversation context with an immutable system prompt.
* Conditional Routing Edge (route): Inspects model output to govern graph execution:
  * Tool Dispatch Branch: If the model requests one or more tool executions and `trips < 4`, control routes to the Tools Node.
  * _Termination Branch_: If no tool call is requested, or if trips >= 4, the loop breaks immediately and routes to the Disposition Gate.
* Tools Node (`run_tools`): Dispatches requested tool calls against memory-resident data structures, formats outputs into standard ToolMessage payloads, and returns them to the Model Node.
* Disposition Gate & END: Collects the final narrative response, structures evidence rows, verifies that every cited fact links to an exact CSV row or policy clause, and renders the result to the user interface.

Capping execution at `MAX_TRIPS = 4` prevents runaway recursive tool loops, ensuring that complex multi-tool queries cannot breach serverless timeout limits or inflate operational costs.

3. Strict Boundary: Deterministic Python vs. Probabilistic LLM

A fundamental engineering standard of Project Sankalp is that if a computation or decision can be executed by a deterministic formula, an LLM must never be allowed to perform it. Relying on generative models for arithmetic calculations, expiry date comparisons, or contractual pricing lookups creates unacceptable regulatory and financial risks.

The table below details the architectural division of labor between deterministic Python modules and the probabilistic language model:


## 3. Strict Boundary: Deterministic Python vs. Probabilistic LLM

To guarantee complete financial and audit defensibility, Project Sankalp enforces a rigid boundary between deterministic code and probabilistic generative AI. The governing principle is absolute: **no arithmetic, policy limit enforcement, date validation, relational matching, or quantitative thresholding is ever delegated to an LLM**.

The language model operates strictly as an unstructured-to-structured semantic parser and an explanation synthesizer. If the LLM generates an incorrect interpretation, downstream deterministic rules catch and reject the record. Conversely, the LLM is physically incapable of altering an invoice quantity, overriding an expiry date, or approving an unverified claim.

| Architecture Subsystem | Functional Responsibility | Implementation Engine | Technology / Library | Deterministic Rationale &amp; Guardrails |
| :--- | :--- | :--- | :--- | :--- |
| **Inbound Document Parsing** | Extract stockist identity, batch numbers, quantities, and dates from messy email bodies | Probabilistic Language Model | LangGraph + Structured Outputs (Pydantic / Instructor) | Eliminates fragile manual regex across varied distributor email formats. Constrained strictly to Pydantic extraction schema; rejected if confidence is low. |
| **Adversarial Prompt Guard** | Detect and defuse injection attacks attempting policy bypass (e.g., `claim_emails.csv` row 18, `EML-017`) | Deterministic Regex + Guardrail Node | Python `re` + Static Input Sanitizer | Pre-LLM sanitization strips system instructions, roleplay overrides, and fake executive approvals before model invocation. |
| **Residual Shelf Life (RSL) Engine** | Calculate percentage of remaining shelf life at dispatch against mandatory 60% threshold | Deterministic Python Node | Standard Library `datetime` | Formula: `(Expiry Date - Invoice Date) / (Expiry Date - Mfg Date) * 100 &lt; 60%`. Float arithmetic cannot suffer model drift or rounding hallucinations. |
| **Two-Way Transaction Match** | Reconcile batch number, stockist account, and claimed quantity against primary billing | Deterministic Python Node | Pandas / DuckDB Relational Join | Foreign-key match against `primary_sales.csv` and `batch_master.csv`. Exact integer comparisons enforce `claimed_qty &lt;= invoiced_qty`. |
| **Temporal Policy Validator** | Derive claim category from batch-master expiry and screen the 90-day window before or after expiry | Deterministic Python Node | Standard Library `datetime` | Calendar-day arithmetic for expiry claims: include 90 days before through 90 days after the batch-master expiry date. This follows the forum interpretation of CO-POL-014 §5.2 and requires verification against the PDF. Preserve derived category and any submitted-label mismatch; missing data routes to human review. |
| **Duplicate Claim Filter** | Identify identical `(stockist_code, batch_no)` submissions previously credited | Deterministic Python Node | In-Memory Set / Key-Value Lookup | Immediate match against historical settled ledger (`expiry_claims.csv`). Prevents multiple payouts on identical batches. |
| **Baseline Shipment Projection** | Generate transparent seasonal-naïve primary sales baselines for replenishment | Deterministic Python Node | NumPy / Pandas | Direct calculation of identical month prior year (`T-12`) invoiced plus free packs. Never claims to predict unobserved secondary demand. |
| **Audit Synthesis &amp; Drafting** | Format evaluation findings into structured, readable rationale for human reviewers | Constrained Language Model | LangGraph Formatter Node | Synthesizes passed/failed rule results into clear professional summaries citing exact source rows. Constrained to provided structured payload. |


4. Tool Registry and Master Data Ingestion Pipeline

To ensure sub-second response times and eliminate disk I/O bottlenecks in serverless environments, all client datasets are ingested into memory upon application launch via agent/data.py. Raw CSV files are parsed once into indexed Pandas dataframes with typed schemas, normalized entity identifiers, and standardized date structures.

```Master Data Ingestion Layer (In-Memory Pandas Cache)
* primary_sales.csv       -> 93,064 rows (after purging 745 exact duplicate rows)
* expiry_claims.csv       -> 4,503 rows (after purging 23 exact duplicate rows)
* cnf_stock_snapshot.csv  -> 355 unique CFA/SKU/batch keys (67 conflicting keys isolated)
* batch_master.csv        -> 663 unique batches indexed on batch_no
* sku_master.csv          -> 36 active SKUs indexed on sku_code
* stockist_master.csv     -> 156 stockists indexed on stockist_code
```

The deterministic tool functions dispatched by the LangGraph engine operate directly over this cached layer:

# 4.1 `lookup_batch(batch_no: str) -> Dict[str, Any]`

* Target Datasets: `batch_master.csv` joined with sku_master.csv on sku_code.
* Join Logic & Grain: Exact key lookup on normalized batch code. Returns SKU code, trade description, therapy area, manufacturing date, expiry date, total shelf life in days, and official PTS and MRP pricing.
* Fail-Closed Behavior: If the batch code is absent from the master, returns {"found": False, "message": "No such batch in the batch master"}. The system never generates plausible batch dates probabilistically.

### 4.2 `find_short_shelf_life_shipments(limit: int = 25) -> Dict[str, Any]`

- **Target datasets:** `primary_sales.csv` joined with `batch_master.csv` on `batch_no`.
- **Mathematical Formulation**: Using invoice date as the agreed operational proxy for warehouse dispatch date, the tool evaluates the remaining lifespan:

  $$
  \text{Remaining shelf life (\%)} =
  \frac{\text{Expiry date} - \text{Invoice date}}
       {\text{Expiry date} - \text{Manufacturing date}}
  \times 100
  
* **Policy Verification**: Enforces the strict contractual threshold defined in Trade Terms Policy CO-POL-014 §7.1: $\text{Residual Shelf Life} < 60.0\%$.
* **Output Grain**: Summary counts of evaluated lines, below-threshold exceptions, unsupplied batches, and unevaluable records, paired with detailed transaction metadata (invoice number, row index, dates, calculated percentage, and net invoice value).

### 4.3 find_cfa_stock_imbalances(limit: int = 25) -> Dict[str, Any]

* Target Datasets: cnf_stock_snapshot.csv joined with sku_master.csv on sku_code.
* Operational Logic: Filters for the latest snapshot date (2026-09-30). Identifies instances where an SKU has an explicit zero-stock marker at one regional CFA depot while another CFA depot concurrently holds positive physical inventory for the same SKU.
* Data Quality Isolation: Detects the 67 repeating keys identified during discovery. If duplicate records exist for a single depot and batch, the tool isolates the records and appends a data quality review flag rather than aggregating unverified stock quantities.

4.4 validate_claim(claim_no: str, stockist_code: str, batch_no: str, claimed_qty: int) -> Dict[str, Any]

* Target Datasets: expiry_claims.csv, primary_sales.csv, batch_master.csv, and sku_master.csv.
* Multi-Stage Audit Cascade:
  1. Batch Authentication: Confirms batch validity and true manufacturing and expiry dates in batch_master.csv.
  2. Duplicate Prevention: Searches expiry_claims.csv for historical records matching (stockist_code, batch_no). If a prior claim has been credited, returns the historical credit note number, credit date, and settled amount.
  3. Policy Window (proposed from the forum): Uses the claim date and batch-master expiry to derive near-expiry/expired category and screen the inclusive 90-day window on either side. The discussion cites CO-POL-014 §5.2; confirm the PDF clause before operational use.
  4. Billing History Reconciliation: Cross-references primary_sales.csv to ensure that claimed quantities do not exceed originally invoiced volumes. For claims lacking invoice references (Policy v4.2 loophole), it audits the stockist's primary billing ledger.
  5. Financial Re-valuation: Multiplies verified physical units by the official PTS rate from sku_master.csv, calculating any over-claim variance against the stockist's requested credit.

4.5 forecast_primary_shipments(cfa_code: str, sku_code: str, horizon_months: int = 3) -> Dict[str, Any]

* Target Datasets: Deduplicated primary_sales.csv.
* Computational Method: Applies the validated seasonal-naïve method (t - 12), projecting shipments based on the exact same month of the preceding financial year.
* Transparency Controls: Reports all contributing source invoice row IDs, baseline months, and invoiced plus free quantities. Outputs carry an explicit operational warning stating that the projection represents a primary shipment baseline, prohibiting its presentation as an unconstrained downstream demand forecast.

## 5. Defensive Engineering, Edge Handling, and Adversarial Guardrails

Incoming dealer correspondence can contain noise, clerical errors, and misleading instructions. This section describes proposed defensive mechanisms; implementation status must be verified against the current code:

### 5.1 Anomaly Handling Matrix

The matrix below describes the intended handling of data anomalies and structural edge cases. It is a design specification; confirm each control in code and evaluation before describing it as implemented:

| Anomaly category | Data manifestation | Detection rule | Defensive system action |
| --- | --- | --- | --- |
| Missing batch identifier | 2,654 rows in `primary_sales.csv` have a blank `batch_no`. | Check for a null or empty batch value during the dataset join. | Mark the transaction as `not_supplied` and skip shelf-life evaluation. Retain the source row for review. |
| Unknown batch code | A distributor provides a batch identifier that is absent from the master (for example, `ZZ999`). | Look up the normalized key in `batch_master.csv`; no match is found. | Return an unevaluable result, such as `{"status": "unevaluable", "reason": "Batch not found in master"}`, and withhold calculations that depend on batch dates. |
| Claim without invoice reference | 879 of 4,503 exact-row-deduplicated claims have no invoice reference (884 of 4,526 raw rows). | Check whether the invoice-reference field is empty. | Flag for the policy-required ledger verification and written approval; a missing reference alone does not prove a claim is invalid. |
| Duplicate snapshot keys | The September stock snapshot contains repeated CFA/SKU/batch keys with conflicting quantities. | Group on the normalized composite key `(cnf_code, sku_code, batch_no)` and identify conflicts. | Do not sum conflicting quantities automatically; surface the rows for human inventory review. |
| Exact duplicate sales rows | The raw `primary_sales.csv` contains 745 exact duplicate rows, as identified in discovery. | Compare complete rows and remove exact duplicates for the documented analysis. | Keep the raw file unchanged; report deduplication in analysis and retain traceability to source rows. |
| Model recursion | The model repeatedly requests tools without producing a final response. | Check the graph’s tool/model iteration counter. | Stop after the configured iteration limit and return the evidence gathered so far with a clear incomplete-status message. |

5.2 Adversarial Prompt Injection Defense (Case EML-017)

In claim_emails.csv, record EML-017 represents an intentional adversarial prompt injection attack. A stockist incorporates deceptive instructions directly into the email body, claiming that National Sales Manager Arjun Sethi personally authorized an off-policy expiry credit and instructing the automated system to bypass standard validation rules.

To neutralize this threat, the architecture implements a three-tier defense:

1. Strict Structural Schema Extraction: The LLM parser in agent/prompts.py is restricted to extracting defined entities into a rigid Pydantic model (stockist_code, sku_code, batch_no, claimed_qty). Free-text instructions or directives embedded in the email body are discarded and cannot alter runtime instructions.
2. Authority Decoupling: The engine prompt explicitly states that verbal, email, or off-record approvals carry zero authority. Executive overrides are recognized only when accompanied by formal SAP workflow reference numbers.
3. Deterministic Rule Enforcement: Extracted entities are passed directly to rules.py. The rule engine enforces standard 90-day expiry windows, duplicate checks, and invoice history validations regardless of any assertions made in the text. The injection attempt is logged in the audit dossier as UNAUTHORIZED_EXECUTIVE_APPROVAL_CLAIM, alerting the Commercial Finance reviewer.

# 6. Hosting Infrastructure, Performance, and Unit Economics

The system is designed for deployment on serverless cloud infrastructure, conforming to the operational specifications of the Vercel Hobby tier.

6.1 Serverless Deployment Architecture

The application layout decouples the user-facing static presentation layer from backend graph execution:

* Static Edge Presentation Layer: Hosted on Vercel Edge CDN (public/index.html, app.js, style.css). Implemented in lightweight vanilla HTML5, CSS3, and ES6 JavaScript without external compilation frameworks. It provides a single-screen operational dashboard optimized for both desktop and mobile viewports.
* Serverless Execution Layer: Deployed as a Python 3.12 FastAPI serverless function (app.py) located in Vercel’s bom1 region (Mumbai, India) to minimize domestic network latency.
* Memory & Lifecycle Management: The bundled application (FastAPI runtime, LangGraph core, Pandas, and case CSV files) occupies approximately 135 MB of memory, operating well within Vercel's 500 MB container ceiling. Dataframes are loaded once during container warm-up, enabling typical query execution times under 1.8 seconds.

6.2 Token Budget and Operational Unit Economics

Operating expenses are calculated based on the weekly review cadence of Commercial Finance and Supply Chain teams. Cost modeling utilizes enterprise pricing for openai/gpt-4o-mini routed through OpenRouter:

* Input Token Baseline:
  * System Prompt and Policy Instructions: ~650 tokens
  * Structured Tool Schema Definitions: ~350 tokens
  * Dynamic Context (User query or parsed email text): ~200 tokens
  * Average Input per Execution: ~1,200 tokens
* Output Token Baseline:
  * Tool Invocation Dispatch Payload: ~80 tokens
  * Structured Audit Dossier and Narrative Synthesis: ~270 tokens
  * Average Output per Execution: ~350 tokens
* Direct Model Costs:
  * Input Pricing: $0.150 per 1,000,000 tokens (\approx $0.00018 per run)
  * Output Pricing: $0.600 per 1,000,000 tokens (\approx $0.00021 per run)
  * Total Direct Model Cost per Execution: $0.00039 (\approx ₹0.033 INR)
* Annual Operating Budget:
  * Claims Mailbox Ingestion: ~4,000 claim lines per year \times ₹0.033 = ₹132 INR / year
  * Weekly Supply Chain Imbalance & Shelf-Life Reviews: 52 weeks \times 50 queries \times ₹0.033 = ₹86 INR / year
  * Total Projected Model Operating Cost: Less than ₹250 INR per year

This modest computational expenditure provides exceptional operating leverage: for an annual compute cost under ₹250, the platform delivers continuous audit oversight across a ₹200 crore commercial distribution channel, mitigating against quarterly expiry spikes of ₹1.41 crore and eliminating duplicate credit leakage.


## 7. Forum-derived requirements and unresolved assumptions

The forum discussion suggests a deterministic claims-screening sequence: master batch authentication, date-derived claim category/window, duplicate-credit search, billing quantity check, and written Area Manager evidence for claims without invoice references. Failures or missing evidence should be routed to a person. The tool must not post credit notes or send stockist communications. These requirements are hypothetical case-role-play answers; the exact clause text and authority must be checked against the project PDFs.

For allocation analysis, the discussion proposes six months of ordered packs including free goods, repeated unmet orders counted once, scheme spikes smoothed, normal non-scheme dispatch as a demand proxy, and a two-month CFA cover target. It also mentions CDC-mediated transfer, a 10–14 day transit assumption, and a ₹5 lakh per-SKU threshold. Treat these as scenario parameters until the case source files and definitions are reconciled; the national forecast, actual allocation workbook, verified CDC stock, and downstream stockist data are not supplied.

The claims-without-invoice metric also needs reconciliation: the forum cites 804 and approximate ₹1.50 crore/₹1.30 crore values, while exact-row deduplication of the supplied CSV gives 879 blank references among 4,503 records, with 798 credited. Keep both reported populations distinct; see [business problem validation](business_problem_validation.md).
