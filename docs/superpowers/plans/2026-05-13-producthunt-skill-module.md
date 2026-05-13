# Product Hunt Skill Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-class `skills/producthunt-daily` source module, exportable self-contained skill package, and stable Agent Mode (`--no-enrichment`) support while keeping `src/ph_daily` as the only CLI source of truth.

**Architecture:** Keep `src/ph_daily` as the deterministic collection core and add `skills/producthunt-daily` as documentation/template source only. Add `tools/export_producthunt_skill.py` to build a distribution skill package by copying the skill source plus current CLI core into `dist/skills/producthunt-daily`. Add tests for Agent Mode, export hygiene, and skill validation so the skill can evolve as the primary product surface without creating a second maintained Python source tree.

**Tech Stack:** Python 3.11 stdlib (`argparse`, `pathlib`, `shutil`, `tomllib`, `compileall`-free file copying), pytest, existing `ph_daily` CLI package, Markdown skill files.

---

## File Structure

- Modify `src/ph_daily/config.py`: keep `LLM_API_KEY` optional at config load time; enforce LLM key only when enrichment is actually attempted through `LlmClient`.
- Modify `src/ph_daily/collector.py`: add `enrichment_enabled: bool = True` to `collect_period`; skip LLM enrichment and the all-enrichment-failed guard when false.
- Modify `src/ph_daily/cli.py`: add `ph-daily collect --no-enrichment`; pass the flag into `Collector.collect_period`.
- Modify `tests/test_config.py`: update expectations for optional LLM configuration.
- Modify `tests/test_collector.py`: add no-enrichment collector behavior tests.
- Modify `tests/test_cli.py`: add no-enrichment CLI argument forwarding test.
- Create `skills/producthunt-daily/SKILL.md`: concise skill entrypoint adapted from the external working skill.
- Create `skills/producthunt-daily/references/config-reference.md`: configuration reference.
- Create `skills/producthunt-daily/references/agent-templates.md`: agent prompt templates.
- Create `skills/producthunt-daily/references/enrichment-prompt.md`: Agent Mode enrichment contract.
- Create `skills/producthunt-daily/scripts/setup.sh`: setup script for exported skill packages.
- Create `skills/producthunt-daily/scripts/.env.example`: skill-local env template.
- Create `tools/export_producthunt_skill.py`: export source skill + CLI core into a self-contained distribution directory.
- Create `tests/test_skill_export.py`: validates export content and hygiene.
- Modify `.gitignore`: ignore `dist/` export artifacts if not already ignored.
- Modify `README.md`, `docs/agent-integration-v0.2.md`, and `docs/releases/v0.2.md` or create a v0.3 note as appropriate: document Agent Mode and skill/core iteration split.

## Task 1: Stabilize Agent Mode Core

**Files:**
- Modify: `tests/test_config.py`
- Modify: `tests/test_collector.py`
- Modify: `tests/test_cli.py`
- Modify: `src/ph_daily/config.py`
- Modify: `src/ph_daily/collector.py`
- Modify: `src/ph_daily/cli.py`

- [ ] **Step 1: Update config test for optional LLM key**

Replace the old missing-key failure test in `tests/test_config.py`:

```python
def test_missing_llm_api_key_is_allowed_for_agent_mode(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("LLM_API_KEY", "   ")

    settings = load_settings(load_dotenv_file=False)

    assert settings.llm_api_key == ""
    assert settings.llm_model == "model-a"
```

Keep `tests/test_llm.py::test_llm_client_requires_api_key` unchanged because `LlmClient` should still reject enrichment without a key.

- [ ] **Step 2: Run config tests and verify the changed expectation**

Run:

```bash
.venv/bin/python -m pytest tests/test_config.py tests/test_llm.py -q
```

Expected before implementation is aligned: if `src/ph_daily/config.py` still raises on missing `LLM_API_KEY`, the new config test fails with `ConfigError`. If it already accepts optional keys, this step can pass; still keep the test because it locks the intended Agent Mode contract.

