import json
from dataclasses import replace

import pytest

from ph_daily.collector import Collector
from ph_daily.config import QualitySettings, Settings
from ph_daily.errors import ConfigError, LlmError
from ph_daily.models import Product, ProductEnrichment
from ph_daily.producthunt import ProductHuntPostFilters


def make_product(name: str, votes: int, comments: int) -> Product:
    return Product(
        id=name.lower().replace(" ", "-"),
        name=name,
        tagline=f"{name} tagline",
        description=f"{name} description",
        votes_count=votes,
        comments_count=comments,
        daily_rank=None,
        created_at="2026-05-10T08:00:00Z",
        featured_at="2026-05-10T08:00:00Z",
        website_url=f"https://example.com/{name.lower().replace(' ', '-')}",
        product_hunt_url=f"https://www.producthunt.com/posts/{name.lower().replace(' ', '-')}",
        media_urls=[],
        topics=["Productivity"],
        makers=["Maker"],
        raw={"name": name, "votesCount": votes, "commentsCount": comments},
    )


class FakeProductHuntClient:
    def __init__(self, products: list[Product] | None = None) -> None:
        self.products = products or [
            make_product("Pass Product", votes=500, comments=25),
            make_product("Fail Product", votes=1000, comments=2),
        ]
        self.calls: list[dict[str, object]] = []

    def fetch_posts_for_window(
        self,
        posted_after: str,
        posted_before: str,
        limit: int = 30,
        filters: ProductHuntPostFilters | None = None,
        context: str | None = None,
    ) -> tuple[list[Product], list[dict[str, object]]]:
        self.calls.append(
            {
                "posted_after": posted_after,
                "posted_before": posted_before,
                "limit": limit,
                "filters": filters,
                "context": context,
            }
        )
        return (
            self.products,
            [
                {
                    "data": {"posts": {"nodes": ["raw-node"]}},
                    "posted_after": posted_after,
                    "posted_before": posted_before,
                    "limit": limit,
                    "context": context,
                }
            ],
        )


class FakeLlmClient:
    def enrich_product(self, product: Product) -> ProductEnrichment:
        return ProductEnrichment(
            summary_zh=f"{product.name} 的中文说明",
            purpose_zh="有用产品",
            target_users_zh=["创业者"],
            use_cases_zh=["寻找工具"],
            example_workflow_zh=["打开产品", "试用功能"],
            why_interesting_zh="讨论和票数都不错。",
            caveat_zh="需要进一步验证。",
        )


class FailingLlmClient:
    def enrich_product(self, product: Product) -> ProductEnrichment:
        raise LlmError(f"boom for {product.name}")


class SelectiveLlmClient:
    def enrich_product(self, product: Product) -> ProductEnrichment:
        if product.name == "First Product":
            raise LlmError(f"temporary failure for {product.name}")
        return FakeLlmClient().enrich_product(product)


class ConfigFailingLlmClient:
    def enrich_product(self, product: Product) -> ProductEnrichment:
        raise ConfigError("LLM_API_KEY is required")


class LlmErrorFailingClient:
    def enrich_product(self, product: Product) -> ProductEnrichment:
        raise LlmError(f"upstream failed for {product.name}")


class UnexpectedLlmClient:
    def enrich_product(self, product: Product) -> ProductEnrichment:
        raise AssertionError("LLM should not be called in no-enrichment mode")


def make_settings(tmp_path) -> Settings:
    period_quality = {
        "daily": QualitySettings(300, 0.04, 8, 42),
        "weekly": QualitySettings(800, 0.035, 20, 150),
        "monthly": QualitySettings(1000, 0.03, 40, 200),
        "yearly": QualitySettings(5000, 0.02, 120, 300),
    }
    return Settings(
        product_hunt_token="ph-token",
        llm_base_url="https://example.com/v1",
        llm_api_key="llm-key",
        llm_model="model-a",
        min_votes=300,
        comment_ratio=0.04,
        min_comments=8,
        fetch_limit=42,
        period_quality=period_quality,
        output_formats=("markdown",),
        product_hunt_featured=None,
        product_hunt_order="VOTES",
        product_hunt_topic="",
        product_hunt_url="",
        product_hunt_twitter_url="",
        include_keywords=(),
        exclude_keywords=(),
        output_dir=str(tmp_path),
        http_timeout_seconds=10,
    )


