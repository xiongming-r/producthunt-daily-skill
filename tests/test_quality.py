from ph_daily.models import Product
from ph_daily.quality import evaluate_product, required_comments_for_votes


def make_product(votes: int, comments: int) -> Product:
    return Product(
        id="1",
        name="Demo",
        tagline="Demo tagline",
        description="Demo description",
        votes_count=votes,
        comments_count=comments,
        daily_rank=1,
        created_at="2026-05-10T08:00:00Z",
        featured_at=None,
        website_url="https://example.com",
        product_hunt_url="https://www.producthunt.com/posts/demo",
        media_urls=[],
        topics=[],
        makers=[],
        raw={},
    )


def test_required_comments_scales_with_votes():
    assert required_comments_for_votes(300, min_comments=8, comment_ratio=0.04) == 12
    assert required_comments_for_votes(500, min_comments=8, comment_ratio=0.04) == 20
    assert required_comments_for_votes(1000, min_comments=8, comment_ratio=0.04) == 40
    assert required_comments_for_votes(2000, min_comments=8, comment_ratio=0.04) == 80


def test_product_passes_when_votes_and_comments_match_threshold():
    decision = evaluate_product(
        make_product(512, 33),
        min_votes=300,
        min_comments=8,
        comment_ratio=0.04,
    )

    assert decision.passed is True
    assert decision.required_comments == 21
    assert decision.reason == "votes 512 >= 300 and comments 33 >= required 21"


def test_product_fails_when_votes_are_too_low():
    decision = evaluate_product(
        make_product(299, 99),
        min_votes=300,
        min_comments=8,
        comment_ratio=0.04,
    )

    assert decision.passed is False
    assert decision.reason == "votes 299 < 300"


def test_product_fails_when_comments_are_too_low():
    decision = evaluate_product(
        make_product(1000, 10),
        min_votes=300,
        min_comments=8,
        comment_ratio=0.04,
    )

    assert decision.passed is False
    assert decision.required_comments == 40
    assert decision.reason == "votes 1000 >= 300 but comments 10 < required 40"
