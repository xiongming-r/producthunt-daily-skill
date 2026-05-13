from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE = ROOT / "skills" / "producthunt-daily"
DEFAULT_DESTINATION = ROOT / "dist" / "skills" / "producthunt-daily"
FORBIDDEN_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}


def _ignore_runtime_artifacts(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        path = Path(directory) / name
        if name in FORBIDDEN_DIRS or name == ".DS_Store":
            ignored.add(name)
        elif path.suffix in FORBIDDEN_SUFFIXES:
            ignored.add(name)
        elif name.endswith(".egg-info"):
            ignored.add(name)
    return ignored


def _copytree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=_ignore_runtime_artifacts)


def export_skill(destination: Path = DEFAULT_DESTINATION) -> Path:
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SKILL_SOURCE / "SKILL.md", destination / "SKILL.md")
    _copytree(SKILL_SOURCE / "references", destination / "references")

    scripts_destination = destination / "scripts"
    scripts_destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL_SOURCE / "scripts" / "setup.sh", scripts_destination / "setup.sh")
    shutil.copy2(
        SKILL_SOURCE / "scripts" / ".env.example",
        scripts_destination / ".env.example",
    )
    shutil.copy2(ROOT / "pyproject.toml", scripts_destination / "pyproject.toml")
    _copytree(ROOT / "src", scripts_destination / "src")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DESTINATION,
        help="Destination directory for exported skill package",
    )
    args = parser.parse_args()
    destination = export_skill(args.dest)
    print(destination)


if __name__ == "__main__":
    main()