def test_collect_writes_raw_processed_and_report(tmp_path):
    ph_client = FakeProductHuntClient()
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=ph_client,
        llm_client=FakeLlmClient(),
    )

    result = collector.collect("2026-05-10")

    assert ph_client.calls == [
        {
            "posted_after": "2026-05-10T00:00:00Z",
            "posted_before": "2026-05-10T23:59:59Z",
            "limit": 42,
            "filters": ProductHuntPostFilters(order="VOTES"),
            "context": "daily:2026-05-10",
        }
    ]
    assert result.fetched_count == 2
    assert result.selected_count == 1
    assert result.paths.raw_json.exists()
    assert result.paths.processed_json.exists()
    assert result.paths.markdown_report.exists()
    assert not result.paths.html_report.exists()

    report = result.paths.markdown_report.read_text(encoding="utf-8")
    assert "Pass Product 的中文说明" in report
    assert "Fail Product" not in report

    raw_data = json.loads(result.paths.raw_json.read_text(encoding="utf-8"))
    assert raw_data["date"] == "2026-05-10"
    assert raw_data["period"] == "daily"
    assert raw_data["posted_after"] == "2026-05-10T00:00:00Z"
    assert raw_data["posted_before"] == "2026-05-10T23:59:59Z"
    assert raw_data["source"] == "producthunt_api_v2_graphql"
    assert raw_data["raw_payloads"] == [
        {
            "data": {"posts": {"nodes": ["raw-node"]}},
            "posted_after": "2026-05-10T00:00:00Z",
            "posted_before": "2026-05-10T23:59:59Z",
            "limit": 42,
            "context": "daily:2026-05-10",
        }
    ]
    assert [product["name"] for product in raw_data["products"]] == [
        "Pass Product",
        "Fail Product",
    ]

    processed_data = json.loads(result.paths.processed_json.read_text(encoding="utf-8"))
    assert processed_data["filter"] == {
        "min_votes": 300,
        "min_comments": 8,
        "comment_ratio": 0.04,
        "rule": "votes >= 300 and comments_count >= max(8, ceil(votes * 0.04))",
        "include_keywords": [],
        "exclude_keywords": [],
    }
    assert processed_data["products"][0]["enrichment"]["purpose_zh"] == "有用产品"
    assert processed_data["products"][1]["enrichment"] is None


def test_collect_monthly_uses_month_window_and_period_quality(tmp_path):
    products = [
        make_product("Almost Monthly", votes=999, comments=80),
        make_product("Pass Monthly", votes=1200, comments=80),
    ]
    ph_client = FakeProductHuntClient(products=products)
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=ph_client,
        llm_client=FakeLlmClient(),
    )

    result = collector.collect_period("2026-05-12", period="monthly")

    assert ph_client.calls[0]["posted_after"] == "2026-05-01T00:00:00Z"
    assert ph_client.calls[0]["posted_before"] == "2026-05-31T23:59:59Z"
    assert ph_client.calls[0]["limit"] == 200
    assert ph_client.calls[0]["context"] == "monthly:2026-05"
    assert result.selected_count == 1
    assert str(result.paths.markdown_report).endswith("reports/monthly/2026-05.md")

    processed_data = json.loads(result.paths.processed_json.read_text(encoding="utf-8"))
    assert processed_data["period"] == "monthly"
    assert processed_data["output_key"] == "2026-05"
    assert processed_data["filter"]["min_votes"] == 1000
    assert processed_data["products"][0]["filter_decision"]["passed"] is False
    assert processed_data["products"][1]["filter_decision"]["passed"] is True


