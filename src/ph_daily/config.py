from __future__ import annotations

import math
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from ph_daily.errors import ConfigError


DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"
VALID_POST_ORDERS = {"VOTES", "NEWEST", "FEATURED_AT"}


@dataclass(frozen=True)
class QualitySettings:
    min_votes: int
    comment_ratio: float
    min_comments: int
    fetch_limit: int


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
    period_quality: dict[str, QualitySettings]
    output_formats: tuple[str, ...]
    product_hunt_featured: bool | None
    product_hunt_order: str
    product_hunt_topic: str
    product_hunt_url: str
    product_hunt_twitter_url: str
    include_keywords: tuple[str, ...]
    exclude_keywords: tuple[str, ...]
    output_dir: str
    http_timeout_seconds: float

    def quality_for_period(self, period: str) -> QualitySettings:
        return self.period_quality[period]


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


def _read_csv(name: str) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    return tuple(item.strip().lower() for item in raw.split(",") if item.strip())


def _read_optional_bool(name: str) -> bool | None:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return None
    if raw in {"1", "true", "yes", "y"}:
        return True
    if raw in {"0", "false", "no", "n"}:
        return False
    raise ConfigError(f"{name} must be true or false")


def _period_quality(
    period: str,
    *,
    default_min_votes: int,
    default_comment_ratio: float,
    default_min_comments: int,
    default_fetch_limit: int,
) -> QualitySettings:
    prefix = period.upper()
    min_votes = _read_int(f"{prefix}_MIN_VOTES", default_min_votes)
    comment_ratio = _read_float(f"{prefix}_COMMENT_RATIO", default_comment_ratio)
    min_comments = _read_int(f"{prefix}_MIN_COMMENTS", default_min_comments)
    fetch_limit = _read_int(f"{prefix}_FETCH_LIMIT", default_fetch_limit)

    if min_votes < 1:
        raise ConfigError(f"{prefix}_MIN_VOTES must be at least 1")
    if comment_ratio <= 0:
        raise ConfigError(f"{prefix}_COMMENT_RATIO must be greater than 0")
    if min_comments < 0:
        raise ConfigError(f"{prefix}_MIN_COMMENTS must be at least 0")
    if fetch_limit < 1:
        raise ConfigError(f"{prefix}_FETCH_LIMIT must be at least 1")

    return QualitySettings(
        min_votes=min_votes,
        comment_ratio=comment_ratio,
        min_comments=min_comments,
        fetch_limit=fetch_limit,
    )


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
    product_hunt_featured = _read_optional_bool("PRODUCT_HUNT_FEATURED")
    product_hunt_order = os.getenv("PRODUCT_HUNT_ORDER", "VOTES").strip().upper()
    product_hunt_topic = os.getenv("PRODUCT_HUNT_TOPIC", "").strip()
    product_hunt_url = os.getenv("PRODUCT_HUNT_URL", "").strip()
    product_hunt_twitter_url = os.getenv("PRODUCT_HUNT_TWITTER_URL", "").strip()
    include_keywords = _read_csv("INCLUDE_KEYWORDS")
    exclude_keywords = _read_csv("EXCLUDE_KEYWORDS")
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
    if product_hunt_order not in VALID_POST_ORDERS:
        allowed_orders = ", ".join(sorted(VALID_POST_ORDERS))
        raise ConfigError(f"PRODUCT_HUNT_ORDER must be one of: {allowed_orders}")
    if http_timeout_seconds <= 0:
        raise ConfigError("HTTP_TIMEOUT_SECONDS must be greater than 0")
    if not llm_model:
        raise ConfigError("LLM_MODEL is required")

    period_quality = {
        "daily": _period_quality(
            "daily",
            default_min_votes=min_votes,
            default_comment_ratio=comment_ratio,
            default_min_comments=min_comments,
            default_fetch_limit=fetch_limit,
        ),
        "weekly": _period_quality(
            "weekly",
            default_min_votes=800,
            default_comment_ratio=0.035,
            default_min_comments=20,
            default_fetch_limit=150,
        ),
        "monthly": _period_quality(
            "monthly",
            default_min_votes=1000,
            default_comment_ratio=0.03,
            default_min_comments=40,
            default_fetch_limit=200,
        ),
        "yearly": _period_quality(
            "yearly",
            default_min_votes=5000,
            default_comment_ratio=0.02,
            default_min_comments=120,
            default_fetch_limit=300,
        ),
    }

    return Settings(
        product_hunt_token=product_hunt_token,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        min_votes=min_votes,
        comment_ratio=comment_ratio,
        min_comments=min_comments,
        fetch_limit=fetch_limit,
        period_quality=period_quality,
        output_formats=output_formats,
        product_hunt_featured=product_hunt_featured,
        product_hunt_order=product_hunt_order,
        product_hunt_topic=product_hunt_topic,
        product_hunt_url=product_hunt_url,
        product_hunt_twitter_url=product_hunt_twitter_url,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        output_dir=output_dir,
        http_timeout_seconds=http_timeout_seconds,
    )
