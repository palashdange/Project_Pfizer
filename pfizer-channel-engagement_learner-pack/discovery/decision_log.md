# Decision log

Project Sankalp · fictional training case · 24 November 2026

Each entry records the selected direction, the main alternative, the rationale, and evidence. Monetary screens below are candidates or exposure indicators, not verified savings.

**1. Decision:** Do not build a new demand-forecasting model.
**Options considered:** new model vs. improve scheme, allocation, and claim controls.
**Why we chose this:** No direct recovery from a new forecast is demonstrated; the case separates the national forecast from CFA allocation, and the Head of Supply Chain says she needs "not another forecast".
**Evidence:** Doc 04 p. 3 (Vaishali Kapoor: "The forecast is national. The allocation sheet splits it."); doc 04 p. 2 (Kavita Rao); Discovery_note.md §3.

**2. Decision:** First user is the Commercial Finance claims executive; owner Neha Bansal (Controller).
**Options considered:** Finance-first vs. Supply Chain-first.
**Why we chose this:** She has a clear weekly claim-review decision and the rules provide testable screens; screened amounts still need ledger validation.
**Evidence:** Doc 04 p. 2; CO-POL-014 §§5.2, 5.4, 5.5, 5.6; sizing_results.csv rows 27, 38, 49, 60.

**3. Decision:** Kavita Rao's Supply Chain team is the second user.
**Options considered:** make it the first pilot vs. secondary workflow.
**Why we chose this:** The ₹15.33 cr order gap is an upper-bound signal; available sales rows lack order status and stockist sell-through/on-hand data.
**Evidence:** Discovery_note.md §§2, 4, 6; starter/data/primary_sales.csv and cnf_stock_snapshot.csv schemas.

**4. Decision:** Keep business calculations and evidence joins in deterministic Python.
**Options considered:** model-generated numbers vs. code-computed results with model-assisted language handling.
**Why we chose this:** Financial and policy figures must be reproducible; the model should not calculate or invent them.
**Evidence:** Project brief pp. 2, 4; starter/config.py, starter/agent/rules.py, starter/tests/test_rules.py.

**5. Decision:** Route incomplete or ambiguous claims to a person.
**Options considered:** infer a disposition vs. return NEEDS_PERSON with the reason.
**Why we chose this:** Missing evidence cannot support a safe decision; §5.4 calls for written Area Manager approval, which the extract does not contain.
**Evidence:** Project brief p. 5 (accuracy bar rule 2); CO-POL-014 §5.4; `decide` node in starter/agent/graph.py; check set cases blank_invoice_01/02, missing_batch_01.

**6. Decision:** Keep the pilot read-only: no credit posting, SAP/WMS write-back, or stock transfer.
**Options considered:** execute actions vs. present evidence for human action.
**Why we chose this:** A named person retains decisions that move money or stock; system writes are outside pilot scope.
**Evidence:** Project brief pp. 4–5; starter/app.py.

**7. Decision:** Do not add a vector store, embeddings, or retrieval pipeline.
**Options considered:** retrieval architecture vs. direct rules and supplied records.
**Why we chose this:** The pilot uses short policy references and structured CSV extracts; retrieval adds no demonstrated need.
**Evidence:** Project brief p. 5 (out-of-scope list); starter/requirements.txt.

**8. Decision:** Do not train or add a machine-learning model of our own.
**Options considered:** predictive model vs. deterministic checks and historical baselines.
**Why we chose this:** The identified gaps are control, matching, and allocation issues; none needs prediction.
**Evidence:** Project brief p. 5 (out-of-scope list); Discovery_note.md §§2–3.

**9. Decision:** Load the supplied CSV extracts once in memory; no database.
**Options considered:** database vs. in-memory extracts loaded once.
**Why we chose this:** The case is a small, static dataset; loading once keeps requests fast on Vercel.
**Evidence:** Project brief p. 5 ("Load CSVs once"); build guide §05; starter/agent/data.py, starter/tests/test_data.py.

**10. Decision:** Use openai/gpt-4o-mini through OpenRouter.
**Options considered:** larger model vs. lower-cost model for language handling.
**Why we chose this:** The model only extracts fields and explains results while Python supplies the facts; measured cost is a fraction of a cent per request.
**Evidence:** starter/agent/llm.py; architecture_note.md cost table.

**11. Decision:** Use FastAPI, plain HTML, and Vercel.
**Options considered:** guided lightweight stack vs. Streamlit or a React build.
**Why we chose this:** It follows the course build path and serves the single-page pilot without a separate frontend build.
**Evidence:** Project brief p. 3; build guide §00; starter/app.py, starter/public/, starter/vercel.json.

**12. Decision:** Do not report the ₹15.33 cr order gap as savings or lost sales.
**Options considered:** count it as recoverable revenue vs. retain it as an availability upper bound.
**Why we chose this:** The records cannot distinguish cancelled, repeated, delayed, or later-filled orders, so attribution as lost sales is unsupported.
**Evidence:** Discovery_note.md §§2, 6; primary_sales.csv has no order-status field.

**13. Decision:** Fixed claims workflow with conditional routing instead of a free model/tool loop.
**Options considered:** model chooses tools and outcome vs. code runs every check and decides the route.
**Why we chose this:** Credit decisions move money; every claim must get the same checks in the same order. The check set rose from 6/16 (baseline) to 16/16.
**Evidence:** Project brief p. 4 (conditional edges; "a named person decides"); starter/agent/graph.py; checks/run_checks.py output, 24 Nov 2026.

**14. Decision:** Model used only for structured extraction from messy emails and a plain-language explanation.
**Options considered:** model reads and decides vs. model fills a fixed schema that code acts on.
**Why we chose this:** A schema keeps the model from inventing a batch, quantity or approval; emails such as EML-017 contain instructions that must be ignored.
**Evidence:** Project brief p. 4 ("structured output with a schema"); claim_emails.csv row 28; starter/agent/prompts.py; check set case email_injection_01.

**15. Decision:** Run the six claim checks as parallel nodes.
**Options considered:** one large function vs. one node per rule.
**Why we chose this:** The checks are independent; each writes its own result with its clause and evidence rows, so a failure is easy to trace and test.
**Evidence:** Project brief p. 4 ("several independent checks: parallel nodes, one key each"); starter/agent/graph.py; starter/tests/test_graph.py.

PDF page references checked against the source PDFs on 24 Nov 2026. Code, Markdown, and CSV references checked directly.