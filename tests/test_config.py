import pytest

from ph_daily.config import Settings, load_settings
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

    assert settings == Settings(
        product_hunt_token="ph-token",
        llm_base_url="https://example.com/v1",
        llm_api_key="llm-key",
        llm_model="model-a",
        min_votes=300,
        comment_ratio=0.04,
        min_comments=8,
        fetch_limit=125,
        output_formats=("markdown",),
        output_dir="/tmp/ph-daily",
        http_timeout_seconds=15.0,
    )


def test_missing_product_hunt_token_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.delenv("PRODUCT_HUNT_TOKEN", raising=False)

    with pytest.raises(ConfigError, match="PRODUCT_HUNT_TOKEN is required"):
        load_settings(load_dotenv_file=False)


def test_missing_llm_api_key_fails(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("LLM_API_KEY", "   ")

    with pytest.raises(ConfigError, match="LLM_API_KEY is required"):
        load_settings(load_dotenv_file=False)


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
