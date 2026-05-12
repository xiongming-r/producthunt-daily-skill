from __future__ import annotations

from ph_daily.models import Product


def normalize_keywords(items: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(item.strip().lower() for item in items if item.strip())


def product_search_text(product: Product) -> str:
    parts = [
        product.name,
        product.tagline,
        product.description,
        " ".join(product.topics),
    ]
    return " ".join(parts).lower()


def keyword_filter_reason(
    product: Product,
    include_keywords: tuple[str, ...] = (),
    exclude_keywords: tuple[str, ...] = (),
) -> str | None:
    text = product_search_text(product)
    excluded = [keyword for keyword in exclude_keywords if keyword in text]
    if excluded:
        return f"excluded by keyword: {excluded[0]}"

    if include_keywords and not any(keyword in text for keyword in include_keywords):
        return "missing required include keyword"

    return None
