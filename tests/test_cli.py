from datetime import date as real_date
from types import SimpleNamespace

import pytest

import ph_daily.cli as cli
from ph_daily.cli import parse_date_arg, run
from ph_daily.errors import ConfigError, ExitCode


def test_parse_date_arg_accepts_explicit_date():
    assert parse_date_arg("2026-05-10") == "2026-05-10"


def test_parse_date_arg_rejects_bad_date():
    with pytest.raises(ValueError, match="date must be YYYY-MM-DD or today"):
        parse_date_arg("2026/05/10")


@pytest.mark.parametrize("value", ["2026-5-10", "2026-05-1"])
def test_parse_date_arg_rejects_non_padded_dates(value):
    with pytest.raises(ValueError, match="date must be YYYY-MM-DD or today"):
        parse_date_arg(value)


def test_healthcheck_returns_config_error_without_token(monkeypatch, capsys):
    def fail_load_settings():
        raise ConfigError("PRODUCT_HUNT_TOKEN is required")

    monkeypatch.setattr(cli, "load_settings", fail_load_settings)

    exit_code = run(["healthcheck"])

    captured = capsys.readouterr()
    assert exit_code == ExitCode.CONFIG_ERROR
    assert "Error: PRODUCT_HUNT_TOKEN is required" in captured.err


def test_backfill_zero_days_returns_config_error(monkeypatch):
    def fail_load_settings():
        raise AssertionError("load_settings should not be called")

    monkeypatch.setattr(cli, "load_settings", fail_load_settings)

    assert run(["backfill", "--days", "0"]) == ExitCode.CONFIG_ERROR


def test_collect_invalid_date_returns_config_error_before_loading_settings(monkeypatch):
    def fail_load_settings():
        raise AssertionError("load_settings should not be called")

    monkeypatch.setattr(cli, "load_settings", fail_load_settings)

    assert run(["collect", "--date", "2026/05/10"]) == ExitCode.CONFIG_ERROR


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
