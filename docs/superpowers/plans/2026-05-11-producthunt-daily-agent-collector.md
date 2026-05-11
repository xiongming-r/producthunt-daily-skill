# Product Hunt Daily Agent Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Product Hunt daily collector that fetches high-signal launches, filters them by dynamic vote/comment quality rules, enriches them with an OpenAI-compatible LLM, and writes JSON plus Markdown reports.

**Architecture:** Implement a small Python CLI package under `src/ph_daily`. Keep Product Hunt access, normalization, filtering, LLM enrichment, storage, and report rendering in separate modules. Use open source projects only as references; do not fork or copy repository code unless attribution is explicitly preserved.

**Tech Stack:** Python 3.11+, stdlib `argparse`, `dataclasses`, `json`, `logging`, `pathlib`, `datetime`; third-party `httpx` and `python-dotenv`; test stack `pytest`.

---

## File Structure

- Create `pyproject.toml`: package metadata, console script, dependencies, pytest config.
- Create `README.md`: local setup, CLI examples, and operational notes.
- Modify `.env.example`: align final env names and add optional settings.
- Modify `.gitignore`: keep generated runtime artifacts out of git.
- Create `src/ph_daily/__init__.py`: package version.
- Create `src/ph_daily/errors.py`: typed exceptions and CLI exit codes.
- Create `src/ph_daily/config.py`: environment loading and validation.
- Create `src/ph_daily/models.py`: dataclasses for raw-normalized products, filter decisions, enrichment, and run result.
- Create `src/ph_daily/quality.py`: dynamic vote/comment threshold rule.
- Create `src/ph_daily/producthunt.py`: Product Hunt GraphQL adapter and field validation query.
- Create `src/ph_daily/llm.py`: OpenAI-compatible chat completions client and JSON enrichment parser.
- Create `src/ph_daily/storage.py`: date-based output path handling and JSON writing.
- Create `src/ph_daily/report.py`: Markdown report renderer.
- Create `src/ph_daily/collector.py`: orchestration for collect/backfill.
- Create `src/ph_daily/cli.py`: `ph-daily` command line entrypoint.
- Create `tests/fixtures/producthunt_posts.json`: representative Product Hunt API payload.
- Create `tests/fixtures/llm_enrichment.json`: representative LLM response.
- Create `tests/test_config.py`: configuration tests.
- Create `tests/test_quality.py`: dynamic filter tests.
- Create `tests/test_models.py`: normalization tests.
- Create `tests/test_report.py`: Markdown rendering tests.
- Create `tests/test_llm.py`: LLM parsing tests.
- Create `tests/test_cli.py`: CLI exit code tests.
- Create `docs/deployment-zh.md`: cloud server cron deployment notes.
- Create `docs/agent-integration-zh.md`: Codex/Hermes/WorkBuddy/Qclaw invocation notes.
- Modify `docs/progress.md` and `docs/progress-zh.md`: mark the implementation plan as active.

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Modify: `.env.example`
- Modify: `.gitignore`
- Create: `src/ph_daily/__init__.py`
- Create: `src/ph_daily/errors.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create packaging and test config**

Create `pyproject.toml` with this content:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "producthunt-daily-agent"
version = "0.1.0"
description = "Agent-friendly Product Hunt daily collector with LLM enrichment"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27.0",
  "python-dotenv>=1.0.1",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
]

[project.scripts]
ph-daily = "ph_daily.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-q"
```

- [ ] **Step 2: Create package marker and exit code definitions**

Create `src/ph_daily/__init__.py`:

```python
"""Product Hunt daily collector package."""

__version__ = "0.1.0"
```

Create `src/ph_daily/errors.py`:

```python
from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    CONFIG_ERROR = 1
    PRODUCT_HUNT_ERROR = 2
    LLM_ERROR = 3
    OUTPUT_ERROR = 4


class PhDailyError(Exception):
    exit_code = ExitCode.CONFIG_ERROR


class ConfigError(PhDailyError):
    exit_code = ExitCode.CONFIG_ERROR


class ProductHuntError(PhDailyError):
    exit_code = ExitCode.PRODUCT_HUNT_ERROR


class LlmError(PhDailyError):
    exit_code = ExitCode.LLM_ERROR


class OutputError(PhDailyError):
    exit_code = ExitCode.OUTPUT_ERROR
```

- [ ] **Step 3: Update `.env.example`**

Replace `.env.example` with:

```env
PRODUCT_HUNT_TOKEN=

LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=
LLM_MODEL=gpt-4.1-mini

MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
OUTPUT_DIR=.
HTTP_TIMEOUT_SECONDS=30
```

- [ ] **Step 4: Confirm `.gitignore` protects runtime output**

Ensure `.gitignore` contains these lines:

```gitignore
.env
.env.*
!.env.example

__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
venv/

logs/
data/raw/
data/processed/
reports/daily/

*.log
.DS_Store
```

- [ ] **Step 5: Add a concise README**

Create `README.md`:

```markdown
# Product Hunt Daily Agent Collector

Agent-friendly Product Hunt daily collector. It fetches Product Hunt daily launches through the official GraphQL API, filters products with dynamic vote/comment quality rules, enriches selected products with an OpenAI-compatible LLM endpoint, and writes JSON plus Markdown reports.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill `.env` with `PRODUCT_HUNT_TOKEN`, `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`.

## Commands

```bash
ph-daily healthcheck
ph-daily collect --date today
ph-daily collect --date 2026-05-11
ph-daily backfill --days 7
```

Generated runtime files are written under `data/`, `reports/`, and `logs/`; those paths are ignored by git.
```

- [ ] **Step 6: Add test package marker**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 7: Run skeleton verification**

Run:

```bash
python -m pytest
```

Expected: pytest starts successfully and reports no tests collected or no failures.

- [ ] **Step 8: Commit skeleton**

```bash
git add pyproject.toml README.md .env.example .gitignore src/ph_daily/__init__.py src/ph_daily/errors.py tests/__init__.py
git commit -m "chore: add python collector skeleton"
```

## Task 2: Configuration Loading