- [ ] **Step 3: Add collector no-enrichment test**

Append to `tests/test_collector.py`:

```python
class UnexpectedLlmClient:
    def enrich_product(self, product):
        raise AssertionError("LLM should not be called in no-enrichment mode")


def test_collect_period_skips_llm_when_enrichment_disabled(tmp_path):
    products = [
        make_product("First Product", votes=500, comments=25),
        make_product("Second Product", votes=600, comments=30),
    ]
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=FakeProductHuntClient(products=products),
        llm_client=UnexpectedLlmClient(),
    )

    result = collector.collect_period(
        "2026-05-10",
        period="daily",
        enrichment_enabled=False,
    )

    assert result.selected_count == 2
    processed_data = json.loads(result.paths.processed_json.read_text(encoding="utf-8"))
    assert processed_data["products"][0]["enrichment"] is None
    assert processed_data["products"][0]["enrichment_error"] is None
    assert processed_data["products"][1]["enrichment"] is None
    assert processed_data["products"][1]["enrichment_error"] is None
```

- [ ] **Step 4: Run collector no-enrichment test and verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_collector.py::test_collect_period_skips_llm_when_enrichment_disabled -q
```

Expected: FAIL with `TypeError: Collector.collect_period() got an unexpected keyword argument 'enrichment_enabled'` until collector support is implemented.

- [ ] **Step 5: Add CLI no-enrichment forwarding test**

In `tests/test_cli.py`, update fake collector method signatures used by collect tests to accept `enrichment_enabled=True`. Then append:

```python
def test_collect_passes_no_enrichment_flag(monkeypatch, capsys):
    settings = SimpleNamespace(
        product_hunt_featured=None,
        product_hunt_order="VOTES",
        product_hunt_topic="",
        product_hunt_url="",
        product_hunt_twitter_url="",
    )

    class FakeCollector:
        def __init__(self, actual_settings):
            assert actual_settings is settings

        def collect_period(
            self,
            target_date,
            period="daily",
            post_filters=None,
            include_keywords=None,
            exclude_keywords=None,
            enrichment_enabled=True,
        ):
            assert target_date == "2026-05-10"
            assert period == "daily"
            assert enrichment_enabled is False
            return SimpleNamespace(
                fetched_count=8,
                selected_count=2,
                paths=SimpleNamespace(markdown_report="/tmp/report.md"),
            )

    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "Collector", FakeCollector)

    exit_code = run(["collect", "--date", "2026-05-10", "--no-enrichment"])

    captured = capsys.readouterr()
    assert exit_code == ExitCode.SUCCESS
    assert "Selected 2/8 products" in captured.out
```

- [ ] **Step 6: Run CLI no-enrichment test and verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::test_collect_passes_no_enrichment_flag -q
```

Expected: FAIL with argparse rejecting `--no-enrichment`.

- [ ] **Step 7: Implement collector no-enrichment switch**

In `src/ph_daily/collector.py`, change the method signature:

```python
    def collect_period(
        self,
        date: str,
        period: str = "daily",
        post_filters: ProductHuntPostFilters | None = None,
        include_keywords: tuple[str, ...] | None = None,
        exclude_keywords: tuple[str, ...] | None = None,
        enrichment_enabled: bool = True,
    ) -> CollectionResult:
```

Change the enrichment block:

```python
            if filter_decision.passed and enrichment_enabled:
                try:
                    enrichment = self.llm_client.enrich_product(product)
                    successful_enrichments += 1
                except ConfigError:
                    raise
                except LlmError as exc:
                    enrichment_error = str(exc)
```

Change the guard:

```python
        if enrichment_enabled and selected_count and successful_enrichments == 0:
            raise LlmError("No selected products could be enriched")
```

- [ ] **Step 8: Implement CLI flag**

In `src/ph_daily/cli.py`, add the argument to the collect parser:

```python
    collect_parser.add_argument(
        "--no-enrichment",
        action="store_true",
        default=False,
        help="Skip LLM enrichment; output filtered Product Hunt data for agent-side analysis",
    )
```

