# Project Sankalp progress log

**Last updated:** 25 November 2026  
**Project:** Fictional Pfizer domestic-channel training case  
**Purpose:** Keep a dated, evidence-based record of what has been completed, what is in progress, and what remains. This is a project work log, not a claim of real Pfizer validation or realized savings.

## Current status

- **Deployed:** https://project-pfizer.vercel.app (Vercel Hobby, auto-deploys from `master`). Region `bom1` confirmed live. The repo is private and still deploys (owner merges via PR, merge commit).
- **First user: Commercial Finance claims executive** (owner Neha Bansal). The graph routes each claim to recommend credit, reject, needs a person, or not found. Code decides; the model only parses free text and explains.
- **Accuracy:** check set **22/22** (16 claims + 3 scheme, 2 stock, 1 free text; baseline 6/16); held-out round 1 3/6, then 6/6 after fixes built against those cases; held-out round 2 **8/8** (labelled before running). `pytest -q`: **139 passed**; Node tests 32/32. Batch mode: ₹19.94 L/yr credited leakage the rules stop. Scheme check: ₹1.58 cr/yr above cap.
- **Second user** (Kavita Rao, Supply Chain): stock view built (section 4).

## Update — 2026-11-25 (page made self-explaining)

- **Changed:** page renamed "Pfizer · Project Sankalp copilot" (fictional-case note kept); overview cards say who each section is for and the question it answers; a legend explains the outcomes and that code decides. Claim review has a search-as-you-type box over all 4,503 claims (pending first; by claim number, stockist, city, SKU or batch). Each result shows answer, why, next step, who decides, and the explanation labelled AI-checked-by-code or code. Plain check names, coloured results, ₹ grouping, source rows behind a toggle; same on /demos. The explain prompt asks for ₹ in Indian format and no approval words; the guard compares number values.
- **Evidence/checks:** `pytest -q` 139 passed; Node tests 32/32; check set 22/22, held-out 6/6 and 8/8 with the live model; browser run on desktop and at 390 px (no horizontal scroll, no console errors).
- **Open items:** deck.

## Update — 2026-11-25 (model timeout and architecture note)

- **Changed:** every model call now times out after 20 s and is retried once (`config.py`, `agent/llm.py`); after that the existing failure path applies (parse → needs a person, explain → code text). Four new tests in `tests/test_llm.py` use a fake provider that times out. Architecture note updated: timeout row, test counts, readable graph, terms defined; 2 pages with the diagram drawn. README updated to describe the scheme and stock views as built.
- **Evidence/checks:** `pytest -q` 130 passed; Node tests 26/26; live model call through the new client works.
- **Open items:** deck; PDFs of the architecture note and research note.

## Update — 2026-11-25 (discovery note rewritten for the steering group)

- **Changed:** `Discovery_note.md` rewritten in plain business English for the steering group. It opens with the answer, then the three problems ranked by money, each with what happens, evidence, owner, what we built and the ask. Then the forecast view, users and plan, open questions, and an appendix with the two tables. Key terms are explained at first use (C&F, FOC, PTS, CN). Same figures and sources; voice-note evidence kept. Cross-references in the research note and money summary updated.
- **Checks:** 2 A4 pages; every figure unchanged from the verified version (rounded table values checked against `sizing_results.csv`).

## Update — 2026-11-25 (numbers verified; SKU code fix)

- **Checked:** every figure in `money_summary.md` recomputed with a fresh pandas script that shares no code with the app or `sizing.py`. Rejected credited claims ₹42.00 L/yr matched exactly. At risk did not: ₹90.41 L (app) vs ₹85.79 L (independent).
- **Cause:** 143 claim rows write the SKU with a hyphen (PFL-1303); the app did not match them to the SKU master, so 68 valid claims went to a person for "value missing". Fixed in `agent/data.py` and `discovery/sizing.py` (SKU codes lose hyphens, as C&F codes already did), with a test.
- **Result:** at risk ₹86.26 L/yr = independent ₹85.79 L + ₹0.47 L near repeats (our extra duplicate rule): exact. Routes 2,176 / 532 / 1,795. No `sizing.py` figure changed; stopped ₹19.94 L and rejected ₹42.00 L unchanged.