**Files:**
- Create: `src/ph_daily/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
import pytest

from ph_daily.config import Settings, load_settings
from ph_daily.errors import ConfigError


def test_load_settings_from_environment(monkeypatch):
    monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "ph-token")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.setenv("LLM_MODEL", "model-a")
    monkeypatch.setenv("MIN_VOTES", "300")
    monkeypatch.setenv("COMMENT_RATIO", "0.04")
    monkeypatch.setenv("MIN_COMMENTS", "8")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/ph-daily")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "15")

    settings = load_settings(load_dotenv_file=False)

    assert settings == Settings(
        product_hunt_token="ph-token",
        llm_base_url="https://example.com/v1",
        llm_api_key="llm-key",
        llm_model="model-a",
        min_votes=300,
        comment_ratio=0.04,
        min_comments=8,
        output_dir="/tmp/ph-daily",
        http_timeout_seconds=15.0,
    )


def test_missing_product_hunt_token_fails(monkeypatch):
    monkeypatch.delenv("PRODUCT_HUNT_TOKEN", raising=False)

    with pytest.raises(ConfigError, match="PRODUCT_HUNT_TOKEN is required"):
        load_settings(load_dotenv_file=False)


def test_invalid_thresholds_fail(monkeypatch):
    monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "ph-token")
    monkeypatch.setenv("COMMENT_RATIO", "-1")

    with pytest.raises(ConfigError, match="COMMENT_RATIO must be greater than 0"):
        load_settings(load_dotenv_file=False)
```

- [ ] **Step 2: Run config tests and verify failure**

Run:

```bash
python -m pytest tests/test_config.py -q
```

Expected: fails because `ph_daily.config` does not exist.

- [ ] **Step 3: Implement config module**

Create `src/ph_daily/config.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from ph_daily.errors import ConfigError


@dataclass(frozen=True)
class Settings:
    product_hunt_token: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    min_votes: int
    comment_ratio: float
    min_comments: int
    output_dir: str
    http_timeout_seconds: float


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number") from exc


def load_settings(load_dotenv_file: bool = True) -> Settings:
    if load_dotenv_file:
        load_dotenv()

    product_hunt_token = os.getenv("PRODUCT_HUNT_TOKEN", "").strip()
    if not product_hunt_token:
        raise ConfigError("PRODUCT_HUNT_TOKEN is required")

    llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    llm_model = os.getenv("LLM_MODEL", "gpt-4.1-mini").strip()
    min_votes = _read_int("MIN_VOTES", 300)
    comment_ratio = _read_float("COMMENT_RATIO", 0.04)
    min_comments = _read_int("MIN_COMMENTS", 8)
    output_dir = os.getenv("OUTPUT_DIR", ".").strip() or "."
    http_timeout_seconds = _read_float("HTTP_TIMEOUT_SECONDS", 30.0)

    if min_votes < 1:
        raise ConfigError("MIN_VOTES must be at least 1")
    if comment_ratio <= 0:
        raise ConfigError("COMMENT_RATIO must be greater than 0")
    if min_comments < 0:
        raise ConfigError("MIN_COMMENTS must be at least 0")
    if http_timeout_seconds <= 0:
        raise ConfigError("HTTP_TIMEOUT_SECONDS must be greater than 0")
    if not llm_model:
        raise ConfigError("LLM_MODEL is required")

    return Settings(
        product_hunt_token=product_hunt_token,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        min_votes=min_votes,
        comment_ratio=comment_ratio,
        min_comments=min_comments,
        output_dir=output_dir,
        http_timeout_seconds=http_timeout_seconds,
    )
```

- [ ] **Step 4: Run config tests and verify success**

Run:

```bash
python -m pytest tests/test_config.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit config module**

```bash
git add src/ph_daily/config.py tests/test_config.py
git commit -m "feat: add environment configuration"
```

## Task 3: Data Models And Normalization

**Files:**
- Create: `src/ph_daily/models.py`
- Create: `tests/fixtures/producthunt_posts.json`
- Create: `tests/test_models.py`

- [ ] **Step 1: Add representative Product Hunt fixture**

Create `tests/fixtures/producthunt_posts.json`:

```json
{
  "data": {
    "posts": {
      "nodes": [
        {
          "id": "123",
          "name": "Acme AI",
          "tagline": "Automate support replies with context",
          "description": "Acme AI reads your docs and drafts support answers.",
          "votesCount": 512,
          "commentsCount": 33,
          "dailyRank": 4,
          "createdAt": "2026-05-10T08:00:00Z",
          "featuredAt": "2026-05-10T08:00:00Z",
          "website": "https://example.com",
          "url": "https://www.producthunt.com/posts/acme-ai",
          "media": [
            {
              "url": "https://ph-files.imgix.net/acme.png",
              "type": "image",
              "videoUrl": null
            }
          ],
          "topics": {
            "nodes": [
              {
                "name": "Artificial Intelligence"
              }
            ]
          },
          "makers": {
            "nodes": [
              {
                "name": "Jane Maker",
                "username": "jane"
              }
            ]
          }
        }
      ],
      "pageInfo": {
        "hasNextPage": false,
        "endCursor": "cursor-1"
      }
    }
  }
}
```

- [ ] **Step 2: Write failing model tests**

Create `tests/test_models.py`:

```python
import json
from pathlib import Path

from ph_daily.models import Product


def test_product_from_api_node_normalizes_fields():
    payload = json.loads(Path("tests/fixtures/producthunt_posts.json").read_text())
    node = payload["data"]["posts"]["nodes"][0]

    product = Product.from_api_node(node)

    assert product.id == "123"
    assert product.name == "Acme AI"
    assert product.tagline == "Automate support replies with context"
    assert product.description == "Acme AI reads your docs and drafts support answers."
    assert product.votes_count == 512
    assert product.comments_count == 33
    assert product.daily_rank == 4
    assert product.website_url == "https://example.com"
    assert product.product_hunt_url == "https://www.producthunt.com/posts/acme-ai"
    assert product.media_urls == ["https://ph-files.imgix.net/acme.png"]
    assert product.topics == ["Artificial Intelligence"]
    assert product.makers == ["Jane Maker"]
    assert product.raw["id"] == "123"
