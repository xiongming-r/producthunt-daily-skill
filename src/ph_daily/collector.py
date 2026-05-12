from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ph_daily.config import Settings
from ph_daily.llm import LlmClient
from ph_daily.models import ProcessedProduct, Product, ProductEnrichment
from ph_daily.producthunt import ProductHuntClient
from ph_daily.quality import evaluate_product
from ph_daily.report import render_daily_report
from ph_daily.storage import OutputPaths, build_output_paths, write_json, write_text


class ProductHuntClientProtocol(Protocol):
    def fetch_posts_for_date(
        self, date: str, limit: int = 30
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
            limit=30,
        )

        processed_products: list[ProcessedProduct] = []
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
                except Exception as exc:  # noqa: BLE001 - one bad enrichment must not fail collection.
                    enrichment_error = str(exc)

            processed_products.append(
                ProcessedProduct(
                    product=product,
                    filter_decision=filter_decision,
                    enrichment=enrichment,
                    enrichment_error=enrichment_error,
                )
            )

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
        report = render_daily_report(
            date=date,
            fetched_count=len(products),
            processed_products=processed_products,
            filter_rule=filter_rule,
        )

        write_json(paths.raw_json, raw_payload)
        write_json(paths.processed_json, processed_payload)
        write_text(paths.markdown_report, report)

        selected_count = sum(
            processed_product.filter_decision.passed
            for processed_product in processed_products
        )
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
