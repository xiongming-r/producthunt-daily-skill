# Product Hunt Daily Skill

Product Hunt Daily Skill is a self-contained agent skill package for collecting, filtering, and analyzing Product Hunt launches with the `ph-daily` CLI.

It supports daily, weekly, monthly, and yearly collection modes, Product Hunt official filters, local keyword filters, OpenAI-compatible LLM enrichment, and Agent Mode for host-agent-side analysis.

## What This Skill Does

- Runs Product Hunt collection through the bundled `ph-daily` CLI.
- Keeps Product Hunt fetching, filtering, storage, and report rendering inside the CLI.
- Generates raw JSON, processed JSON, Markdown reports, and optional HTML reports.
- Supports Agent Mode with `--no-enrichment`, where the CLI fetches and filters data while the host agent performs the product analysis.
- Provides reference prompts and templates for agent orchestration.

## Package Layout

```text
producthunt-daily/
  SKILL.md
  README.md
  references/
    config-reference.md
    agent-templates.md
    enrichment-prompt.md
  scripts/
    setup.sh
    .env.example
    pyproject.toml
    src/ph_daily/
```

`SKILL.md` is the entrypoint used by agents. This README is for humans who need to install, inspect, or distribute the skill package.

## Requirements

- Python 3.11+
- Product Hunt API token
- Optional OpenAI-compatible LLM endpoint and API key

For Product Hunt read-only collection, a developer token from the Product Hunt API dashboard is enough.

## Installation

From the exported skill package directory:

```bash
bash scripts/setup.sh
```

By default, setup installs the CLI into:

```text
~/.ph-daily
```

You can choose another install directory:

```bash
bash scripts/setup.sh /your/install/path
```

After setup, edit:

```text
~/.ph-daily/.env
```

Minimum configuration:

```env
PRODUCT_HUNT_TOKEN=your_product_hunt_token
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini
```

When using Agent Mode, `LLM_API_KEY` may be empty if you run collection with `--no-enrichment`.

## Basic Usage

```bash
cd ~/.ph-daily
source .venv/bin/activate

ph-daily healthcheck
ph-daily collect --period daily --date today
ph-daily collect --period weekly --date today
ph-daily collect --period monthly --date today
ph-daily collect --period yearly --date today
```

## Agent Mode

Agent Mode skips external LLM enrichment:

```bash
ph-daily collect --period daily --date today --no-enrichment
```

In this mode, `ph-daily` still performs Product Hunt fetching, quality filtering, keyword filtering, and JSON/report writing. Selected products will not contain CLI-generated LLM analysis. The host agent can read `data/processed/...json` and follow `references/enrichment-prompt.md` to produce analysis in the conversation.

Unless the user explicitly asks for a new file, the host agent should not create custom Markdown or HTML reports. For consistent report files, use normal CLI enrichment by configuring `LLM_API_KEY` and running `ph-daily collect` without `--no-enrichment`.

## Outputs

Daily outputs keep the compatibility paths:

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
reports/html/YYYY-MM-DD.html
```

Non-daily outputs use period-specific paths:

```text
data/raw/weekly/YYYY-Www.json
data/processed/weekly/YYYY-Www.json
reports/weekly/YYYY-Www.md
reports/html/weekly/YYYY-Www.html

data/raw/monthly/YYYY-MM.json
data/processed/monthly/YYYY-MM.json
reports/monthly/YYYY-MM.md
reports/html/monthly/YYYY-MM.html

data/raw/yearly/YYYY.json
data/processed/yearly/YYYY.json
reports/yearly/YYYY.md
reports/html/yearly/YYYY.html
```

## Useful References

- `references/config-reference.md`: environment variables and defaults.
- `references/agent-templates.md`: prompts for scheduler, Agent Mode, and secondary analysis.
- `references/enrichment-prompt.md`: product analysis schema for host-agent-side enrichment.

## Safety Rules

- Never print `.env`, tokens, or API keys.
- Do not call the Product Hunt API directly from the host agent.
- Do not reimplement Product Hunt filtering in prompts.
- Do not edit `data/raw`, `data/processed`, or generated reports as a repair step.
