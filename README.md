# Product Hunt Daily Agent Collector

[中文说明](#中文说明)

An agent-friendly Product Hunt daily collector that fetches daily launches through the official Product Hunt GraphQL API, filters high-signal products with a dynamic vote/comment rule, enriches selected products with an OpenAI-compatible LLM, and writes readable Markdown/HTML reports plus structured JSON data.

It is designed for cloud cron jobs and agent workflows such as Codex automations, Hermes, WorkBuddy, and Qclaw: agents schedule and observe the CLI, while this repository owns the deterministic collection, filtering, enrichment, and report generation logic.

## Features

- **Official Product Hunt API**: fetches daily launches through Product Hunt API v2 GraphQL.
- **Dynamic quality filter**: keeps products with `votes >= MIN_VOTES` and enough discussion:
  `comments_count >= max(MIN_COMMENTS, ceil(votes * COMMENT_RATIO))`.
- **OpenAI-compatible LLM enrichment**: supports `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`.
- **Chinese explanatory analysis**: explains product purpose, target users, use cases, workflow examples, why it matters, and caveats.
- **Multiple report formats**: writes Markdown and/or HTML with `OUTPUT_FORMATS=markdown,html`.
- **Machine-readable artifacts**: stores raw Product Hunt payloads and processed enriched records as JSON.
- **Agent-ready CLI**: exposes `healthcheck`, `collect`, and `backfill` commands.
- **Cloud-friendly deployment**: works with simple cron on a VPS or server.

## How It Works

1. Fetch Product Hunt launches for a target date.
2. Normalize API data into local product models.
3. Apply the dynamic vote/comment quality filter.
4. Enrich selected products with an OpenAI-compatible LLM.
5. Write raw JSON, processed JSON, and configured human-readable reports.

```text
Product Hunt API
  -> normalize products
  -> dynamic quality filter
  -> LLM enrichment
  -> data/raw + data/processed + reports/daily + reports/html
```

## Requirements

- Python 3.11+
- Product Hunt API token
- OpenAI-compatible LLM endpoint and API key

For Product Hunt, a `developer_token` from the Product Hunt API dashboard is enough for this collector. Full user OAuth is not required for this read-only use case.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env`:

```env
PRODUCT_HUNT_TOKEN=your_product_hunt_token

LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini

MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
FETCH_LIMIT=100
OUTPUT_FORMATS=markdown,html
OUTPUT_DIR=.
HTTP_TIMEOUT_SECONDS=90
```

## Usage

Run a configuration check:

```bash
ph-daily healthcheck
```

Collect today's launches:

```bash
ph-daily collect --date today
```

Collect a specific date:

```bash
ph-daily collect --date 2026-05-11
```

Backfill recent days:

```bash
ph-daily backfill --days 7
```

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `PRODUCT_HUNT_TOKEN` | required | Product Hunt API token. |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL. |
| `LLM_API_KEY` | required | API key for the LLM endpoint. |
| `LLM_MODEL` | `gpt-4.1-mini` | Model name sent to `/chat/completions`. |
| `MIN_VOTES` | `300` | Minimum vote count for selected products. |
| `COMMENT_RATIO` | `0.04` | Dynamic discussion threshold ratio. |
| `MIN_COMMENTS` | `8` | Minimum discussion floor. |
| `FETCH_LIMIT` | `100` | Maximum Product Hunt candidates fetched before filtering. |
| `OUTPUT_FORMATS` | `markdown` | Comma-separated formats: `markdown`, `html`, or both. |
| `OUTPUT_DIR` | `.` | Root directory for generated artifacts. |
| `HTTP_TIMEOUT_SECONDS` | `30` | HTTP timeout for Product Hunt and LLM requests. |

## Outputs

Generated files are ignored by git by default.

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
reports/html/YYYY-MM-DD.html
```

`data/processed` keeps detailed enrichment errors for debugging. User-facing Markdown and HTML reports show friendly Chinese error messages instead of raw stack-like operational errors.

## Deployment

For a VPS or cloud server:

```bash
git clone <repo-url>
cd <repo-directory>
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
mkdir -p logs
```

Cron example, daily at 09:15 Beijing time:

```cron
15 9 * * * cd /path/to/repo && . .venv/bin/activate && mkdir -p logs && ph-daily collect --date today >> logs/cron.log 2>&1
```

See [docs/deployment-zh.md](docs/deployment-zh.md) for Chinese deployment notes.

## Agent Integration

Agents should call the CLI rather than duplicating business logic.

Recommended commands:

```bash
ph-daily healthcheck
ph-daily collect --date today
ph-daily backfill --days 7
```

Recommended automation behavior:

- On success, report the Markdown/HTML report path and selected product count.
- On failure, report stderr/stdout and the configured cron log if available.
- Do not rewrite the filtering or enrichment rules in the agent prompt.

See [docs/agent-integration-zh.md](docs/agent-integration-zh.md) for Chinese agent integration notes.

## Project Structure

```text
src/ph_daily/
  cli.py            # ph-daily command line entrypoint
  collector.py      # orchestration: fetch, filter, enrich, write outputs
  config.py         # environment loading and validation
  html_report.py    # HTML report renderer
  llm.py            # OpenAI-compatible chat completions adapter
  models.py         # dataclasses for products and enrichment
  producthunt.py    # Product Hunt GraphQL client
  quality.py        # dynamic vote/comment filter
  report.py         # Markdown report renderer
  storage.py        # output paths and writers

tests/              # pytest coverage for core modules
docs/               # design, deployment, agent integration, progress notes
```

## Development

Run tests:

```bash
.venv/bin/python -m pytest
```

Run a local healthcheck with dummy credentials:

```bash
env PRODUCT_HUNT_TOKEN=dummy LLM_API_KEY=dummy .venv/bin/ph-daily healthcheck
```

## Roadmap

- Retry policy for transient LLM timeouts.
- Optional enrichment-only rerun for products that failed in a previous report.
- More output formats, such as email-ready HTML.
- Optional notification hooks for Slack, email, or agent inboxes.

## License

No license has been selected yet.

---

# 中文说明

[Back to English](#product-hunt-daily-agent-collector)

一个面向 Agent 和定时任务的 Product Hunt 每日产品采集器。它通过 Product Hunt 官方 GraphQL API 抓取每日发布产品，用动态票数/评论规则过滤高信号产品，再调用兼容 OpenAI 格式的大模型生成中文解释型分析，最后输出结构化 JSON、Markdown 日报和 HTML 阅读版报告。

这个项目的定位是：业务逻辑留在代码里，Codex 自动化、Hermes、WorkBuddy、Qclaw 等 Agent 工具只负责调度、观察和报告结果。

## 功能特性

- **官方 API 抓取**：使用 Product Hunt API v2 GraphQL。
- **动态质量筛选**：要求 `votes >= MIN_VOTES`，并且评论数满足：
  `comments_count >= max(MIN_COMMENTS, ceil(votes * COMMENT_RATIO))`。
- **兼容 OpenAI 的 LLM 配置**：支持 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`。
- **中文解释型分析**：不是简单翻译，会说明产品用途、目标用户、使用场景、工作流示例、关注理由和注意事项。
- **多格式输出**：通过 `OUTPUT_FORMATS=markdown,html` 同时生成 Markdown 和 HTML。
- **结构化数据留存**：保留 raw JSON 和 processed JSON，方便后续分析和排错。
- **Agent 友好的 CLI**：提供 `healthcheck`、`collect`、`backfill`。
- **适合云服务器部署**：可以直接用 cron 定时运行。

## 工作流程

1. 按日期从 Product Hunt 拉取候选产品。
2. 归一化 API 返回数据。
3. 使用动态票数/评论规则筛选。
4. 对入选产品调用 LLM 生成中文解读。
5. 写入 JSON、Markdown 和 HTML 报告。

```text
Product Hunt API
  -> 产品数据归一化
  -> 动态质量筛选
  -> LLM 中文解读
  -> data/raw + data/processed + reports/daily + reports/html
```

## 环境要求

- Python 3.11+
- Product Hunt API token
- 兼容 OpenAI 的 LLM endpoint 和 API key

Product Hunt 只读采集场景使用 API dashboard 里的 `developer_token` 即可，不需要完整用户 OAuth 授权流程。

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

编辑 `.env`：

```env
PRODUCT_HUNT_TOKEN=your_product_hunt_token

LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini

MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
FETCH_LIMIT=100
OUTPUT_FORMATS=markdown,html
OUTPUT_DIR=.
HTTP_TIMEOUT_SECONDS=90
```

## 使用方式

检查配置：

```bash
ph-daily healthcheck
```

采集当天：

```bash
ph-daily collect --date today
```

采集指定日期：

```bash
ph-daily collect --date 2026-05-11
```

回填最近 7 天：

```bash
ph-daily backfill --days 7
```

## 配置项

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `PRODUCT_HUNT_TOKEN` | 必填 | Product Hunt API token。 |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | 兼容 OpenAI 的接口地址。 |
| `LLM_API_KEY` | 必填 | LLM API key。 |
| `LLM_MODEL` | `gpt-4.1-mini` | `/chat/completions` 使用的模型名。 |
| `MIN_VOTES` | `300` | 入选产品最低票数。 |
| `COMMENT_RATIO` | `0.04` | 动态评论门槛比例。 |
| `MIN_COMMENTS` | `8` | 最低评论数下限。 |
| `FETCH_LIMIT` | `100` | 过滤前最多抓取多少个候选产品。 |
| `OUTPUT_FORMATS` | `markdown` | 输出格式，可选 `markdown`、`html` 或两者。 |
| `OUTPUT_DIR` | `.` | 输出根目录。 |
| `HTTP_TIMEOUT_SECONDS` | `30` | Product Hunt 和 LLM 请求超时时间。 |

## 输出文件

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
reports/html/YYYY-MM-DD.html
```

`data/processed` 会保留详细错误，方便排查。Markdown 和 HTML 面向阅读，会把 LLM 超时等问题转换成中文友好提示。

## 部署

云服务器部署示例：

```bash
git clone <repo-url>
cd <repo-directory>
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
mkdir -p logs
```

北京时间每天 09:15 运行：

```cron
15 9 * * * cd /path/to/repo && . .venv/bin/activate && mkdir -p logs && ph-daily collect --date today >> logs/cron.log 2>&1
```

更详细的中文部署说明见 [docs/deployment-zh.md](docs/deployment-zh.md)。

## Agent 集成

Agent 不应该重写筛选和解读逻辑，只需要调用 CLI。

推荐暴露命令：

```bash
ph-daily healthcheck
ph-daily collect --date today
ph-daily backfill --days 7
```

推荐行为：

- 成功时汇报 Markdown/HTML 报告路径和入选产品数量。
- 失败时汇报 stderr/stdout，以及配置的 cron 日志。
- 不在 Agent prompt 里复制一份筛选或 enrichment 逻辑。

更详细的中文 Agent 集成说明见 [docs/agent-integration-zh.md](docs/agent-integration-zh.md)。

## 项目结构

```text
src/ph_daily/
  cli.py            # CLI 入口
  collector.py      # 抓取、筛选、解读、输出编排
  config.py         # 环境变量加载与校验
  html_report.py    # HTML 报告渲染
  llm.py            # OpenAI-compatible LLM 适配器
  models.py         # 产品与解读数据模型
  producthunt.py    # Product Hunt GraphQL 客户端
  quality.py        # 动态票数/评论筛选规则
  report.py         # Markdown 报告渲染
  storage.py        # 输出路径与文件写入

tests/              # pytest 测试
docs/               # 设计、部署、Agent 集成、进度文档
```

## 开发

运行测试：

```bash
.venv/bin/python -m pytest
```

使用虚拟凭据做本地 healthcheck：

```bash
env PRODUCT_HUNT_TOKEN=dummy LLM_API_KEY=dummy .venv/bin/ph-daily healthcheck
```

## 路线图

- 增加 LLM 超时重试策略。
- 支持只重跑上次失败的 enrichment。
- 增加更适合邮件发送的 HTML 格式。
- 增加 Slack、邮件或 Agent inbox 通知。

## 许可证

当前尚未选择许可证。
