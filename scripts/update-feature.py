#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_GATES = [
    "01-discovery.md",
    "02-tech-design.md",
    "03-execution.md",
    "04-verification.md",
]


def load_feature_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def find_active_feature(data: dict) -> dict:
    active_id = data.get("active_feature")
    if not active_id:
        raise ValueError("feature-list.json must define active_feature")

    for feature in data.get("features", []):
        if feature.get("id") == active_id:
            return feature

    raise ValueError(f"active_feature {active_id!r} is not present in features")


def check_gate(feature_file: Path) -> tuple[bool, list[str]]:
    root_dir = feature_file.parent
    data = load_feature_file(feature_file)
    active_feature = find_active_feature(data)
    feature_id = active_feature["id"]
    gate_dir = root_dir / "stage-gates" / "active" / feature_id
    errors = []

    if not gate_dir.is_dir():
        errors.append(f"missing gate directory: {gate_dir}")
        return False, errors

    for gate_name in REQUIRED_GATES:
        gate_path = gate_dir / gate_name
        if not gate_path.is_file():
            errors.append(f"missing gate file: {gate_path}")

    verification_path = gate_dir / "04-verification.md"
    if verification_path.is_file():
        verification = verification_path.read_text(encoding="utf-8")
        status_match = re.search(r"^STATUS:\s*(PASS|FAIL)\s*$", verification, re.MULTILINE)
        if not status_match:
            errors.append("verification gate must contain an exact STATUS line")
        elif status_match.group(1) != "PASS":
            errors.append("verification gate status must be PASS")

    return not errors, errors


def update_active_feature(feature_file: Path) -> None:
    ok, errors = check_gate(feature_file)
    if not ok:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)

    data = load_feature_file(feature_file)
    active_feature = find_active_feature(data)
    active_feature["passes"] = True
    feature_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {active_feature['id']} passes=true")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or update active feature status.")
    parser.add_argument("feature_file", nargs="?", default="feature-list.json")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    feature_file = Path(args.feature_file).resolve()

    if args.check_only:
        ok, errors = check_gate(feature_file)
        if ok:
            print("Gate check passed")
            return 0
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    update_active_feature(feature_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