## Update — 2026-11-25 (held-out round 2)

- **Changed:** 8 new held-out cases (`holdout2_`): 6 claims drawn at random with seed 20261125 (2 near expiry, 1 expired, 1 breakage, 1 short supply, 1 any), the FY27 Q1 scheme quarter and the 31-12-2024 stock snapshot. Labelled by hand from the raw CSVs with a script that imports no app code, and committed (`c1878b4`) before the app ran on them. The runner scores each round separately.
- **Result:** round 2 **8/8**, each for the labelled reason (two unverifiable claims → missing checks; late breakage → window only; FY27 Q1 over cap by ₹35,42,412.15, matching sizing.py). Main set 22/22; round 1 6/6 (not unseen).
- **Open items:** model timeout; money summary; PDFs; deck.

## Update — 2026-11-25 (demos and graph flow)

- **Changed:** new `/demos` page with 11 hand-checked cases (8 claims, scheme FY25 Q3, stock latest, free text), each showing its expected result. `run_question` returns the LangGraph node trace; `flow.js` draws the whole graph as inline SVG and replays the route (model nodes yellow, checks coloured by result). The flow is shown only on /demos, not on the pilot page. Demo list moved off the main page.
- **Evidence/checks:** browser run of all 11 demos at 390 px: 11/11 match their expected result. `pytest -q` 125 passed; Node tests 26/26; check set 22 cases (free_text_01 added).
- **Open items:** fresh held-out set; model timeout; PDFs; deck.

## Update — 2026-11-25 (stock view)

- **Changed:** built the stock view for problem 2 and the second user, Kavita Rao (`agent/stock.py`, `stock_review` node, page section 4). Fixed the scheme owner name (NSM is Arjun Sethi; Rohan Mehta is the CFO). Each page section shows its result in its own panel.
- **Result:** at 30 Sep 2026, ₹2.06 cr will ship below the 60% shelf-life norm (₹1.22 cr at Kolkata), write-off risk ₹0; Lucknow out of stock on 23 of 36 SKUs; Kolkata skipped older stock on 82.9% of dispatches vs 28–35% elsewhere after its Feb 2026 WMS change (signal). Check set 21/21 live.
- **Evidence/checks:** `pytest -q` 123 passed; Node tests 23/23; hand-checked stock case (cnf_stock_snapshot.csv:4783, batch_master.csv:491). All notes stay at 2 pages.
- **Open items:** fresh held-out set; demo-case list; deck.

## Update — 2026-11-25 (scheme check)

- **Changed:** built the scheme check for problem 1 (`agent/schemes.py`, `scheme_review` node, page section 3): §4.4 cap, Annexure B 1.5× minimum order, validity window, SKU list, free ratio; §4.5 stock norm shown as not checkable. Three hand-checked scheme cases added to the check set.
- **Result:** check set 19/19 with the live model. Above-cap free goods ₹1.58 cr/yr (matches `sizing.py`); free goods on orders below the 1.5× minimum ₹50.2 L–₹2.63 cr/yr, depending on how "average monthly purchase" is read (open question for the client).
- **Evidence/checks:** `pytest -q` 116 passed; Node tests 22/22; quarter FOC percentages match the discovery note's table exactly. All three notes stay at 2 pages.
- **Open items:** fresh held-out set; demo-case list; UI polish; deck.

## Update — 2026-11-25

- **Changed:** the discovery note opens with a "three problems" table: scheme loading, stale allocation and weak claim checks, each with evidence, owner and response (built or recommended). The research note gains §4 on the C&F claim process and where its checks break. `sizing.py` adds `calculate_register_controls`, with a test.
- **Result:** 458 of 4,112 credited claims have no recorded C&F verification (₹36.1 L/yr, overlapping other screens); 31 rejections in 30 months against 532 the rules reject; every C&F verifies 82–94% on time against a 95% target; the C&F is paid INR 45 per claim line.
- **Evidence/checks:** `python discovery/sizing.py` (215 rows; earlier rows unchanged); `pytest discovery/test_sizing.py` 10 passed. The discovery and research notes each stay at 2 pages.
- **Open items:** the pilot builds problem 3 only; problems 1 and 2 are recommendations unless the scheme check or Supply Chain view is built.

