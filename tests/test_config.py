import pytest

from ph_daily.config import load_settings
from ph_daily.errors import ConfigError


def _set_valid_env(monkeypatch):
    monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "ph-token")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.setenv("LLM_MODEL", "model-a")
    monkeypatch.setenv("MIN_VOTES", "300")
    monkeypatch.setenv("COMMENT_RATIO", "0.04")
    monkeypatch.setenv("MIN_COMMENTS", "8")
    monkeypatch.setenv("FETCH_LIMIT", "125")
    monkeypatch.setenv("OUTPUT_FORMATS", "markdown")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/ph-daily")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "15")


def test_load_settings_from_environment(monkeypatch):
    _set_valid_env(monkeypatch)

    settings = load_settings(load_dotenv_file=False)

    assert settings.product_hunt_token == "ph-token"
    assert settings.llm_base_url == "https://example.com/v1"
    assert settings.llm_api_key == "llm-key"
    assert settings.llm_model == "model-a"
    assert settings.min_votes == 300
    assert settings.comment_ratio == 0.04
    assert settings.min_comments == 8
    assert settings.fetch_limit == 125
    assert settings.output_formats == ("markdown",)
    assert settings.output_dir == "/tmp/ph-daily"
    assert settings.http_timeout_seconds == 15.0
    assert settings.quality_for_period("daily").min_votes == 300
    assert settings.quality_for_period("weekly").min_votes == 800
    assert settings.quality_for_period("monthly").min_votes == 1000
    assert settings.quality_for_period("yearly").min_votes == 5000
    assert settings.product_hunt_order == "VOTES"
    assert settings.product_hunt_featured is None
    assert settings.include_keywords == ()
    assert settings.exclude_keywords == ()


def test_missing_product_hunt_token_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.delenv("PRODUCT_HUNT_TOKEN", raising=False)

    with pytest.raises(ConfigError, match="PRODUCT_HUNT_TOKEN is required"):
        load_settings(load_dotenv_file=False)


def test_missing_llm_api_key_is_allowed_for_agent_mode(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("LLM_API_KEY", "   ")

    settings = load_settings(load_dotenv_file=False)

    assert settings.llm_api_key == ""
    assert settings.llm_model == "model-a"


def test_invalid_thresholds_fail(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("COMMENT_RATIO", "-1")

    with pytest.raises(ConfigError, match="COMMENT_RATIO must be greater than 0"):
        load_settings(load_dotenv_file=False)


def test_invalid_fetch_limit_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("FETCH_LIMIT", "0")

    with pytest.raises(ConfigError, match="FETCH_LIMIT must be at least 1"):
        load_settings(load_dotenv_file=False)


def test_period_specific_quality_settings(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("MONTHLY_MIN_VOTES", "1200")
    monkeypatch.setenv("YEARLY_FETCH_LIMIT", "350")

    settings = load_settings(load_dotenv_file=False)

    monthly = settings.quality_for_period("monthly")
    yearly = settings.quality_for_period("yearly")
    assert monthly.min_votes == 1200
    assert monthly.min_comments == 40
    assert yearly.min_votes == 5000
    assert yearly.fetch_limit == 350


def test_product_hunt_filter_settings(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("PRODUCT_HUNT_FEATURED", "true")
    monkeypatch.setenv("PRODUCT_HUNT_ORDER", "FEATURED_AT")
    monkeypatch.setenv("PRODUCT_HUNT_TOPIC", "artificial-intelligence")
    monkeypatch.setenv("PRODUCT_HUNT_URL", "https://example.com")
    monkeypatch.setenv("PRODUCT_HUNT_TWITTER_URL", "https://x.com/example")
    monkeypatch.setenv("INCLUDE_KEYWORDS", " AI, agent ")
    monkeypatch.setenv("EXCLUDE_KEYWORDS", " crypto ")

    settings = load_settings(load_dotenv_file=False)

    assert settings.product_hunt_featured is True
    assert settings.product_hunt_order == "FEATURED_AT"
    assert settings.product_hunt_topic == "artificial-intelligence"
    assert settings.product_hunt_url == "https://example.com"
    assert settings.product_hunt_twitter_url == "https://x.com/example"
    assert settings.include_keywords == ("ai", "agent")
    assert settings.exclude_keywords == ("crypto",)


def test_invalid_product_hunt_order_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("PRODUCT_HUNT_ORDER", "POPULAR")

    with pytest.raises(ConfigError, match="PRODUCT_HUNT_ORDER must be one of"):
        load_settings(load_dotenv_file=False)


def test_load_settings_accepts_multiple_output_formats(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("OUTPUT_FORMATS", "markdown, html, markdown")

    settings = load_settings(load_dotenv_file=False)

    assert settings.output_formats == ("markdown", "html")


def test_invalid_output_format_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("OUTPUT_FORMATS", "markdown,pdf")

    with pytest.raises(
        ConfigError,
        match="OUTPUT_FORMATS contains unsupported format: pdf",
    ):
        load_settings(load_dotenv_file=False)


def test_empty_output_formats_fail(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("OUTPUT_FORMATS", " , ")

    with pytest.raises(
        ConfigError,
        match="OUTPUT_FORMATS must include at least one format",
    ):
        load_settings(load_dotenv_file=False)


def test_nan_comment_ratio_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("COMMENT_RATIO", "nan")

    with pytest.raises(ConfigError, match="COMMENT_RATIO must be finite"):
        load_settings(load_dotenv_file=False)


def test_infinite_http_timeout_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "inf")

    with pytest.raises(ConfigError, match="HTTP_TIMEOUT_SECONDS must be finite"):
        load_settings(load_dotenv_file=False)


def test_blank_llm_base_url_uses_default(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("LLM_BASE_URL", "   ")

    settings = load_settings(load_dotenv_file=False)

    assert settings.llm_base_url == "https://api.openai.com/v1"