Pass it into `collect_period`:

```python
                enrichment_enabled=not args.no_enrichment,
```

- [ ] **Step 9: Align config optional LLM behavior**

In `src/ph_daily/config.py`, ensure missing `LLM_API_KEY` is accepted at load time:

```python
    if llm_api_key and not llm_model:
        raise ConfigError("LLM_MODEL is required when LLM_API_KEY is set")
```

Do not raise `ConfigError("LLM_API_KEY is required")` in `load_settings`; keep that validation in `src/ph_daily/llm.py`.

- [ ] **Step 10: Run Agent Mode core tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_config.py tests/test_collector.py tests/test_cli.py tests/test_llm.py -q
```

Expected: all selected tests PASS.

- [ ] **Step 11: Commit Agent Mode core**

Run:

```bash
git add src/ph_daily/config.py src/ph_daily/collector.py src/ph_daily/cli.py tests/test_config.py tests/test_collector.py tests/test_cli.py
git commit -m "feat: add agent no-enrichment mode"
```

## Task 2: Add Skill Source Module

**Files:**
- Create: `skills/producthunt-daily/SKILL.md`
- Create: `skills/producthunt-daily/references/config-reference.md`
- Create: `skills/producthunt-daily/references/agent-templates.md`
- Create: `skills/producthunt-daily/references/enrichment-prompt.md`
- Create: `skills/producthunt-daily/scripts/setup.sh`
- Create: `skills/producthunt-daily/scripts/.env.example`

- [ ] **Step 1: Create skill directories**

Run:

```bash
mkdir -p skills/producthunt-daily/references skills/producthunt-daily/scripts
```

Expected: directories exist under `skills/producthunt-daily`.

- [ ] **Step 2: Create `SKILL.md`**

Create `skills/producthunt-daily/SKILL.md` based on the external working skill, but keep it concise and point detailed material to references:

````markdown
---
name: producthunt-daily
description: "Collect, filter, and analyze Product Hunt daily/weekly/monthly/yearly launches using the ph-daily CLI. Use when users mention Product Hunt, PH reports, product hunt 抓取/采集, 日报/周报/月报/年报, tech product monitoring, new product discovery, Product Hunt trend summaries, backfills, or agent-driven Product Hunt automation."
---

# Product Hunt Daily Collector

Use this skill to run the `ph-daily` CLI, generate Product Hunt period reports, and optionally perform agent-side analysis.

## Core Rule

`ph-daily` owns Product Hunt fetching, filtering, enrichment, and report generation. The agent should call the CLI, report results, diagnose failures, and optionally summarize generated reports. Do not reimplement Product Hunt API calls or filtering logic in the agent prompt.

## Setup

If this is an exported skill package, run:

```bash
bash /path/to/producthunt-daily/scripts/setup.sh
```

Then edit the generated `.env` file with:

```env
PRODUCT_HUNT_TOKEN=your_product_hunt_token
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini
```

For Agent Mode, `LLM_API_KEY` may be empty and commands should use `--no-enrichment`.

## Commands

```bash
ph-daily healthcheck
ph-daily collect --period daily --date today
ph-daily collect --period weekly --date today
ph-daily collect --period monthly --date today
ph-daily collect --period yearly --date today
ph-daily collect --period daily --date today --no-enrichment
ph-daily backfill --days 7
```

## References

- Configuration: `references/config-reference.md`
- Agent templates: `references/agent-templates.md`
- Agent-side enrichment contract: `references/enrichment-prompt.md`

## Safety

- Never print `.env`, tokens, or API keys.
- On success, report selected/fetched counts and generated report paths.
- On failure, report the command, exit code, stdout/stderr, and relevant log excerpts.
- Do not edit `data/raw`, `data/processed`, or `reports` as a repair step.
````

- [ ] **Step 3: Create config reference**

Create `skills/producthunt-daily/references/config-reference.md` by adapting the external `references/config-reference.md`. Include these sections exactly:

```markdown
# Configuration Reference

## Required For Fetching

