from __future__ import annotations

import math
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from ph_daily.errors import ConfigError


DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"


@dataclass(frozen=True)
class Settings:
    product_hunt_token: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    min_votes: int
    comment_ratio: float
    min_comments: int
    fetch_limit: int
    output_formats: tuple[str, ...]
    output_dir: str
    http_timeout_seconds: float


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number") from exc
    if not math.isfinite(value):
        raise ConfigError(f"{name} must be finite")
    return value


def _read_output_formats() -> tuple[str, ...]:
    raw = os.getenv("OUTPUT_FORMATS", "markdown")
    formats = tuple(item.strip().lower() for item in raw.split(",") if item.strip())
    if not formats:
        raise ConfigError("OUTPUT_FORMATS must include at least one format")

    allowed_formats = {"markdown", "html"}
    invalid_formats = sorted(set(formats) - allowed_formats)
    if invalid_formats:
        joined = ", ".join(invalid_formats)
        raise ConfigError(f"OUTPUT_FORMATS contains unsupported format: {joined}")

    return tuple(dict.fromkeys(formats))


def load_settings(load_dotenv_file: bool = True) -> Settings:
    if load_dotenv_file:
        load_dotenv()

    product_hunt_token = os.getenv("PRODUCT_HUNT_TOKEN", "").strip()
    if not product_hunt_token:
        raise ConfigError("PRODUCT_HUNT_TOKEN is required")

    llm_base_url = os.getenv("LLM_BASE_URL", DEFAULT_LLM_BASE_URL).strip().rstrip("/")
    if not llm_base_url:
        llm_base_url = DEFAULT_LLM_BASE_URL
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    llm_model = os.getenv("LLM_MODEL", "gpt-4.1-mini").strip()
    min_votes = _read_int("MIN_VOTES", 300)
    comment_ratio = _read_float("COMMENT_RATIO", 0.04)
    min_comments = _read_int("MIN_COMMENTS", 8)
    fetch_limit = _read_int("FETCH_LIMIT", 100)
    output_formats = _read_output_formats()
    output_dir = os.getenv("OUTPUT_DIR", ".").strip() or "."
    http_timeout_seconds = _read_float("HTTP_TIMEOUT_SECONDS", 30.0)

    if not llm_api_key:
        raise ConfigError("LLM_API_KEY is required")
    if min_votes < 1:
        raise ConfigError("MIN_VOTES must be at least 1")
    if comment_ratio <= 0:
        raise ConfigError("COMMENT_RATIO must be greater than 0")
    if min_comments < 0:
        raise ConfigError("MIN_COMMENTS must be at least 0")
    if fetch_limit < 1:
        raise ConfigError("FETCH_LIMIT must be at least 1")
    if http_timeout_seconds <= 0:
        raise ConfigError("HTTP_TIMEOUT_SECONDS must be greater than 0")
    if not llm_model:
        raise ConfigError("LLM_MODEL is required")

    return Settings(
        product_hunt_token=product_hunt_token,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        min_votes=min_votes,
        comment_ratio=comment_ratio,
        min_comments=min_comments,
        fetch_limit=fetch_limit,
        output_formats=output_formats,
        output_dir=output_dir,
        http_timeout_seconds=http_timeout_seconds,
    )
