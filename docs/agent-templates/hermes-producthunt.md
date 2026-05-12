# Hermes Product Hunt 集成模板

Hermes 可以作为调度器，也可以作为 OpenAI-compatible LLM 端点。

## Hermes 作为调度器

```text
请作为调度器执行 Product Hunt <period> 采集：
1. 运行 ph-daily healthcheck。
2. 运行 ph-daily collect --period <period> --date <date>。
3. 成功时报告 selected/fetched 和报告路径。
4. 失败时报告 stdout/stderr，不要继续通知。

约束：只调用 ph-daily，不要直接实现 Product Hunt API、关键词过滤或 LLM 富化。
```

## Hermes 作为 LLM 端点

`.env` 配置片段：

```bash
LLM_BASE_URL=https://your-hermes-endpoint/v1
LLM_API_KEY=your_hermes_api_key
LLM_MODEL=your_hermes_model
```

注意：调度器角色不应读取或改写仓库内 LLM 富化的中间数据；模型端点只负责响应仓库 LLM client 的请求。
