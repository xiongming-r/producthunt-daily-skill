# Product Hunt 每日采集器进度索引

## 当前阶段

当前正在分支 `feat/producthunt-daily-agent-collector` 上实施。任务 1-10 已完成并完成文档记录。任务 11 的本地集成验证已于 2026-05-12 完成：editable install 成功，`ph-daily` 控制台命令可用，完整测试集通过。由于本地 healthcheck 提示缺少 Product Hunt 凭证，本次未运行真实采集。下一道关卡：配置有效真实凭证后，重新运行 healthcheck 和真实采集验证，然后进入最终审阅。

- 英文设计文档：`docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design.md`
- 中文设计文档：`docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design-zh.md`
- 英文开源评估：`docs/research/open-source-evaluation.md`
- 中文开源评估：`docs/research/open-source-evaluation-zh.md`
- 当前实施计划：`docs/superpowers/plans/2026-05-11-producthunt-daily-agent-collector.md`
- 中文部署文档：`docs/deployment-zh.md`
- 中文 Agent 集成文档：`docs/agent-integration-zh.md`
- 下一步：配置有效真实凭证，重新运行任务 11 真实采集验证，然后进入最终审阅。

## 最新验证记录

任务 11 于 2026-05-12 在 `feat/producthunt-daily-agent-collector` 分支执行验证：

- `.venv/bin/python -m pip install -e ".[dev]"` 退出码 0；editable package 安装成功。
- `.venv/bin/python -m pytest -q` 退出码 0；65 个测试通过。
- 安装后 `.venv/bin/ph-daily` 控制台命令存在。
- `.venv/bin/ph-daily healthcheck` 退出码 1；已脱敏输出：`Error: PRODUCT_HUNT_TOKEN is required`。
- 由于 healthcheck 因缺少必需 Product Hunt 配置而失败，本次未运行 `.venv/bin/ph-daily collect --date today`。
- `data/`、`reports/`、`logs/` 下的运行时产物继续保持不追踪。

下一道关卡：在本地环境或 `.env` 中配置有效 `PRODUCT_HUNT_TOKEN`，重新运行 `.venv/bin/ph-daily healthcheck`，只有当退出码为 0 后再运行 `.venv/bin/ph-daily collect --date today`。如果真实采集成功，需要验证 `data/raw/YYYY-MM-DD.json`、`data/processed/YYYY-MM-DD.json`、`reports/daily/YYYY-MM-DD.md` 是否存在，并检查日报中的产品名、votes、comments 和中文章节。

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
- 默认 Product Hunt 候选抓取数量：`FETCH_LIMIT=100`。

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
- [x] 任务 11 本地安装、测试、CLI healthcheck 验证完成。
- [ ] 配置有效 Product Hunt 凭证后完成任务 11 真实采集验证。
- [ ] 最终审阅完成。
