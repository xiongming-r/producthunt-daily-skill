# Claude Code Product Hunt Skill 模板

用途：把本仓库 `ph-daily` CLI 封装成 Claude Code skill / command 的说明文本。

## Skill 描述

```text
Skill: producthunt-collector
Description: 调度本仓库 ph-daily CLI，生成 Product Hunt daily/weekly/monthly/yearly 报告，并汇总结果。
```

## Inputs

```text
period: daily | weekly | monthly | yearly
date: today | YYYY-MM-DD
featured: optional true | false
order: optional VOTES | NEWEST | FEATURED_AT
topic: optional Product Hunt topic slug
include_keywords: optional comma-separated keywords
exclude_keywords: optional comma-separated keywords
```

## Rules

```text
- Run ph-daily healthcheck before collection.
- Run ph-daily collect --period <period> --date <date>.
- Do not call Product Hunt API directly.
- Do not reimplement filters, LLM enrichment, or report rendering.
- Do not print .env secrets.
- On success, summarize selected/fetched and generated file paths.
- On failure, summarize command, exit code, stdout/stderr, and logs/cron.log if available.
```