def test_collect_applies_keyword_filters_before_enrichment(tmp_path):
    products = [
        make_product("AI Research", votes=500, comments=30),
        make_product("Crypto Helper", votes=700, comments=40),
    ]
    settings = replace(
        make_settings(tmp_path),
        include_keywords=("ai",),
        exclude_keywords=("crypto",),
    )
    collector = Collector(
        settings=settings,
        product_hunt_client=FakeProductHuntClient(products=products),
        llm_client=FakeLlmClient(),
    )

    result = collector.collect("2026-05-10")

    assert result.selected_count == 1
    processed_data = json.loads(result.paths.processed_json.read_text(encoding="utf-8"))
    assert processed_data["filter"]["include_keywords"] == ["ai"]
    assert processed_data["filter"]["exclude_keywords"] == ["crypto"]
    assert processed_data["products"][0]["filter_decision"]["passed"] is True
    assert processed_data["products"][1]["filter_decision"]["passed"] is False
    assert (
        processed_data["products"][1]["filter_decision"]["reason"]
        == "excluded by keyword: crypto"
    )


def test_collect_passes_product_hunt_filters_from_settings(tmp_path):
    settings = replace(
        make_settings(tmp_path),
        product_hunt_featured=True,
        product_hunt_order="NEWEST",
        product_hunt_topic="artificial-intelligence",
        product_hunt_url="https://example.com",
        product_hunt_twitter_url="https://x.com/example",
    )
    ph_client = FakeProductHuntClient()
    collector = Collector(
        settings=settings,
        product_hunt_client=ph_client,
        llm_client=FakeLlmClient(),
    )

    collector.collect("2026-05-10")

    assert ph_client.calls[0]["filters"] == ProductHuntPostFilters(
        featured=True,
        order="NEWEST",
        topic="artificial-intelligence",
        url="https://example.com",
        twitter_url="https://x.com/example",
    )


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


def test_collect_raises_when_only_selected_product_fails_enrichment(tmp_path):
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=FakeProductHuntClient(),
        llm_client=FailingLlmClient(),
    )

    with pytest.raises(LlmError, match="No selected products could be enriched"):
        collector.collect("2026-05-10")


def test_collect_propagates_enrichment_config_error(tmp_path):
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=FakeProductHuntClient(),
        llm_client=ConfigFailingLlmClient(),
    )

    with pytest.raises(ConfigError, match="LLM_API_KEY is required"):
        collector.collect("2026-05-10")


def test_collect_allows_partial_selected_product_llm_failures(tmp_path):
    products = [
        make_product("First Product", votes=500, comments=25),
        make_product("Second Product", votes=600, comments=30),
    ]
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=FakeProductHuntClient(products=products),
        llm_client=SelectiveLlmClient(),
    )

    result = collector.collect("2026-05-10")

    assert result.selected_count == 2
    processed_data = json.loads(result.paths.processed_json.read_text(encoding="utf-8"))
    assert processed_data["products"][0]["enrichment"] is None
    assert (
        processed_data["products"][0]["enrichment_error"]
        == "temporary failure for First Product"
    )
    assert processed_data["products"][1]["enrichment"]["purpose_zh"] == "有用产品"


def test_collect_raises_when_all_selected_products_fail_enrichment(tmp_path):
    products = [
        make_product("First Product", votes=500, comments=25),
        make_product("Second Product", votes=600, comments=30),
    ]
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=FakeProductHuntClient(products=products),
        llm_client=LlmErrorFailingClient(),
    )

    with pytest.raises(LlmError, match="No selected products could be enriched"):
        collector.collect("2026-05-10")


def test_collect_writes_markdown_and_html_when_configured(tmp_path):
    settings = make_settings(tmp_path)
    settings = replace(settings, output_formats=("markdown", "html"))
    collector = Collector(
        settings=settings,
        product_hunt_client=FakeProductHuntClient(),
        llm_client=FakeLlmClient(),
    )

    result = collector.collect("2026-05-10")

    assert result.paths.markdown_report.exists()
    assert result.paths.html_report.exists()
    assert "Pass Product 的中文说明" in result.paths.markdown_report.read_text(
        encoding="utf-8"
    )
    assert "Pass Product 的中文说明" in result.paths.html_report.read_text(
        encoding="utf-8"
    )
