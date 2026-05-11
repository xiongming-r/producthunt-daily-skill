# Product Hunt 每日 Agent 采集器设计文档

## 目标说明

构建一个自动化系统，每天从 Product Hunt 的 daily leaderboard 中收集高信号产品，过滤掉那些“票数很高但讨论很少、疑似刷票”的产品，并用中文生成更容易理解的产品说明。

这个系统的重点不是简单翻译 Product Hunt 文案，而是解释产品到底能做什么、谁会用、在什么场景下有用，并给出具体案例。第一版要优先保证稳定、可复跑、方便放到云服务器上定时执行，同时参考已有开源项目，避免闭门重复造轮子。Codex 自动化、Hermes、WorkBuddy、Qclaw 等现代 agent 工具可以参与调度、监控和补救，但核心采集逻辑不绑定任何单一 agent 平台。

## 建设目标

- 通过 Product Hunt 官方 API v2 GraphQL 获取每日产品数据。
- 只保留至少 300 票，并且讨论数量与票数匹配的产品。
- 使用兼容 OpenAI 格式的大模型接口，对筛选后的产品进行中文翻译和用途解释。
- 每天生成机器可读的 JSON 数据，以及适合人阅读的 Markdown 日报。
- 在仓库中维护设计文档、实施计划和进度索引，确保每次继续开发时都能准确衔接。
- 在实施前记录已评估开源项目和复用边界。
- 支持未来由 Codex 自动化、Hermes、WorkBuddy、Qclaw 或普通服务器 cron 调度。

## 非目标

- 第一版不做 Web Dashboard。
- 默认不使用浏览器爬虫。
- 第一版不直接 fork 整个开源项目。
- 核心采集逻辑不依赖某一个特定 agent runtime。
- 第一版不自动发送到社交媒体、邮件或聊天工具。
- 不默认假设 Product Hunt API 可以商用。如果未来要做公开商业产品，需要先向 Product Hunt 确认授权。

## 推荐架构

采用参考开源项目后的确定性 Python CLI Worker，并拆成多个小而可测试的模块：

```text
开源项目评估记录
  -> Product Hunt API
  -> 数据拉取器
  -> 数据标准化
  -> 动态讨论门槛过滤
  -> LLM 增强解释
  -> JSON 写入
  -> Markdown 日报生成
  -> cron 或 agent 触发
```

CLI 是整个系统的稳定调用契约。任何 agent 都可以调用同一组命令：

```bash
ph-daily collect --date today
ph-daily collect --date 2026-05-11
ph-daily backfill --days 7
ph-daily healthcheck
```

这样做的好处是：Product Hunt 采集、筛选、报告生成都保持确定性；agent 系统可以自由负责调度、监控、重试和人机交互，不会把核心价值锁死在某一个工具里。

## 开源复用策略

第一版应参考相近开源项目，但不直接 fork 整个仓库。详细评估记录放在：

- `docs/research/open-source-evaluation.md`
- `docs/research/open-source-evaluation-zh.md`

复用方向：

- `ViggoZ/producthunt-daily-hot` 作为最接近的 Product Hunt GraphQL、每日自动化和 Markdown 输出参考。
- `zdz72113/DayHot` 作为 scraper、translator、renderer 模块边界的参考。
- `daimajia/huntscreens` 只作为未来截图式产品预览的灵感来源。

如果后续复制或紧密改写开源代码，必须保留源项目的 license 和 attribution notice。没有明确 license 的仓库不能复制代码。

## 数据源

主要数据源是 Product Hunt API v2 GraphQL，通过 `.env` 中的 bearer token 认证：

```env
PRODUCT_HUNT_TOKEN=...
```

Worker 应该为目标日期获取与 daily leaderboard 等价或接近的数据。具体 GraphQL query 需要在实施阶段根据 Product Hunt 当前 schema 验证，并和已评估开源项目使用过的字段做对照。采集器至少需要保留以下字段：

- Product Hunt id
- 产品名称
- tagline
- Product Hunt 链接
- 官网链接，如果 API 提供
- 票数
- 评论数
- daily rank，如果 API 提供
- 发布日期
- topic 或分类，如果 API 提供
- maker 信息，如果 API 提供
- 原始 API payload，方便追踪和排查

如果 API 无法直接提供与公开 daily leaderboard 完全一致的排序，Worker 应该获取目标日期的 posts，并在本地按票数排序或过滤，同时在 raw metadata 中记录使用了什么方法。

## 筛选规则

第一版使用票数和讨论数量双阈值：

```text
votes >= MIN_VOTES
comments_count >= max(MIN_COMMENTS, ceil(votes * COMMENT_RATIO))
```

默认配置：

```env
MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
```

示例：

| 票数 | 需要的最低评论数 |
| ---: | ---: |
| 300 | 12 |
| 500 | 20 |
| 1000 | 40 |
| 2000 | 80 |

这个规则会随着票数升高而提高评论要求。它不是完美的反作弊算法，但能过滤掉一类明显异常的产品：票数很高，讨论却异常稀薄。这正是第一版最需要的质量信号。

筛选结果需要包含解释对象：

```json
{
  "passed": true,
  "reason": "votes 512 >= 300 and comments 33 >= required 21",
  "required_comments": 21
}
```

