# Product Hunt Daily Agent Collector

Agent-friendly Product Hunt daily collector. It fetches Product Hunt daily launches through the official GraphQL API, filters products with dynamic vote/comment quality rules, enriches selected products with an OpenAI-compatible LLM endpoint, and writes JSON plus Markdown reports.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill `.env` with `PRODUCT_HUNT_TOKEN`, `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`.

## Commands

```bash
ph-daily healthcheck
ph-daily collect --date today
ph-daily collect --date 2026-05-11
ph-daily backfill --days 7
```

Generated runtime files are written under `data/`, `reports/`, and `logs/`; those paths are ignored by git.
