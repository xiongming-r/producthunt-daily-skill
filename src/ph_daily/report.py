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
            lines.append(f"- Media: {product.media_urls[0]}")

        if enrichment is None:
            message = processed_product.enrichment_error or "No enrichment available"
            lines.extend(["", "#### Enrichment", message])
        else:
            lines.extend(
                [
                    "",
                    "#### Summary / What it does",
                    enrichment.summary_zh,
                    "",
                    "#### Purpose",
                    enrichment.purpose_zh,
                    "",
                    "#### Target users",
                    _bullet_list(enrichment.target_users_zh),
                    "",
                    "#### Use cases",
                    _bullet_list(enrichment.use_cases_zh),
                    "",
                    "#### Example workflow",
                    _bullet_list(enrichment.example_workflow_zh),
                    "",
                    "#### Why interesting",
                    enrichment.why_interesting_zh,
                    "",
                    "#### Caveat",
                    enrichment.caveat_zh,
                ]
            )

        sections.append("\n".join(lines))

    return "\n\n".join(sections) + "\n"
