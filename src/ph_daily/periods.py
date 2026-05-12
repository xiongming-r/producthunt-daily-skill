from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta


VALID_PERIODS = ("daily", "weekly", "monthly", "yearly")


@dataclass(frozen=True)
class PeriodWindow:
    period: str
    anchor_date: date
    start_date: date
    end_date: date
    output_key: str
    label_en: str
    label_zh: str

    @property
    def posted_after(self) -> str:
        return f"{self.start_date.isoformat()}T00:00:00Z"

    @property
    def posted_before(self) -> str:
        return f"{self.end_date.isoformat()}T23:59:59Z"


def parse_period(value: str) -> str:
    period = value.strip().lower()
    if period not in VALID_PERIODS:
        allowed = ", ".join(VALID_PERIODS)
        raise ValueError(f"period must be one of: {allowed}")
    return period


def parse_anchor_date(value: str) -> date:
    if value == "today":
        return date.today()
    if len(value) != 10:
        raise ValueError("date must be YYYY-MM-DD or today")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("date must be YYYY-MM-DD or today") from exc
    if parsed.isoformat() != value:
        raise ValueError("date must be YYYY-MM-DD or today")
    return parsed


def build_period_window(period: str, anchor: str) -> PeriodWindow:
    parsed_period = parse_period(period)
    anchor_date = parse_anchor_date(anchor)

    if parsed_period == "daily":
        return PeriodWindow(
            period=parsed_period,
            anchor_date=anchor_date,
            start_date=anchor_date,
            end_date=anchor_date,
            output_key=anchor_date.isoformat(),
            label_en="Daily",
            label_zh="每日",
        )

    if parsed_period == "weekly":
        start_date = anchor_date - timedelta(days=anchor_date.weekday())
        end_date = start_date + timedelta(days=6)
        iso_year, iso_week, _ = anchor_date.isocalendar()
        return PeriodWindow(
            period=parsed_period,
            anchor_date=anchor_date,
            start_date=start_date,
            end_date=end_date,
            output_key=f"{iso_year}-W{iso_week:02d}",
            label_en="Weekly",
            label_zh="每周",
        )

    if parsed_period == "monthly":
        last_day = calendar.monthrange(anchor_date.year, anchor_date.month)[1]
        start_date = anchor_date.replace(day=1)
        end_date = anchor_date.replace(day=last_day)
        return PeriodWindow(
            period=parsed_period,
            anchor_date=anchor_date,
            start_date=start_date,
            end_date=end_date,
            output_key=f"{anchor_date.year:04d}-{anchor_date.month:02d}",
            label_en="Monthly",
            label_zh="每月",
        )

    start_date = anchor_date.replace(month=1, day=1)
    end_date = anchor_date.replace(month=12, day=31)
    return PeriodWindow(
        period=parsed_period,
        anchor_date=anchor_date,
        start_date=start_date,
        end_date=end_date,
        output_key=f"{anchor_date.year:04d}",
        label_en="Yearly",
        label_zh="年度",
    )
