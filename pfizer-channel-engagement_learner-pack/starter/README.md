# Project Sankalp pilot

Read-only weekly review copilot for claims and domestic supply signals. A FastAPI API
routes questions through a LangGraph tool loop; deterministic Python tools read the
case CSVs and return source-row evidence. The model explains tool results but cannot
approve claims, move stock, or write to ERP/WMS systems.

```
app.py            FastAPI entrypoint (Vercel looks for `app` here)
agent/llm.py      the only file that knows the model provider (OpenRouter)
agent/tools.py    tools that read data/; exact facts come from here
agent/graph.py    the LangGraph graph; replace it with yours
data/             seven case CSVs used by the supply and claims review tools
public/           index.html, app.js, style.css: the frontend
tests/            run with pytest; no API key needed
AGENTS.md         instructions for your AI coding agent
vercel.json       Vercel function settings; keeps development files out of the bundle
```

## Run it on your laptop

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt uvicorn pytest httpx
cp .env.example .env               # then put your OpenRouter key in .env
node --test tests/test_frontend.js # check the evidence display formatting
pytest -q
uvicorn app:app --reload
```

Open http://127.0.0.1:8000. Quick actions cover batch lookup, short shelf-life
screening, CFA stock signals, a primary-shipment baseline, a claims ledger review,
and an untrusted-email example. Claim review results are always advisory and require
human review.

## Deploy

Set the Vercel project root to `starter/`, add `OPENROUTER_API_KEY` as an environment
variable, and deploy using the Vercel CLI or connected Git repository. The local `.env`
file is ignored; do not upload or commit it. `vercel.json` preserves the CSVs and public
files while excluding tests and local development artifacts from the function bundle.

This exercise app has no login, as required by the course blueprint. Do not put real
customer or patient information in it or expose non-training data through a public URL.
