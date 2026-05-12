# Product Hunt Daily Collector Progress

## Current Stage

Implementation is in progress on branch `feat/producthunt-daily-agent-collector`. Tasks 1-9 are complete and reviewed. Task 10 deployment and agent integration documentation is complete in this update. Next gate: Task 11 live integration verification, then final review.

- Spec: `docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design.md`
- Research: `docs/research/open-source-evaluation.md`
- Active plan: `docs/superpowers/plans/2026-05-11-producthunt-daily-agent-collector.md`
- Deployment docs: `docs/deployment-zh.md`
- Agent integration docs: `docs/agent-integration-zh.md`
- Next required step: Task 11 live integration verification.

## Key Decisions

- Use Product Hunt official API v2 GraphQL as the primary data source.
- Store the Product Hunt token in `.env`; never commit secrets.
- First version runs as an open-source-informed deterministic Python CLI worker on a cloud server cron schedule.
- Do not fork an entire open source project for the first implementation.
- Use `ViggoZ/producthunt-daily-hot` as the closest Product Hunt API and GitHub Actions reference.
- Use `zdz72113/DayHot` as a module-boundary reference, not as a broad multi-source base.
- Treat `daimajia/huntscreens` as inspiration for future screenshot-based product previews only.
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
docs/deployment-zh.md
docs/agent-integration-zh.md
docs/progress.md
docs/superpowers/specs/
docs/superpowers/plans/
```

Generated data, reports, logs, and `.env` are ignored by git by default. Source code, config examples, specs, and plans should be committed.

## Open Gates

- [x] User reviews and approves written design spec.
- [x] User reviews and approves open source evaluation notes.
- [x] Implementation plan is created after spec approval.
- [x] Development starts from the approved plan.
- [x] Tasks 1-9 are complete and reviewed.
- [x] Task 10 deployment and agent integration docs are completed.
- [ ] Task 11 live integration verification is completed.
- [ ] Final review is completed.
