# Product Hunt 每日采集器进度索引

## 当前阶段

当前正在分支 `feat/producthunt-daily-agent-collector` 上实施。任务 1-9 已完成并通过审阅。任务 10 的部署文档和 Agent 集成文档已在本次更新中完成。下一道关卡：任务 11 真实集成验证，然后进入最终审阅。

- 英文设计文档：`docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design.md`
- 中文设计文档：`docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design-zh.md`
- 英文开源评估：`docs/research/open-source-evaluation.md`
- 中文开源评估：`docs/research/open-source-evaluation-zh.md`
- 当前实施计划：`docs/superpowers/plans/2026-05-11-producthunt-daily-agent-collector.md`
- 中文部署文档：`docs/deployment-zh.md`
- 中文 Agent 集成文档：`docs/agent-integration-zh.md`
- 下一步：任务 11 真实集成验证。

## 关键决策

- 使用 Product Hunt 官方 API v2 GraphQL 作为主要数据源。
- Product Hunt token 放在 `.env` 中，不能提交到 git。
- 第一版做成参考开源项目后的确定性 Python CLI Worker，优先部署到云服务器，用 cron 定时运行。
- 第一版不直接 fork 整个开源项目。
- `ViggoZ/producthunt-daily-hot` 作为最接近的 Product Hunt API 和 GitHub Actions 参考。
- `zdz72113/DayHot` 作为模块边界参考，不采用它的多源聚合大范围架构。
- `daimajia/huntscreens` 只作为未来截图/视觉预览功能的灵感来源。
- Codex 自动化、Hermes、WorkBuddy、Qclaw 等 agent 工具只负责调度、监控、失败补救和人机交互，不承载核心业务逻辑。
- 大模型配置必须兼容 OpenAI 格式，通过 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 配置。
- 每天输出 JSON 数据和适合人阅读的 Markdown 日报。
- 产品筛选规则：
  `votes >= 300`，并且 `comments_count >= max(MIN_COMMENTS, ceil(votes * COMMENT_RATIO))`。
- 默认讨论门槛：
  - `MIN_VOTES=300`
  - `COMMENT_RATIO=0.04`
  - `MIN_COMMENTS=8`

## 计划中的文件结构

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
docs/deployment-zh.md
docs/agent-integration-zh.md
docs/progress.md
docs/progress-zh.md
docs/superpowers/specs/
docs/superpowers/plans/
```

生成的数据、报告、可选本地日志和 `.env` 默认不进入 git。当前采集器会写入 raw JSON、processed JSON 和 Markdown 报告；cron 的 stdout/stderr 可单独配置到 `logs/cron.log` 等文件。源码、配置示例、设计文档和实施计划需要提交到 git。

## 未完成关卡

- [x] 用户审阅并确认设计文档。
- [x] 用户审阅并确认开源项目评估记录。
- [x] 设计确认后创建实施计划。
- [x] 根据确认后的计划开始开发。
- [x] 任务 1-9 已完成并通过审阅。
- [x] 任务 10 部署文档和 Agent 集成文档完成。
- [ ] 任务 11 真实集成验证完成。
- [ ] 最终审阅完成。