| Variable | Description |
| --- | --- |
| `PRODUCT_HUNT_TOKEN` | Product Hunt API token. A developer token is enough for read-only collection. |

## Required For CLI Enrichment

| Variable | Description |
| --- | --- |
| `LLM_BASE_URL` | OpenAI-compatible base URL ending at `/v1`. |
| `LLM_API_KEY` | Required only when not using `--no-enrichment`. |
| `LLM_MODEL` | Model name for `/chat/completions`. |

## Period Thresholds

| Variable | Default |
| --- | ---: |
| `DAILY_MIN_VOTES` | `300` |
| `WEEKLY_MIN_VOTES` | `800` |
| `MONTHLY_MIN_VOTES` | `1000` |
| `YEARLY_MIN_VOTES` | `5000` |

## Filters

| Variable | Description |
| --- | --- |
| `PRODUCT_HUNT_FEATURED` | Optional `true` or `false`. |
| `PRODUCT_HUNT_ORDER` | `VOTES`, `NEWEST`, or `FEATURED_AT`. |
| `PRODUCT_HUNT_TOPIC` | Product Hunt topic slug. |
| `INCLUDE_KEYWORDS` | Comma-separated local include keywords. |
| `EXCLUDE_KEYWORDS` | Comma-separated local exclude keywords. |

## Output

| Variable | Default |
| --- | --- |
| `OUTPUT_FORMATS` | `markdown` |
| `OUTPUT_DIR` | `.` |
| `HTTP_TIMEOUT_SECONDS` | `30` |
```

- [ ] **Step 4: Create agent templates reference**

Create `skills/producthunt-daily/references/agent-templates.md` with these reusable templates:

````markdown
# Agent Integration Templates

## Scheduler

```text
Run Product Hunt <period> collection.
1. cd <INSTALL_DIR>
2. source .venv/bin/activate
3. ph-daily healthcheck
4. ph-daily collect --period <period> --date <date>
5. Report selected/fetched count and generated report paths.
6. On failure, report command, exit code, stdout/stderr, and logs/cron.log excerpt if present.
Never print secrets and never reimplement Product Hunt filtering.
```

## Agent Mode

```text
Run Product Hunt <period> collection without external LLM enrichment:
ph-daily collect --period <period> --date <date> --no-enrichment
Then read data/processed/<period-output>.json and enrich selected products using references/enrichment-prompt.md.
Do not modify data/raw, data/processed, or reports.
```

## Secondary Analysis

```text
Read the generated report at <report_path>.
Summarize:
1. Top 3 products to watch.
2. Opportunities for developers or entrepreneurs.
3. Keywords to monitor next.
Only use report content.
```
````

- [ ] **Step 5: Create enrichment prompt reference**

Create `skills/producthunt-daily/references/enrichment-prompt.md`:

````markdown
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
````

- [ ] **Step 6: Create exported-package setup script**

Create `skills/producthunt-daily/scripts/setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="${1:-$HOME/.ph-daily}"

echo "=== Product Hunt Daily Setup ==="
echo "Install directory: $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"
cp -R "$SCRIPT_DIR/src" "$INSTALL_DIR/src"
cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/pyproject.toml"
cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env.example"

if [ ! -d "$INSTALL_DIR/.venv" ]; then
  python3 -m venv "$INSTALL_DIR/.venv"
fi

source "$INSTALL_DIR/.venv/bin/activate"
python -m pip install -e "$INSTALL_DIR"

if [ ! -f "$INSTALL_DIR/.env" ]; then
  cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
fi

cd "$INSTALL_DIR"
ph-daily healthcheck || true

