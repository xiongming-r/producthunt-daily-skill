from ph_daily.filters import keyword_filter_reason, normalize_keywords
from ph_daily.models import Product


def make_product() -> Product:
    return Product(
        id="1",
        name="AI Agent Builder",
        tagline="Build developer tools with agents",
        description="A platform for coding automation.",
        votes_count=500,
        comments_count=30,
        daily_rank=1,
        created_at="2026-05-11T00:00:00Z",
        featured_at=None,
        website_url="https://example.com",
        product_hunt_url="https://producthunt.com/posts/ai-agent-builder",
        media_urls=[],
        topics=["Artificial Intelligence", "Developer Tools"],
        makers=[],
        raw={},
    )


def test_normalize_keywords_trims_and_lowercases():
    assert normalize_keywords((" AI ", "", "Agent")) == ("ai", "agent")


def test_keyword_filter_accepts_matching_include_keyword():
    assert keyword_filter_reason(make_product(), include_keywords=("agent",)) is None


def test_keyword_filter_rejects_missing_include_keyword():
    assert (
        keyword_filter_reason(make_product(), include_keywords=("finance",))
        == "missing required include keyword"
    )


def test_keyword_filter_exclude_wins_over_include():
    assert (
        keyword_filter_reason(
            make_product(),
            include_keywords=("agent",),
            exclude_keywords=("automation",),
        )
        == "excluded by keyword: automation"
    )
