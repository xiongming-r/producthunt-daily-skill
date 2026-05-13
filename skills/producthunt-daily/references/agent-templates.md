# Agent Integration Templates

## Scheduler

```text
Run Product Hunt <period> collection.
1. cd <INSTALL_DIR>
2. source .venv/bin/activate
3. ph-daily healthcheck
4. ph-daily collect --period <period> --date <date>
5. Report selected/fetched count and generated report paths.
6. On failure, report command, exit code, stdout/stderr, and logs/cron.log excerpt if present.
Never print secrets and never reimplement Product Hunt filtering.
```

## Agent Mode

```text
Run Product Hunt <period> collection without external LLM enrichment:
ph-daily collect --period <period> --date <date> --no-enrichment
Then read data/processed/<period-output>.json and enrich selected products using references/enrichment-prompt.md.
Do not modify data/raw, data/processed, or reports.
```

## Secondary Analysis

```text
Read the generated report at <report_path>.
Summarize:
1. Top 3 products to watch.
2. Opportunities for developers or entrepreneurs.
3. Keywords to monitor next.
Only use report content.
```