echo "Setup files installed. Edit $INSTALL_DIR/.env before live collection."
```

Then make it executable:

```bash
chmod +x skills/producthunt-daily/scripts/setup.sh
```

- [ ] **Step 7: Create skill `.env.example`**

Copy the project root `.env.example` into `skills/producthunt-daily/scripts/.env.example`, then adjust comments if needed to mention:

```env
# LLM_API_KEY may be empty only when using:
# ph-daily collect --no-enrichment
```

- [ ] **Step 8: Verify no forbidden files are present**

Run:

```bash
find skills/producthunt-daily -name .git -o -name .DS_Store -o -name __pycache__ -o -name '*.pyc' -o -name '*.egg-info'
```

Expected: no output.

- [ ] **Step 9: Commit skill source module**

Run:

```bash
git add skills/producthunt-daily
git commit -m "feat: add producthunt skill source module"
```

## Task 3: Add Skill Export Script

**Files:**
- Create: `tools/export_producthunt_skill.py`
- Modify: `.gitignore`
- Test: `tests/test_skill_export.py`

- [ ] **Step 1: Write failing export tests**

Create `tests/test_skill_export.py`:

```python
from pathlib import Path

from tools.export_producthunt_skill import export_skill


def test_export_skill_creates_self_contained_package(tmp_path):
    destination = tmp_path / "producthunt-daily"

    export_skill(destination)

    assert (destination / "SKILL.md").exists()
    assert (destination / "references" / "config-reference.md").exists()
    assert (destination / "references" / "agent-templates.md").exists()
    assert (destination / "references" / "enrichment-prompt.md").exists()
    assert (destination / "scripts" / "setup.sh").exists()
    assert (destination / "scripts" / ".env.example").exists()
    assert (destination / "scripts" / "pyproject.toml").exists()
    assert (destination / "scripts" / "src" / "ph_daily" / "cli.py").exists()


def test_export_skill_excludes_runtime_artifacts(tmp_path):
    destination = tmp_path / "producthunt-daily"

    export_skill(destination)

    forbidden_names = {".git", ".DS_Store", "__pycache__"}
    exported_paths = {path.name for path in destination.rglob("*")}
    assert forbidden_names.isdisjoint(exported_paths)
    assert not list(destination.rglob("*.pyc"))
    assert not list(destination.rglob("*.egg-info"))
```

- [ ] **Step 2: Run export tests and verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_skill_export.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools'` or missing `export_producthunt_skill`.

- [ ] **Step 3: Make `tools` importable**

Create `tools/__init__.py`:

```python
"""Project maintenance tools."""
```

- [ ] **Step 4: Implement export script**

Create `tools/export_producthunt_skill.py`:

```python
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE = ROOT / "skills" / "producthunt-daily"
DEFAULT_DESTINATION = ROOT / "dist" / "skills" / "producthunt-daily"
FORBIDDEN_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}


def _ignore_runtime_artifacts(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        path = Path(directory) / name
        if name in FORBIDDEN_DIRS or name == ".DS_Store":
            ignored.add(name)
        elif path.suffix in FORBIDDEN_SUFFIXES:
            ignored.add(name)
        elif name.endswith(".egg-info"):
            ignored.add(name)
    return ignored


def _copytree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=_ignore_runtime_artifacts)


def export_skill(destination: Path = DEFAULT_DESTINATION) -> Path:
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SKILL_SOURCE / "SKILL.md", destination / "SKILL.md")
    _copytree(SKILL_SOURCE / "references", destination / "references")

    scripts_destination = destination / "scripts"
    scripts_destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL_SOURCE / "scripts" / "setup.sh", scripts_destination / "setup.sh")
    shutil.copy2(
        SKILL_SOURCE / "scripts" / ".env.example",
        scripts_destination / ".env.example",
    )
    shutil.copy2(ROOT / "pyproject.toml", scripts_destination / "pyproject.toml")
    _copytree(ROOT / "src", scripts_destination / "src")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DESTINATION,
        help="Destination directory for exported skill package",
    )
    args = parser.parse_args()
    destination = export_skill(args.dest)
    print(destination)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Ignore export artifacts**

Add to `.gitignore` if absent:

```gitignore
dist/
```

- [ ] **Step 6: Run export tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_skill_export.py -q
```

Expected: PASS.

- [ ] **Step 7: Run export command manually**

Run:

```bash
.venv/bin/python tools/export_producthunt_skill.py
```

