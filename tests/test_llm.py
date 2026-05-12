import json
from pathlib import Path

import httpx
import pytest

from ph_daily.config import QualitySettings, Settings
from ph_daily.errors import ConfigError, LlmError
from ph_daily.llm import LlmClient, parse_enrichment_json
from ph_daily.models import Product, ProductEnrichment


def make_settings(api_key: str = "llm-key") -> Settings:
    period_quality = {
        "daily": QualitySettings(300, 0.04, 8, 100),
        "weekly": QualitySettings(800, 0.035, 20, 150),
        "monthly": QualitySettings(1000, 0.03, 40, 200),
        "yearly": QualitySettings(5000, 0.02, 120, 300),
    }
    return Settings(
        product_hunt_token="ph-token",
        llm_base_url="https://llm.example.com/v1",
        llm_api_key=api_key,
        llm_model="model-a",
        min_votes=300,
        comment_ratio=0.04,
        min_comments=8,
        fetch_limit=100,
        period_quality=period_quality,
        output_formats=("markdown",),
        product_hunt_featured=None,
        product_hunt_order="VOTES",
        product_hunt_topic="",
        product_hunt_url="",
        product_hunt_twitter_url="",
        include_keywords=(),
        exclude_keywords=(),
        output_dir=".",
        http_timeout_seconds=5,
    )


def make_product() -> Product:
    return Product(
        id="123",
        name="Acme AI",
        tagline="Automate support replies with context",
        description="Acme AI reads your docs and drafts support answers.",
        votes_count=512,
        comments_count=33,
        daily_rank=4,
        created_at="2026-05-10T08:00:00Z",
        featured_at=None,
        website_url="https://example.com",
        product_hunt_url="https://www.producthunt.com/posts/acme-ai",
        media_urls=[],
        topics=["Artificial Intelligence"],
        makers=["Jane Maker"],
        raw={},
    )


def test_parse_enrichment_json():
    raw = Path("tests/fixtures/llm_enrichment.json").read_text()

    enrichment = parse_enrichment_json(raw)

    assert enrichment == ProductEnrichment(
        purpose_zh="结合上下文自动生成客服回复",
        summary_zh="Acme AI 会读取团队文档，并根据上下文起草客服回复。",
        target_users_zh=["客服团队", "SaaS 创始人", "需要减少重复答疑的运营团队"],
        use_cases_zh=["根据帮助文档回答用户问题", "把常见问题整理成客服草稿", "让新人客服更快理解产品"],
        example_workflow_zh=["连接知识库", "导入历史问题", "让系统生成回复草稿", "人工确认后发送"],
        why_interesting_zh="它把知识库和客服回复结合，适合正在扩张支持团队的产品。",
        caveat_zh="Product Hunt 信息有限，实际效果需要看它支持哪些知识库和客服系统。",
    )


@pytest.mark.parametrize(
    "raw",
    [
        "{}",
        "[]",
        "null",
        json.dumps(
            {
                "purpose_zh": "结合上下文自动生成客服回复",
                "summary_zh": None,
                "target_users_zh": ["客服团队"],
                "use_cases_zh": ["根据帮助文档回答用户问题"],
                "example_workflow_zh": ["连接知识库"],
                "why_interesting_zh": "它把知识库和客服回复结合。",
                "caveat_zh": "需要看实际集成。",
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "purpose_zh": "结合上下文自动生成客服回复",
                "summary_zh": 123,
                "target_users_zh": ["客服团队"],
                "use_cases_zh": ["根据帮助文档回答用户问题"],
                "example_workflow_zh": ["连接知识库"],
                "why_interesting_zh": "它把知识库和客服回复结合。",
                "caveat_zh": "需要看实际集成。",
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "purpose_zh": "结合上下文自动生成客服回复",
                "summary_zh": "Acme AI 会读取团队文档，并根据上下文起草客服回复。",
                "target_users_zh": ["客服团队"],
                "use_cases_zh": "根据帮助文档回答用户问题",
                "example_workflow_zh": ["连接知识库"],
                "why_interesting_zh": "它把知识库和客服回复结合。",
                "caveat_zh": "需要看实际集成。",
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "purpose_zh": "结合上下文自动生成客服回复",
                "summary_zh": "Acme AI 会读取团队文档，并根据上下文起草客服回复。",
                "target_users_zh": ["客服团队"],
                "use_cases_zh": ["根据帮助文档回答用户问题", ""],
                "example_workflow_zh": ["连接知识库"],
                "why_interesting_zh": "它把知识库和客服回复结合。",
                "caveat_zh": "需要看实际集成。",
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "purpose_zh": "结合上下文自动生成客服回复",
                "summary_zh": "Acme AI 会读取团队文档，并根据上下文起草客服回复。",
                "target_users_zh": ["客服团队"],
                "use_cases_zh": ["根据帮助文档回答用户问题", 42],
                "example_workflow_zh": ["连接知识库"],
                "why_interesting_zh": "它把知识库和客服回复结合。",
                "caveat_zh": "需要看实际集成。",
            },
            ensure_ascii=False,
        ),
    ],
)
def test_parse_enrichment_json_rejects_schema_mismatches(raw):
    with pytest.raises(LlmError, match="LLM response did not match enrichment schema"):
        parse_enrichment_json(raw)


