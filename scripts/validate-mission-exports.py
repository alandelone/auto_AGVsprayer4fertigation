#!/usr/bin/env python3
"""Validate FEAT-007 mission source, QGC .plan, and ArduPilot WPL 110 exports."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "missions" / "cucumber-row-mission.v0.json"

MAV_FRAME_GLOBAL_RELATIVE_ALT = 3
MAV_FRAME_MISSION = 2
MAV_CMD_NAV_WAYPOINT = 16
MAV_CMD_DO_CHANGE_SPEED = 178
MAV_CMD_DO_SET_RELAY = 181
MAV_CMD_DO_SET_SERVO = 183


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def mission_transitions(source: dict[str, Any]) -> dict[str, str]:
    item_ids = {item["id"] for item in source["mission_items"]}
    transitions: dict[str, str] = {}
    for transition in source["actuator_transitions"]:
        item_id = transition["at_item_id"]
        require(item_id in item_ids, f"transition references unknown item {item_id}")
        require(item_id not in transitions, f"duplicate actuator transition for {item_id}")
        state = transition["spray_state"]
        require(state in source["spray_states"], f"transition uses unknown spray state {state}")
        transitions[item_id] = state
    return transitions


def actuator_rows_for_state(source: dict[str, Any], state_name: str) -> list[dict[str, Any]]:
    state = source["spray_states"][state_name]
    commands = source["actuator_commands"]
    return [
        {"command": MAV_CMD_DO_SET_SERVO, "frame": MAV_FRAME_MISSION, "params": [commands["pump_pwm"]["servo_channel"], state["pump_pwm_us"], 0, 0, 0, 0, 0]},
        {"command": MAV_CMD_DO_SET_RELAY, "frame": MAV_FRAME_MISSION, "params": [commands["left_spray_valve"]["relay_number"], state["left_valve"], 0, 0, 0, 0, 0]},
        {"command": MAV_CMD_DO_SET_RELAY, "frame": MAV_FRAME_MISSION, "params": [commands["right_spray_valve"]["relay_number"], state["right_valve"], 0, 0, 0, 0, 0]},
        {"command": MAV_CMD_DO_SET_RELAY, "frame": MAV_FRAME_MISSION, "params": [commands["agitation"]["relay_number"], state["agitation"], 0, 0, 0, 0, 0]},
    ]


def expected_sequence(source: dict[str, Any]) -> list[dict[str, Any]]:
    transitions = mission_transitions(source)
    sequence: list[dict[str, Any]] = []
    for item in source["mission_items"]:
        if item["type"] == "home":
            continue
        if item["id"] in transitions:
            sequence.extend(actuator_rows_for_state(source, transitions[item["id"]]))
        sequence.append({"command": MAV_CMD_DO_CHANGE_SPEED, "frame": MAV_FRAME_MISSION, "params": [1, item["target_speed_mps"], -1, 0, 0, 0, 0]})
        sequence.append({"command": MAV_CMD_NAV_WAYPOINT, "frame": MAV_FRAME_GLOBAL_RELATIVE_ALT, "params": [0, source["vehicle"]["acceptance_radius_m"], 0, 0, item["lat"], item["lon"], item["alt_m"]]})
    return sequence


def validate_source(source: dict[str, Any]) -> None:
    require(source["feature_id"] == "FEAT-007", "source feature_id must be FEAT-007")
    require(source["coordinate_policy"]["type"] == "synthetic_test_only", "source coordinates must be synthetic_test_only")
    mission_items = source["mission_items"]
    require(mission_items[0]["type"] == "home", "first mission item must be home")
    require([item["seq"] for item in mission_items] == list(range(len(mission_items))), "mission item seq values must be contiguous")
    for item in mission_items:
        require(abs(item["lat"]) < 0.01 and abs(item["lon"]) < 0.01, f"non-synthetic-looking coordinate on {item['id']}")
        require(item["spray_state"] in source["spray_states"], f"unknown spray state on {item['id']}")
    transitions = mission_transitions(source)
    require(transitions["WP001"] == "OFF", "mission must start with explicit OFF transition at WP001")
    require(transitions["WP006"] == "OFF", "mission must end with explicit OFF transition at WP006")


def same_params(actual: list[Any], expected: list[Any]) -> bool:
    if len(actual) != len(expected):
        return False
    for left, right in zip(actual, expected):
        if isinstance(left, (int, float)) or isinstance(right, (int, float)):
            if abs(float(left) - float(right)) > 1e-9:
                return False
        elif left != right:
            return False
    return True


def validate_plan(source: dict[str, Any], expected: list[dict[str, Any]]) -> dict[int, int]:
    plan_path = ROOT / source["required_exports"]["qgc_plan"]
    plan = load_json(plan_path)
    require(plan["fileType"] == "Plan", "QGC plan fileType must be Plan")
    home = source["mission_items"][0]
    require(same_params(plan["mission"]["plannedHomePosition"], [home["lat"], home["lon"], home["alt_m"]]), "QGC plannedHomePosition does not match source home")
    items = plan["mission"]["items"]
    require(len(items) == len(expected), f"QGC item count mismatch: actual={len(items)} expected={len(expected)}")
    for seq, (actual, wanted) in enumerate(zip(items, expected)):
        require(actual["type"] == "SimpleItem", f"QGC item {seq} type must be SimpleItem")
        require(actual["doJumpId"] == seq + 1, f"QGC item {seq} doJumpId mismatch")
        require(actual["command"] == wanted["command"], f"QGC item {seq} command mismatch")
        require(actual["frame"] == wanted["frame"], f"QGC item {seq} frame mismatch")
        require(same_params(actual["params"], wanted["params"]), f"QGC item {seq} params mismatch")
    return Counter(item["command"] for item in items)


def parse_wpl_number(value: str) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def validate_waypoints(source: dict[str, Any], expected: list[dict[str, Any]]) -> dict[int, int]:
    wpl_path = ROOT / source["required_exports"]["ardupilot_wpl110"]
    if not wpl_path.exists():
        raise FileNotFoundError(f"missing required file: {wpl_path.relative_to(ROOT)}")
    lines = wpl_path.read_text(encoding="utf-8").splitlines()
    require(lines and lines[0] == "QGC WPL 110", "WPL header must be QGC WPL 110")
    rows = [line.split("\t") for line in lines[1:]]
    require(len(rows) == len(expected), f"WPL item count mismatch: actual={len(rows)} expected={len(expected)}")
    for seq, (row, wanted) in enumerate(zip(rows, expected)):
        require(len(row) == 12, f"WPL row {seq} must contain 12 tab-separated columns")
        require(int(row[0]) == seq, f"WPL row {seq} sequence mismatch")
        require(int(row[1]) == (1 if seq == 0 else 0), f"WPL row {seq} current flag mismatch")
        require(int(row[2]) == wanted["frame"], f"WPL row {seq} frame mismatch")
        require(int(row[3]) == wanted["command"], f"WPL row {seq} command mismatch")
        params = [parse_wpl_number(value) for value in row[4:11]]
        require(same_params(params, wanted["params"]), f"WPL row {seq} params mismatch")
        require(int(row[11]) == 1, f"WPL row {seq} autocontinue must be 1")
    return Counter(int(row[3]) for row in rows)


def main() -> int:
    source = load_json(SOURCE)
    validate_source(source)
    expected = expected_sequence(source)
    plan_counts = validate_plan(source, expected)
    wpl_counts = validate_waypoints(source, expected)
    require(plan_counts == wpl_counts, "QGC and WPL command counts differ")

    waypoint_count = plan_counts[MAV_CMD_NAV_WAYPOINT]
    speed_count = plan_counts[MAV_CMD_DO_CHANGE_SPEED]
    relay_count = plan_counts[MAV_CMD_DO_SET_RELAY]
    servo_count = plan_counts[MAV_CMD_DO_SET_SERVO]
    actuator_count = relay_count + servo_count
    print("MISSION_EXPORT_VALIDATION_OK")
    print(f"SOURCE_ITEMS={len(source['mission_items'])} EXPORT_ITEMS={len(expected)} WAYPOINTS={waypoint_count}")
    print(f"COMMAND_COUNTS NAV_WAYPOINT={waypoint_count} DO_CHANGE_SPEED={speed_count} DO_SET_RELAY={relay_count} DO_SET_SERVO={servo_count}")
    print(f"SAFETY_TRANSITIONS={len(source['actuator_transitions'])} ACTUATOR_COMMANDS={actuator_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
