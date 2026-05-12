import pytest

from ph_daily.periods import build_period_window, parse_anchor_date, parse_period


def test_parse_period_accepts_supported_values():
    assert parse_period("Daily") == "daily"
    assert parse_period("weekly") == "weekly"
    assert parse_period("monthly") == "monthly"
    assert parse_period("yearly") == "yearly"


def test_parse_period_rejects_unknown_value():
    with pytest.raises(ValueError, match="period must be one of"):
        parse_period("quarterly")


def test_parse_anchor_date_requires_strict_iso_date():
    assert parse_anchor_date("2026-05-11").isoformat() == "2026-05-11"
    with pytest.raises(ValueError, match="date must be YYYY-MM-DD or today"):
        parse_anchor_date("2026-5-11")


def test_build_daily_window():
    window = build_period_window("daily", "2026-05-11")

    assert window.start_date.isoformat() == "2026-05-11"
    assert window.end_date.isoformat() == "2026-05-11"
    assert window.output_key == "2026-05-11"
    assert window.posted_after == "2026-05-11T00:00:00Z"
    assert window.posted_before == "2026-05-11T23:59:59Z"


def test_build_weekly_window_uses_iso_week():
    window = build_period_window("weekly", "2026-05-13")

    assert window.start_date.isoformat() == "2026-05-11"
    assert window.end_date.isoformat() == "2026-05-17"
    assert window.output_key == "2026-W20"


def test_build_monthly_window():
    window = build_period_window("monthly", "2026-02-12")

    assert window.start_date.isoformat() == "2026-02-01"
    assert window.end_date.isoformat() == "2026-02-28"
    assert window.output_key == "2026-02"


def test_build_yearly_window():
    window = build_period_window("yearly", "2026-05-11")

    assert window.start_date.isoformat() == "2026-01-01"
    assert window.end_date.isoformat() == "2026-12-31"
    assert window.output_key == "2026"
