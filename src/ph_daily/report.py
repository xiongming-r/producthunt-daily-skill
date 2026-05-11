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
    selected_products = [
        processed_product
        for processed_product in processed_products
        if processed_product.filter_decision.passed
    ]

    sections = [
        f"# Product Hunt Daily Report - {date}",
        "## Summary",
        f"Products fetched: {fetched_count}",
        f"Products passing filters: {len(selected_products)}",
        f"Filter rule: `{filter_rule}`",
    ]

    if not selected_products:
        sections.append("No products passed the filter today.")
        return "\n\n".join(sections) + "\n"

    sections.append("## Products")

    for index, processed_product in enumerate(selected_products, start=1):
        product = processed_product.product
        enrichment = processed_product.enrichment
        website_url = product.website_url or "Not provided"

        lines = [
            f"### {index}. {product.name}",
            f"- Product Hunt: {product.product_hunt_url}",
            f"- Website: {website_url}",
            f"- Votes/comments: {product.votes_count}/{product.comments_count}",
            f"- Filter reason: {processed_product.filter_decision.reason}",
        ]

        if product.media_urls:
            lines.append(f"![{product.name}]({product.media_urls[0]})")

        if enrichment is None:
            message = processed_product.enrichment_error or "No enrichment available"
            lines.extend(["", "#### Enrichment", message])
        else:
            lines.extend(
                [
                    "",
                    "#### 产品概述 / 它做什么",
                    enrichment.summary_zh,
                    "",
                    "#### 核心用途",
                    enrichment.purpose_zh,
                    "",
                    "#### 目标用户",
                    _bullet_list(enrichment.target_users_zh),
                    "",
                    "#### 使用场景",
                    _bullet_list(enrichment.use_cases_zh),
                    "",
                    "#### 示例工作流",
                    _bullet_list(enrichment.example_workflow_zh),
                    "",
                    "#### 为什么值得关注",
                    enrichment.why_interesting_zh,
                    "",
                    "#### 注意事项",
                    enrichment.caveat_zh,
                ]
            )

        sections.append("\n".join(lines))

    return "\n\n".join(sections) + "\n"
