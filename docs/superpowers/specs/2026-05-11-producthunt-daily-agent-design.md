# Product Hunt Daily Agent Collector Design

## Purpose

Build an automated system that collects high-signal products from Product Hunt's daily leaderboard, filters out products that look like vote-only noise, and generates Chinese explanations that help a reader quickly understand each product's actual use cases.

The first version should be boringly reliable: a cloud-server-friendly command line worker that can run from cron. Modern agent tools can then trigger, monitor, and repair that worker without locking the project into any single agent platform.

## Goals

- Fetch Product Hunt daily product data through the official Product Hunt API v2 GraphQL endpoint.
- Keep only products with at least 300 votes and enough discussion relative to their vote count.
- Use an OpenAI-compatible LLM endpoint to translate and explain selected products in Chinese.
- Generate both machine-readable JSON and human-readable Markdown daily reports.
- Make the project easy to resume by maintaining design, plan, and progress documents in the repository.
- Support future orchestration through Codex automations, Hermes, WorkBuddy, Qclaw, or plain server cron.

## Non-Goals

- No web dashboard in the first version.
- No browser scraping as the default data source.
- No dependency on a specific agent runtime for core collection logic.
- No automatic posting to social media, email, or chat in the first version.
- No paid/commercial Product Hunt workflow assumptions. Commercial API usage must be checked with Product Hunt before shipping as a public product.

## Recommended Architecture

Use a deterministic Python CLI worker with small, testable modules:

```text
Product Hunt API
  -> fetcher
  -> normalizer
  -> dynamic discussion filter
  -> LLM enrichment
  -> JSON writer
  -> Markdown report writer
  -> cron or agent trigger
```

The CLI is the stable contract. Any agent can call the same commands:

```bash
ph-daily collect --date today
ph-daily collect --date 2026-05-11
ph-daily backfill --days 7
ph-daily healthcheck
```

This keeps Product Hunt collection, filtering, and reporting deterministic while leaving agent systems free to handle scheduling, monitoring, retries, and human-facing interaction.

## Data Source

The primary source is Product Hunt API v2 GraphQL, authenticated with a bearer token stored in `.env`:

```env
PRODUCT_HUNT_TOKEN=...
```

The worker should fetch daily leaderboard-equivalent data for a target date. The exact query can be finalized during implementation after validating Product Hunt's current GraphQL schema, but the collector must capture at least:

- Product Hunt id
- product name
- tagline
- Product Hunt URL
- website URL if available
- votes count
- comments count
- launch date
- topics or categories if available
- maker information if available
- raw API payload for traceability

If the API cannot provide the same ordering as the public daily leaderboard, the worker should fetch posts for the target date, sort or filter locally by votes, and record the method used in the raw metadata.

## Filtering

The first version uses vote and discussion thresholds:

```text
votes >= MIN_VOTES
comments_count >= max(MIN_COMMENTS, ceil(votes * COMMENT_RATIO))
```

Default values:

```env
MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
```

Examples:

| Votes | Required Comments |
| ---: | ---: |
| 300 | 12 |
| 500 | 20 |
| 1000 | 40 |
| 2000 | 80 |

This rule is intentionally stricter as vote count rises. It is not a perfect anti-fraud detector, but it catches products with high votes and unusually thin discussion, which is the first quality signal the user wants.

The filter result should include an explanation object:

```json
{
  "passed": true,
  "reason": "votes 512 >= 300 and comments 33 >= required 21",
  "required_comments": 21
}
```

Products that fail should be retained in raw data and omitted from the daily report by default.

## LLM Enrichment

The LLM layer must use OpenAI-compatible configuration:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=gpt-4.1-mini
```

The enrichment prompt should produce structured Chinese output, not a direct translation only. Each selected product should include:

- Chinese product name handling: keep official name, translate tagline meaningfully.
- One-sentence summary: what the product does.
- Target users: who would use it.
- Core use cases: concrete scenarios.
- Example workflow: how a user might use it step by step.
- Why it is interesting today: based on votes, discussion, category, and product positioning.
- Caution or uncertainty: note if the available Product Hunt data is thin or ambiguous.

The model output should be stored as structured JSON first, then rendered into Markdown. This avoids making the Markdown report the only source of enriched data.

## Output

The worker writes three primary artifacts:

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
```

Raw JSON stores the API response, run metadata, and failed filter candidates.

Processed JSON stores normalized products, filter decisions, and LLM enrichment.

Markdown report is optimized for human reading. Suggested structure:

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

Generated data and reports are ignored by git by default to avoid committing daily operational output accidentally. The user can later choose to track reports if the repository should become an archive.

## Error Handling

The worker should fail loudly for configuration errors:

- Missing Product Hunt token.
- Missing LLM key when enrichment is enabled.
- Invalid numeric threshold settings.

Runtime failures should be logged with enough context for agent tools to act:

- Product Hunt API errors include status, response body snippet, and date.
- Rate limit responses include retry headers when available.
- LLM errors include model name, base URL host, and product id.
- JSON and Markdown write failures include target path.

The first version can stop the run if LLM enrichment fails for all products. For partial LLM failures, it should still write processed JSON and mark affected products with an enrichment error.

## Agent And Cron Integration

The first deployment target is a cloud server cron job:

```cron
15 9 * * * cd /path/to/project && /path/to/venv/bin/ph-daily collect --date today
```

Agent tools should call the same CLI commands:

- Codex automation: run the daily command, inspect output files, and notify on failure.
- Hermes: act as scheduler, supervisor, or OpenAI-compatible LLM endpoint.
- WorkBuddy or Qclaw: expose natural-language triggers that execute `ph-daily collect`, `backfill`, or `healthcheck`.

The CLI should use conventional exit codes:

- `0`: success
- `1`: configuration or validation failure
- `2`: Product Hunt fetch failure
- `3`: LLM enrichment failure
- `4`: output write failure

This lets any agent or cron wrapper detect status without parsing prose.

## Project Documentation And Progress Tracking

Use these documents as the continuity system:

- `docs/progress.md`: current stage, decisions, next gate.
- `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`: approved design specs.
- `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`: implementation plans with checkboxes.

Each development session should start by reading `docs/progress.md` and the latest active plan.

## Testing Strategy

The implementation plan should use test-driven development for risky logic:

- Config loading and validation.
- Dynamic comment threshold calculation.
- Product normalization from representative API payloads.
- Markdown report rendering.
- LLM response parsing and fallback behavior.
- CLI exit codes for common failure modes.

External network calls should be mocked in unit tests. A manual integration command can validate live Product Hunt and LLM credentials once `.env` is configured.

## First Implementation Scope

The first implementation plan should produce a working CLI that can:

1. Load `.env` configuration.
2. Run `healthcheck`.
3. Fetch a target date from Product Hunt API.
4. Normalize and filter products.
5. Enrich selected products through an OpenAI-compatible LLM endpoint.
6. Write raw JSON, processed JSON, and Markdown report.
7. Provide deployment notes for cron and agent invocation.

That is enough to start daily collection on a cloud server and leaves the door open for dashboard, notifications, or richer anti-spam heuristics later.
