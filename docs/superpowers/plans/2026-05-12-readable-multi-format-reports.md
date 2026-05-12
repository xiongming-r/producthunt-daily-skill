# Readable Multi-Format Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Product Hunt daily reports easier to read by fully localizing Markdown, hiding raw LLM errors from user-facing reports, and adding optional HTML output.

**Architecture:** Extend configuration with `OUTPUT_FORMATS`, extend storage paths with `reports/html/YYYY-MM-DD.html`, keep Markdown rendering in `report.py`, add dependency-free HTML rendering in `html_report.py`, and let `Collector` write selected report formats.

**Tech Stack:** Python stdlib (`dataclasses`, `html`, `pathlib`), existing pytest suite, existing CLI/config/collector modules.

---

## File Structure

- Modify `src/ph_daily/config.py`: parse and validate `OUTPUT_FORMATS`.
- Modify `src/ph_daily/storage.py`: add `html_report` to `OutputPaths`.
- Modify `src/ph_daily/report.py`: Chinese labels and friendly enrichment failure text.
- Create `src/ph_daily/html_report.py`: dependency-free HTML renderer.
- Modify `src/ph_daily/collector.py`: write configured report formats.
- Modify `.env.example`, `README.md`, `docs/deployment-zh.md`: document `OUTPUT_FORMATS`.
- Modify tests: `tests/test_config.py`, `tests/test_report.py`, `tests/test_collector.py`.
- Add `tests/test_html_report.py`.

## Task 1: Config And Paths

**Files:**
- Modify: `src/ph_daily/config.py`
- Modify: `src/ph_daily/storage.py`
- Modify: `.env.example`
- Modify: `tests/test_config.py`
- Modify: `tests/test_report.py`

- [ ] Add `output_formats: tuple[str, ...]` to `Settings`.
- [ ] Parse `OUTPUT_FORMATS`, defaulting to `("markdown",)`.
- [ ] Accept only `markdown` and `html`; reject empty/unknown values with `ConfigError`.
- [ ] Add `html_report` path to `OutputPaths`.
- [ ] Update tests for default format, multiple formats, invalid formats, and HTML path.
- [ ] Run `.venv/bin/python -m pytest tests/test_config.py tests/test_report.py -q`.
- [ ] Commit with `feat: configure report output formats`.

## Task 2: Markdown Readability

**Files:**
- Modify: `src/ph_daily/report.py`
- Modify: `tests/test_report.py`

- [ ] Add a helper that maps enrichment errors to friendly Chinese messages.
- [ ] Convert report framework labels to Chinese.
- [ ] Add AI success/failure counts to the summary.
- [ ] Keep detailed errors out of Markdown.
- [ ] Update tests to assert Chinese labels and friendly timeout message.
- [ ] Run `.venv/bin/python -m pytest tests/test_report.py -q`.
- [ ] Commit with `feat: localize markdown reports`.

## Task 3: HTML Report

**Files:**
- Create: `src/ph_daily/html_report.py`
- Create: `tests/test_html_report.py`

- [ ] Implement `render_html_report(date, fetched_count, processed_products, filter_rule) -> str`.
- [ ] Escape dynamic text with `html.escape`.
- [ ] Render Chinese summary, selected product sections, images, links, enrichment sections, and friendly enrichment failures.
- [ ] Add tests for title, Chinese labels, escaped product names, enrichment success, and friendly failure text.
- [ ] Run `.venv/bin/python -m pytest tests/test_html_report.py -q`.
- [ ] Commit with `feat: add html daily reports`.

## Task 4: Collector Integration

**Files:**
- Modify: `src/ph_daily/collector.py`
- Modify: `tests/test_collector.py`
- Modify: `README.md`
- Modify: `docs/deployment-zh.md`

- [ ] Import and use `render_html_report`.
- [ ] Always write raw and processed JSON.
- [ ] Write Markdown only when `markdown` is configured.
- [ ] Write HTML only when `html` is configured.
- [ ] Update collector tests for markdown-only and markdown+html outputs.
- [ ] Document `OUTPUT_FORMATS=markdown,html`.
- [ ] Run `.venv/bin/python -m pytest -q`.
- [ ] Commit with `feat: write configured report formats`.

## Self-Review

- Spec coverage: config, Markdown readability, HTML output, collector integration, docs, and tests are covered.
- Placeholder scan: no placeholder work remains.
- Type consistency: `output_formats` is a tuple on `Settings`; `html_report` is a `Path` on `OutputPaths`; renderer signatures match the existing Markdown renderer shape.

