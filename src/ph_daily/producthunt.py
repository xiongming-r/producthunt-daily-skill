from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from ph_daily.errors import ProductHuntError
from ph_daily.models import Product


def _snippet(text: str, secret: str | None = None, limit: int = 200) -> str:
    if secret:
        text = text.replace(secret, "[redacted]")
    text = " ".join(text.split())
    if len(text) > limit:
        return f"{text[:limit]}..."
    return text


class ProductHuntClient:
    endpoint = "https://api.producthunt.com/v2/api/graphql"

    def __init__(
        self,
        token: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    @staticmethod
    def build_posts_query() -> str:
        return """
        query DailyPosts($postedAfter: DateTime!, $postedBefore: DateTime!, $after: String) {
          posts(order: VOTES, postedAfter: $postedAfter, postedBefore: $postedBefore, after: $after) {
            nodes {
              id
              name
              tagline
              description
              votesCount
              commentsCount
              dailyRank
              createdAt
              featuredAt
              website
              url
              media {
                url
                type
                videoUrl
              }
              topics {
                nodes {
                  name
                }
              }
              makers {
                name
                username
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """

    def fetch_posts_for_date(
        self, date: str, limit: int = 30
    ) -> tuple[list[Product], list[dict[str, Any]]]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "ph-daily-agent/0.1.0",
        }
        posted_after = f"{date}T00:00:00Z"
        posted_before = f"{date}T23:59:59Z"
        cursor: str | None = None
        products: list[Product] = []
        raw_payloads: list[dict[str, Any]] = []

        with httpx.Client(
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            while len(products) < limit:
                payload = {
                    "query": self.build_posts_query(),
                    "variables": {
                        "postedAfter": posted_after,
                        "postedBefore": posted_before,
                        "after": cursor,
                    },
                }
                try:
                    response = client.post(self.endpoint, headers=headers, json=payload)
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    response = exc.response
                    raise ProductHuntError(
                        "Product Hunt request failed: "
                        f"date={date} endpoint={self.endpoint} "
                        f"status={response.status_code} "
                        f"snippet={_snippet(response.text, self.token)!r}"
                    ) from exc
                except httpx.HTTPError as exc:
                    raise ProductHuntError(
                        "Product Hunt request failed: "
                        f"date={date} endpoint={self.endpoint} error={exc}"
                    ) from exc

                try:
                    data = response.json()
                except ValueError as exc:
                    raise ProductHuntError(
                        f"Product Hunt response was not valid JSON: {exc}"
                    ) from exc

                if not isinstance(data, dict):
                    raise ProductHuntError("Product Hunt response must be a JSON object")

                raw_payloads.append(data)
                if data.get("errors"):
                    raise ProductHuntError(f"Product Hunt GraphQL error: {data['errors']}")

                data_obj = data.get("data")
                if not isinstance(data_obj, Mapping):
                    raise ProductHuntError("Product Hunt response missing data")

                posts = data_obj.get("posts")
                if not isinstance(posts, Mapping):
                    raise ProductHuntError("Product Hunt response missing data.posts")

                nodes = posts.get("nodes")
                if not isinstance(nodes, list):
                    raise ProductHuntError(
                        "Product Hunt response data.posts.nodes must be a list"
                    )
                for node in nodes:
                    if not isinstance(node, dict):
                        raise ProductHuntError(
                            "Product Hunt response contained invalid post node"
                        )
                    try:
                        products.append(Product.from_api_node(node))
                    except (AttributeError, TypeError, ValueError) as exc:
                        raise ProductHuntError(
                            f"Product Hunt post normalization failed: {exc}"
                        ) from exc

                page_info = posts.get("pageInfo")
                if not isinstance(page_info, Mapping):
                    raise ProductHuntError(
                        "Product Hunt response data.posts.pageInfo must be an object"
                    )
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                if not cursor:
                    raise ProductHuntError(
                        "Product Hunt response missing pageInfo.endCursor"
                    )

        products.sort(key=lambda item: item.votes_count, reverse=True)
        return products[:limit], raw_payloads

    def validate_fields(self) -> dict[str, bool]:
        products, _ = self.fetch_posts_for_date("2026-05-10", limit=1)
        if not products:
            return {"has_sample_product": False}
        product = products[0]
        return {
            "has_sample_product": True,
            "has_votes_count": isinstance(product.votes_count, int),
            "has_comments_count": isinstance(product.comments_count, int),
            "has_product_hunt_url": bool(product.product_hunt_url),
        }
