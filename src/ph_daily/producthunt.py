from __future__ import annotations

from typing import Any

import httpx

from ph_daily.errors import ProductHuntError
from ph_daily.models import Product


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
                nodes {
                  name
                  username
                }
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
                except httpx.HTTPError as exc:
                    raise ProductHuntError(f"Product Hunt request failed: {exc}") from exc

                data = response.json()
                raw_payloads.append(data)
                if data.get("errors"):
                    raise ProductHuntError(f"Product Hunt GraphQL error: {data['errors']}")

                posts = data.get("data", {}).get("posts")
                if not posts:
                    raise ProductHuntError("Product Hunt response missing data.posts")

                nodes = posts.get("nodes", [])
                products.extend(Product.from_api_node(node) for node in nodes)

                page_info = posts.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
                if not cursor:
                    break

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