Expected: prints `.../dist/skills/producthunt-daily`.

- [ ] **Step 8: Inspect exported package hygiene**

Run:

```bash
find dist/skills/producthunt-daily -name .git -o -name .DS_Store -o -name __pycache__ -o -name '*.pyc' -o -name '*.egg-info'
```

Expected: no output.

- [ ] **Step 9: Commit export script**

Run:

```bash
git add .gitignore tools/__init__.py tools/export_producthunt_skill.py tests/test_skill_export.py
git commit -m "feat: add producthunt skill export"
```

## Task 4: Add Skill Validation Command

**Files:**
- Modify: `tools/export_producthunt_skill.py`
- Modify: `tests/test_skill_export.py`

- [ ] **Step 1: Add validation tests**

Append to `tests/test_skill_export.py`:

```python
from tools.export_producthunt_skill import validate_export


def test_validate_export_accepts_clean_package(tmp_path):
    destination = tmp_path / "producthunt-daily"
    export_skill(destination)

    validate_export(destination)


def test_validate_export_rejects_forbidden_artifact(tmp_path):
    destination = tmp_path / "producthunt-daily"
    export_skill(destination)
    (destination / ".DS_Store").write_text("noise", encoding="utf-8")

    try:
        validate_export(destination)
    except ValueError as exc:
        assert ".DS_Store" in str(exc)
    else:
        raise AssertionError("validate_export should reject forbidden artifacts")
```

