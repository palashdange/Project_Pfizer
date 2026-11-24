# Project Sankalp pilot (app)

A read-only claims-screening pilot for the Commercial Finance claims team. A FastAPI endpoint runs each input through a LangGraph graph. Python checks the claim against policy CO-POL-014 and the case CSVs, then routes it to recommend credit, reject, needs a person, or not found, citing the clause and source rows. The model only reads free text into fields and explains the result. It cannot approve a claim, post a credit note, or write to ERP/WMS. A named person decides.

The project overview, live URL and demo inputs are in the [root README](../../README.md). The design is in the [architecture note](../discovery/architecture_note.md).

```
app.py            FastAPI routes only (/api/health, /api/ask); Vercel looks for `app` here
config.py         every policy number, with its CO-POL-014 clause and page
agent/graph.py    the LangGraph graph: state, nodes, edges, route priority
agent/rules.py    plain-Python date, quantity, value and shelf-life rules
agent/data.py     loads the CSVs once, de-duplicates, keeps source rows
agent/prompts.py  the two prompts (field extraction, explanation)
agent/llm.py      the only file that knows the model provider (OpenRouter)
agent/tools.py    earlier tool-loop functions; tested but not wired into the graph
data/             the case CSVs
public/           index.html, app.js, evidence.js, progress.js, style.css
tests/            pytest (no API key needed) and Node frontend tests
checks/           check_set.csv (16 hand-checked + 6 held-out) and run_checks.py
AGENTS.md         instructions for the coding agent
vercel.json       region bom1; keeps tests and local files out of the bundle
```

## Run it on your laptop

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt uvicorn pytest httpx
cp .env.example .env               # then put your OpenRouter key in .env
pytest -q
node --test tests/test_frontend.js
python checks/run_checks.py        # needs the key; prints check-set and held-out scores
uvicorn app:app --reload           # open http://127.0.0.1:8000
```

## Deploy

Vercel Hobby, with root directory `pfizer-channel-engagement_learner-pack/starter` and env vars `OPENROUTER_API_KEY` and `MODEL`. Only the repo owner's commits deploy, so changes go in through a pull request that the owner merges into `master` as a merge commit. Check `/api/health` after each deploy. The local `.env` is git-ignored; never commit it.

This exercise app has no login. Use it only with the fictional case data.
