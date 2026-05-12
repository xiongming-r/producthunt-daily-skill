from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta

from ph_daily.collector import Collector
from ph_daily.config import load_settings
from ph_daily.errors import ExitCode, PhDailyError


DATE_ERROR = "date must be YYYY-MM-DD or today"


def parse_date_arg(value: str) -> str:
    if value == "today":
        return date.today().isoformat()

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(DATE_ERROR) from exc
    return parsed.date().isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ph-daily")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("healthcheck")

    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--date", default="today")

    backfill_parser = subparsers.add_parser("backfill")
    backfill_parser.add_argument("--days", required=True, type=int)

    return parser


def run(argv: list[str] | None = None) -> ExitCode:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = load_settings()

        if args.command == "healthcheck":
            print("Configuration OK")
            return ExitCode.SUCCESS

        collector = Collector(settings)
        if args.command == "collect":
            result = collector.collect(parse_date_arg(args.date))
            print(f"Selected {result.selected_count}/{result.fetched_count} products")
            print(f"Report: {result.paths.markdown_report}")
            return ExitCode.SUCCESS

        if args.days < 1:
            raise ValueError("--days must be at least 1")

        for days_ago in range(1, args.days + 1):
            target_date = (date.today() - timedelta(days=days_ago)).isoformat()
            result = collector.collect(target_date)
            print(
                f"{result.date}: selected "
                f"{result.selected_count}/{result.fetched_count} products"
            )
        return ExitCode.SUCCESS
    except PhDailyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return exc.exit_code
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return ExitCode.CONFIG_ERROR


def main() -> None:
    raise SystemExit(int(run()))
