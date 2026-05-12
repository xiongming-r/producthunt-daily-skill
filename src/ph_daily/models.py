from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    tagline: str
    description: str
    votes_count: int
    comments_count: int
    daily_rank: int | None
    created_at: str
    featured_at: str | None
    website_url: str
    product_hunt_url: str
    media_urls: list[str]
    topics: list[str]
    makers: list[str]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_api_node(cls, node: dict[str, Any]) -> "Product":
        media_nodes = node.get("media") or []
        topic_nodes = (node.get("topics") or {}).get("nodes") or []
        raw_makers = node.get("makers") or []
        if isinstance(raw_makers, dict):
            maker_nodes = raw_makers.get("nodes") or []
        else:
            maker_nodes = raw_makers

        media_urls = [
            media.get("url", "")
            for media in media_nodes
            if media.get("url")
        ]
        topics = [
            topic.get("name", "")
            for topic in topic_nodes
            if topic.get("name")
        ]
        makers = [
            maker.get("name") or maker.get("username", "")
            for maker in maker_nodes
            if maker.get("name") or maker.get("username")
        ]

        return cls(
            id=str(node.get("id", "")),
            name=node.get("name") or "",
            tagline=node.get("tagline") or "",
            description=node.get("description") or "",
            votes_count=int(node.get("votesCount") or 0),
            comments_count=int(node.get("commentsCount") or 0),
            daily_rank=node.get("dailyRank"),
            created_at=node.get("createdAt") or "",
            featured_at=node.get("featuredAt"),
            website_url=node.get("website") or "",
            product_hunt_url=node.get("url") or "",
            media_urls=media_urls,
            topics=topics,
            makers=makers,
            raw=node,
        )


@dataclass(frozen=True)
class FilterDecision:
    passed: bool
    reason: str
    required_comments: int


@dataclass(frozen=True)
class ProductEnrichment:
    purpose_zh: str
    summary_zh: str
    target_users_zh: list[str]
    use_cases_zh: list[str]
    example_workflow_zh: list[str]
    why_interesting_zh: str
    caveat_zh: str


@dataclass(frozen=True)
class ProcessedProduct:
    product: Product
    filter_decision: FilterDecision
    enrichment: ProductEnrichment | None = None
    enrichment_error: str | None = None
