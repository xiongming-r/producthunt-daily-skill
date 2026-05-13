---
name: producthunt-daily
description: "Collect, filter, and analyze Product Hunt daily/weekly/monthly/yearly launches using the ph-daily CLI. Use when users mention Product Hunt, PH reports, product hunt 抓取/采集, 日报/周报/月报/年报, tech product monitoring, new product discovery, Product Hunt trend summaries, backfills, or agent-driven Product Hunt automation."
---

# Product Hunt Daily Collector

Use this skill to run the `ph-daily` CLI, generate Product Hunt period reports, and optionally perform agent-side analysis.

## Core Rule

`ph-daily` owns Product Hunt fetching, filtering, enrichment, and report generation. The agent should call the CLI, report results, diagnose failures, and optionally summarize generated reports. Do not reimplement Product Hunt API calls or filtering logic in the agent prompt.

## Setup

If this is an exported skill package, run:

```bash
bash /path/to/producthunt-daily/scripts/setup.sh
```

Then edit the generated `.env` file with:

```env
PRODUCT_HUNT_TOKEN=your_product_hunt_token
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini
```

For Agent Mode, `LLM_API_KEY` may be empty and commands should use `--no-enrichment`.

## Commands

```bash
ph-daily healthcheck
ph-daily collect --period daily --date today
ph-daily collect --period weekly --date today
ph-daily collect --period monthly --date today
ph-daily collect --period yearly --date today
ph-daily collect --period daily --date today --no-enrichment
ph-daily backfill --days 7
```

## References

- Configuration: `references/config-reference.md`
- Agent templates: `references/agent-templates.md`
- Agent-side enrichment contract: `references/enrichment-prompt.md`

## Safety

- Never print `.env`, tokens, or API keys.
- On success, report selected/fetched counts and generated report paths.
- On failure, report the command, exit code, stdout/stderr, and relevant log excerpts.
- Do not edit `data/raw`, `data/processed`, or `reports` as a repair step.