```

- [ ] **Step 3: Run model tests and verify failure**

Run:

```bash
python -m pytest tests/test_models.py -q
```

Expected: fails because `ph_daily.models` does not exist.

- [ ] **Step 4: Implement model dataclasses**

Create `src/ph_daily/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    tagline: str
    description: str
    votes_count: int
    comments_count: int
    daily_rank: int | None
    created_at: str
    featured_at: str | None
    website_url: str
    product_hunt_url: str
    media_urls: list[str]
    topics: list[str]
    makers: list[str]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api_node(cls, node: dict[str, Any]) -> "Product":
        media_urls = [
            media.get("url", "")
            for media in node.get("media", [])
            if media.get("url")
        ]
        topics = [
            topic.get("name", "")
            for topic in node.get("topics", {}).get("nodes", [])
            if topic.get("name")
        ]
        makers = [
            maker.get("name") or maker.get("username", "")
            for maker in node.get("makers", {}).get("nodes", [])
            if maker.get("name") or maker.get("username")
        ]

        return cls(
            id=str(node.get("id", "")),
            name=node.get("name", ""),
            tagline=node.get("tagline", ""),
            description=node.get("description", ""),
            votes_count=int(node.get("votesCount") or 0),
            comments_count=int(node.get("commentsCount") or 0),
            daily_rank=node.get("dailyRank"),
            created_at=node.get("createdAt", ""),
            featured_at=node.get("featuredAt"),
            website_url=node.get("website", ""),
            product_hunt_url=node.get("url", ""),
            media_urls=media_urls,
            topics=topics,
            makers=makers,
            raw=node,
        )


@dataclass(frozen=True)
class FilterDecision:
    passed: bool
    reason: str
    required_comments: int


@dataclass(frozen=True)
class ProductEnrichment:
    tagline_zh: str
    summary_zh: str
    target_users_zh: list[str]
    use_cases_zh: list[str]
    example_workflow_zh: list[str]
    why_interesting_zh: str
    caveat_zh: str


@dataclass(frozen=True)
class ProcessedProduct:
    product: Product
    filter_decision: FilterDecision
    enrichment: ProductEnrichment | None = None
    enrichment_error: str | None = None
```

- [ ] **Step 5: Run model tests and verify success**

Run:

```bash
python -m pytest tests/test_models.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit models**

```bash
git add src/ph_daily/models.py tests/fixtures/producthunt_posts.json tests/test_models.py
git commit -m "feat: add product data models"
```

## Task 4: Dynamic Quality Filter

**Files:**
- Create: `src/ph_daily/quality.py`
- Create: `tests/test_quality.py`

- [ ] **Step 1: Write failing quality tests**

Create `tests/test_quality.py`:

```python
from ph_daily.models import Product
from ph_daily.quality import evaluate_product, required_comments_for_votes


def make_product(votes: int, comments: int) -> Product:
    return Product(
        id="1",
        name="Demo",
        tagline="Demo tagline",
        description="Demo description",
        votes_count=votes,
        comments_count=comments,
        daily_rank=1,
        created_at="2026-05-10T08:00:00Z",
        featured_at=None,
        website_url="https://example.com",
        product_hunt_url="https://www.producthunt.com/posts/demo",
        media_urls=[],
        topics=[],
        makers=[],
        raw={},
    )


def test_required_comments_scales_with_votes():
    assert required_comments_for_votes(300, min_comments=8, comment_ratio=0.04) == 12
    assert required_comments_for_votes(500, min_comments=8, comment_ratio=0.04) == 20
    assert required_comments_for_votes(1000, min_comments=8, comment_ratio=0.04) == 40
    assert required_comments_for_votes(2000, min_comments=8, comment_ratio=0.04) == 80


def test_product_passes_when_votes_and_comments_match_threshold():
    decision = evaluate_product(
        make_product(512, 33),
        min_votes=300,
        min_comments=8,
        comment_ratio=0.04,
    )

    assert decision.passed is True
    assert decision.required_comments == 21
    assert decision.reason == "votes 512 >= 300 and comments 33 >= required 21"


def test_product_fails_when_votes_are_too_low():
    decision = evaluate_product(
        make_product(299, 99),
        min_votes=300,
        min_comments=8,
        comment_ratio=0.04,
    )

    assert decision.passed is False
    assert decision.reason == "votes 299 < 300"


def test_product_fails_when_comments_are_too_low():
    decision = evaluate_product(
        make_product(1000, 10),
        min_votes=300,
        min_comments=8,
        comment_ratio=0.04,
    )

    assert decision.passed is False
    assert decision.required_comments == 40
    assert decision.reason == "votes 1000 >= 300 but comments 10 < required 40"
```

- [ ] **Step 2: Run quality tests and verify failure**

Run:

```bash
python -m pytest tests/test_quality.py -q
```

Expected: fails because `ph_daily.quality` does not exist.

- [ ] **Step 3: Implement quality filter**

Create `src/ph_daily/quality.py`:

```python
from __future__ import annotations

import math

from ph_daily.models import FilterDecision, Product


def required_comments_for_votes(votes: int, min_comments: int, comment_ratio: float) -> int:
    return max(min_comments, math.ceil(votes * comment_ratio))


def evaluate_product(
    product: Product,
    min_votes: int,
    min_comments: int,
    comment_ratio: float,
) -> FilterDecision:
    required_comments = required_comments_for_votes(
        product.votes_count,
        min_comments=min_comments,
        comment_ratio=comment_ratio,
    )

    if product.votes_count < min_votes:
        return FilterDecision(
            passed=False,
            reason=f"votes {product.votes_count} < {min_votes}",
            required_comments=required_comments,
        )

    if product.comments_count < required_comments:
        return FilterDecision(
            passed=False,
            reason=(
                f"votes {product.votes_count} >= {min_votes} "
                f"but comments {product.comments_count} < required {required_comments}"
            ),
            required_comments=required_comments,
        )

    return FilterDecision(
        passed=True,
        reason=(
            f"votes {product.votes_count} >= {min_votes} "
            f"and comments {product.comments_count} >= required {required_comments}"
        ),
        required_comments=required_comments,
    )
```

- [ ] **Step 4: Run quality tests and verify success**

Run:

```bash
python -m pytest tests/test_quality.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit filter**

```bash
git add src/ph_daily/quality.py tests/test_quality.py
git commit -m "feat: add dynamic quality filter"
```

## Task 5: Product Hunt API Adapter

**Files:**
- Create: `src/ph_daily/producthunt.py`
- Create: `tests/test_producthunt.py`

- [ ] **Step 1: Write failing Product Hunt adapter tests**

Create `tests/test_producthunt.py`:

```python
import httpx
import pytest

from ph_daily.errors import ProductHuntError
from ph_daily.producthunt import ProductHuntClient


def test_build_posts_query_contains_required_fields():
    query = ProductHuntClient.build_posts_query()

    assert "votesCount" in query
    assert "commentsCount" in query
    assert "dailyRank" in query
    assert "media" in query
    assert "topics" in query
    assert "makers" in query


