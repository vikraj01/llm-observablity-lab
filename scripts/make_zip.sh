#!/usr/bin/env bash
#
# Build a shareable zip of this project.
#
#   ./scripts/make_zip.sh
#
# Output lands in dist/, which is gitignored. The zip deliberately excludes:
#   .venv/       rebuild it with `uv sync`
#   .git/        history is on GitHub
#   langfuse/    clone it yourself, it is ~261 MB
#   .env         secrets, never ship these
#
# Whoever receives it runs:
#   unzip llm-observability-lab.zip && cd llm-observability-lab
#   uv sync && cp .env.example .env   # then fill in .env
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="llm-observability-lab"
OUT="$ROOT/dist"
ZIP="$OUT/$NAME.zip"

cd "$ROOT"
mkdir -p "$OUT"
rm -f "$ZIP"

zip -r -q "$ZIP" . \
  -x '.git/*' \
  -x '.venv/*' \
  -x 'langfuse/*' \
  -x 'dist/*' \
  -x '.env' \
  -x '*/.env' \
  -x '*__pycache__/*' \
  -x '*.pyc' \
  -x '.pytest_cache/*' \
  -x '.ruff_cache/*'

echo "built $ZIP"
echo "size:  $(du -h "$ZIP" | cut -f1)"
echo "files: $(unzip -l "$ZIP" | tail -1 | awk '{print $2}')"

# Safety net: fail loudly if a secret slipped in.
if unzip -l "$ZIP" | grep -qE '(^|/)\.env$'; then
  echo "ERROR: .env is inside the zip. Delete it and fix the exclude list." >&2
  exit 1
fi
echo "verified: no .env inside"