未通过筛选的产品仍然保存在 raw 数据中，但默认不进入每日 Markdown 报告。

## LLM 增强解释

LLM 层必须使用 OpenAI-compatible 配置：

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=gpt-4.1-mini
```

增强提示词应该输出结构化中文内容，而不是只做直译。每个入选产品至少包括：

- 产品名称处理：保留官方名称，对 tagline 做自然中文解释。
- 一句话总结：这个产品到底做什么。
- 目标用户：哪些人或团队会用它。
- 核心使用场景：具体在哪些场景有用。
- 示例流程：用户可能如何一步步使用它。
- 今日值得关注的原因：结合票数、讨论、分类和产品定位说明。
- 注意事项或不确定性：如果 Product Hunt 上的信息较少，需要明确提示。

模型输出应先保存为结构化 JSON，再渲染为 Markdown。这样 Markdown 不是唯一数据源，后续做搜索、汇总或 Dashboard 时更容易复用。

## 输出文件

Worker 每天写入三个主要产物：

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
```

Raw JSON 保存 API 响应、运行元数据，以及未通过筛选的候选产品。

Processed JSON 保存标准化产品、筛选决策和 LLM 增强解释。

Markdown 日报面向人阅读，建议结构如下：

```markdown
# Product Hunt Daily Report - YYYY-MM-DD

## Summary

- Products fetched:
- Products passing filters:
- Filter rule:

## Selected Products

### Product Name

- Product Hunt:
- Website:
- Votes / Comments:
- What it does:
- Who it is for:
- Use cases:
- Example:
- Why it is worth attention:
- Caveat:
```

生成数据和报告默认被 git 忽略，避免每天运行时误提交大量产物。未来如果你希望这个仓库也作为日报归档，可以再决定是否追踪 `reports/daily/`。

## 错误处理

配置错误应该明确失败：

- 缺少 Product Hunt token。
- 开启 LLM 增强时缺少 LLM key。
- 数值型阈值配置无效。

运行时错误需要记录足够上下文，方便 agent 工具判断和补救：

- Product Hunt API 错误要包含状态码、响应片段和日期。
- 遇到 rate limit 时记录可用的 retry header。
- LLM 错误要包含模型名称、base URL host 和 product id。
- JSON 或 Markdown 写入失败时记录目标路径。

第一版中，如果所有产品的 LLM 增强都失败，可以让整次运行失败。若只有部分产品增强失败，则仍然写出 processed JSON，并在对应产品上标记 enrichment error。

## Agent 与 Cron 集成

第一部署目标是云服务器 cron：

```cron
15 9 * * * cd /path/to/project && /path/to/venv/bin/ph-daily collect --date today
```

Agent 工具调用同一组 CLI 命令：

- Codex 自动化：每天运行命令，检查输出文件，失败时提醒用户。
- Hermes：作为调度器、监督器，或作为 OpenAI-compatible LLM endpoint。
- WorkBuddy 或 Qclaw：通过自然语言触发 `ph-daily collect`、`backfill`、`healthcheck` 等命令。

CLI 使用常规退出码：

- `0`：成功
- `1`：配置或校验失败
- `2`：Product Hunt 拉取失败
- `3`：LLM 增强失败
- `4`：输出写入失败

这样任何 agent 或 cron wrapper 都能通过退出码判断运行状态，不需要解析自然语言日志。

## 项目文档与进度追踪

使用以下文档作为长期衔接系统：

- `docs/progress.md`：英文进度索引，记录当前阶段、关键决策和下一道关卡。
- `docs/progress-zh.md`：中文进度索引，方便人工阅读。
- `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`：英文设计文档。
- `docs/superpowers/specs/YYYY-MM-DD-<topic>-design-zh.md`：中文设计文档。
- `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`：实施计划，使用 checkbox 跟踪任务。

每次开发开始前，应先阅读 `docs/progress.md` 或 `docs/progress-zh.md`，再阅读最新的 active plan。

## 测试策略

实施计划应对高风险逻辑使用测试驱动开发：

- 配置加载与校验。
- 动态评论门槛计算。
- 从代表性 API payload 中标准化产品数据。
- Markdown 报告渲染。
- LLM 响应解析与 fallback 行为。
- 常见失败场景下的 CLI 退出码。

单元测试中应 mock 外部网络调用。配置好 `.env` 后，可以再提供一个手动 integration command，用于验证真实 Product Hunt 和 LLM 凭证。

## 第一版实施范围

第一份实施计划应交付一个可工作的 CLI，能够：

1. 加载 `.env` 配置。
2. 运行 `healthcheck`。
3. 验证 Product Hunt GraphQL 字段是否符合当前 API schema 或真实查询结果。
4. 从 Product Hunt API 获取目标日期数据。
5. 标准化并筛选产品。
6. 通过 OpenAI-compatible LLM endpoint 增强解释入选产品。
7. 写出 raw JSON、processed JSON 和 Markdown 日报。
8. 提供 cron 和 agent 调用方式的部署说明。

完成这些就足够开始在云服务器上做每日采集。后续可以再扩展 Dashboard、通知系统或更复杂的反刷票启发式规则。