def test_fetch_posts_normalizes_products(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["Authorization"]
        return httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [
                            {
                                "id": "123",
                                "name": "Acme AI",
                                "tagline": "Automate support replies",
                                "description": "Draft support replies.",
                                "votesCount": 512,
                                "commentsCount": 33,
                                "dailyRank": 4,
                                "createdAt": "2026-05-10T08:00:00Z",
                                "featuredAt": None,
                                "website": "https://example.com",
                                "url": "https://www.producthunt.com/posts/acme-ai",
                                "media": [],
                                "topics": {"nodes": []},
                                "makers": {"nodes": []},
                            }
                        ],
                        "pageInfo": {
                            "hasNextPage": False,
                            "endCursor": None,
                        },
                    }
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    products, raw_payloads = client.fetch_posts_for_date("2026-05-10", limit=30)

    assert captured["authorization"] == "Bearer token-1"
    assert len(products) == 1
    assert products[0].name == "Acme AI"
    assert products[0].comments_count == 33
    assert raw_payloads[0]["data"]["posts"]["nodes"][0]["id"] == "123"


def test_fetch_posts_raises_on_graphql_errors():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"errors": [{"message": "bad query"}]})
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(ProductHuntError, match="Product Hunt GraphQL error"):
        client.fetch_posts_for_date("2026-05-10", limit=30)
```

- [ ] **Step 2: Run Product Hunt tests and verify failure**

Run:

```bash
python -m pytest tests/test_producthunt.py -q
```

Expected: fails because `ph_daily.producthunt` does not exist.

- [ ] **Step 3: Implement Product Hunt adapter**

Create `src/ph_daily/producthunt.py`:

```python
from __future__ import annotations

from typing import Any

import httpx

from ph_daily.errors import ProductHuntError
from ph_daily.models import Product


