#!/bin/bash
set -euo pipefail

rm -rf dist
uv sync --locked --extra catppuccin
uv build --wheel
uv pip install --python .venv/bin/python --no-deps --reinstall dist/*.whl
rm -rf .cache
uv run --locked --no-sync zensical serve "$@"
