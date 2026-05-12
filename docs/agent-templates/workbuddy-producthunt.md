# WorkBuddy Product Hunt 采集模板

用途：让 WorkBuddy 调度本仓库 `ph-daily` CLI，并把结果转成人类可读摘要。

## 固定规则

- 只调用 `ph-daily`，不要重写 Product Hunt API 请求、过滤、LLM 富化或报告生成逻辑。
- 不输出 `.env`、token、API key。
- 失败时报告命令、退出码、stdout、stderr，以及 `logs/cron.log` 中相关片段。
- 成功时报告 selected/fetched 数量、Markdown / HTML 报告路径、raw / processed JSON 路径。

## 命令模板

```bash
ph-daily healthcheck
ph-daily collect --period daily --date today
ph-daily collect --period weekly --date today
ph-daily collect --period monthly --date today
ph-daily collect --period yearly --date today
```

## 提示词模板

```text
帮我运行 Product Hunt <daily|weekly|monthly|yearly> 采集。
请在仓库根目录执行：
1. ph-daily healthcheck
2. ph-daily collect --period <period> --date <date>

如果成功，请输出报告路径和 selected/fetched 数量。
如果失败，请输出命令、退出码、stdout/stderr，并检查 logs/cron.log 是否有相关错误。
不要输出密钥，不要重写筛选或富化逻辑。
```