class ProductHuntClient:
    endpoint = "https://api.producthunt.com/v2/api/graphql"

    def __init__(
        self,
        token: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    @staticmethod
    def build_posts_query() -> str:
        return """
        query DailyPosts($postedAfter: DateTime!, $postedBefore: DateTime!, $after: String) {
          posts(order: VOTES, postedAfter: $postedAfter, postedBefore: $postedBefore, after: $after) {
            nodes {
              id
              name
              tagline
              description
              votesCount
              commentsCount
              dailyRank
              createdAt
              featuredAt
              website
              url
              media {
                url
                type
                videoUrl
              }
              topics {
                nodes {
                  name
                }
              }
              makers {
                nodes {
                  name
                  username
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """

    def fetch_posts_for_date(self, date: str, limit: int = 30) -> tuple[list[Product], list[dict[str, Any]]]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "ph-daily-agent/0.1.0",
        }
        posted_after = f"{date}T00:00:00Z"
        posted_before = f"{date}T23:59:59Z"
        cursor: str | None = None
        products: list[Product] = []
        raw_payloads: list[dict[str, Any]] = []

        with httpx.Client(
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            while len(products) < limit:
                payload = {
                    "query": self.build_posts_query(),
                    "variables": {
                        "postedAfter": posted_after,
                        "postedBefore": posted_before,
                        "after": cursor,
                    },
                }
                try:
                    response = client.post(self.endpoint, headers=headers, json=payload)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    raise ProductHuntError(f"Product Hunt request failed: {exc}") from exc

                data = response.json()
                raw_payloads.append(data)
                if data.get("errors"):
                    raise ProductHuntError(f"Product Hunt GraphQL error: {data['errors']}")

                posts = data.get("data", {}).get("posts")
                if not posts:
                    raise ProductHuntError("Product Hunt response missing data.posts")

                nodes = posts.get("nodes", [])
                products.extend(Product.from_api_node(node) for node in nodes)

                page_info = posts.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                if not cursor:
                    break

        products.sort(key=lambda item: item.votes_count, reverse=True)
        return products[:limit], raw_payloads

    def validate_fields(self) -> dict[str, bool]:
        products, _ = self.fetch_posts_for_date("2026-05-10", limit=1)
        if not products:
            return {"has_sample_product": False}
        product = products[0]
        return {
            "has_sample_product": True,
            "has_votes_count": isinstance(product.votes_count, int),
            "has_comments_count": isinstance(product.comments_count, int),
            "has_product_hunt_url": bool(product.product_hunt_url),
        }
```

- [ ] **Step 4: Run Product Hunt tests and verify success**

Run:

```bash
python -m pytest tests/test_producthunt.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit Product Hunt adapter**

```bash
git add src/ph_daily/producthunt.py tests/test_producthunt.py
git commit -m "feat: add product hunt graphql adapter"
```

## Task 6: OpenAI-Compatible LLM Adapter

**Files:**
- Create: `src/ph_daily/llm.py`
- Create: `tests/fixtures/llm_enrichment.json`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Add representative LLM fixture**

Create `tests/fixtures/llm_enrichment.json`:

```json
{
  "tagline_zh": "结合上下文自动生成客服回复",
  "summary_zh": "Acme AI 会读取团队文档，并根据上下文起草客服回复。",
  "target_users_zh": ["客服团队", "SaaS 创始人", "需要减少重复答疑的运营团队"],
  "use_cases_zh": ["根据帮助文档回答用户问题", "把常见问题整理成客服草稿", "让新人客服更快理解产品"],
  "example_workflow_zh": ["连接知识库", "导入历史问题", "让系统生成回复草稿", "人工确认后发送"],
  "why_interesting_zh": "它把知识库和客服回复结合，适合正在扩张支持团队的产品。",
  "caveat_zh": "Product Hunt 信息有限，实际效果需要看它支持哪些知识库和客服系统。"
}
```

- [ ] **Step 2: Write failing LLM tests**

Create `tests/test_llm.py`:

```python
import json
from pathlib import Path

import httpx

from ph_daily.llm import LlmClient, parse_enrichment_json
from ph_daily.models import Product, ProductEnrichment


def make_product() -> Product:
    return Product(
        id="123",
        name="Acme AI",
        tagline="Automate support replies with context",
        description="Acme AI reads your docs and drafts support answers.",
        votes_count=512,
        comments_count=33,
        daily_rank=4,
        created_at="2026-05-10T08:00:00Z",
        featured_at=None,
        website_url="https://example.com",
        product_hunt_url="https://www.producthunt.com/posts/acme-ai",
        media_urls=[],
        topics=["Artificial Intelligence"],
        makers=["Jane Maker"],
        raw={},
    )


def test_parse_enrichment_json():
    raw = Path("tests/fixtures/llm_enrichment.json").read_text()

    enrichment = parse_enrichment_json(raw)

    assert enrichment == ProductEnrichment(
        tagline_zh="结合上下文自动生成客服回复",
        summary_zh="Acme AI 会读取团队文档，并根据上下文起草客服回复。",
        target_users_zh=["客服团队", "SaaS 创始人", "需要减少重复答疑的运营团队"],
        use_cases_zh=["根据帮助文档回答用户问题", "把常见问题整理成客服草稿", "让新人客服更快理解产品"],
        example_workflow_zh=["连接知识库", "导入历史问题", "让系统生成回复草稿", "人工确认后发送"],
        why_interesting_zh="它把知识库和客服回复结合，适合正在扩张支持团队的产品。",
        caveat_zh="Product Hunt 信息有限，实际效果需要看它支持哪些知识库和客服系统。",
    )


def test_enrich_product_calls_openai_compatible_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://llm.example.com/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer llm-key"
        payload = json.loads(request.content)
        assert payload["model"] == "model-a"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": Path("tests/fixtures/llm_enrichment.json").read_text()
                        }
                    }
                ]
            },
        )

    client = LlmClient(
        base_url="https://llm.example.com/v1",
        api_key="llm-key",
        model="model-a",
        timeout_seconds=5,
        transport=httpx.MockTransport(handler),
    )

    enrichment = client.enrich_product(make_product())

    assert enrichment.summary_zh.startswith("Acme AI")
```

- [ ] **Step 3: Run LLM tests and verify failure**

Run:

```bash
python -m pytest tests/test_llm.py -q
```

Expected: fails because `ph_daily.llm` does not exist.

- [ ] **Step 4: Implement LLM adapter**

Create `src/ph_daily/llm.py`:

```python
from __future__ import annotations

import json
from typing import Any

import httpx

from ph_daily.errors import LlmError
from ph_daily.models import Product, ProductEnrichment


def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def parse_enrichment_json(raw_content: str) -> ProductEnrichment:
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise LlmError("LLM response was not valid JSON") from exc

    return ProductEnrichment(
        tagline_zh=str(data.get("tagline_zh", "")),
        summary_zh=str(data.get("summary_zh", "")),
        target_users_zh=_ensure_list(data.get("target_users_zh")),
        use_cases_zh=_ensure_list(data.get("use_cases_zh")),
        example_workflow_zh=_ensure_list(data.get("example_workflow_zh")),
        why_interesting_zh=str(data.get("why_interesting_zh", "")),
        caveat_zh=str(data.get("caveat_zh", "")),
    )


class LlmClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def enrich_product(self, product: Product) -> ProductEnrichment:
        if not self.api_key:
            raise LlmError("LLM_API_KEY is required for enrichment")

        prompt = self._build_prompt(product)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是产品研究员。只返回合法 JSON，不要使用 Markdown。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
            try:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise LlmError(f"LLM request failed: {exc}") from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(f"LLM response missing message content: {data}") from exc

        return parse_enrichment_json(content)

    @staticmethod
    def _build_prompt(product: Product) -> str:
        return json.dumps(
            {
                "task": "把 Product Hunt 产品信息转成中文产品分析，解释用途、用户、场景和例子。",
                "output_schema": {
                    "tagline_zh": "自然中文 tagline",
                    "summary_zh": "一句话说明产品做什么",
                    "target_users_zh": ["目标用户1", "目标用户2"],
                    "use_cases_zh": ["具体使用场景1", "具体使用场景2"],
                    "example_workflow_zh": ["步骤1", "步骤2", "步骤3"],
                    "why_interesting_zh": "为什么今天值得关注",
                    "caveat_zh": "基于信息不足时的注意事项",
                },
                "product": {
                    "name": product.name,
                    "tagline": product.tagline,
                    "description": product.description,
                    "votes_count": product.votes_count,
                    "comments_count": product.comments_count,
                    "daily_rank": product.daily_rank,
                    "topics": product.topics,
                    "makers": product.makers,
                    "product_hunt_url": product.product_hunt_url,
                    "website_url": product.website_url,
                },
            },
            ensure_ascii=False,
        )
```

- [ ] **Step 5: Run LLM tests and verify success**

Run:

```bash
python -m pytest tests/test_llm.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit LLM adapter**

```bash
git add src/ph_daily/llm.py tests/fixtures/llm_enrichment.json tests/test_llm.py
git commit -m "feat: add openai compatible llm adapter"
```

## Task 7: Storage And Markdown Report Rendering

**Files:**
- Create: `src/ph_daily/storage.py`
- Create: `src/ph_daily/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write failing report tests**

Create `tests/test_report.py`:

```python
from ph_daily.models import FilterDecision, ProcessedProduct, Product, ProductEnrichment
from ph_daily.report import render_daily_report
from ph_daily.storage import build_output_paths


def make_processed_product() -> ProcessedProduct:
    product = Product(
        id="123",
        name="Acme AI",
        tagline="Automate support replies with context",
        description="Acme AI reads your docs and drafts support answers.",
        votes_count=512,
        comments_count=33,
        daily_rank=4,
        created_at="2026-05-10T08:00:00Z",
        featured_at=None,
        website_url="https://example.com",
        product_hunt_url="https://www.producthunt.com/posts/acme-ai",
        media_urls=["https://ph-files.imgix.net/acme.png"],
        topics=["Artificial Intelligence"],
        makers=["Jane Maker"],
        raw={},
    )
    enrichment = ProductEnrichment(
        tagline_zh="结合上下文自动生成客服回复",
        summary_zh="Acme AI 会读取团队文档，并根据上下文起草客服回复。",
        target_users_zh=["客服团队", "SaaS 创始人"],
        use_cases_zh=["根据帮助文档回答用户问题", "整理客服草稿"],
        example_workflow_zh=["连接知识库", "导入历史问题", "确认回复草稿"],
        why_interesting_zh="它把知识库和客服回复结合。",
        caveat_zh="需要确认实际支持的客服系统。",
    )
    return ProcessedProduct(
        product=product,
        filter_decision=FilterDecision(
            passed=True,
            reason="votes 512 >= 300 and comments 33 >= required 21",
            required_comments=21,
        ),
        enrichment=enrichment,
    )


def test_build_output_paths():
    paths = build_output_paths("/tmp/out", "2026-05-10")

    assert str(paths.raw_json).endswith("data/raw/2026-05-10.json")
    assert str(paths.processed_json).endswith("data/processed/2026-05-10.json")
    assert str(paths.markdown_report).endswith("reports/daily/2026-05-10.md")
    assert str(paths.log_file).endswith("logs/2026-05-10.log")


def test_render_daily_report_contains_enriched_sections():
    report = render_daily_report(
        date="2026-05-10",
        fetched_count=12,
        processed_products=[make_processed_product()],
        filter_rule="votes >= 300 and comments_count >= max(8, ceil(votes * 0.04))",
    )

    assert "# Product Hunt Daily Report - 2026-05-10" in report
    assert "Products fetched: 12" in report
    assert "### 1. Acme AI" in report
    assert "Acme AI 会读取团队文档" in report
    assert "客服团队" in report
    assert "votes 512 >= 300" in report
```

- [ ] **Step 2: Run report tests and verify failure**

Run:

```bash
python -m pytest tests/test_report.py -q
```

Expected: fails because `ph_daily.storage` and `ph_daily.report` do not exist.

- [ ] **Step 3: Implement storage module**

Create `src/ph_daily/storage.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ph_daily.errors import OutputError


@dataclass(frozen=True)
class OutputPaths:
    raw_json: Path
    processed_json: Path
    markdown_report: Path
    log_file: Path


def build_output_paths(output_dir: str, date: str) -> OutputPaths:
    root = Path(output_dir)
    return OutputPaths(
        raw_json=root / "data" / "raw" / f"{date}.json",
        processed_json=root / "data" / "processed" / f"{date}.json",
        markdown_report=root / "reports" / "daily" / f"{date}.md",
        log_file=root / "logs" / f"{date}.log",
    )


def write_json(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = asdict(payload) if hasattr(payload, "__dataclass_fields__") else payload
        path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise OutputError(f"Failed to write JSON to {path}: {exc}") from exc


def write_text(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise OutputError(f"Failed to write text to {path}: {exc}") from exc
```

- [ ] **Step 4: Implement Markdown renderer**

Create `src/ph_daily/report.py`:

```python
from __future__ import annotations

from ph_daily.models import ProcessedProduct


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- 信息不足"
    return "\n".join(f"- {item}" for item in items)


def render_daily_report(
    date: str,
    fetched_count: int,
    processed_products: list[ProcessedProduct],
    filter_rule: str,
) -> str:
    selected = [item for item in processed_products if item.filter_decision.passed]
    lines = [
        f"# Product Hunt Daily Report - {date}",
        "",
        "## Summary",
        "",
        f"- Products fetched: {fetched_count}",
        f"- Products passing filters: {len(selected)}",
        f"- Filter rule: `{filter_rule}`",
        "",
        "## Selected Products",
        "",
    ]

    if not selected:
        lines.extend(["No products passed the filter today.", ""])
        return "\n".join(lines)

    for index, item in enumerate(selected, start=1):
        product = item.product
        enrichment = item.enrichment
        lines.extend(
            [
                f"### {index}. {product.name}",
                "",
                f"- Product Hunt: {product.product_hunt_url}",
                f"- Website: {product.website_url or 'Not provided'}",
                f"- Votes / Comments: {product.votes_count} / {product.comments_count}",
                f"- Filter: {item.filter_decision.reason}",
                "",
            ]
        )
        if product.media_urls:
            lines.extend([f"![{product.name}]({product.media_urls[0]})", ""])
        if enrichment is None:
            lines.extend(
                [
                    "#### Enrichment",
                    "",
                    f"- Error: {item.enrichment_error or 'No enrichment available'}",
                    "",
                ]
            )
            continue

        lines.extend(
            [
                "#### What It Does",
                "",
                enrichment.summary_zh,
                "",
                "#### Tagline",
                "",
                enrichment.tagline_zh,
                "",
                "#### Target Users",
                "",
                _bullet_list(enrichment.target_users_zh),
                "",
                "#### Use Cases",
                "",
                _bullet_list(enrichment.use_cases_zh),
                "",
                "#### Example Workflow",
                "",
                _bullet_list(enrichment.example_workflow_zh),
                "",
                "#### Why It Is Worth Attention",
                "",
                enrichment.why_interesting_zh,
                "",
                "#### Caveat",
                "",
                enrichment.caveat_zh,
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines)
```

- [ ] **Step 5: Run report tests and verify success**

Run:

```bash
python -m pytest tests/test_report.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit storage and reporting**

```bash
git add src/ph_daily/storage.py src/ph_daily/report.py tests/test_report.py
git commit -m "feat: add output storage and markdown reports"
```

## Task 8: Collector Orchestration

**Files:**
- Create: `src/ph_daily/collector.py`
- Create: `tests/test_collector.py`

- [ ] **Step 1: Write failing collector tests**

Create `tests/test_collector.py`:

```python
from pathlib import Path

from ph_daily.collector import Collector
from ph_daily.config import Settings
from ph_daily.models import Product, ProductEnrichment


class FakeProductHuntClient:
    def fetch_posts_for_date(self, date: str, limit: int = 30):
        return (
            [
                Product(
                    id="1",
                    name="Pass Product",
                    tagline="Useful product",
                    description="Useful description",
                    votes_count=500,
                    comments_count=25,
                    daily_rank=1,
                    created_at="2026-05-10T08:00:00Z",
                    featured_at=None,
                    website_url="https://example.com/pass",
                    product_hunt_url="https://www.producthunt.com/posts/pass",
                    media_urls=[],
                    topics=[],
                    makers=[],
                    raw={"id": "1"},
                ),
                Product(
                    id="2",
                    name="Fail Product",
                    tagline="Thin discussion",
                    description="Thin description",
                    votes_count=1000,
                    comments_count=2,
                    daily_rank=2,
                    created_at="2026-05-10T08:00:00Z",
                    featured_at=None,
                    website_url="https://example.com/fail",
                    product_hunt_url="https://www.producthunt.com/posts/fail",
                    media_urls=[],
                    topics=[],
                    makers=[],
                    raw={"id": "2"},
                ),
            ],
            [{"raw": "payload"}],
        )


class FakeLlmClient:
    def enrich_product(self, product: Product):
        return ProductEnrichment(
            tagline_zh="有用产品",
            summary_zh=f"{product.name} 的中文说明",
            target_users_zh=["创业者"],
            use_cases_zh=["寻找工具"],
            example_workflow_zh=["打开产品", "试用功能"],
            why_interesting_zh="讨论和票数都不错。",
            caveat_zh="需要进一步验证。",
        )


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        product_hunt_token="ph-token",
        llm_base_url="https://llm.example.com/v1",
        llm_api_key="llm-key",
        llm_model="model-a",
        min_votes=300,
        comment_ratio=0.04,
        min_comments=8,
        output_dir=str(tmp_path),
        http_timeout_seconds=10,
    )


