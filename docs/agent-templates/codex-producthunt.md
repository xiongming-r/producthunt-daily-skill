# Codex Product Hunt 执行模板

用途：在 Codex 中执行一次采集、排查失败或总结产物。适合 repo-local 的一次性任务。

## 提示词模板

```text
在当前仓库执行 Product Hunt <period> 采集。

约束：
- 不修改 src/、tests/、README.md、.env.example。
- 不输出 .env、token 或 API key。
- 不重写 Product Hunt 采集、过滤、LLM 富化或报告生成逻辑。

步骤：
1. 运行 ph-daily healthcheck。
2. 运行 ph-daily collect --period <period> --date <date>。
3. 汇总 selected/fetched 数量、Markdown / HTML 报告路径、raw / processed JSON 路径。
4. 如果失败，汇总命令、退出码、stdout/stderr，以及可用的 cron 日志片段。
```

## 常用命令

```bash
ph-daily collect --period daily --date today
ph-daily collect --period weekly --date today
ph-daily collect --period monthly --date today
ph-daily collect --period yearly --date today
```
