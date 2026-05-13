from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta

from ph_daily.collector import Collector
from ph_daily.config import VALID_POST_ORDERS, load_settings
from ph_daily.errors import ExitCode, PhDailyError
from ph_daily.filters import normalize_keywords
from ph_daily.periods import parse_period
from ph_daily.producthunt import ProductHuntPostFilters


DATE_ERROR = "date must be YYYY-MM-DD or today"
BOOL_ERROR = "value must be true or false"


def parse_date_arg(value: str) -> str:
    if value == "today":
        return date.today().isoformat()

    if (
        len(value) != 10
        or value[4] != "-"
        or value[7] != "-"
        or not value[:4].isdigit()
        or not value[5:7].isdigit()
        or not value[8:].isdigit()
    ):
        raise ValueError(DATE_ERROR)

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(DATE_ERROR) from exc
    return value


def parse_optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(BOOL_ERROR)


def build_post_filters(args, settings) -> ProductHuntPostFilters:
    order = (args.order or settings.product_hunt_order).strip().upper()
    if order not in VALID_POST_ORDERS:
        allowed = ", ".join(sorted(VALID_POST_ORDERS))
        raise ValueError(f"--order must be one of: {allowed}")

    featured_override = parse_optional_bool(args.featured)
    featured = (
        settings.product_hunt_featured
        if featured_override is None
        else featured_override
    )
    return ProductHuntPostFilters(
        featured=featured,
        order=order,
        topic=args.topic or settings.product_hunt_topic,
        url=args.url or settings.product_hunt_url,
        twitter_url=args.twitter_url or settings.product_hunt_twitter_url,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ph-daily")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("healthcheck")

    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--date", default="today")
    collect_parser.add_argument("--period", default="daily")
    collect_parser.add_argument("--featured")
    collect_parser.add_argument("--order")
    collect_parser.add_argument("--topic")
    collect_parser.add_argument("--url")
    collect_parser.add_argument("--twitter-url")
    collect_parser.add_argument("--include-keyword", action="append", default=None)
    collect_parser.add_argument("--exclude-keyword", action="append", default=None)
    collect_parser.add_argument(
        "--no-enrichment",
        action="store_true",
        default=False,
        help="Skip LLM enrichment; output filtered Product Hunt data for agent-side analysis",
    )

    backfill_parser = subparsers.add_parser("backfill")
    backfill_parser.add_argument("--days", required=True, type=int)

    return parser


def run(argv: list[str] | None = None) -> ExitCode:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        target_date = None
        period = "daily"
        if args.command == "collect":
            target_date = parse_date_arg(args.date)
            period = parse_period(args.period)
        elif args.command == "backfill" and args.days < 1:
            raise ValueError("--days must be at least 1")

        settings = load_settings()

        if args.command == "healthcheck":
            print("Configuration OK")
            return ExitCode.SUCCESS

        collector = Collector(settings)
        if args.command == "collect":
            result = collector.collect_period(
                target_date,
                period=period,
                post_filters=build_post_filters(args, settings),
                include_keywords=(
                    normalize_keywords(args.include_keyword)
                    if args.include_keyword is not None
                    else None
                ),
                exclude_keywords=(
                    normalize_keywords(args.exclude_keyword)
                    if args.exclude_keyword is not None
                    else None
                ),
                enrichment_enabled=not args.no_enrichment,
            )
            print(f"Selected {result.selected_count}/{result.fetched_count} products")
            print(f"Report: {result.paths.markdown_report}")
            return ExitCode.SUCCESS

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