def test_collect_writes_raw_processed_and_report(tmp_path):
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=FakeProductHuntClient(),
        llm_client=FakeLlmClient(),
    )

    result = collector.collect("2026-05-10")

    assert result.fetched_count == 2
    assert result.selected_count == 1
    assert result.paths.raw_json.exists()
    assert result.paths.processed_json.exists()
    assert result.paths.markdown_report.exists()
    assert "Pass Product 的中文说明" in result.paths.markdown_report.read_text()
    assert "Fail Product" not in result.paths.markdown_report.read_text()
```

- [ ] **Step 2: Run collector tests and verify failure**

Run:

```bash
python -m pytest tests/test_collector.py -q
```

Expected: fails because `ph_daily.collector` does not exist.

- [ ] **Step 3: Implement collector orchestration**

Create `src/ph_daily/collector.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ph_daily.config import Settings
from ph_daily.llm import LlmClient
from ph_daily.models import ProcessedProduct, Product, ProductEnrichment
from ph_daily.producthunt import ProductHuntClient
from ph_daily.quality import evaluate_product
from ph_daily.report import render_daily_report
from ph_daily.storage import OutputPaths, build_output_paths, write_json, write_text


class ProductHuntClientProtocol(Protocol):
    def fetch_posts_for_date(self, date: str, limit: int = 30) -> tuple[list[Product], list[dict[str, Any]]]:
        ...