def test_enrich_product_calls_openai_compatible_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://llm.example.com/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer llm-key"
        payload = json.loads(request.content)
        assert payload["model"] == "model-a"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": Path("tests/fixtures/llm_enrichment.json").read_text()
                        }
                    }
                ]
            },
        )

    client = LlmClient(make_settings(), transport=httpx.MockTransport(handler))

    enrichment = client.enrich_product(make_product())

    assert enrichment.summary_zh.startswith("Acme AI")


def test_enrich_product_prompt_asks_for_explanatory_chinese_enrichment():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        user_message = payload["messages"][1]["content"]
        assert "解释" in user_message
        assert "用途" in user_message
        assert "使用场景" in user_message
        assert "示例" in user_message
        assert "不要只做文本翻译" in user_message
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": Path("tests/fixtures/llm_enrichment.json").read_text()
                        }
                    }
                ]
            },
        )

    client = LlmClient(make_settings(), transport=httpx.MockTransport(handler))

    client.enrich_product(make_product())


def test_enrich_product_wraps_non_json_response_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    client = LlmClient(make_settings(), transport=httpx.MockTransport(handler))

    with pytest.raises(LlmError, match="LLM response body was not valid JSON"):
        client.enrich_product(make_product())


def test_enrich_product_rejects_none_message_content():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": None}}]},
        )

    client = LlmClient(make_settings(), transport=httpx.MockTransport(handler))

    with pytest.raises(LlmError, match="LLM response missing message content"):
        client.enrich_product(make_product())


def test_enrich_product_rejects_missing_message_content_key():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {}}]},
        )

    client = LlmClient(make_settings(), transport=httpx.MockTransport(handler))

    with pytest.raises(LlmError, match="LLM response missing message content"):
        client.enrich_product(make_product())


def test_enrich_product_rejects_non_string_message_content():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": 123}}]},
        )

    client = LlmClient(make_settings(), transport=httpx.MockTransport(handler))

    with pytest.raises(LlmError, match="LLM response missing message content"):
        client.enrich_product(make_product())


def test_enrich_product_rejects_invalid_enrichment_schema():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "{}"}}]},
        )

    client = LlmClient(make_settings(), transport=httpx.MockTransport(handler))

    with pytest.raises(LlmError, match="LLM response did not match enrichment schema"):
        client.enrich_product(make_product())


def test_enrich_product_requires_api_key():
    client = LlmClient(
        make_settings(api_key=" "),
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )

    with pytest.raises(ConfigError, match="LLM_API_KEY is required for enrichment"):
        client.enrich_product(make_product())


def test_enrich_product_http_error_has_operational_context_without_api_key():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            text="rate limited: retry later with token secret",
            request=request,
        )

    client = LlmClient(
        make_settings(api_key="secret-llm-key"),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LlmError) as exc_info:
        client.enrich_product(make_product())

    message = str(exc_info.value)
    assert "Acme AI" in message
    assert "123" in message
    assert "model-a" in message
    assert "https://llm.example.com/v1/chat/completions" in message
    assert "status=429" in message
    assert "rate limited" in message
    assert "secret-llm-key" not in message
