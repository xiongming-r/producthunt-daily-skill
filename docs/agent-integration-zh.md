# Agent 集成说明

## 核心原则

Agent 负责调度、观察和汇报 CLI 执行结果；Product Hunt 采集、筛选、富化和报告生成等核心业务逻辑都保留在本仓库内。

所有集成工具都应该调用仓库提供的 `ph-daily` CLI，避免在外部 Agent 中单独重写筛选或富化逻辑。这样可以保证手动运行、定时任务和 Agent 调度得到一致结果。

## Codex 自动化

推荐把 Codex 自动化配置为每天运行：

```bash
ph-daily collect --date today
```

推荐任务提示词：

```text
运行 ph-daily collect --date today。
如果失败，请报告 stdout/stderr；如果任务来自 cron，也请检查已配置的 cron 日志，例如 logs/cron.log。
如有生成的 data/raw、data/processed 或 reports/daily 文件，请一起说明这些文件是否完整。
如果成功，请报告生成的 Markdown 日报路径，以及本次入选产品数量。
不要重写 Product Hunt 筛选或富化逻辑，只调用仓库 CLI。
```

注意：`ph-daily healthcheck` 只确认必需配置可以加载，不验证线上 Product Hunt 或 LLM 凭据。Agent 判断集成是否可用时，应以真实 `ph-daily collect --date today` 运行为准。

## Hermes

Hermes 可以承担两种角色：

- 调度器：按计划触发 `ph-daily healthcheck`、`ph-daily collect --date today` 或回填命令。
- OpenAI 兼容大模型端点：作为日报富化步骤使用的大模型服务。

当 Hermes 作为 OpenAI 兼容端点时，在 `.env` 中配置：

```bash
LLM_BASE_URL=https://your-hermes-endpoint/v1
LLM_API_KEY=your_hermes_api_key
LLM_MODEL=your_hermes_model
```

## WorkBuddy / Qclaw

建议向 WorkBuddy 或 Qclaw 暴露以下命令：

```bash
ph-daily healthcheck
ph-daily collect --date today
ph-daily backfill --days 7
```

自然语言触发示例：

```text
帮我运行今天的 Product Hunt 日报采集；如果失败，请报告 stdout/stderr、cron 日志（如果已配置）以及已生成的数据/报告文件状态，再执行健康检查确认配置是否能加载。
```

这些工具可以负责触发、观察、告警和把结果转成人类可读摘要，但不应该在自身内部重新实现筛选、富化或 Markdown 生成逻辑。