class LlmClientProtocol(Protocol):
    def enrich_product(self, product: Product) -> ProductEnrichment:
        ...


@dataclass(frozen=True)
class CollectionResult:
    date: str
    fetched_count: int
    selected_count: int
    paths: OutputPaths


class Collector:
    def __init__(
        self,
        settings: Settings,
        product_hunt_client: ProductHuntClientProtocol | None = None,
        llm_client: LlmClientProtocol | None = None,
    ) -> None:
        self.settings = settings
        self.product_hunt_client = product_hunt_client or ProductHuntClient(
            token=settings.product_hunt_token,
            timeout_seconds=settings.http_timeout_seconds,
        )
        self.llm_client = llm_client or LlmClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.http_timeout_seconds,
        )

    def collect(self, date: str) -> CollectionResult:
        products, raw_payloads = self.product_hunt_client.fetch_posts_for_date(date, limit=30)
        processed: list[ProcessedProduct] = []

        for product in products:
            decision = evaluate_product(
                product,
                min_votes=self.settings.min_votes,
                min_comments=self.settings.min_comments,
                comment_ratio=self.settings.comment_ratio,
            )
            enrichment = None
            enrichment_error = None
            if decision.passed:
                try:
                    enrichment = self.llm_client.enrich_product(product)
                except Exception as exc:
                    enrichment_error = str(exc)
            processed.append(
                ProcessedProduct(
                    product=product,
                    filter_decision=decision,
                    enrichment=enrichment,
                    enrichment_error=enrichment_error,
                )
            )

        paths = build_output_paths(self.settings.output_dir, date)
        raw_payload = {
            "date": date,
            "source": "producthunt_api_v2_graphql",
            "raw_payloads": raw_payloads,
            "products": [product.raw for product in products],
        }
        processed_payload = {
            "date": date,
            "filter": {
                "min_votes": self.settings.min_votes,
                "comment_ratio": self.settings.comment_ratio,
                "min_comments": self.settings.min_comments,
            },
            "products": processed,
        }
        filter_rule = (
            f"votes >= {self.settings.min_votes} and comments_count >= "
            f"max({self.settings.min_comments}, ceil(votes * {self.settings.comment_ratio}))"
        )
        report = render_daily_report(
            date=date,
            fetched_count=len(products),
            processed_products=processed,
            filter_rule=filter_rule,
        )

        write_json(paths.raw_json, raw_payload)
        write_json(paths.processed_json, processed_payload)
        write_text(paths.markdown_report, report)

        return CollectionResult(
            date=date,
            fetched_count=len(products),
            selected_count=sum(1 for item in processed if item.filter_decision.passed),
            paths=paths,
        )
```

- [ ] **Step 4: Run collector tests and verify success**

Run:

```bash
python -m pytest tests/test_collector.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit collector**

```bash
git add src/ph_daily/collector.py tests/test_collector.py
git commit -m "feat: orchestrate daily collection"
```

## Task 9: CLI Commands

**Files:**
- Create: `src/ph_daily/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
import pytest

from ph_daily.cli import parse_date_arg, run
from ph_daily.errors import ExitCode


def test_parse_date_arg_accepts_explicit_date():
    assert parse_date_arg("2026-05-10") == "2026-05-10"


def test_parse_date_arg_rejects_bad_date():
    with pytest.raises(ValueError, match="date must be YYYY-MM-DD or today"):
        parse_date_arg("2026/05/10")


def test_healthcheck_returns_config_error_without_token(monkeypatch):
    monkeypatch.delenv("PRODUCT_HUNT_TOKEN", raising=False)

    code = run(["healthcheck"])

    assert code == ExitCode.CONFIG_ERROR
```

- [ ] **Step 2: Run CLI tests and verify failure**

Run:

```bash
python -m pytest tests/test_cli.py -q
```

Expected: fails because `ph_daily.cli` does not exist.

- [ ] **Step 3: Implement CLI**

Create `src/ph_daily/cli.py`:

