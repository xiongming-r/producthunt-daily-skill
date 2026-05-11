from __future__ import annotations

import math

from ph_daily.models import FilterDecision, Product


def required_comments_for_votes(votes: int, min_comments: int, comment_ratio: float) -> int:
    return max(min_comments, math.ceil(votes * comment_ratio))


def evaluate_product(
    product: Product,
    min_votes: int,
    min_comments: int,
    comment_ratio: float,
) -> FilterDecision:
    required_comments = required_comments_for_votes(
        product.votes_count,
        min_comments=min_comments,
        comment_ratio=comment_ratio,
    )

    if product.votes_count < min_votes:
        return FilterDecision(
            passed=False,
            reason=f"votes {product.votes_count} < {min_votes}",
            required_comments=required_comments,
        )

    if product.comments_count < required_comments:
        return FilterDecision(
            passed=False,
            reason=(
                f"votes {product.votes_count} >= {min_votes} "
                f"but comments {product.comments_count} < required {required_comments}"
            ),
            required_comments=required_comments,
        )

    return FilterDecision(
        passed=True,
        reason=(
            f"votes {product.votes_count} >= {min_votes} "
            f"and comments {product.comments_count} >= required {required_comments}"
        ),
        required_comments=required_comments,
    )
