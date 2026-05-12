from __future__ import annotations

from html import escape

from ph_daily.models import ProcessedProduct
from ph_daily.report import friendly_enrichment_error


def _html_list(items: list[str]) -> str:
    if not items:
        return "<li>信息不足</li>"
    return "\n".join(f"<li>{escape(item)}</li>" for item in items)


def _stat(label: str, value: int | str) -> str:
    return (
        '<div class="stat">'
        f'<span class="stat-label">{escape(label)}</span>'
        f'<strong>{escape(str(value))}</strong>'
        "</div>"
    )


def render_html_report(
    date: str,
    fetched_count: int,
    processed_products: list[ProcessedProduct],
    filter_rule: str,
    period_label: str = "每日",
) -> str:
    selected_products = [
        item for item in processed_products if item.filter_decision.passed
    ]
    enrichment_success_count = sum(1 for item in selected_products if item.enrichment)
    enrichment_failure_count = len(selected_products) - enrichment_success_count

    product_sections = "\n".join(
        _render_product(index, item)
        for index, item in enumerate(selected_products, start=1)
    )
    if not product_sections:
        product_sections = '<p class="empty">今天没有产品通过筛选。</p>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Product Hunt {escape(period_label)}精选 - {escape(date)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f5f2;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #687385;
      --line: #dedbd3;
      --accent: #0f766e;
      --soft: #e8f3f0;
      --warn: #9a3412;
      --warn-bg: #fff7ed;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.65;
    }}
    main {{
      width: min(1040px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 56px;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      padding-bottom: 20px;
      margin-bottom: 24px;
    }}
    h1, h2, h3, h4 {{ line-height: 1.25; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    h2 {{ margin: 32px 0 16px; }}
    h3 {{ margin: 0; font-size: 24px; }}
    h4 {{ margin: 22px 0 8px; font-size: 16px; }}
    a {{ color: var(--accent); }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin: 20px 0;
    }}
    .stat, .product {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgba(31, 41, 51, 0.04);
    }}
    .stat {{ padding: 14px 16px; }}
    .stat-label {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 4px;
    }}
    .product {{
      padding: 22px;
      margin-bottom: 20px;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 12px 0 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    .pill {{
      background: var(--soft);
      color: #0f4f4a;
      border-radius: 999px;
      padding: 3px 10px;
    }}
    img {{
      display: block;
      max-width: min(100%, 760px);
      border-radius: 8px;
      border: 1px solid var(--line);
      margin: 14px 0 18px;
    }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin: 10px 0;
    }}
    .failure {{
      background: var(--warn-bg);
      color: var(--warn);
      border: 1px solid #fed7aa;
      border-radius: 8px;
      padding: 12px 14px;
      margin-top: 16px;
    }}
    .empty {{ color: var(--muted); }}
    code {{
      background: #ece9e1;
      border-radius: 4px;
      padding: 2px 5px;
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Product Hunt {escape(period_label)}精选</h1>
      <p>{escape(date)} 的高票且讨论充分产品摘要。</p>
    </header>
    <section aria-labelledby="summary-title">
      <h2 id="summary-title">概览</h2>
      <div class="summary">
        {_stat("抓取产品数", fetched_count)}
        {_stat("入选产品数", len(selected_products))}
        {_stat("AI 解读成功", enrichment_success_count)}
        {_stat("AI 解读失败", enrichment_failure_count)}
      </div>
      <p>筛选规则：<code>{escape(filter_rule)}</code></p>
    </section>
    <section aria-labelledby="products-title">
      <h2 id="products-title">入选产品</h2>
      {product_sections}
    </section>
  </main>
</body>
</html>
"""


def _render_product(index: int, item: ProcessedProduct) -> str:
    product = item.product
    enrichment = item.enrichment
    website = product.website_url or ""
    image = (
        f'<img src="{escape(product.media_urls[0], quote=True)}" '
        f'alt="{escape(product.name, quote=True)}">'
        if product.media_urls
        else ""
    )
    website_link = (
        f'<a href="{escape(website, quote=True)}">官网 / 跳转链接</a>'
        if website
        else '<span class="empty">未提供官网链接</span>'
    )

    if enrichment is None:
        body = (
            '<div class="failure">'
            f"{escape(friendly_enrichment_error(item.enrichment_error))}"
            "</div>"
        )
    else:
        body = f"""
        <h4>产品概述 / 它做什么</h4>
        <p>{escape(enrichment.summary_zh)}</p>
        <h4>核心用途</h4>
        <p>{escape(enrichment.purpose_zh)}</p>
        <h4>目标用户</h4>
        <ul>{_html_list(enrichment.target_users_zh)}</ul>
        <h4>使用场景</h4>
        <ul>{_html_list(enrichment.use_cases_zh)}</ul>
        <h4>示例工作流</h4>
        <ul>{_html_list(enrichment.example_workflow_zh)}</ul>
        <h4>为什么值得关注</h4>
        <p>{escape(enrichment.why_interesting_zh)}</p>
        <h4>注意事项</h4>
        <p>{escape(enrichment.caveat_zh)}</p>
        """

    return f"""
      <article class="product">
        <h3>{index}. {escape(product.name)}</h3>
        <div class="meta">
          <span class="pill">票数 {product.votes_count}</span>
          <span class="pill">评论 {product.comments_count}</span>
          <span>{escape(item.filter_decision.reason)}</span>
        </div>
        <div class="links">
          <a href="{escape(product.product_hunt_url, quote=True)}">Product Hunt 页面</a>
          {website_link}
        </div>
        {image}
        {body}
      </article>
    """
