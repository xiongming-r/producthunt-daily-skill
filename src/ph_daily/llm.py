from __future__ import annotations

import json
from typing import Any

import httpx

from ph_daily.config import Settings
from ph_daily.errors import ConfigError, LlmError
from ph_daily.models import Product, ProductEnrichment


SCHEMA_ERROR = "LLM response did not match enrichment schema"


def _snippet(text: str, secret: str | None = None, limit: int = 200) -> str:
    if secret:
        text = text.replace(secret, "[redacted]")
    text = " ".join(text.split())
    if len(text) > limit:
        return f"{text[:limit]}..."
    return text


def _schema_error() -> LlmError:
    return LlmError(SCHEMA_ERROR)


def _required_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str):
        raise _schema_error()
    value = value.strip()
    if not value:
        raise _schema_error()
    return value


def _required_list(data: dict[str, Any], field: str) -> list[str]:
    value = data.get(field)
    if not isinstance(value, list):
        raise _schema_error()

    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise _schema_error()
        item = item.strip()
        if not item:
            raise _schema_error()
        items.append(item)

    if not items:
        raise _schema_error()
    return items


def parse_enrichment_json(raw_content: str) -> ProductEnrichment:
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise LlmError("LLM response was not valid JSON") from exc

    if not isinstance(data, dict):
        raise _schema_error()

    return ProductEnrichment(
        purpose_zh=_required_string(data, "purpose_zh"),
        summary_zh=_required_string(data, "summary_zh"),
        target_users_zh=_required_list(data, "target_users_zh"),
        use_cases_zh=_required_list(data, "use_cases_zh"),
        example_workflow_zh=_required_list(data, "example_workflow_zh"),
        why_interesting_zh=_required_string(data, "why_interesting_zh"),
        caveat_zh=_required_string(data, "caveat_zh"),
    )


class LlmClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key.strip()
        self.model = settings.llm_model
        self.timeout_seconds = settings.http_timeout_seconds
        self.transport = transport

    def enrich_product(self, product: Product) -> ProductEnrichment:
        if not self.api_key:
            raise ConfigError("LLM_API_KEY is required for enrichment")

        prompt = self._build_prompt(product)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是产品研究员。只返回合法 JSON，不要使用 Markdown。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        endpoint = f"{self.base_url}/chat/completions"
        product_context = (
            f"product_id={product.id} product_name={product.name!r} "
            f"model={self.model} endpoint={endpoint}"
        )

        with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
            try:
                response = client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                response = exc.response
                raise LlmError(
                    "LLM request failed: "
                    f"{product_context} status={response.status_code} "
                    f"snippet={_snippet(response.text, self.api_key)!r}"
                ) from exc
            except httpx.HTTPError as exc:
                raise LlmError(
                    f"LLM request failed: {product_context} error={exc}"
                ) from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise LlmError(
                f"LLM response body was not valid JSON: {product_context}"
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(
                f"LLM response missing message content: {product_context}; {data}"
            ) from exc
        if not isinstance(content, str):
            raise LlmError(
                f"LLM response missing message content: {product_context}; {data}"
            )

        try:
            return parse_enrichment_json(content)
        except LlmError as exc:
            raise LlmError(f"{exc}: {product_context}") from exc

    @staticmethod
    def _build_prompt(product: Product) -> str:
        return json.dumps(
            {
                "task": "把 Product Hunt 产品信息转成中文产品分析，解释用途、用户、使用场景和示例，不要只做文本翻译。",
                "output_schema": {
                    "purpose_zh": "解释产品核心用途，不是简单翻译 tagline",
                    "summary_zh": "一句话说明产品做什么",
                    "target_users_zh": ["目标用户1", "目标用户2"],
                    "use_cases_zh": ["具体使用场景1", "具体使用场景2"],
                    "example_workflow_zh": ["步骤1", "步骤2", "步骤3"],
                    "why_interesting_zh": "为什么今天值得关注",
                    "caveat_zh": "基于信息不足时的注意事项",
                },
                "product": {
                    "name": product.name,
                    "tagline": product.tagline,
                    "description": product.description,
                    "votes_count": product.votes_count,
                    "comments_count": product.comments_count,
                    "daily_rank": product.daily_rank,
                    "topics": product.topics,
                    "makers": product.makers,
                    "product_hunt_url": product.product_hunt_url,
                    "website_url": product.website_url,
                },
            },
            ensure_ascii=False,
        )
