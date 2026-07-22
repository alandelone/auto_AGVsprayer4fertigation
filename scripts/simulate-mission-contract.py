#!/usr/bin/env python3
"""Run a deterministic FEAT-002 mission contract simulation.

This is a lightweight simulator for the route/spray/safety contract. It does not
claim physical vehicle dynamics; it proves the mission state machine that must be
mapped onto ArduRover mission DO commands before live hardware.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT / "routes" / "examples" / "cucumber-row-route.example.json"
FAULT_SEGMENT_ID = "row_01_left_spray"
FAULT_NAME = "front_obstacle"
SAFE_OUTPUT = {"pump": False, "left_valve": False, "right_valve": False}


def output_state(mapping: dict, spray_mode: str) -> dict:
    return mapping[spray_mode]


def assert_state(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    route = json.loads(ROUTE_PATH.read_text(encoding="utf-8"))
    mapping = route["mission_output_mapping"]

    events: list[str] = []
    saw_row_entry = False
    saw_spray_on = False
    saw_row_exit_off = False
    saw_fault_stop = False

    previous_spray = None
    for segment in route["segments"]:
        spray = segment["spray"]
        state = output_state(mapping, spray)
        segment_id = segment["id"]
        segment_type = segment["type"]

        assert_state("pump" in state and "left_valve" in state and "right_valve" in state, f"{segment_id}: incomplete output state")
        assert_state(segment["target_speed_mps"] > 0, f"{segment_id}: speed must be positive")

        if segment_type == "TRANSIT" and segment_id == "entry_transit":
            assert_state(state == SAFE_OUTPUT, "entry transit must start safe/off")
            saw_row_entry = True
            events.append(f"ROW_ENTRY {segment_id}: spray=OFF outputs={state}")

        if segment_type == "IN_ROW" and spray in {"LEFT", "RIGHT", "BOTH"}:
            assert_state(state["pump"] is True, f"{segment_id}: spray segment must enable pump")
            saw_spray_on = True
            events.append(f"SPRAY_ON {segment_id}: spray={spray} speed={segment['target_speed_mps']} outputs={state}")

        if previous_spray and previous_spray != spray:
            events.append(f"SPRAY_TRANSITION {previous_spray}->{spray} at {segment_id}")

        if segment_id == FAULT_SEGMENT_ID:
            fault_state = SAFE_OUTPUT
            assert_state(fault_state == SAFE_OUTPUT, "fault override must force all outputs off")
            saw_fault_stop = True
            events.append(f"FAULT_STOP {FAULT_NAME} during {segment_id}: mode=HOLD outputs={fault_state} operator_review_required=True")

        if segment_id == "row_01_exit_off":
            assert_state(state == SAFE_OUTPUT, "row exit must force spray off")
            saw_row_exit_off = True
            events.append(f"ROW_EXIT {segment_id}: spray=OFF outputs={state}")

        if segment_type == "MISSION_END":
            assert_state(state == SAFE_OUTPUT, "mission end must force spray off")
            events.append(f"MISSION_END {segment_id}: spray=OFF outputs={state}")

        previous_spray = spray

    assert_state(saw_row_entry, "missing row-entry proof")
    assert_state(saw_spray_on, "missing in-row spray proof")
    assert_state(saw_row_exit_off, "missing row-exit off proof")
    assert_state(saw_fault_stop, "missing fault-stop proof")

    print(f"Mission contract simulation PASS: {ROUTE_PATH.relative_to(ROOT)}")
    for event in events:
        print(f"- {event}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
