import json

from ph_daily.collector import Collector
from ph_daily.config import Settings
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
    def fetch_posts_for_date(
        self, date: str, limit: int = 30
    ) -> tuple[list[Product], list[dict[str, object]]]:
        return (
            [
                make_product("Pass Product", votes=500, comments=25),
                make_product("Fail Product", votes=1000, comments=2),
            ],
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
        raise RuntimeError(f"boom for {product.name}")


def make_settings(tmp_path) -> Settings:
    return Settings(
        product_hunt_token="ph-token",
        llm_base_url="https://example.com/v1",
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

    report = result.paths.markdown_report.read_text(encoding="utf-8")
    assert "Pass Product 的中文说明" in report
    assert "Fail Product" not in report

    raw_data = json.loads(result.paths.raw_json.read_text(encoding="utf-8"))
    assert raw_data["date"] == "2026-05-10"
    assert raw_data["source"] == "producthunt_api_v2_graphql"
    assert raw_data["raw_payloads"] == [
        {"data": {"posts": {"nodes": ["raw-node"]}}, "date": "2026-05-10", "limit": 30}
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


def test_collect_keeps_selected_product_when_enrichment_fails(tmp_path):
    collector = Collector(
        settings=make_settings(tmp_path),
        product_hunt_client=FakeProductHuntClient(),
        llm_client=FailingLlmClient(),
    )

    result = collector.collect("2026-05-10")

    assert result.fetched_count == 2
    assert result.selected_count == 1

    processed_data = json.loads(result.paths.processed_json.read_text(encoding="utf-8"))
    selected_product = processed_data["products"][0]
    assert selected_product["product"]["name"] == "Pass Product"
    assert selected_product["filter_decision"]["passed"] is True
    assert selected_product["enrichment"] is None
    assert selected_product["enrichment_error"] == "boom for Pass Product"

    report = result.paths.markdown_report.read_text(encoding="utf-8")
    assert "### 1. Pass Product" in report
    assert "boom for Pass Product" in report
