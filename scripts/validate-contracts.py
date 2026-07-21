#!/usr/bin/env python3
"""Validate deterministic FEAT-002 route/spray/safety contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT / "routes" / "examples" / "cucumber-row-route.example.json"

VALID_SEGMENT_TYPES = {"TRANSIT", "IN_ROW", "TURN", "RTL", "ABORT", "MISSION_END"}
VALID_SPRAY_MODES = {"OFF", "LEFT", "RIGHT", "BOTH"}
FORCED_OFF_TYPES = {"TRANSIT", "TURN", "RTL", "ABORT", "MISSION_END"}
REQUIRED_OUTPUTS = {
    "OFF": {"pump": False, "left_valve": False, "right_valve": False},
    "LEFT": {"pump": True, "left_valve": True, "right_valve": False},
    "RIGHT": {"pump": True, "left_valve": False, "right_valve": True},
    "BOTH": {"pump": True, "left_valve": True, "right_valve": True},
}
REQUIRED_FAULTS = {
    "front_obstacle",
    "invalid_side_sensor",
    "low_liquid",
    "pressure_low",
    "pressure_high",
    "low_battery",
    "rc_loss",
    "telemetry_loss",
    "emergency_stop",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_route(errors: list[str]) -> dict:
    if not ROUTE_PATH.is_file():
        fail(errors, f"missing route example: {ROUTE_PATH.relative_to(ROOT)}")
        return {}
    try:
        return json.loads(ROUTE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, f"invalid JSON in route example: {exc}")
        return {}


def validate_route(route: dict, errors: list[str]) -> None:
    if not route:
        return

    waypoints = route.get("waypoints")
    if not isinstance(waypoints, dict) or len(waypoints) < 2:
        fail(errors, "route must define at least two waypoints")
        waypoints = {}

    segments = route.get("segments")
    if not isinstance(segments, list) or not segments:
        fail(errors, "route must define at least one segment")
        return

    seen_ids: set[str] = set()
    has_spray_segment = False
    has_off_in_row_segment = False

    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            fail(errors, f"segment {index} must be an object")
            continue

        segment_id = segment.get("id")
        if not isinstance(segment_id, str) or not segment_id:
            fail(errors, f"segment {index} must define non-empty id")
        elif segment_id in seen_ids:
            fail(errors, f"duplicate segment id: {segment_id}")
        else:
            seen_ids.add(segment_id)

        segment_type = segment.get("type")
        if segment_type not in VALID_SEGMENT_TYPES:
            fail(errors, f"segment {segment_id or index} has invalid type: {segment_type!r}")

        spray = segment.get("spray")
        if spray not in VALID_SPRAY_MODES:
            fail(errors, f"segment {segment_id or index} has invalid spray mode: {spray!r}")

        if segment_type in FORCED_OFF_TYPES and spray != "OFF":
            fail(errors, f"segment {segment_id or index} type {segment_type} must force spray OFF")

        if segment_type != "IN_ROW" and spray in {"LEFT", "RIGHT", "BOTH"}:
            fail(errors, f"segment {segment_id or index} sprays outside IN_ROW")

        if segment_type == "IN_ROW" and spray in {"LEFT", "RIGHT", "BOTH"}:
            has_spray_segment = True
        if segment_type == "IN_ROW" and spray == "OFF":
            has_off_in_row_segment = True

        speed = segment.get("target_speed_mps")
        if not isinstance(speed, (int, float)) or speed <= 0:
            fail(errors, f"segment {segment_id or index} must define positive target_speed_mps")

        refs = segment.get("waypoints")
        if not isinstance(refs, list) or len(refs) < 2:
            fail(errors, f"segment {segment_id or index} must reference at least two waypoints")
        else:
            missing = [ref for ref in refs if ref not in waypoints]
            if missing:
                fail(errors, f"segment {segment_id or index} references missing waypoints: {missing}")

    if not has_spray_segment:
        fail(errors, "route must include at least one IN_ROW spray segment")
    if not has_off_in_row_segment:
        fail(errors, "route must include at least one IN_ROW spray OFF/alignment segment")


def validate_outputs(route: dict, errors: list[str]) -> None:
    mapping = route.get("mission_output_mapping") if route else None
    if not isinstance(mapping, dict):
        fail(errors, "route must define mission_output_mapping")
        return

    for mode, expected in REQUIRED_OUTPUTS.items():
        actual = mapping.get(mode)
        if actual != expected:
            fail(errors, f"spray mode {mode} maps to {actual!r}, expected {expected!r}")


def validate_faults(route: dict, errors: list[str]) -> None:
    faults = route.get("required_faults") if route else None
    if not isinstance(faults, list):
        fail(errors, "route must define required_faults list")
        return
    missing = sorted(REQUIRED_FAULTS - set(faults))
    if missing:
        fail(errors, f"missing required faults: {missing}")


def main() -> int:
    errors: list[str] = []
    route = load_route(errors)
    validate_route(route, errors)
    validate_outputs(route, errors)
    validate_faults(route, errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(f"Validated route/spray/safety contracts: {ROUTE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
