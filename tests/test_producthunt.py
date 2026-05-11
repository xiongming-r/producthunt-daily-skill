import httpx
import pytest

from ph_daily.errors import ProductHuntError
from ph_daily.producthunt import ProductHuntClient


def test_build_posts_query_contains_required_fields():
    query = ProductHuntClient.build_posts_query()

    assert "votesCount" in query
    assert "commentsCount" in query
    assert "dailyRank" in query
    assert "media" in query
    assert "topics" in query
    assert "makers" in query


def test_fetch_posts_normalizes_products(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["Authorization"]
        return httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [
                            {
                                "id": "123",
                                "name": "Acme AI",
                                "tagline": "Automate support replies",
                                "description": "Draft support replies.",
                                "votesCount": 512,
                                "commentsCount": 33,
                                "dailyRank": 4,
                                "createdAt": "2026-05-10T08:00:00Z",
                                "featuredAt": None,
                                "website": "https://example.com",
                                "url": "https://www.producthunt.com/posts/acme-ai",
                                "media": [],
                                "topics": {"nodes": []},
                                "makers": {"nodes": []},
                            }
                        ],
                        "pageInfo": {
                            "hasNextPage": False,
                            "endCursor": None,
                        },
                    }
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    products, raw_payloads = client.fetch_posts_for_date("2026-05-10", limit=30)

    assert captured["authorization"] == "Bearer token-1"
    assert len(products) == 1
    assert products[0].name == "Acme AI"
    assert products[0].comments_count == 33
    assert raw_payloads[0]["data"]["posts"]["nodes"][0]["id"] == "123"


def test_fetch_posts_raises_on_graphql_errors():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"errors": [{"message": "bad query"}]})
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(ProductHuntError, match="Product Hunt GraphQL error"):
        client.fetch_posts_for_date("2026-05-10", limit=30)
