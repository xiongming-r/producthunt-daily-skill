# Product Hunt Daily Collector Progress

## Current Stage

Implementation is in progress on branch `feat/producthunt-daily-agent-collector`. Tasks 1-10 are complete and reviewed/documented. Task 11 local integration verification is complete as of 2026-05-12: editable install succeeds, the `ph-daily` console script is available, and the full test suite passes. Live collection was skipped because the local healthcheck reported missing Product Hunt credentials. Next gate: provide valid live credentials and rerun healthcheck plus live collection, then final review.

- Spec: `docs/superpowers/specs/2026-05-11-producthunt-daily-agent-design.md`
- Research: `docs/research/open-source-evaluation.md`
- Active plan: `docs/superpowers/plans/2026-05-11-producthunt-daily-agent-collector.md`
- Deployment docs: `docs/deployment-zh.md`
- Agent integration docs: `docs/agent-integration-zh.md`
- Next required step: configure valid live credentials, rerun Task 11 live collection verification, then final review.

## Latest Verification

Task 11 verification run on 2026-05-12 from branch `feat/producthunt-daily-agent-collector`:

- `.venv/bin/python -m pip install -e ".[dev]"` exited 0; editable package install succeeded.
- `.venv/bin/python -m pytest -q` exited 0; 65 tests passed.
- `.venv/bin/ph-daily` exists after install.
- `.venv/bin/ph-daily healthcheck` exited 1 with sanitized output: `Error: PRODUCT_HUNT_TOKEN is required`.
- Live collection command `.venv/bin/ph-daily collect --date today` was not run because healthcheck failed due to missing required Product Hunt configuration.
- Generated runtime outputs under `data/`, `reports/`, and `logs/` remain untracked.

Next gate: add a valid `PRODUCT_HUNT_TOKEN` in the local environment or `.env`, rerun `.venv/bin/ph-daily healthcheck`, and only after it exits 0 run `.venv/bin/ph-daily collect --date today`. If live collection succeeds, verify `data/raw/YYYY-MM-DD.json`, `data/processed/YYYY-MM-DD.json`, and `reports/daily/YYYY-MM-DD.md`, including product names, votes, comments, and Chinese report sections.

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
- Default Product Hunt fetch limit: `FETCH_LIMIT=100`.

## Planned Artifact Layout

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
docs/deployment-zh.md
docs/agent-integration-zh.md
docs/progress.md
docs/superpowers/specs/
docs/superpowers/plans/
```

Generated data, reports, optional local logs, and `.env` are ignored by git by default. The collector currently writes raw JSON, processed JSON, and Markdown reports; cron stdout/stderr capture can be configured separately, such as `logs/cron.log`. Source code, config examples, specs, and plans should be committed.

## Open Gates

- [x] User reviews and approves written design spec.
- [x] User reviews and approves open source evaluation notes.
- [x] Implementation plan is created after spec approval.
- [x] Development starts from the approved plan.
- [x] Tasks 1-9 are complete and reviewed.
- [x] Task 10 deployment and agent integration docs are completed.
- [x] Task 11 local install/test/CLI healthcheck verification is completed.
- [ ] Task 11 live collection verification is completed after valid Product Hunt credentials are configured.
- [ ] Final review is completed.