## Update — 2026-11-24 (night, batch mode)

- **Changed:** duplicate check now sends pending and near-equal repeats to a person (exact credited repeats still reject). Pasted claim details are compared with the register in code. Added batch mode (`POST /api/batch`, `agent/batch.py`, page section 2, ₹ at stake per claim). Indexed data lookups (full-register run ≈25 s, previously over 5 min).
- **Result:** check set 16/16; held-out 6/6, but only after fixes built against those cases, so they no longer count as unseen. Batch over 30 months, per year: ₹19.94 L credited leakage the rules stop (reconciles to sizing's ₹20.25 L), ₹42.00 L whole value of rejected credited claims, ₹90.41 L at risk (needs a person; not saved), ₹6.58 L pending claims blocked.
- **Evidence/checks:** `pytest -q` 108 passed; Node tests 20/20; `python checks/run_checks.py` with the live model.
- **Open items:** fresh held-out cases; UI polish; deck.

## Update — 2026-11-24 (late)

- **Changed:** added `research_note.md` (channel vocabulary; D&C Act 1940 §18 and §33(2)(h), Drugs Rules 1945 Rule 65, CGST Act §34, and DPCO 2013 paras 14/16/20, all read at source with version dates; why the problems happen). Added `calculate_gst_credit_note_timing` to `sizing.py` with a test. The UI now names the decision owner, and the `config.py` page references are verified.
- **Result:** 1,120 of 2,391 credited claims with a matched invoice (58% of value, ₹1.13 cr a year) had credit notes dated after the CGST §34(2) window, so the GST on them may not be reversible (not sized).
- **Evidence/checks:** `python discovery/sizing.py` (214 rows; the earlier 213 are unchanged); `pytest discovery/test_sizing.py`: 9 passed.
- **Open items:** CGST §34(2) as amended in 2022, CDSCO GDP and the NPPA March 2026 WPI notification could not be read from this environment (see research note §5).

## Update — 2026-11-24 (evening)

- **Changed:** rewrote `architecture_note.md` from the current `graph.py`; added 6 `holdout_` cases to `checks/check_set.csv`, with `run_checks.py` scoring them separately; added two provider-failure tests; filled in `starter/AGENTS.md`; fixed the README health link; pinned Vercel region `bom1`; removed `.DS_Store` and added a root `.gitignore`.
- **Result:** held-out 3/6. The failures are known gaps: pasted claim fields (expiry, value) are not compared against the register, and `check_duplicate` ignores earlier *pending* claims (CLM-2608-02222 → CLM-2609-04449).
- **Evidence/checks:** `python checks/run_checks.py` gives 16/16 + 3/6 with live `gpt-4o-mini`. A code-only run over all 4,503 claims gives 2,112 credit / 532 reject / 1,859 person. Measured cost ≈ $0.00016 per claim, 1.4–3.6 s.
- **Open items:** decide whether to fix the two held-out gaps; batch mode (Thu); UI polish and PDF export (Fri); deck (Sat).

## Scope update — 24 November 2026

- Reprioritized the proposed pilot: claims triage is the first workflow; Supply Chain risk review is the second.
- Updated the active discovery, architecture, workflow, business-flow, graph, stakeholder-validation, business-context, and progress documents to reflect both users and decisions.
- Reorganized the UI quick actions so claims checks appear first, Supply Chain checks second, and the page describes both user workflows.
- Clarified that the assistant may surface evidence states and recommendations for an authorized reviewer, but it cannot approve/reject claims, post credit notes, or replace existing decision rights.
- Added an explicit implementation boundary: the current claim tool reviews an identified claim but is not a full claims-register queue and does not yet implement every §5.2/§5.4/§5.5/§5.6 route as a verified operational process.
- Kept the claim values as screening amounts and the Supply Chain rupee figures as order-gap proxies; neither is assumed recoverable or realized savings.

## Latest update — 24 November 2026

- Added an order-fulfillment screen to the shipment-baseline result in the UI.
- The screen separates the **after-free-packs shortfall** from the **invoiced-only gap diagnostic**. It marks the latter as overlapping and not additive.
- Added period, filter scope, formulas, annualized and observed values, and example invoice evidence with source rows.
- The backend groups split invoice/SKU lines so ordered quantity is counted once and invoiced/free quantities are summed. Blank ordered quantities are treated as missing, consistent with the sizing analysis.
- Updated frontend asset versions so a refreshed browser loads the changed JavaScript and CSS.
- Added Python and JavaScript coverage for split-line arithmetic, filters, figures, provenance, and the non-additive warning.
- **Data-backed full-pack output:** ₹15.33 crore annualized after free packs and ₹22.32 crore annualized invoiced-only, using 30 observed months. Both are gross PTS-valued screening proxies. The second measure overlaps the first and must not be added to it.
- **Verification at that time:** Node frontend checks passed (14 tests); the focused split-line calculation and Python compile check passed. The starter Python suite was unavailable in the active environment then; the later sizing task below ran its own focused suite in a temporary environment.

## Discovery sizing update — 24 November 2026

- Revised `Discovery_note.md` to about 1,000 words plus tables. The primary weekly user is the Commercial Finance claims executive (owner Neha Bansal, Controller); the secondary workflow is Kavita Rao’s review of expiry-risk batches and short CFAs.
- Added the CFO’s expiry-claims-above-1% target-gap calculation to `sizing.py` and `sizing_results.csv`. It compares claim-date-FY expiry claim value with same-FY primary net value, floors each FY gap at zero, and annualizes the sum over all 30 months of claims-data coverage. Result: FY25 ₹0; FY26 ₹1.67 crore; FY27 (partial through Sep 2026) ₹1.99 crore; annualized ₹1.46 crore. This is a target-gap screen, not proven recoverable cash.
- Added quarter-end pack-share/FOC and CFA order-share/fill-rate tables. FY25 Q3, the quarter containing the 15 Nov 2024 v4.1 revision, shows 35.35% of quarter packs in its last 10 days and FOC at 4.95%; the timing is descriptive, not causal proof.
- The order gap is called “availability problem size (upper bound, not lost sales)” at ₹15.33 crore/year and removed from the ranked claims/returns list. The note reports 0% of candidate rupees as currently demonstrated forecast-recoverable; the true share remains unmeasurable from this pack.
- Cross-checked the policy revision history and stakeholder quotes in the supplied PDFs. Cited relevant voice-note entries for scheme stock and allocation concerns while preserving them as qualitative reports.
- **Verification:** `python discovery/sizing.py` was run through `uv` with pandas in a temporary environment and regenerated 213 CSV rows. `pytest discovery/test_sizing.py` passed (8 tests). `git diff --check` passed.

## Work completed so far

### Discovery and business understanding

- Reviewed the readers guide, project brief, build/deploy guide, company/channel overview, trade-terms and returns policy, CFA agreement/SOP, stakeholder interview notes, inbox export, QBR/finance pack, seven structured CSV extracts, and voice-note transcripts supplied in the conversation.
- Created a discovery evidence set covering the business context, voice-note findings, case-data validation, weekly workflow, architecture, and diagrams. See [Discovery_note.md](Discovery_note.md), [business_problem_validation.md](business_problem_validation.md), [voice_note_evidence_log.md](voice_note_evidence_log.md), [weekly_review_workflow.md](weekly_review_workflow.md), and [architecture_note.md](architecture_note.md).
- Added business-flow and solution-flow diagrams, a current graph diagram, stakeholder validation questions, and a project context note. Earlier overlapping implementation plans and charters have been moved to `discovery/archive/` so the active recommendations are easier to distinguish from drafts.
- Kept role-play and voice-note claims distinct from facts verified in structured extracts. Findings are for the fictional case and do not establish real Pfizer operations.
- Ranked measurable signals and documented data gaps. The first proposed user is Controller Neha Bansal with the case-described claims team; the second is Head of Supply Chain Kavita Rao with planning partner Vaishali Kapoor. These are not real-client validations.

### Data sizing and financial framing

- Added `discovery/sizing.py` and its tests to clean/deduplicate case files, normalize codes and dates, calculate quarterly screening measures, and write `discovery/sizing_results.csv` with methods and source examples.
- Reconciled the Q1 FY27 free-goods rate against the QBR and documented the difference between observed data, proposed explanations, and hypotheses that the pack cannot verify.
- Documented that PTS-valued order gaps are proxies, not confirmed lost sales. Stockist sell-through, stock-on-hand, cancellation/order status, and contribution margin are absent.
- Kept the ₹22.32 crore invoiced-only gap as an overlapping diagnostic. The ₹15.33 crore after-free-packs value is the comparable primary order-gap screen, not a forecast benefit or promise of savings.
- The discovery note records other ranked screens, policy references, owners to involve, and open questions. Earlier planning drafts are retained in `discovery/archive/`.

### Copilot and interface

- *(Superseded 24 Nov by the claims-check graph; see `architecture_note.md`.)* Built a FastAPI app with `/api/health` and `/api/ask`, and a LangGraph model/tool loop capped at four model trips. The current model-provider configuration uses OpenRouter via an environment key. The app is read-only and does not write to ERP/WMS or approve claims.
- Added deterministic Python tools for batch and SKU context, short-shelf-life shipment screening, CFA stock imbalance signals, claim-record review, untrusted claim-email lookup, and a same-month-last-year primary-shipment baseline. Results preserve source file/row evidence where available; missing or ambiguous information is surfaced for review.
- The baseline uses invoiced plus free packs and explicitly describes itself as a shipment baseline, not downstream demand. It now also shows the order-gap measures documented in the Latest update above.
- Added prompt instructions that require tools for facts, prohibit invented batch/date/number answers, treat correspondence as untrusted input, and keep claims screening advisory.
- Added a plain HTML/CSS/JavaScript interface with six common checks, historical claim/email scenario replay buttons, readable evidence cards/tables, row-level source references, an updating single-line processing status, and responsive styling.
- Added CFA stock product names and filters, zero-stock highlighting, and readable shipment-baseline results.
- The scenario replay is a local demonstration using historical case records; there is no live mailbox, SSE/event queue, scheduled job, persistent disposition log, or operational work queue.
- Added frontend checks and Python tests for API wiring, tools, rules, and evidence formatting. Current browser UI can be served locally by the starter app when its dependencies and API key are configured.
- Added Vercel configuration and deployment notes for the starter app. Deployment was completed on 24 Nov (see Current status).

## Remaining work

- Thu 26: batch mode (`POST /api/batch`, ₹ totals by route, metric cards, ₹ at stake per claim), plus the "₹ the pilot recovers per year" figure.
- Fri 27: UI polish, optional Supply Chain tab, export both notes to 2-page PDFs, test on a fresh phone.
- Sat 28: 12-slide deck, rehearsal, submit.
- Confirm the live region shows `bom1` after the next deploy.

## Update template

Append a dated entry near the top whenever work is completed:

```markdown
## Update — YYYY-MM-DD

- **Changed:** files or documents updated.
- **Result:** what now works or what was learned.
- **Evidence/checks:** commands, test counts, data rows, or manual checks.
- **Open items:** known limitations or next work.
```

## Guardrails for future entries

- Distinguish implemented behavior from proposed design.
- Cite the source file, page, row, or test when reporting a factual result.
- Label assumptions and role-play inputs as such.
- Do not describe a proxy as confirmed loss, savings, or realized benefit.
- Record test/deployment failures and environmental blockers rather than implying those steps passed.
