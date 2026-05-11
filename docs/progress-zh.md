# Product Hunt 每日采集器进度索引

## 当前阶段

设计方向已经在对话中确认。当前的下一道关卡是：你需要审阅已经写好的设计文档。

- 英文设计文档：`docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design.md`
- 中文设计文档：`docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design-zh.md`
- 下一步：设计文档确认后，在 `docs/superpowers/plans/` 中创建详细实施计划。

## 关键决策

- 使用 Product Hunt 官方 API v2 GraphQL 作为主要数据源。
- Product Hunt token 放在 `.env` 中，不能提交到 git。
- 第一版做成确定性的 Python CLI Worker，优先部署到云服务器，用 cron 定时运行。
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
logs/YYYY-MM-DD.log
docs/progress.md
docs/progress-zh.md
docs/superpowers/specs/
docs/superpowers/plans/
```

生成的数据、报告、日志和 `.env` 默认不进入 git。源码、配置示例、设计文档和实施计划需要提交到 git。

## 未完成关卡

- [ ] 用户审阅并确认设计文档。
- [ ] 设计确认后创建实施计划。
- [ ] 根据确认后的计划开始开发。
