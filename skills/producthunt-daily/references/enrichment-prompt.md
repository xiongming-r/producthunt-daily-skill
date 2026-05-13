# Enrichment Prompt

Use this when `ph-daily collect ... --no-enrichment` has produced filtered Product Hunt data and the agent will perform product analysis itself.

Read `data/processed/...json` and select products where `filter_decision.passed == true`.

For each selected product, produce:

```json
{
  "summary_zh": "一句话说明产品做什么",
  "purpose_zh": "解释产品核心用途、解决的问题和基本工作方式",
  "target_users_zh": ["目标用户1", "目标用户2"],
  "use_cases_zh": ["具体使用场景1", "具体使用场景2"],
  "example_workflow_zh": ["步骤1", "步骤2", "步骤3"],
  "why_interesting_zh": "为什么值得关注",
  "caveat_zh": "注意事项或不确定性"
}
```

Rules:

- Base analysis only on Product Hunt data and generated JSON.
- Do not invent integrations, pricing, users, or capabilities absent from the source.
- Write Chinese analysis.
- Keep uncertainty in `caveat_zh`.
