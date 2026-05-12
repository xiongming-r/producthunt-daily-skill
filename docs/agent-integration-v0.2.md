# v0.2 Agent 集成文档与模板

本文档用于 v0.2 的 Agent 集成切片：在保留脚本模式的前提下，把 Product Hunt 采集器接入 WorkBuddy、Qclaw、Hermes、Codex 和 Claude Code。核心原则是：Agent 负责调度、编排、观察、二次富化和交付；采集、Product Hunt 官方过滤、本地关键词过滤、质量阈值、LLM 富化和报告生成仍由仓库内的 `ph-daily` CLI 与 Python 模块负责。

不要在外部 Agent 里重写 Product Hunt 筛选、关键词过滤或报告生成逻辑。所有集成都应优先调用 `ph-daily`，这样手动运行、cron、服务器任务和 Agent 调度得到的是同一套结果。

## 当前边界

v0.2 目标能力包括：

- 周期采集：`daily`、`weekly`、`monthly`、`yearly`。
- Product Hunt 官方过滤：`featured`、`order`、`topic`、`url`、`twitterUrl`。
- 本地关键词过滤：include / exclude keywords。
- OpenAI-compatible LLM 配置：可接 OpenAI、Hermes 或其他兼容 `/v1` Chat Completions 的服务。
- Agent 集成：WorkBuddy、Qclaw、Hermes、Codex、Claude Code。

本文示例里的 v0.2 周期和过滤参数已经由当前 CLI 支持。外部 Agent 应直接传入 CLI 参数，或通过 `.env` 固化默认值，不要创建同名脚本来重复实现这些能力。

## 集成模式一：CLI 手动运行

先做配置健康检查：

```bash
ph-daily healthcheck
```

`healthcheck` 只验证配置能加载，不验证 Product Hunt token 或 LLM key 是否在线可用。真实验收应至少跑一次采集：

```bash
ph-daily collect --date today
```

v0.2 周期采集示例：

```bash
ph-daily collect --period daily --date today
ph-daily collect --period weekly --date 2026-05-12
ph-daily collect --period monthly --date 2026-05-12
ph-daily collect --period yearly --date 2026-05-12
```

v0.2 Product Hunt 官方过滤示例：

```bash
ph-daily collect --period weekly --date today --featured true --order VOTES
ph-daily collect --period monthly --date today --topic artificial-intelligence
ph-daily collect --period daily --date today --url https://example.com
ph-daily collect --period daily --date today --twitter-url https://twitter.com/example
```

回填仍以脚本模式为主：

```bash
ph-daily backfill --days 7
```

## 集成模式二：cron / server mode

cron 适合稳定的“无人值守采集”。Agent 不需要替代 cron，但可以读取日志、重试失败任务、总结产物状态。

```cron
15 9 * * * cd /path/to/repo && . .venv/bin/activate && mkdir -p logs && ph-daily collect --period daily --date today >> logs/cron.log 2>&1
30 9 * * 1 cd /path/to/repo && . .venv/bin/activate && mkdir -p logs && ph-daily collect --period weekly --date today >> logs/cron.log 2>&1
45 9 1 * * cd /path/to/repo && . .venv/bin/activate && mkdir -p logs && ph-daily collect --period monthly --date today >> logs/cron.log 2>&1
0 10 1 1 * cd /path/to/repo && . .venv/bin/activate && mkdir -p logs && ph-daily collect --period yearly --date today >> logs/cron.log 2>&1
```

建议服务器时区固定为 `Asia/Shanghai`。如果服务器使用 UTC，应换算 cron 时间，避免日报日期和实际业务日期错位。

## OpenAI-compatible LLM 配置

仓库使用 OpenAI-compatible LLM 设置，因此 Hermes 或其他兼容服务只需要替换 base URL、key 和 model。

```bash
PRODUCT_HUNT_TOKEN=your_product_hunt_token

LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini
```

接入 Hermes 作为 LLM 端点：

```bash
LLM_BASE_URL=https://your-hermes-endpoint/v1
LLM_API_KEY=your_hermes_api_key
LLM_MODEL=your_hermes_model
```

注意事项：

