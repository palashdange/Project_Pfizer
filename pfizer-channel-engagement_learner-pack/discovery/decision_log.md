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

**16. Decision:** Send repeats of a pending claim, and near-equal quantities, to a person; reject only an exact repeat of a credited claim.
**Options considered:** exact credited repeats only (as before) vs. also reject near repeats vs. send near and pending repeats to a person.
**Why we chose this:** §5.6 says to check for "an earlier claim on the same stockist and batch" without a quantity rule, so a near repeat is a question, not a breach. The 1% / 1-pack tolerance is our pilot threshold, not a policy number: 17 register claims sit within it before the spread widens.
**Evidence:** CO-POL-014 §5.6 p.4; CLM-2608-02222 → CLM-2609-04449 (expiry_claims.csv rows 4134, 4345); CLM-2505-00789 → CLM-2507-04457 (rows 1489, 1710); config.py; tests/test_rules.py, tests/test_graph.py.

**17. Decision:** Compare pasted claim details with the register in code; any conflict goes to a person.
**Options considered:** register is the only truth (ignore pasted text) vs. compare and flag.
**Why we chose this:** A stockist message that disagrees with the register on expiry or value is exactly the case a person should see. The model only reads the text into fields; code drops any value not present in the text and does the comparison. Bare claim IDs make no extra model call.
**Evidence:** CO-POL-014 §5.3, §5.7; held-out cases holdout_expiry_mismatch_01, holdout_value_mismatch_01; tests/test_graph.py.

**18. Decision:** Batch mode reports "leakage stopped" separately from "credited claims the rules reject", and counts needs-a-person as at risk, not saved.
**Options considered:** one "caught" total vs. separating the invalid part.
**Why we chose this:** An over-quantity claim (§5.5) is invalid only for its excess packs; counting the whole claim gives ₹42.0 L/yr instead of ₹19.94 L/yr. The leakage figure reconciles to discovery/sizing.py (₹20.25 L/yr); the small gap is claims the pilot sends to a person because the batch or invoice is missing.
**Evidence:** starter/agent/batch.py; tests/test_batch.py; discovery/sizing_results.csv.

**19. Decision:** Build a quarter-end scheme check for Commercial Finance and the National Sales Manager, as a branch of the same graph.
**Options considered:** recommend only vs. pre-approval what-if (needs a forecast) vs. quarter review on actual sales.
**Why we chose this:** Scheme loading is the largest driver found (problem 1), and §4.3 already makes Commercial Finance the cost check. A quarter review uses only the extract, so every number has a source row; a what-if would need the forecast we argue against. Code checks the cap and Annexure B terms; the model only explains.
**Evidence:** CO-POL-014 §4.2–4.5, Annexure B pp.5–6; starter/agent/schemes.py; tests/test_rules.py, tests/test_graph.py; check set scheme_cap_01, scheme_eligibility_01, scheme_not_found_01.

**20. Decision:** Read Annexure B's "average monthly purchase" as all purchases (the policy wording), and report the non-scheme-only reading as a range.
**Options considered:** all purchases vs. non-scheme purchases only vs. no pass/fail.
**Why we chose this:** The policy does not define it, and the choice moves free goods on ineligible orders from ₹50.2 L to ₹2.63 cr a year. Using the wording keeps us faithful to the document, showing both keeps us honest, and the question goes to the client. Months before the extract count as zero, so a pass that relies on them is flagged as uncertain.
**Evidence:** Annexure B p.5; discovery/Discovery_note.md open question 5; starter/agent/schemes.py.

**21. Decision:** Build a stock view for Kavita Rao (Head of Supply Chain): expiry risk, cover and a FEFO signal per C&F, at a month-end snapshot.
**Options considered:** recommendation only vs. allocation-drift table vs. stock view vs. return-to-CDC suggestions.
**Why we chose this:** Her ask is "not another forecast. I need to know where the stock is going to expire before it does" (interviews p. 2). The snapshot has stock by batch with a rolling outward rate, so code can apply §7.1–7.2 and the C&F §2.2 norm without forecasting. The 60% shelf-life figure is labelled "stockists may refuse", not a write-off; write-off risk is the 60-day block. The FEFO signal is a pilot threshold (2× the other C&Fs' median) and a prompt to check the WMS, not proof. Transfers are not suggested: they need her approval and 10–14 days (§2.5).
**Evidence:** CO-POL-014 §7.1–7.2 p.4; C&F agreement clauses 4.3, 6.3, Schedule 2 §2.2–2.5; cnf_stock_snapshot.csv; starter/agent/stock.py; tests/test_rules.py, tests/test_graph.py; check set stock_latest_01.

**22. Decision:** Give every model call a 20-second timeout and one retry, then fall back to the existing failure path.
**Options considered:** no timeout (rely on the Vercel function limit) vs. timeout without retry vs. timeout with one retry vs. several retries.
**Why we chose this:** A review normally answers in 2–3 s, so 20 s means the provider is stuck. One retry covers a dropped connection; more retries would only keep the user waiting. After that, code takes over: a failed parse goes to a person and a failed explanation uses the code text, so the route never depends on the model. Both values are pilot choices, not policy numbers, and sit in `config.py`.
**Evidence:** starter/config.py (MODEL_TIMEOUT_SECONDS, MODEL_MAX_RETRIES); starter/agent/llm.py; tests/test_llm.py (fake provider that times out: one timeout then success; two timeouts stop after one retry with the code route kept; stuck parse goes to a person).

**23. Decision:** Make the page self-explaining: claim search, plain result layout, and a visible code-vs-AI label.
**Options considered:** keep the claim-number box vs. ship the whole claim list to the browser vs. a search endpoint; keep the single explanation paragraph vs. answer / why / next step written by code.
**Why we chose this:** A first-time user could not tell what each section was for, and the claims team does not know claim numbers by heart. A code-only search endpoint (pending first, any identifying field) keeps the page light and works on a phone. Why and next step are generated by code from the checks, so they can never contradict the route; the model's text stays labelled and guarded. The guard now compares number values, not spellings, so the model may write ₹ in Indian format but still cannot change or invent a figure.
**Evidence:** starter/agent/search.py, app.py `/api/claims/search`; public/claim-search.js, evidence.js, app.js; tests/test_search.py, tests/test_graph.py (₹ formatting allowed, changed value rejected), tests/test_result_view.js; check set 22/22, held-out 6/6 and 8/8 after the change.

PDF page references checked against the source PDFs on 24 Nov 2026. Code, Markdown, and CSV references checked directly.