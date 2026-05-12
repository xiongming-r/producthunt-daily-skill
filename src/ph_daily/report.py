from __future__ import annotations

from ph_daily.models import ProcessedProduct


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- 信息不足"
    return "\n".join(f"- {item}" for item in items)


def friendly_enrichment_error(error: str | None) -> str:
    if not error:
        return "AI 解读失败：没有可用的错误信息。"
    if "timed out" in error.lower() or "timeout" in error.lower():
        return (
            "AI 解读失败：LLM 响应超时。"
            "建议稍后重试，或调高 HTTP_TIMEOUT_SECONDS。"
        )
    return "AI 解读失败：请查看 processed JSON 中的详细错误信息。"


def render_daily_report(
    date: str,
    fetched_count: int,
    processed_products: list[ProcessedProduct],
    filter_rule: str,
    period_label: str = "每日",
) -> str:
    selected_products = [
        processed_product
        for processed_product in processed_products
        if processed_product.filter_decision.passed
    ]
    enrichment_success_count = sum(
        1 for item in selected_products if item.enrichment is not None
    )
    enrichment_failure_count = len(selected_products) - enrichment_success_count

    sections = [
        f"# Product Hunt {period_label}精选 - {date}",
        "## 概览",
        f"- 抓取产品数：{fetched_count}",
        f"- 入选产品数：{len(selected_products)}",
        f"- AI 解读成功：{enrichment_success_count}",
        f"- AI 解读失败：{enrichment_failure_count}",
        f"- 筛选规则：`{filter_rule}`",
    ]

    if not selected_products:
        sections.append("今天没有产品通过筛选。")
        return "\n\n".join(sections) + "\n"

    sections.append("## 入选产品")

    for index, processed_product in enumerate(selected_products, start=1):
        product = processed_product.product
        enrichment = processed_product.enrichment
        website_url = product.website_url or "Not provided"

        lines = [
            f"### {index}. {product.name}",
            f"- Product Hunt 页面：{product.product_hunt_url}",
            f"- 官网 / 跳转链接：{website_url}",
            f"- 票数 / 评论数：{product.votes_count}/{product.comments_count}",
            f"- 筛选原因：{processed_product.filter_decision.reason}",
        ]

        if product.media_urls:
            lines.append(f"![{product.name}]({product.media_urls[0]})")

        if enrichment is None:
            message = friendly_enrichment_error(processed_product.enrichment_error)
            lines.extend(["", "#### AI 解读状态", message])
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