- `LLM_BASE_URL` 建议填到 `/v1`，不要带最后的 `/chat/completions`。
- 不要把 `.env`、token 或 API key 发给 Agent 对话上下文。
- 如果 LLM 富化失败但 Product Hunt 采集成功，Agent 应报告 stdout/stderr 和已生成文件，不要自行补写 processed JSON。

## v0.2 过滤配置片段

当 CLI 参数不方便由外部调度器传入时，建议用 `.env` 固化默认规则。

```bash
# 默认兼容 v0.1
MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
FETCH_LIMIT=100

# v0.2 周期阈值
DAILY_MIN_VOTES=300
DAILY_COMMENT_RATIO=0.04
DAILY_MIN_COMMENTS=8
DAILY_FETCH_LIMIT=100

WEEKLY_MIN_VOTES=800
WEEKLY_COMMENT_RATIO=0.035
WEEKLY_MIN_COMMENTS=20
WEEKLY_FETCH_LIMIT=150

MONTHLY_MIN_VOTES=1000
MONTHLY_COMMENT_RATIO=0.03
MONTHLY_MIN_COMMENTS=40
MONTHLY_FETCH_LIMIT=200

YEARLY_MIN_VOTES=5000
YEARLY_COMMENT_RATIO=0.02
YEARLY_MIN_COMMENTS=120
YEARLY_FETCH_LIMIT=300

# Product Hunt 官方 posts 过滤
PRODUCT_HUNT_FEATURED=true
PRODUCT_HUNT_ORDER=VOTES
PRODUCT_HUNT_TOPIC=artificial-intelligence
PRODUCT_HUNT_URL=
PRODUCT_HUNT_TWITTER_URL=

# 本地关键词过滤，逗号分隔，小写匹配更容易排查
INCLUDE_KEYWORDS=ai,agent,developer
EXCLUDE_KEYWORDS=crypto,gambling

OUTPUT_FORMATS=markdown,html
OUTPUT_DIR=.
HTTP_TIMEOUT_SECONDS=30
```

默认建议：

- 日报保留较宽筛选，便于观察新品。
- 月报和年报提高 `MIN_VOTES`，默认目标分别是 1000 和 5000 票级别的高信号产品。
- `INCLUDE_KEYWORDS` 会把不含任一关键词的产品排除；为空表示不过滤。
- `EXCLUDE_KEYWORDS` 命中任一关键词即排除。

## Agent 作为调度器 / 编排器

Agent 适合处理“什么时候跑、跑什么、失败后怎么报告”。

通用调度提示词：

```text
你是 Product Hunt 采集任务的调度器。请只调用仓库提供的 ph-daily CLI，不要重写采集、筛选、LLM 富化或报告生成逻辑。

任务：
1. 先运行 ph-daily healthcheck。
2. 如果配置正常，运行指定采集命令：<在这里填 collect 命令>。
3. 如果失败，报告命令、退出码、stdout、stderr，并检查 logs/cron.log 是否有相关错误。
4. 如果成功，报告 Markdown / HTML 报告路径、raw / processed JSON 路径，以及 selected/fetched 数量。
5. 不要输出密钥、.env 原文或 token。
```

常见编排：

```text
每天 09:15 跑 daily；每周一 09:30 跑 weekly；每月 1 日 09:45 跑 monthly；每年 1 月 1 日 10:00 跑 yearly。每次只调用 ph-daily collect，失败时附 stdout/stderr 和日志摘要。
```

## Agent 作为富化层

仓库内 LLM 富化负责每个产品的基础摘要和判断。Agent 的二次富化应站在报告之后做“消费层加工”，不要回写核心数据文件，除非未来另有明确接口。

适合 Agent 做的事情：

- 把日报改写成老板摘要、投研摘要、开发者摘要。
- 对入选产品做行业聚类、机会假设、竞品提示。
- 根据报告内容生成飞书、Slack、邮件或 Notion 消息。
- 读取多日 / 多周报告，做趋势观察。

不建议 Agent 做的事情：

- 直接调用 Product Hunt API 并绕过 `ph-daily`。
- 自己重新实现 votes/comments/keyword 过滤。
- 修改 `data/raw` 或 `data/processed` 来“修复”结果。
- 把 Agent 自己的判断伪装成本仓库采集器输出。

二次富化提示词：

