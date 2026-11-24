# Decision log

**Project Sankalp · fictional training case · 24 November 2026**

Each entry records the selected direction, the main alternative, the rationale, and evidence. Monetary screens below are candidates or exposure indicators, not verified savings.

1. **Decision:** Do not build a new demand-forecasting model. **Options considered:** new model vs. improve scheme, allocation, and claim controls.
   **Why we chose this:** No direct recovery from a new forecast is demonstrated; the case separates the national forecast from CFA allocation.
   **Evidence:** Stakeholder interviews, doc 04 p. 3; [`Discovery_note.md` §3](Discovery_note.md#3-forecast-verdict).

2. **Decision:** First user is the Commercial Finance claims executive; owner Neha Bansal (Controller). **Options considered:** Finance-first vs. Supply Chain-first.
   **Why we chose this:** She has a clear weekly claim-review decision and the rules provide testable screens; screened amounts still need ledger validation.
   **Evidence:** Doc 04 p. 2; CO-POL-014 §§5.2, 5.4, 5.5, 5.6; [`sizing_results.csv` rows 27, 38, 49, 60](sizing_results.csv).

3. **Decision:** Kavita Rao’s Supply Chain team is the second user. **Options considered:** make it the first pilot vs. secondary workflow.
   **Why we chose this:** The ₹15.33 cr order gap is an upper-bound signal; available sales rows lack order status and stockist sell-through/on-hand data.
   **Evidence:** [`Discovery_note.md` §§2, 4, 6](Discovery_note.md); `starter/data/primary_sales.csv` and `cnf_stock_snapshot.csv` schemas.

4. **Decision:** Keep business calculations and evidence joins in deterministic Python. **Options considered:** model-generated numbers vs. code-computed results with model-assisted language handling.
   **Why we chose this:** Financial and policy figures must be reproducible; the model should not calculate or invent them.
   **Evidence:** Project brief pp. 2, 4 (as cited in the case brief); [`starter/agent/rules.py`](../starter/agent/rules.py), [`starter/agent/tools.py`](../starter/agent/tools.py), `starter/tests/test_rules.py`.

5. **Decision:** Route incomplete or ambiguous claims to a person. **Options considered:** infer a disposition vs. return a review status.
   **Why we chose this:** Missing evidence cannot support a safe decision; §5.4 calls for written Area Manager approval, which the extract does not establish.
   **Evidence:** Project brief p. 5 accuracy-bar rule 2; CO-POL-014 §5.4; `claim_audit_report()` in [`starter/agent/tools.py`](../starter/agent/tools.py) and `starter/tests/test_tools.py`.

6. **Decision:** Keep the pilot read-only: no credit posting, SAP/WMS write-back, or stock transfer. **Options considered:** execute actions vs. present evidence for human action.
   **Why we chose this:** A named person retains decisions that move money or stock; system writes are outside pilot scope.
   **Evidence:** Project brief pp. 4–5 (as cited in the case brief); [`starter/app.py`](../starter/app.py), [`starter/agent/tools.py`](../starter/agent/tools.py).

7. **Decision:** Do not add a vector store, embeddings, or retrieval pipeline. **Options considered:** retrieval architecture vs. direct rules and supplied records.
   **Why we chose this:** The pilot uses short policy references and structured CSV extracts; retrieval adds no demonstrated need.
   **Evidence:** Project brief p. 5 out-of-scope list; [`starter/requirements.txt`](../starter/requirements.txt), [`starter/agent/tools.py`](../starter/agent/tools.py).

8. **Decision:** Do not train or add a machine-learning model of our own. **Options considered:** predictive model vs. deterministic checks and historical baselines.
   **Why we chose this:** The identified gaps are control, matching, and allocation issues; the current baseline is a simple prior-year comparison, not a learned forecast.
   **Evidence:** Project brief p. 5 out-of-scope list; [`Discovery_note.md` §§2–3](Discovery_note.md); `starter/agent/tools.py`.

9. **Decision:** Use the supplied CSV extracts in memory; do not add a database for this pilot. **Options considered:** database vs. local file-backed extracts.
   **Why we chose this:** The case is a small, static pilot dataset and the guided build path specifies pandas/in-memory data.
   **Evidence:** Project brief p. 5 and build guide §05 (as cited in the case materials); [`starter/data/`](../starter/data/), [`starter/agent/tools.py`](../starter/agent/tools.py). **Implementation note:** most tools currently read CSVs per call; only batch lookup is cached, so load-once behavior remains future work.

10. **Decision:** Use `openai/gpt-4o-mini` through OpenRouter. **Options considered:** larger model vs. lower-cost model for language handling.
    **Why we chose this:** The model interprets questions and explains tool evidence while Python supplies the facts; five recorded requests averaged about $0.00138 in model charges.
    **Evidence:** [`starter/agent/llm.py`](../starter/agent/llm.py), [`architecture_note.md` cost table](architecture_note.md#deployment-latency-and-cost). Latency is not established by that cost measurement.

11. **Decision:** Use FastAPI, plain HTML, and Vercel. **Options considered:** guided lightweight stack vs. Streamlit or a React build.
    **Why we chose this:** It follows the course build path and serves the existing single-page pilot without a separate frontend build.
    **Evidence:** Project brief p. 3; build guide §00 (as cited in the case materials); [`starter/app.py`](../starter/app.py), [`starter/public/`](../starter/public/), [`starter/vercel.json`](../starter/vercel.json).

12. **Decision:** Do not report the ₹15.33 cr order gap as savings or lost sales. **Options considered:** count it as recoverable revenue vs. retain it as an availability upper bound.
    **Why we chose this:** The records cannot distinguish cancelled, repeated, delayed, or later-filled orders, so attribution as lost sales is unsupported.
    **Evidence:** [`Discovery_note.md` §§2, 6](Discovery_note.md); `starter/data/primary_sales.csv` has no order-status field.

**Evidence note:** References to PDF page numbers above follow the case citations supplied with the decisions; the PDF text was not independently extractable in this workspace session. Code, Markdown, and CSV references were checked directly.
