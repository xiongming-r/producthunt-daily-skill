# Product Hunt Daily Collector Progress

## Current Stage

Design approved at conversation level. The next gate is user review of the written spec:

- Spec: `docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design.md`
- Next required step: after spec review approval, create the implementation plan in `docs/superpowers/plans/`

## Key Decisions

- Use Product Hunt official API v2 GraphQL as the primary data source.
- Store the Product Hunt token in `.env`; never commit secrets.
- First version runs as a deterministic Python CLI worker on a cloud server cron schedule.
- Agent tools such as Codex automations, Hermes, WorkBuddy, and Qclaw should call the same CLI commands instead of owning core business logic.
- LLM access must support OpenAI-compatible configuration through `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`.
- Output daily JSON data and a human-readable Markdown report.
- Filter products with `votes >= 300` and dynamic discussion threshold:
  `comments_count >= max(MIN_COMMENTS, ceil(votes * COMMENT_RATIO))`.
- Default discussion settings:
  - `MIN_VOTES=300`
  - `COMMENT_RATIO=0.04`
  - `MIN_COMMENTS=8`

## Planned Artifact Layout

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
logs/YYYY-MM-DD.log
docs/progress.md
docs/superpowers/specs/
docs/superpowers/plans/
```

Generated data, reports, logs, and `.env` are ignored by git by default. Source code, config examples, specs, and plans should be committed.

## Open Gates

- [ ] User reviews and approves written design spec.
- [ ] Implementation plan is created after spec approval.
- [ ] Development starts from the approved plan.
