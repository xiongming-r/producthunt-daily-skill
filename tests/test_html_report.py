from ph_daily.html_report import render_html_report
from ph_daily.models import FilterDecision, ProcessedProduct, Product, ProductEnrichment


def make_processed_product(
    *,
    name: str = "Acme <AI>",
    enrichment: ProductEnrichment | None = None,
    enrichment_error: str | None = None,
) -> ProcessedProduct:
    return ProcessedProduct(
        product=Product(
            id="123",
            name=name,
            tagline="Automate support replies",
            description="Draft support replies.",
            votes_count=512,
            comments_count=33,
            daily_rank=4,
            created_at="2026-05-10T08:00:00Z",
            featured_at=None,
            website_url="https://example.com?a=1&b=2",
            product_hunt_url="https://www.producthunt.com/posts/acme-ai",
            media_urls=["https://ph-files.imgix.net/acme.png?auto=format&fit=crop"],
            topics=[],
            makers=[],
            raw={},
        ),
        filter_decision=FilterDecision(
            passed=True,
            reason="votes 512 >= 300 and comments 33 >= required 21",
            required_comments=21,
        ),
        enrichment=enrichment,
        enrichment_error=enrichment_error,
    )


def make_enrichment() -> ProductEnrichment:
    return ProductEnrichment(
        summary_zh="Acme AI 会读取团队文档，并自动草拟客服回复。",
        purpose_zh="帮助团队把知识库转成客服答案。",
        target_users_zh=["客服团队"],
        use_cases_zh=["处理重复客户问题"],
        example_workflow_zh=["连接知识库", "审核回复"],
        why_interesting_zh="它能减少重复劳动。",
        caveat_zh="需要确认权限控制。",
    )


def test_render_html_report_contains_readable_sections_and_escapes_text():
    html = render_html_report(
        date="2026-05-10",
        fetched_count=12,
        processed_products=[make_processed_product(enrichment=make_enrichment())],
        filter_rule="votes >= 300 and comments_count >= max(8, ceil(votes * 0.04))",
    )

    assert "<!doctype html>" in html
    assert "Product Hunt 每日精选" in html
    assert "抓取产品数" in html
    assert "入选产品数" in html
    assert "AI 解读成功" in html
    assert "Acme &lt;AI&gt;" in html
    assert "Acme <AI>" not in html
    assert "产品概述 / 它做什么" in html
    assert "客服团队" in html
    assert "https://example.com?a=1&amp;b=2" in html


def test_render_html_report_uses_friendly_error_message():
    html = render_html_report(
        date="2026-05-10",
        fetched_count=1,
        processed_products=[
            make_processed_product(
                enrichment=None,
                enrichment_error="LLM request failed: read operation timed out",
            )
        ],
        filter_rule="votes >= 300",
    )

    assert "AI 解读失败" in html
    assert "LLM 响应超时" in html
    assert "LLM request failed" not in html
