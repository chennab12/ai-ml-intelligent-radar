# AI/ML TPM Intelligence Radar

A beginner-friendly Streamlit dashboard that converts trusted AI/ML news into concise meaning, TPM takeaways, measurable KPIs, emerging trend signals, and bounded agentic-AI project ideas.

## What is included

- Executive brief with the strongest topic cluster and three immediate TPM actions
- Ranked signal feed covering agentic AI, inference, deep learning, accelerators, MLOps, and governance
- Transparent relevance scoring and directional trend momentum
- KPI translation playbook for quality, latency, throughput, reliability, cost, capacity, safety, and delivery
- Ranked agentic project ideas with safe pilot guidance
- Curated allowlist of primary and established technical sources
- Offline demo mode plus optional live RSS refresh
- Search and topic filters, responsive layout, source links, caching, and graceful partial-feed failure

## Run locally

Python 3.11 is recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The dashboard opens in demo mode so startup does not depend on the internet. Turn on **Refresh trusted live feeds** in the sidebar to collect current items.

## Deploy on Streamlit Community Cloud

1. Upload this folder to a GitHub repository.
2. In Streamlit Community Cloud, create an app from the repository.
3. Set the main file path to `app.py`.
4. Deploy. No secrets are required.

## Design decisions

- “Top 1%” is implemented honestly as a small curated source allowlist plus ranking—not as an unverifiable percentile claim.
- The app uses extractive/rule-based simplification so it works without paid APIs and does not fabricate summaries or citations.
- Trend “projection” is labeled directional and based on signal momentum, not presented as a statistical forecast.
- RSS failures are isolated; one unavailable source cannot crash the dashboard.

## Extending it

Add a source in `radar/config.py`. For production, persist normalized items in SQLite/Postgres, add scheduled ingestion, and optionally place an LLM summarizer behind structured outputs, citation checks, caching, and evaluation tests.

## Tests

```bash
python -m pytest -q
```

