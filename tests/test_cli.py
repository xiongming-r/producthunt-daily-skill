import pytest

from ph_daily.cli import parse_date_arg, run
from ph_daily.errors import ExitCode


def test_parse_date_arg_accepts_explicit_date():
    assert parse_date_arg("2026-05-10") == "2026-05-10"


def test_parse_date_arg_rejects_bad_date():
    with pytest.raises(ValueError, match="date must be YYYY-MM-DD or today"):
        parse_date_arg("2026/05/10")


def test_healthcheck_returns_config_error_without_token(monkeypatch):
    monkeypatch.delenv("PRODUCT_HUNT_TOKEN", raising=False)

    assert run(["healthcheck"]) == ExitCode.CONFIG_ERROR


def test_backfill_zero_days_returns_config_error(monkeypatch):
    monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "ph-token")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.setenv("LLM_MODEL", "model-a")
    monkeypatch.setenv("MIN_VOTES", "300")
    monkeypatch.setenv("COMMENT_RATIO", "0.04")
    monkeypatch.setenv("MIN_COMMENTS", "8")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/ph-daily")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "15")

    assert run(["backfill", "--days", "0"]) == ExitCode.CONFIG_ERROR
