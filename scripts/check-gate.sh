#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FEATURE_FILE="$ROOT_DIR/feature-list.json"

python "$ROOT_DIR/scripts/update-feature.py" --check-only "$FEATURE_FILE"
