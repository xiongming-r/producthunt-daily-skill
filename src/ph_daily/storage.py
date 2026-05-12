from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any

from ph_daily.errors import OutputError


@dataclass(frozen=True)
class OutputPaths:
    raw_json: Path
    processed_json: Path
    markdown_report: Path
    html_report: Path
    log_file: Path


def build_output_paths(
    output_dir: str,
    date: str,
    period: str = "daily",
    output_key: str | None = None,
) -> OutputPaths:
    base_dir = Path(output_dir)
    key = output_key or date
    if period == "daily":
        raw_json = base_dir / "data" / "raw" / f"{key}.json"
        processed_json = base_dir / "data" / "processed" / f"{key}.json"
        markdown_report = base_dir / "reports" / "daily" / f"{key}.md"
        html_report = base_dir / "reports" / "html" / f"{key}.html"
    else:
        raw_json = base_dir / "data" / "raw" / period / f"{key}.json"
        processed_json = base_dir / "data" / "processed" / period / f"{key}.json"
        markdown_report = base_dir / "reports" / period / f"{key}.md"
        html_report = base_dir / "reports" / "html" / period / f"{key}.html"

    return OutputPaths(
        raw_json=raw_json,
        processed_json=processed_json,
        markdown_report=markdown_report,
        html_report=html_report,
        log_file=base_dir / "logs" / f"{key}.log",
    )


def _normalize_json_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _normalize_json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {
            key: _normalize_json_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [_normalize_json_value(item) for item in value]
    return value


def write_json(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _normalize_json_value(payload)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except TypeError as exc:
        raise OutputError(f"Failed to serialize JSON output for {path}: {exc}") from exc
    except OSError as exc:
        raise OutputError(f"Failed to write JSON output to {path}: {exc}") from exc


def write_text(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise OutputError(f"Failed to write text output to {path}: {exc}") from exc
