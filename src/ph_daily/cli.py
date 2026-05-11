from __future__ import annotations

from ph_daily.errors import ExitCode


def main() -> None:
    raise SystemExit(int(ExitCode.CONFIG_ERROR))
