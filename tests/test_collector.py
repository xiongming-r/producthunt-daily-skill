import json

import pytest

from ph_daily.collector import Collector
from ph_daily.config import Settings
from ph_daily.errors import ConfigError, LlmError
from ph_daily.models import Product, ProductEnrichment


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
        self.calls: list[tuple[str, int]] = []

    def fetch_posts_for_date(
        self, date: str, limit: int = 30
    ) -> tuple[list[Product], list[dict[str, object]]]:
        self.calls.append((date, limit))
        return (
            self.products,
            [{"data": {"posts": {"nodes": ["raw-node"]}}, "date": date, "limit": limit}],
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


def make_settings(tmp_path) -> Settings:
    return Settings(
        product_hunt_token="ph-token",
        llm_base_url="https://example.com/v1",
        llm_api_key="llm-key",
        llm_model="model-a",
        min_votes=300,
        comment_ratio=0.04,
        min_comments=8,
        fetch_limit=42,
        output_formats=("markdown",),
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

    assert ph_client.calls == [("2026-05-10", 42)]
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
    assert raw_data["source"] == "producthunt_api_v2_graphql"
    assert raw_data["raw_payloads"] == [
        {"data": {"posts": {"nodes": ["raw-node"]}}, "date": "2026-05-10", "limit": 42}
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
    }
    assert processed_data["products"][0]["enrichment"]["purpose_zh"] == "有用产品"
    assert processed_data["products"][1]["enrichment"] is None


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
    settings = Settings(
        product_hunt_token=settings.product_hunt_token,
        llm_base_url=settings.llm_base_url,
        llm_api_key=settings.llm_api_key,
        llm_model=settings.llm_model,
        min_votes=settings.min_votes,
        comment_ratio=settings.comment_ratio,
        min_comments=settings.min_comments,
        fetch_limit=settings.fetch_limit,
        output_formats=("markdown", "html"),
        output_dir=settings.output_dir,
        http_timeout_seconds=settings.http_timeout_seconds,
    )
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