```python
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta

from ph_daily.collector import Collector
from ph_daily.config import load_settings
from ph_daily.errors import ExitCode, PhDailyError


def parse_date_arg(value: str) -> str:
    if value == "today":
        return date.today().isoformat()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("date must be YYYY-MM-DD or today") from exc
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ph-daily")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("healthcheck")

    collect = subparsers.add_parser("collect")
    collect.add_argument("--date", default="today")

    backfill = subparsers.add_parser("backfill")
    backfill.add_argument("--days", type=int, required=True)

    return parser


def run(argv: list[str] | None = None) -> ExitCode:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
        if args.command == "healthcheck":
            print("Configuration OK")
            return ExitCode.SUCCESS

        collector = Collector(settings)
        if args.command == "collect":
            target_date = parse_date_arg(args.date)
            result = collector.collect(target_date)
            print(f"Collected {result.selected_count}/{result.fetched_count} products for {target_date}")
            print(f"Report: {result.paths.markdown_report}")
            return ExitCode.SUCCESS

        if args.command == "backfill":
            if args.days < 1:
                raise ValueError("--days must be at least 1")
            today = date.today()
            for offset in range(1, args.days + 1):
                target_date = (today - timedelta(days=offset)).isoformat()
                collector.collect(target_date)
                print(f"Collected {target_date}")
            return ExitCode.SUCCESS

        parser.error(f"unknown command {args.command}")
        return ExitCode.CONFIG_ERROR
    except PhDailyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return exc.exit_code
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return ExitCode.CONFIG_ERROR


def main() -> None:
    raise SystemExit(int(run()))
```

- [ ] **Step 4: Run CLI tests and verify success**

Run:

```bash
python -m pytest tests/test_cli.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Run all unit tests**

Run:

```bash
python -m pytest
```

Expected: all tests pass.

- [ ] **Step 6: Commit CLI**

```bash
git add src/ph_daily/cli.py tests/test_cli.py
git commit -m "feat: add ph-daily cli"
```

## Task 10: Deployment And Agent Integration Docs

**Files:**
- Create: `docs/deployment-zh.md`
- Create: `docs/agent-integration-zh.md`
- Modify: `docs/progress.md`
- Modify: `docs/progress-zh.md`

- [ ] **Step 1: Create cloud deployment document**

Create `docs/deployment-zh.md`:

```markdown
# 云服务器部署说明

## 安装

```bash
git clone <your-repo-url> producthunt-daily-agent
cd producthunt-daily-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

编辑 `.env`：

```env
PRODUCT_HUNT_TOKEN=your_product_hunt_token
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_key
LLM_MODEL=gpt-4.1-mini
MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
OUTPUT_DIR=.
HTTP_TIMEOUT_SECONDS=30
```

## 手动运行

```bash
source .venv/bin/activate
ph-daily healthcheck
ph-daily collect --date today
```

## Cron

每天北京时间 09:15 运行：

```cron
15 9 * * * cd /path/to/producthunt-daily-agent && .venv/bin/ph-daily collect --date today >> logs/cron.log 2>&1
```

## 输出

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
logs/YYYY-MM-DD.log
```
```

- [ ] **Step 2: Create agent integration document**

Create `docs/agent-integration-zh.md`:

```markdown
# Agent 集成说明

核心原则：agent 只调度和观察 CLI，不承载 Product Hunt 采集业务逻辑。

## Codex 自动化

推荐任务提示词：

```text
每天运行 `ph-daily collect --date today`。如果命令失败，读取 stderr 和最新日志，向我报告失败原因。如果成功，报告生成的 Markdown 路径和入选产品数量。
```

## Hermes

Hermes 可以作为调度器或 OpenAI-compatible LLM endpoint。作为 LLM endpoint 时，配置：

```env
LLM_BASE_URL=<Hermes OpenAI-compatible endpoint>/v1
LLM_API_KEY=<Hermes key>
LLM_MODEL=<model name>
```

## WorkBuddy / Qclaw

推荐暴露以下命令：

```bash
ph-daily healthcheck
ph-daily collect --date today
ph-daily backfill --days 7
```

自然语言触发示例：

```text
帮我运行今天的 Product Hunt 日报采集，并告诉我报告路径。
```
```

- [ ] **Step 3: Update progress documents**

In `docs/progress.md`, set current stage to:

```markdown
Implementation plan has been created. Next gate: choose execution mode and begin task-by-task implementation.
```

In `docs/progress-zh.md`, set current stage to:

```markdown
实施计划已经创建。下一道关卡：选择执行方式，并按任务逐步开发。
```

- [ ] **Step 4: Commit docs**

```bash
git add docs/deployment-zh.md docs/agent-integration-zh.md docs/progress.md docs/progress-zh.md
git commit -m "docs: add deployment and agent integration notes"
```

## Task 11: Live Integration Verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/progress-zh.md`

- [ ] **Step 1: Install package locally**

Run:

```bash
python -m pip install -e ".[dev]"
```

Expected: package installs and `ph-daily` console script is available.

- [ ] **Step 2: Run full unit test suite**

Run:

```bash
python -m pytest
```

Expected: all tests pass.

- [ ] **Step 3: Run config healthcheck**

Run:

```bash
ph-daily healthcheck
```

Expected with valid `.env`: exits `0` and prints `Configuration OK`.

Expected without valid `.env`: exits `1` and prints a clear missing configuration message.

- [ ] **Step 4: Run live collection when credentials are available**

Run only after `.env` contains valid Product Hunt and LLM credentials:

```bash
ph-daily collect --date today
```

Expected: exits `0`, writes:

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
```

- [ ] **Step 5: Inspect generated report**

Open the generated Markdown and verify:

```text
Product names are visible.
Votes and comments are visible.
Only products passing the dynamic filter appear in the selected section.
Chinese explanations include summary, users, use cases, workflow, why interesting, and caveat.
```

- [ ] **Step 6: Update progress documents**

In `docs/progress.md`, record the latest verified command and whether live credentials were available.

In `docs/progress-zh.md`, record the same status in Chinese.

- [ ] **Step 7: Commit verification notes**

```bash
git add docs/progress.md docs/progress-zh.md
git commit -m "docs: record collector verification status"
```

## Self-Review

Spec coverage:

- Product Hunt API collection: Task 5 and Task 8.
- Dynamic vote/comment filter: Task 4.
- OpenAI-compatible LLM enrichment: Task 6.
- Raw JSON, processed JSON, Markdown report: Task 7 and Task 8.
- CLI commands for cron and agents: Task 9.
- Cloud cron and agent docs: Task 10.
- Open source evaluation boundary: already captured in `docs/research/`; Task 5 validates the referenced GraphQL fields.
- Progress tracking: Task 10 and Task 11 update progress documents.

Completeness scan:

- This plan intentionally avoids incomplete markers and vague deferred work.
- Every module has concrete files, tests, command expectations, and commit points.

Type consistency:

- `Product`, `FilterDecision`, `ProductEnrichment`, and `ProcessedProduct` are defined in Task 3 and reused by later tasks.
- `Settings` is defined in Task 2 and reused by collector and CLI tasks.
- `OutputPaths` is defined in Task 7 and returned by `CollectionResult` in Task 8.