```text
请读取本次 ph-daily 生成的报告：<报告路径>。
输出三部分：
1. 今日最值得关注的 3 个产品，每个产品说明用户痛点、亮点和可能风险。
2. 对开发者 / 创业者的机会提示。
3. 明天应重点观察的关键词。

要求：只基于报告内容总结，不要猜测报告里没有的数据；不要修改 data/raw、data/processed 或 reports 文件。
```

## Skillization

如果 WorkBuddy、Qclaw、Codex 或 Claude Code 支持“技能 / skill / command / workflow”，建议把集成封装成一个轻量技能，而不是把长提示词散落在多个任务里。

技能边界：

- 输入：周期、日期、可选 Product Hunt 过滤条件、可选关键词。
- 动作：运行 `ph-daily healthcheck` 和 `ph-daily collect ...`。
- 输出：命令结果、报告路径、入选数量、失败诊断。
- 禁止：保存密钥、重写核心逻辑、生成未定义的可执行脚本。

技能说明片段：

```text
Skill: producthunt-collector
Purpose: 调度本仓库 ph-daily CLI，生成 Product Hunt daily/weekly/monthly/yearly 报告。
Inputs: period, date, featured, order, topic, include_keywords, exclude_keywords。
Rules:
- Only call ph-daily CLI from this repository.
- Do not reimplement Product Hunt filters or LLM enrichment.
- Never print .env secrets.
- On failure, return stdout/stderr and relevant log excerpts.
```

## 各 Agent 接入建议

### WorkBuddy

WorkBuddy 适合做日常运营调度和结果分发。建议暴露固定动作：

```bash
ph-daily healthcheck
ph-daily collect --period daily --date today
ph-daily collect --period weekly --date today
ph-daily collect --period monthly --date today
```

自然语言触发：

```text
帮我运行今天的 Product Hunt 日报采集。成功后给出报告路径和入选产品数量；失败后给出 stdout/stderr 和 logs/cron.log 摘要。不要重写筛选逻辑，只调用 ph-daily。
```

### Qclaw

Qclaw 适合做更明确的任务流：检查、采集、验收、通知。

```text
执行 Product Hunt 周报流程：
1. 在仓库根目录运行 ph-daily healthcheck。
2. 运行 ph-daily collect --period weekly --date today。
3. 汇总 selected/fetched 数量和报告路径。
4. 如果失败，保留错误上下文，停止后续通知。
```

### Hermes

Hermes 可以有两种角色：

- 调度器：触发 `ph-daily` 并报告结果。
- LLM 端点：通过 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 被仓库调用。

当 Hermes 同时承担两种角色时，要区分“控制平面”和“模型平面”：调度器不要直接读写 LLM 富化结果，模型端点只响应仓库内 LLM client 的请求。

### Codex

Codex 适合在仓库内做变更、排查和一次性执行。

```text
在当前仓库执行 Product Hunt 月报采集：
- 不修改 src、tests、README 或配置文件。
- 只运行 ph-daily healthcheck 和 ph-daily collect --period monthly --date today。
- 报告命令输出、生成文件路径和异常诊断。
- 不要打印 .env 密钥。
```

### Claude Code

Claude Code 适合封装 repo-local command 或 skill。建议把命令写成文档模板，不要在没有需求时新增脚本。

```text
Use the repository ph-daily CLI as the only execution surface.
Run:
1. ph-daily healthcheck
2. ph-daily collect --period <period> --date <date>
Then summarize selected/fetched counts and generated report paths.
Never reimplement Product Hunt fetching, filters, or report rendering outside the repository code.
```

## 输出路径约定

日报兼容 v0.1 路径：

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
reports/html/YYYY-MM-DD.html
```

非日报使用周期路径：

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

Agent 验收时优先报告 `reports/...`，再报告 `data/raw` 和 `data/processed`。不要承诺存在每日应用日志；如果 cron 配置了 `logs/cron.log`，再读取该文件排障。

## 文档模板

可复用模板位于：

- `docs/agent-templates/workbuddy-producthunt.md`
- `docs/agent-templates/qclaw-producthunt.md`
- `docs/agent-templates/hermes-producthunt.md`
- `docs/agent-templates/codex-producthunt.md`
- `docs/agent-templates/claude-code-producthunt.md`

这些文件是 doc-only 模板，不是可执行脚本。
