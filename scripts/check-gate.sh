#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FEATURE_FILE="$ROOT_DIR/feature-list.json"

python "$ROOT_DIR/scripts/update-feature.py" --check-only "$FEATURE_FILE"

if [[ -x "$ROOT_DIR/scripts/validate-contracts.py" ]]; then
  python "$ROOT_DIR/scripts/validate-contracts.py"
fi

if [[ -x "$ROOT_DIR/scripts/simulate-mission-contract.py" ]]; then
  python "$ROOT_DIR/scripts/simulate-mission-contract.py"
fi

if [[ -x "$ROOT_DIR/scripts/validate-hardware-pinout.py" ]]; then
  python "$ROOT_DIR/scripts/validate-hardware-pinout.py"
fi

if [[ -x "$ROOT_DIR/scripts/validate-bench-ratings.py" ]]; then
  python "$ROOT_DIR/scripts/validate-bench-ratings.py"
fi
