import json

import httpx
import pytest

from ph_daily.errors import ProductHuntError
from ph_daily.producthunt import ProductHuntClient, ProductHuntPostFilters


def test_build_posts_query_contains_required_fields():
    query = ProductHuntClient.build_posts_query()

    assert "votesCount" in query
    assert "commentsCount" in query
    assert "dailyRank" in query
    assert "media" in query
    assert "topics" in query
    assert "makers" in query
    assert "makers {\n                nodes" not in query


def test_fetch_posts_normalizes_products():
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
                                "makers": [],
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


def test_fetch_posts_sends_date_bounds_and_headers():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["variables"] = json.loads(request.content)["variables"]
        captured["headers"] = request.headers
        return httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [],
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

    client.fetch_posts_for_date("2026-05-10", limit=30)

    assert captured["variables"]["postedAfter"] == "2026-05-10T00:00:00Z"
    assert captured["variables"]["postedBefore"] == "2026-05-10T23:59:59Z"
    assert captured["headers"]["Authorization"] == "Bearer token-1"
    assert captured["headers"]["Accept"] == "application/json"
    assert captured["headers"]["Content-Type"].startswith("application/json")
    assert captured["headers"]["User-Agent"] == "ph-daily-agent/0.1.0"


def test_fetch_posts_sends_official_post_filters():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["variables"] = json.loads(request.content)["variables"]
        return httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [],
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

    client.fetch_posts_for_date(
        "2026-05-10",
        limit=30,
        filters=ProductHuntPostFilters(
            featured=True,
            order="FEATURED_AT",
            topic="artificial-intelligence",
            url="https://example.com",
            twitter_url="https://x.com/example",
        ),
    )

    assert captured["variables"]["first"] == 30
    assert captured["variables"]["featured"] is True
    assert captured["variables"]["order"] == "FEATURED_AT"
    assert captured["variables"]["topic"] == "artificial-intelligence"
    assert captured["variables"]["url"] == "https://example.com"
    assert captured["variables"]["twitterUrl"] == "https://x.com/example"


def test_fetch_posts_applies_limit_after_vote_sorting():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [
                            {
                                "id": "1",
                                "name": "Lower Vote Product",
                                "votesCount": 10,
                                "commentsCount": 1,
                            },
                            {
                                "id": "2",
                                "name": "Higher Vote Product",
                                "votesCount": 90,
                                "commentsCount": 2,
                            },
                        ],
                        "pageInfo": {
                            "hasNextPage": False,
                            "endCursor": None,
                        },
                    }
                }
            },
        )
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    products, _ = client.fetch_posts_for_date("2026-05-10", limit=1)

    assert len(products) == 1
    assert products[0].name == "Higher Vote Product"


def test_fetch_posts_raises_on_graphql_errors():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"errors": [{"message": "bad query"}]})
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(ProductHuntError, match="Product Hunt GraphQL error"):
        client.fetch_posts_for_date("2026-05-10", limit=30)


def test_fetch_posts_paginates_with_end_cursor():
    requested_after_values = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_after_values.append(json.loads(request.content)["variables"]["after"])
        if len(requested_after_values) == 1:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "posts": {
                            "nodes": [
                                {
                                    "id": "1",
                                    "name": "First",
                                    "votesCount": 10,
                                    "commentsCount": 1,
                                }
                            ],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": "cursor-1",
                            },
                        }
                    }
                },
            )

        return httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [
                            {
                                "id": "2",
                                "name": "Second",
                                "votesCount": 20,
                                "commentsCount": 2,
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

    assert requested_after_values == [None, "cursor-1"]
    assert [product.name for product in products] == ["Second", "First"]
    assert len(raw_payloads) == 2


def test_fetch_posts_raises_on_http_status_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            text="server failed while using token token-1",
            request=request,
        )

    transport = httpx.MockTransport(handler)
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(ProductHuntError) as exc_info:
        client.fetch_posts_for_date("2026-05-10", limit=30)

    message = str(exc_info.value)
    assert "Product Hunt request failed" in message
    assert "context=2026-05-10" in message
    assert "endpoint=https://api.producthunt.com/v2/api/graphql" in message
    assert "status=500" in message
    assert "server failed" in message
    assert "token-1" not in message


def test_fetch_posts_raises_on_malformed_json():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(
        ProductHuntError,
        match="Product Hunt response was not valid JSON",
    ):
        client.fetch_posts_for_date("2026-05-10", limit=30)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"data": None}, "Product Hunt response missing data"),
        ({"data": {}}, "Product Hunt response missing data.posts"),
        ({"data": {"posts": None}}, "Product Hunt response missing data.posts"),
        ({"data": {"posts": []}}, "Product Hunt response missing data.posts"),
        (
            {"data": {"posts": {"nodes": None, "pageInfo": {"hasNextPage": False}}}},
            "Product Hunt response data.posts.nodes must be a list",
        ),
        (
            {"data": {"posts": {"nodes": {}, "pageInfo": {"hasNextPage": False}}}},
            "Product Hunt response data.posts.nodes must be a list",
        ),
        (
            {"data": {"posts": {"nodes": [], "pageInfo": None}}},
            "Product Hunt response data.posts.pageInfo must be an object",
        ),
        (
            {"data": {"posts": {"nodes": [], "pageInfo": []}}},
            "Product Hunt response data.posts.pageInfo must be an object",
        ),
    ],
)
def test_fetch_posts_raises_on_invalid_response_shape(payload, message):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(ProductHuntError, match=message):
        client.fetch_posts_for_date("2026-05-10", limit=30)


def test_fetch_posts_raises_when_next_page_cursor_is_missing():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [],
                        "pageInfo": {
                            "hasNextPage": True,
                            "endCursor": "",
                        },
                    }
                }
            },
        )
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(
        ProductHuntError,
        match="Product Hunt response missing pageInfo.endCursor",
    ):
        client.fetch_posts_for_date("2026-05-10", limit=30)


def test_fetch_posts_raises_when_post_node_is_not_object():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [None],
                        "pageInfo": {
                            "hasNextPage": False,
                            "endCursor": None,
                        },
                    }
                }
            },
        )
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(ProductHuntError, match="invalid post node"):
        client.fetch_posts_for_date("2026-05-10", limit=30)


def test_fetch_posts_wraps_post_normalization_failure():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [
                            {
                                "id": "1",
                                "media": [None],
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
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    with pytest.raises(ProductHuntError, match="post normalization failed"):
        client.fetch_posts_for_date("2026-05-10", limit=30)


def test_validate_fields_reports_sample_product_fields():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [
                            {
                                "id": "123",
                                "name": "Acme AI",
                                "votesCount": 512,
                                "commentsCount": 33,
                                "url": "https://www.producthunt.com/posts/acme-ai",
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
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    assert client.validate_fields() == {
        "has_sample_product": True,
        "has_votes_count": True,
        "has_comments_count": True,
        "has_product_hunt_url": True,
    }


def test_validate_fields_reports_no_sample_product():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "posts": {
                        "nodes": [],
                        "pageInfo": {
                            "hasNextPage": False,
                            "endCursor": None,
                        },
                    }
                }
            },
        )
    )
    client = ProductHuntClient("token-1", timeout_seconds=5, transport=transport)

    assert client.validate_fields() == {"has_sample_product": False}
