# Open Source Evaluation

Date: 2026-05-11

## Decision

Use existing open source projects as references, but do not fork an entire project for the first implementation.

The recommended implementation remains a small Python CLI worker, adjusted to be open-source-informed:

- Reuse proven ideas from nearby projects.
- Keep our own module boundaries, configuration, CLI contract, filter logic, and LLM output schema.
- Preserve attribution if any source code is copied later.

## Projects Reviewed

### ViggoZ/producthunt-daily-hot

Repository: https://github.com/ViggoZ/producthunt-daily-hot

License: MIT.

Relevant strengths:

- Very close to this project's domain.
- Uses Product Hunt API v2 GraphQL.
- Uses GitHub Actions for daily automation.
- Generates Chinese Markdown output.
- Provides useful examples for Product Hunt token handling and basic Markdown report generation.

Limitations for this project:

- Main logic is concentrated in a single script.
- OpenAI model usage is mostly hardcoded and does not expose a generic OpenAI-compatible `base_url`.
- It translates product text, but does not produce the structured Chinese product analysis we want.
- It does not implement dynamic vote/comment quality filtering.
- It does not write separate raw JSON and processed JSON artifacts.
- It is GitHub Actions oriented, while this project needs cloud cron and agent-friendly CLI commands.

Reuse guidance:

- Use its Product Hunt GraphQL query shape as a reference.
- Use its GitHub Actions schedule as a reference for a future optional workflow.
- Do not fork the full repository for the first implementation.

### zdz72113/DayHot

Repository: https://github.com/zdz72113/DayHot

License: Apache-2.0.

Relevant strengths:

- More modular than `producthunt-daily-hot`.
- Separates scrapers, translator, Markdown generator, scheduler, and static site builder.
- Includes Product Hunt, GitHub Trending, and Hacker News collection.
- Uses DeepSeek-style LLM translation and MkDocs output.

Limitations for this project:

- Scope is much broader than the Product Hunt daily collector.
- Product Hunt handling is shallow for our specific quality filtering and enrichment needs.
- MkDocs, multi-source aggregation, and website generation are not first-version requirements.
- Directly forking it would bring extra responsibilities and configuration surface area.

Reuse guidance:

- Borrow the idea of clear scraper, translator, and renderer boundaries.
- Do not adopt its multi-source architecture in the first version.
- Do not include MkDocs until reports have enough history to justify a website.

### daimajia/huntscreens

Repository: https://github.com/daimajia/huntscreens

License: no license file found during evaluation.

Relevant strengths:

- Strong inspiration for visual product discovery.
- Uses Product Hunt as a source and focuses on screenshots to make product browsing more intuitive.
- Shows a possible later path for visual previews.

Limitations for this project:

- Much heavier stack: Next.js, Supabase, Drizzle, Logto, Trigger.dev, Resend, ScreenshotOne, Cloudflare R2, and analytics.
- The first version does not need a database, auth, screenshot service, email service, or web app.
- No license file was found, so code copying is not appropriate without further confirmation.

Reuse guidance:

- Treat screenshot-based product preview as a possible Phase 2 or Phase 3 enhancement.
- Do not copy code from this repository unless licensing is clarified.

## Fork vs Reference Assessment

| Approach | Initial Code Amount | Change Complexity | Long-Term Fit | Recommendation |
| --- | ---: | ---: | ---: | --- |
| Fork `producthunt-daily-hot` | Lowest | Medium-high | Medium | Not recommended |
| Fork `DayHot` | Low-medium | High | Low-medium | Not recommended |
| Reference projects and implement focused worker | Medium | Low-medium | High | Recommended |

The closest fork, `producthunt-daily-hot`, would save initial lines of code but require restructuring around exactly the areas this project cares about: dynamic quality filtering, structured JSON artifacts, OpenAI-compatible LLM configuration, CLI commands, cloud cron operation, and agent integration.

## Revised Implementation Direction

Build an open-source-informed worker:

```text
Open source research notes
  -> Product Hunt API adapter
  -> dynamic vote/comment quality filter
  -> OpenAI-compatible LLM analyst
  -> raw JSON + processed JSON + Markdown report
  -> cloud cron / Codex automation / Hermes / WorkBuddy / Qclaw
```

The implementation plan should explicitly include a small task that validates Product Hunt GraphQL fields used by the reference projects, including `votesCount`, `commentsCount`, `dailyRank`, URL fields, dates, and media fields.

## Attribution Policy

- If implementation only follows ideas and public API usage patterns, link to the evaluated repositories in documentation.
- If code is copied or closely adapted from MIT or Apache-2.0 sources, preserve copyright and license notices.
- Do not copy code from repositories without a clear license.
