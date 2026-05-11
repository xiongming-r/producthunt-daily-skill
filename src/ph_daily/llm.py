from __future__ import annotations

import json
from typing import Any

import httpx

from ph_daily.errors import LlmError
from ph_daily.models import Product, ProductEnrichment


def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def parse_enrichment_json(raw_content: str) -> ProductEnrichment:
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise LlmError("LLM response was not valid JSON") from exc

    return ProductEnrichment(
        tagline_zh=str(data.get("tagline_zh", "")),
        summary_zh=str(data.get("summary_zh", "")),
        target_users_zh=_ensure_list(data.get("target_users_zh")),
        use_cases_zh=_ensure_list(data.get("use_cases_zh")),
        example_workflow_zh=_ensure_list(data.get("example_workflow_zh")),
        why_interesting_zh=str(data.get("why_interesting_zh", "")),
        caveat_zh=str(data.get("caveat_zh", "")),
    )


class LlmClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def enrich_product(self, product: Product) -> ProductEnrichment:
        if not self.api_key:
            raise LlmError("LLM_API_KEY is required for enrichment")

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

        with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
            try:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise LlmError(f"LLM request failed: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise LlmError("LLM response body was not valid JSON") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(f"LLM response missing message content: {data}") from exc
        if not isinstance(content, str):
            raise LlmError(f"LLM response missing message content: {data}")

        return parse_enrichment_json(content)

    @staticmethod
    def _build_prompt(product: Product) -> str:
        return json.dumps(
            {
                "task": "把 Product Hunt 产品信息转成中文产品分析，解释用途、用户、场景和例子。",
                "output_schema": {
                    "tagline_zh": "自然中文 tagline",
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