- [ ] **Step 2: Run validation tests and verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_skill_export.py::test_validate_export_accepts_clean_package tests/test_skill_export.py::test_validate_export_rejects_forbidden_artifact -q
```

Expected: FAIL because `validate_export` is not defined.

- [ ] **Step 3: Implement validation**

Add to `tools/export_producthunt_skill.py`:

```python
def validate_export(destination: Path) -> None:
    destination = Path(destination)
    required_files = [
        destination / "SKILL.md",
        destination / "references" / "config-reference.md",
        destination / "references" / "agent-templates.md",
        destination / "references" / "enrichment-prompt.md",
        destination / "scripts" / "setup.sh",
        destination / "scripts" / ".env.example",
        destination / "scripts" / "pyproject.toml",
        destination / "scripts" / "src" / "ph_daily" / "cli.py",
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise ValueError(f"export missing required files: {missing}")

    forbidden: list[str] = []
    for path in destination.rglob("*"):
        if (
            path.name in FORBIDDEN_DIRS
            or path.name == ".DS_Store"
            or path.suffix in FORBIDDEN_SUFFIXES
            or path.name.endswith(".egg-info")
        ):
            forbidden.append(str(path))
    if forbidden:
        raise ValueError(f"export contains forbidden artifacts: {forbidden}")
```

Update `main()` after export:

```python
    validate_export(destination)
    print(destination)
```

- [ ] **Step 4: Run skill export tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_skill_export.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit validation**

Run:

```bash
git add tools/export_producthunt_skill.py tests/test_skill_export.py
git commit -m "test: validate producthunt skill export"
```

## Task 5: Document Core And Skill Iteration Tracks

**Files:**
- Modify: `README.md`
- Modify: `docs/agent-integration-v0.2.md`
- Create: `docs/roadmap/core-and-skill.md`
- Create: `docs/releases/v0.3-skill-preview.md`

- [ ] **Step 1: Create roadmap document**

Create `docs/roadmap/core-and-skill.md`:

````markdown
# Core And Skill Iteration Roadmap

## Principle

The skill is the primary product surface. The CLI core is the stable execution engine.

## Core Track

- Owns `src/ph_daily`.
- Provides deterministic Product Hunt fetching, filtering, enrichment, output, and tests.
- Adds stable CLI capabilities only when they benefit both direct script users and skill users.

## Skill Track

- Owns `skills/producthunt-daily`.
- Provides Agent instructions, setup workflow, templates, Agent Mode guidance, and distribution.
- Evolves faster than the core as agent workflows change.

## Versioning

Use release notes to record both dimensions:

```text
Core: 0.3.0
Skill: 0.1.0
```

## Near-Term Priorities

1. Agent Mode with `--no-enrichment`.
2. Exportable self-contained skill package.
3. Skill validation and hygiene checks.
4. Agent-side enrichment templates and examples.
````

- [ ] **Step 2: Update README**

Add a short section under Agent Integration:

````markdown
## Skill Module

The repository keeps `src/ph_daily` as the only CLI source of truth and maintains a separate `skills/producthunt-daily` source module for agent distribution. Exported skill packages are generated from project sources, not hand-maintained as a second Python codebase.

Agent Mode:

```bash
ph-daily collect --period daily --date today --no-enrichment
```

Use Agent Mode when the host agent should perform product analysis with its own model after the CLI has fetched and filtered Product Hunt data.
````

- [ ] **Step 3: Update v0.2 agent integration docs**

In `docs/agent-integration-v0.2.md`, add a note near the Skillization section:

```markdown
The project now treats `skills/producthunt-daily` as the skill source module. Do not edit exported `dist/skills/producthunt-daily/scripts/src/ph_daily` directly; regenerate it with `tools/export_producthunt_skill.py`.
```

- [ ] **Step 4: Add release preview**

Create `docs/releases/v0.3-skill-preview.md`:

```markdown
# v0.3 Skill Preview

This preview introduces the split between the CLI core and the Product Hunt skill module.

## Core

- Adds Agent Mode through `ph-daily collect --no-enrichment`.
- Allows configuration loading without `LLM_API_KEY`; enrichment still requires a key unless skipped.

## Skill

- Adds `skills/producthunt-daily` as the source skill module.
- Adds an export flow for self-contained skill packages.
- Adds validation to prevent runtime artifacts from entering exports.
```

- [ ] **Step 5: Run docs grep check**

Run:

```bash
rg "scripts/src/ph_daily|--no-enrichment|skills/producthunt-daily|dist/skills/producthunt-daily" README.md docs skills -n
```

Expected: references are consistent: `scripts/src/ph_daily` appears only as generated/exported content, not as a project source to edit.

- [ ] **Step 6: Commit docs**

Run:

```bash
git add README.md docs/agent-integration-v0.2.md docs/roadmap/core-and-skill.md docs/releases/v0.3-skill-preview.md
git commit -m "docs: split core and skill iteration tracks"
```

## Task 6: Final Verification

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run full test suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests PASS.

- [ ] **Step 2: Run healthcheck without LLM key**

Run:

```bash
env PRODUCT_HUNT_TOKEN=dummy LLM_API_KEY= .venv/bin/ph-daily healthcheck
```

Expected:

```text
Configuration OK
```

- [ ] **Step 3: Run export**

Run:

```bash
.venv/bin/python tools/export_producthunt_skill.py
```

Expected: prints the exported skill path and exits 0.

- [ ] **Step 4: Verify export hygiene**

Run:

```bash
find dist/skills/producthunt-daily -name .git -o -name .DS_Store -o -name __pycache__ -o -name '*.pyc' -o -name '*.egg-info'
```

Expected: no output.

- [ ] **Step 5: Check git status**

Run:

```bash
git status --short
```

Expected: no tracked changes. `dist/` should be ignored.

- [ ] **Step 6: Optional tag only after user confirms**

Do not tag automatically in this plan. If the user asks for a tag, use:

```bash
git tag v0.3.0-skill-preview
```

## Self-Review Checklist

- Spec coverage: plan covers skill source module, no second maintained CLI source tree, export flow, export validation, Agent Mode, and core/skill roadmap.
- Placeholder scan: no `TBD`, `TODO`, or undefined “implement later” tasks are present.
- Type consistency: `enrichment_enabled` is the only new collector argument; `--no-enrichment` maps to `enrichment_enabled=not args.no_enrichment`.
- Source-of-truth rule: the plan never commits `skills/producthunt-daily/scripts/src/ph_daily`; it is generated into `dist/`.
