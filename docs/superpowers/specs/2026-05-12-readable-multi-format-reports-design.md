# Readable Multi-Format Reports Design

## Goal

Improve daily report readability while preserving machine-readable JSON. The collector should produce fully Chinese Markdown by default and optionally generate a more readable HTML report when configured.

## User Problems

- Current Markdown mixes English framework labels with Chinese enrichment.
- LLM timeouts are rendered as long operational errors in the user-facing report.
- Markdown is convenient for agents and git, but HTML is easier to read visually.

## Design

### Output Formats

Add `OUTPUT_FORMATS`, a comma-separated environment setting.

Default:

```env
OUTPUT_FORMATS=markdown
```

Supported values:

- `markdown`
- `html`

Users can request one or both:

```env
OUTPUT_FORMATS=markdown,html
```

Invalid or empty formats should raise `ConfigError`.

### Markdown Report

The Markdown report remains the primary text output and keeps the existing path:

```text
reports/daily/YYYY-MM-DD.md
```

All framework labels become Chinese:

- `概览`
- `抓取产品数`
- `入选产品数`
- `AI 解读成功`
- `AI 解读失败`
- `筛选规则`
- `入选产品`
- `Product Hunt 页面`
- `官网 / 跳转链接`
- `票数 / 评论数`
- `筛选原因`

When enrichment fails, the report should show a short Chinese status message, not the raw exception:

```text
AI 解读失败：LLM 响应超时。建议稍后重试，或调高 HTTP_TIMEOUT_SECONDS。
```

Detailed errors remain in `data/processed/YYYY-MM-DD.json`.

### HTML Report

Add a human-readable HTML output:

```text
reports/html/YYYY-MM-DD.html
```

The HTML report should be dependency-free and generated with the Python standard library. It should:

- use UTF-8;
- escape dynamic text with `html.escape`;
- show a clear summary band;
- render selected products as readable sections/cards;
- show product image, links, votes/comments, and Chinese enrichment sections;
- show a friendly AI failure message when enrichment is missing.

No JavaScript or external CSS is required.

### Collector Behavior

The collector always writes raw JSON and processed JSON. It writes report formats according to `settings.output_formats`.

`CollectionResult.paths.markdown_report` remains available for compatibility. Add `html_report` to `OutputPaths`.

### Error Handling

User-facing reports should not expose endpoint URLs, model names, stack traces, or raw timeout exceptions. Those stay in processed JSON for debugging.

The collector should still fail when all selected products fail enrichment. This preserves the existing guard that prevents a fully un-enriched successful report.

### Tests

Add or update tests for:

- config parsing of `OUTPUT_FORMATS`;
- invalid output formats;
- output path includes HTML path;
- Markdown labels are Chinese;
- Markdown uses friendly enrichment failure messages;
- HTML report contains escaped content and Chinese sections;
- collector writes only configured formats;
- collector writes both Markdown and HTML when configured.

## Non-Goals

- No template engine.
- No PDF output.
- No web server.
- No retry system in this change.

