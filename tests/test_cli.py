from datetime import date as real_date
from types import SimpleNamespace

import pytest

import ph_daily.cli as cli
from ph_daily.cli import parse_date_arg, run
from ph_daily.errors import ExitCode


def test_parse_date_arg_accepts_explicit_date():
    assert parse_date_arg("2026-05-10") == "2026-05-10"


def test_parse_date_arg_rejects_bad_date():
    with pytest.raises(ValueError, match="date must be YYYY-MM-DD or today"):
        parse_date_arg("2026/05/10")


@pytest.mark.parametrize("value", ["2026-5-10", "2026-05-1"])
def test_parse_date_arg_rejects_non_padded_dates(value):
    with pytest.raises(ValueError, match="date must be YYYY-MM-DD or today"):
        parse_date_arg(value)


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


def test_collect_prints_counts_and_report_path(monkeypatch, capsys):
    settings = object()

    class FakeCollector:
        def __init__(self, actual_settings):
            assert actual_settings is settings

        def collect(self, target_date):
            assert target_date == "2026-05-10"
            return SimpleNamespace(
                fetched_count=12,
                selected_count=3,
                paths=SimpleNamespace(markdown_report="/tmp/report.md"),
            )

    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "Collector", FakeCollector)

    exit_code = run(["collect", "--date", "2026-05-10"])

    captured = capsys.readouterr()
    assert exit_code == ExitCode.SUCCESS
    assert "Selected 3/12 products" in captured.out
    assert "Report: /tmp/report.md" in captured.out


def test_backfill_collects_yesterday_through_requested_days(monkeypatch, capsys):
    settings = object()
    collected_dates = []

    class FrozenDate(real_date):
        @classmethod
        def today(cls):
            return cls(2026, 5, 12)

    class FakeCollector:
        def __init__(self, actual_settings):
            assert actual_settings is settings

        def collect(self, target_date):
            collected_dates.append(target_date)
            return SimpleNamespace(
                date=target_date,
                fetched_count=10,
                selected_count=2,
            )

    monkeypatch.setattr(cli, "date", FrozenDate)
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "Collector", FakeCollector)

    exit_code = run(["backfill", "--days", "2"])

    captured = capsys.readouterr()
    assert exit_code == ExitCode.SUCCESS
    assert collected_dates == ["2026-05-11", "2026-05-10"]
    assert "2026-05-11: selected 2/10 products" in captured.out
    assert "2026-05-10: selected 2/10 products" in captured.out
