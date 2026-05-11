from ph_daily.models import FilterDecision, ProcessedProduct, Product, ProductEnrichment
from ph_daily.report import render_daily_report
from ph_daily.storage import build_output_paths


def make_processed_product() -> ProcessedProduct:
    return ProcessedProduct(
        product=Product(
            id="123",
            name="Acme AI",
            tagline="Automate support replies with context",
            description="Acme AI reads your docs and drafts support answers.",
            votes_count=512,
            comments_count=33,
            daily_rank=4,
            created_at="2026-05-10T08:00:00Z",
            featured_at="2026-05-10T08:00:00Z",
            website_url="https://example.com",
            product_hunt_url="https://www.producthunt.com/posts/acme-ai",
            media_urls=["https://ph-files.imgix.net/acme.png"],
            topics=["Artificial Intelligence"],
            makers=["Jane Maker"],
            raw={"id": "123"},
        ),
        filter_decision=FilterDecision(
            passed=True,
            reason="votes 512 >= 300 and comments 33 >= 21",
            required_comments=21,
        ),
        enrichment=ProductEnrichment(
            summary_zh="Acme AI 会读取团队文档，并自动草拟客服回复。",
            purpose_zh="帮助团队把分散的知识库转成可复用的客服答案。",
            target_users_zh=["客服团队", "运营负责人"],
            use_cases_zh=["处理重复客户问题", "统一回复口径"],
            example_workflow_zh=["连接知识库", "导入历史工单", "审核并发送回复"],
            why_interesting_zh="它把内部文档和客服执行连接起来，降低新人上手成本。",
            caveat_zh="需要确认它对中文知识库和权限控制的支持程度。",
        ),
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
    assert "帮助团队把分散的知识库转成可复用的客服答案" in report
