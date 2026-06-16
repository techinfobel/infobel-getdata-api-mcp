#!/usr/bin/env bash
#
# Build the Claude Desktop extension bundle (.mcpb) for infobel-getdata.
#
# Produces a self-contained, cross-platform bundle using the MCPB "uv" server
# type: the host (Claude Desktop) runs `uv`, which resolves dependencies from
# the bundled pyproject.toml at install time — so users need neither a Python
# install nor any manual config. Credentials are collected via the install
# dialog (see user_config in mcpb/manifest.json).
#
# Requirements: Node.js (for `npx @anthropic-ai/mcpb`). uv is fetched by the
# host at runtime, not needed to build.
#
# Usage: ./build_mcpb.sh
# Output: dist/infobel-getdata.mcpb
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE="$ROOT/dist/mcpb-build"
OUT="$ROOT/dist"

echo "==> Cleaning staging dir"
rm -rf "$STAGE"
mkdir -p "$STAGE" "$OUT"

echo "==> Staging bundle contents"
# Manifest at bundle root
cp "$ROOT/mcpb/manifest.json" "$STAGE/manifest.json"
# Package source (uv builds/installs it from the bundled pyproject)
cp -R "$ROOT/infobel_api" "$STAGE/infobel_api"
# Dependency + build metadata for uv to resolve
cp "$ROOT/pyproject.toml" "$STAGE/pyproject.toml"
cp "$ROOT/README.md" "$STAGE/README.md"
cp "$ROOT/LICENSE" "$STAGE/LICENSE"
# Optional icon shown in the Claude Desktop UI
if [ -f "$ROOT/mcpb/icon.png" ]; then
  cp "$ROOT/mcpb/icon.png" "$STAGE/icon.png"
fi

echo "==> Pruning caches/artifacts from staging"
find "$STAGE" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$STAGE" -type d -name "*.egg-info" -prune -exec rm -rf {} +

echo "==> Validating manifest"
npx --yes @anthropic-ai/mcpb validate "$STAGE/manifest.json"

echo "==> Packing"
npx --yes @anthropic-ai/mcpb pack "$STAGE" "$OUT/infobel-getdata.mcpb"

echo "==> Done: $OUT/infobel-getdata.mcpb"
