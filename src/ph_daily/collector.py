from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ph_daily.config import Settings
from ph_daily.errors import ConfigError, LlmError
from ph_daily.html_report import render_html_report
from ph_daily.llm import LlmClient
from ph_daily.models import ProcessedProduct, Product, ProductEnrichment
from ph_daily.producthunt import ProductHuntClient
from ph_daily.quality import evaluate_product
from ph_daily.report import render_daily_report
from ph_daily.storage import OutputPaths, build_output_paths, write_json, write_text


class ProductHuntClientProtocol(Protocol):
    def fetch_posts_for_date(
        self, date: str, limit: int = 100
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
        products, raw_payloads = self.product_hunt_client.fetch_posts_for_date(
            date,
            limit=self.settings.fetch_limit,
        )

        processed_products: list[ProcessedProduct] = []
        successful_enrichments = 0
        for product in products:
            filter_decision = evaluate_product(
                product,
                min_votes=self.settings.min_votes,
                min_comments=self.settings.min_comments,
                comment_ratio=self.settings.comment_ratio,
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

        paths = build_output_paths(self.settings.output_dir, date)
        filter_rule = self._filter_rule()
        raw_payload = {
            "date": date,
            "source": "producthunt_api_v2_graphql",
            "raw_payloads": raw_payloads,
            "products": [product.raw for product in products],
        }
        processed_payload = {
            "date": date,
            "filter": {
                "min_votes": self.settings.min_votes,
                "min_comments": self.settings.min_comments,
                "comment_ratio": self.settings.comment_ratio,
                "rule": filter_rule,
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
            )
            write_text(paths.markdown_report, report)
        if "html" in self.settings.output_formats:
            html_report = render_html_report(
                date=date,
                fetched_count=len(products),
                processed_products=processed_products,
                filter_rule=filter_rule,
            )
            write_text(paths.html_report, html_report)

        return CollectionResult(
            date=date,
            fetched_count=len(products),
            selected_count=selected_count,
            paths=paths,
        )

    def _filter_rule(self) -> str:
        return (
            f"votes >= {self.settings.min_votes} and comments_count >= "
            f"max({self.settings.min_comments}, "
            f"ceil(votes * {self.settings.comment_ratio:g}))"
        )
