# Qclaw Product Hunt 工作流模板

用途：把 Product Hunt 采集拆成可观察的任务流，便于检查、采集、验收、通知。

## 工作流

```text
Task: Product Hunt <period> report
Inputs:
- period: daily | weekly | monthly | yearly
- date: today | YYYY-MM-DD
- optional filters: featured, order, topic, url, twitter_url

Steps:
1. cd <repo>
2. ph-daily healthcheck
3. ph-daily collect --period <period> --date <date>
4. Parse stdout for selected/fetched.
5. Report generated files under reports/ and data/.
6. On failure, stop and return stdout/stderr plus logs/cron.log excerpt if present.

Rules:
- Do not call Product Hunt API directly.
- Do not edit data/raw, data/processed, or reports as a repair step.
- Do not print secrets.
```

## 示例请求

```text
执行 Product Hunt 周报流程，日期用 today。只调用 ph-daily CLI；成功后给我报告路径和入选数量，失败后给我 stdout/stderr 和日志摘要。
```
