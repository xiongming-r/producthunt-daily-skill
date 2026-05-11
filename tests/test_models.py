import json
from pathlib import Path

from ph_daily.models import Product


def test_product_from_api_node_normalizes_fields():
    payload = json.loads(Path("tests/fixtures/producthunt_posts.json").read_text())
    node = payload["data"]["posts"]["nodes"][0]

    product = Product.from_api_node(node)

    assert product.id == "123"
    assert product.name == "Acme AI"
    assert product.tagline == "Automate support replies with context"
    assert product.description == "Acme AI reads your docs and drafts support answers."
    assert product.votes_count == 512
    assert product.comments_count == 33
    assert product.daily_rank == 4
    assert product.created_at == "2026-05-10T08:00:00Z"
    assert product.featured_at == "2026-05-10T08:00:00Z"
    assert product.website_url == "https://example.com"
    assert product.product_hunt_url == "https://www.producthunt.com/posts/acme-ai"
    assert product.media_urls == ["https://ph-files.imgix.net/acme.png"]
    assert product.topics == ["Artificial Intelligence"]
    assert product.makers == ["Jane Maker"]
    assert product.raw["id"] == "123"
