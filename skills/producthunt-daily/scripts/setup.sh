#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="${1:-$HOME/.ph-daily}"

echo "=== Product Hunt Daily Setup ==="
echo "Install directory: $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"
cp -R "$SCRIPT_DIR/src" "$INSTALL_DIR/src"
cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/pyproject.toml"
cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env.example"

if [ ! -d "$INSTALL_DIR/.venv" ]; then
  python3 -m venv "$INSTALL_DIR/.venv"
fi

source "$INSTALL_DIR/.venv/bin/activate"
python -m pip install -e "$INSTALL_DIR"

if [ ! -f "$INSTALL_DIR/.env" ]; then
  cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
fi

cd "$INSTALL_DIR"
ph-daily healthcheck || true

echo "Setup files installed. Edit $INSTALL_DIR/.env before live collection."
