from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

from ph_daily.errors import OutputError


@dataclass(frozen=True)
class OutputPaths:
    raw_json: Path
    processed_json: Path
    markdown_report: Path
    log_file: Path


def build_output_paths(output_dir: str, date: str) -> OutputPaths:
    base_dir = Path(output_dir)
    return OutputPaths(
        raw_json=base_dir / "data" / "raw" / f"{date}.json",
        processed_json=base_dir / "data" / "processed" / f"{date}.json",
        markdown_report=base_dir / "reports" / "daily" / f"{date}.md",
        log_file=base_dir / "logs" / f"{date}.log",
    )


def write_json(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(payload) if is_dataclass(payload) else payload
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise OutputError(f"Failed to write JSON output to {path}: {exc}") from exc


def write_text(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise OutputError(f"Failed to write text output to {path}: {exc}") from exc
