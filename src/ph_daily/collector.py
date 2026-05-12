from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ph_daily.config import Settings
from ph_daily.errors import ConfigError, LlmError
from ph_daily.filters import keyword_filter_reason
from ph_daily.html_report import render_html_report
from ph_daily.llm import LlmClient
from ph_daily.models import FilterDecision, ProcessedProduct, Product, ProductEnrichment
from ph_daily.periods import build_period_window
from ph_daily.producthunt import ProductHuntClient, ProductHuntPostFilters
from ph_daily.quality import evaluate_product
from ph_daily.report import render_daily_report
from ph_daily.storage import OutputPaths, build_output_paths, write_json, write_text


class ProductHuntClientProtocol(Protocol):
    def fetch_posts_for_window(
        self,
        posted_after: str,
        posted_before: str,
        limit: int = 100,
        filters: ProductHuntPostFilters | None = None,
        context: str | None = None,
    ) -> tuple[list[Product], list[dict[str, Any]]]:
        ...


class LlmClientProtocol(Protocol):
    def enrich_product(self, product: Product) -> ProductEnrichment:
        ...


@dataclass(frozen=True)
class CollectionResult:
    date: str
    fetched_count: int
    selected_count: int
    paths: OutputPaths


class Collector:
    def __init__(
        self,
        settings: Settings,
        product_hunt_client: ProductHuntClientProtocol | None = None,
        llm_client: LlmClientProtocol | None = None,
    ) -> None:
        self.settings = settings
        self.product_hunt_client = product_hunt_client or ProductHuntClient(
            token=settings.product_hunt_token,
            timeout_seconds=settings.http_timeout_seconds,
        )
        self.llm_client = llm_client or LlmClient(settings)

    def collect(self, date: str) -> CollectionResult:
        return self.collect_period(date=date, period="daily")

    def collect_period(
        self,
        date: str,
        period: str = "daily",
        post_filters: ProductHuntPostFilters | None = None,
        include_keywords: tuple[str, ...] | None = None,
        exclude_keywords: tuple[str, ...] | None = None,
    ) -> CollectionResult:
        window = build_period_window(period, date)
        quality = self.settings.quality_for_period(window.period)
        active_filters = post_filters or self._settings_post_filters()
        active_include_keywords = (
            self.settings.include_keywords
            if include_keywords is None
            else include_keywords
        )
        active_exclude_keywords = (
            self.settings.exclude_keywords
            if exclude_keywords is None
            else exclude_keywords
        )
        products, raw_payloads = self.product_hunt_client.fetch_posts_for_window(
            posted_after=window.posted_after,
            posted_before=window.posted_before,
            limit=quality.fetch_limit,
            filters=active_filters,
            context=f"{window.period}:{window.output_key}",
        )

        processed_products: list[ProcessedProduct] = []
        successful_enrichments = 0
        for product in products:
            keyword_reason = keyword_filter_reason(
                product,
                include_keywords=active_include_keywords,
                exclude_keywords=active_exclude_keywords,
            )
            if keyword_reason is None:
                filter_decision = evaluate_product(
                    product,
                    min_votes=quality.min_votes,
                    min_comments=quality.min_comments,
                    comment_ratio=quality.comment_ratio,
                )
            else:
                filter_decision = FilterDecision(
                    passed=False,
                    reason=keyword_reason,
                    required_comments=0,
                )
            enrichment: ProductEnrichment | None = None
            enrichment_error: str | None = None

            if filter_decision.passed:
                try:
                    enrichment = self.llm_client.enrich_product(product)
                    successful_enrichments += 1
                except ConfigError:
                    raise
                except LlmError as exc:
                    enrichment_error = str(exc)

            processed_products.append(
                ProcessedProduct(
                    product=product,
                    filter_decision=filter_decision,
                    enrichment=enrichment,
                    enrichment_error=enrichment_error,
                )
            )

        selected_count = sum(
            processed_product.filter_decision.passed
            for processed_product in processed_products
        )
        if selected_count and successful_enrichments == 0:
            raise LlmError("No selected products could be enriched")

        paths = build_output_paths(
            self.settings.output_dir,
            date,
            period=window.period,
            output_key=window.output_key,
        )
        filter_rule = self._filter_rule(quality)
        raw_payload = {
            "date": window.anchor_date.isoformat(),
            "period": window.period,
            "posted_after": window.posted_after,
            "posted_before": window.posted_before,
            "source": "producthunt_api_v2_graphql",
            "raw_payloads": raw_payloads,
            "products": [product.raw for product in products],
        }
        processed_payload = {
            "date": window.anchor_date.isoformat(),
            "period": window.period,
            "output_key": window.output_key,
            "filter": {
                "min_votes": quality.min_votes,
                "min_comments": quality.min_comments,
                "comment_ratio": quality.comment_ratio,
                "rule": filter_rule,
                "include_keywords": active_include_keywords,
                "exclude_keywords": active_exclude_keywords,
            },
            "products": processed_products,
        }
        write_json(paths.raw_json, raw_payload)
        write_json(paths.processed_json, processed_payload)

        if "markdown" in self.settings.output_formats:
            report = render_daily_report(
                date=date,
                fetched_count=len(products),
                processed_products=processed_products,
                filter_rule=filter_rule,
                period_label=window.label_zh,
            )
            write_text(paths.markdown_report, report)
        if "html" in self.settings.output_formats:
            html_report = render_html_report(
                date=date,
                fetched_count=len(products),
                processed_products=processed_products,
                filter_rule=filter_rule,
                period_label=window.label_zh,
            )
            write_text(paths.html_report, html_report)

        return CollectionResult(
            date=window.anchor_date.isoformat(),
            fetched_count=len(products),
            selected_count=selected_count,
            paths=paths,
        )

    def _settings_post_filters(self) -> ProductHuntPostFilters:
        return ProductHuntPostFilters(
            featured=self.settings.product_hunt_featured,
            order=self.settings.product_hunt_order,
            topic=self.settings.product_hunt_topic,
            url=self.settings.product_hunt_url,
            twitter_url=self.settings.product_hunt_twitter_url,
        )

    def _filter_rule(self, quality) -> str:
        return (
            f"votes >= {quality.min_votes} and comments_count >= "
            f"max({quality.min_comments}, "
            f"ceil(votes * {quality.comment_ratio:g}))"
        )
