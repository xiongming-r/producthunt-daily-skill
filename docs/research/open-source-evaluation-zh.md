# 开源项目评估

日期：2026-05-11

## 结论

第一版采用“参考开源项目重新实现轻量 Worker”的路线，不直接 fork 整个开源项目。

推荐实现方式调整为：

- 借鉴相近项目已经验证过的思路。
- 保留我们自己的模块边界、配置方式、CLI 契约、筛选逻辑和 LLM 输出结构。
- 如果后续复制或紧密改写开源代码，必须保留对应 license 和 attribution。

## 已评估项目

### ViggoZ/producthunt-daily-hot

仓库：https://github.com/ViggoZ/producthunt-daily-hot

许可证：MIT。

值得借鉴的部分：

- 和我们的需求最接近。
- 已经使用 Product Hunt API v2 GraphQL。
- 已经使用 GitHub Actions 做每日自动化。
- 已经生成中文 Markdown 输出。
- Product Hunt token 处理和基础 Markdown 生成方式可作为参考。

不适合直接 fork 的原因：

- 主要逻辑集中在一个脚本里。
- OpenAI 模型调用较硬编码，没有通用 OpenAI-compatible `base_url` 配置。
- 主要做翻译和关键词，不是我们要的结构化中文产品用途分析。
- 没有动态票数/评论质量过滤。
- 没有 raw JSON 和 processed JSON 双产物。
- 更偏 GitHub Actions 运行，而我们需要云服务器 cron 和 agent-friendly CLI。

复用建议：

- 参考它的 Product Hunt GraphQL query 形态。
- 参考它的 GitHub Actions 定时工作流。
- 第一版不 fork 整个仓库。

### zdz72113/DayHot

仓库：https://github.com/zdz72113/DayHot

许可证：Apache-2.0。

值得借鉴的部分：

- 比 `producthunt-daily-hot` 更模块化。
- 拆分了 scraper、translator、Markdown generator、scheduler 和静态站点生成。
- 包含 Product Hunt、GitHub Trending、Hacker News 多源采集。
- 使用 DeepSeek 风格的大模型翻译和 MkDocs 输出。

不适合直接 fork 的原因：

- 范围明显大于 Product Hunt 每日采集器。
- Product Hunt 部分对我们的动态质量过滤和用途解释来说仍然偏浅。
- MkDocs、多源聚合、站点生成不是第一版目标。
- 直接 fork 会带来过多额外配置和维护责任。

复用建议：

- 借鉴 scraper、translator、renderer 的边界划分。
- 第一版不采用多源聚合架构。
- 等日报积累足够多、确实需要浏览历史时，再考虑 MkDocs 或网站化。

### daimajia/huntscreens

仓库：https://github.com/daimajia/huntscreens

许可证：评估时未找到 license 文件。

值得借鉴的部分：

- 对“如何更直观浏览 Product Hunt 产品”很有启发。
- 重点是截图和视觉化浏览，能让用户更快判断产品形态。
- 可作为后续增加截图/视觉预览功能的参考。

不适合直接 fork 的原因：

- 技术栈很重：Next.js、Supabase、Drizzle、Logto、Trigger.dev、Resend、ScreenshotOne、Cloudflare R2、analytics 等。
- 第一版不需要数据库、登录、截图服务、邮件服务或 Web App。
- 没有明确 license 时，不适合复制代码。

复用建议：

- 把截图式产品预览作为第二或第三阶段增强。
- 在 license 明确前，不复制该仓库代码。

## Fork 与参考实现对比

| 方案 | 初始代码量 | 改造复杂度 | 长期匹配度 | 建议 |
| --- | ---: | ---: | ---: | --- |
| fork `producthunt-daily-hot` | 最低 | 中高 | 中 | 不推荐 |
| fork `DayHot` | 低到中 | 高 | 中低 | 不推荐 |
| 参考项目重新实现轻量 Worker | 中 | 低到中 | 高 | 推荐 |

最接近的 `producthunt-daily-hot` 确实能减少初始代码量，但我们需要改的地方刚好都在核心结构上：动态质量过滤、结构化 JSON 产物、OpenAI-compatible LLM 配置、CLI 命令、云服务器 cron、agent 调用接口。直接 fork 会先省一点，后面很容易变成拆旧结构。

## 修订后的实现方向

构建一个“参考开源实现的轻量 Worker”：

```text
开源项目评估记录
  -> Product Hunt API adapter
  -> 动态票数/评论质量过滤
  -> OpenAI-compatible LLM analyst
  -> raw JSON + processed JSON + Markdown report
  -> cloud cron / Codex automation / Hermes / WorkBuddy / Qclaw
```

实施计划中需要明确包含一个小任务：验证参考项目里使用过的 Product Hunt GraphQL 字段，包括 `votesCount`、`commentsCount`、`dailyRank`、URL 字段、日期字段和 media 字段。

## Attribution 规则

- 如果只是参考思路和公开 API 使用方式，在文档中链接评估过的仓库即可。
- 如果复制或紧密改写 MIT / Apache-2.0 项目的代码，需要保留 copyright 和 license notice。
- 不复制没有明确 license 的仓库代码。
