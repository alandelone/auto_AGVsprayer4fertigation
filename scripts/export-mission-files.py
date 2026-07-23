#!/usr/bin/env python3
"""Export FEAT-007 synthetic mission source to QGC .plan and ArduPilot WPL 110."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "missions" / "cucumber-row-mission.v0.json"
MAPPING = ROOT / "hardware" / "pixhawk-actuator-mapping.v0.json"

MAV_FRAME_GLOBAL_RELATIVE_ALT = 3
MAV_FRAME_MISSION = 2
MAV_CMD_NAV_WAYPOINT = 16
MAV_CMD_DO_CHANGE_SPEED = 178
MAV_CMD_DO_SET_RELAY = 181
MAV_CMD_DO_SET_SERVO = 183


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def output_by_id(mapping: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in mapping["outputs"]}


def assert_mapping_matches_source(source: dict[str, Any], mapping: dict[str, Any]) -> None:
    outputs = output_by_id(mapping)
    pump = outputs["pump_pwm"]
    left = outputs["left_spray_valve"]
    right = outputs["right_spray_valve"]
    agitation = outputs["agitation"]
    commands = source["actuator_commands"]

    checks = [
        (commands["pump_pwm"]["command_id"], MAV_CMD_DO_SET_SERVO, "pump command id"),
        (commands["pump_pwm"]["servo_channel"], pump["servo_channel"], "pump servo channel"),
        (commands["pump_pwm"]["off_pwm_us"], pump["safe_pwm_us"], "pump safe PWM"),
        (commands["left_spray_valve"]["relay_number"], left["relay_number"], "left relay"),
        (commands["right_spray_valve"]["relay_number"], right["relay_number"], "right relay"),
        (commands["agitation"]["relay_number"], agitation["relay_number"], "agitation relay"),
    ]
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"{label} mismatch: source={actual!r} mapping={expected!r}")


def transition_by_item(source: dict[str, Any]) -> dict[str, str]:
    transitions: dict[str, str] = {}
    valid_items = {item["id"] for item in source["mission_items"]}
    for transition in source["actuator_transitions"]:
        item_id = transition["at_item_id"]
        if item_id not in valid_items:
            raise ValueError(f"transition references unknown mission item: {item_id}")
        transitions[item_id] = transition["spray_state"]
    return transitions


def command_rows_for_state(source: dict[str, Any], state_name: str) -> list[dict[str, Any]]:
    state = source["spray_states"][state_name]
    commands = source["actuator_commands"]
    return [
        {
            "command": MAV_CMD_DO_SET_SERVO,
            "frame": MAV_FRAME_MISSION,
            "params": [commands["pump_pwm"]["servo_channel"], state["pump_pwm_us"], 0, 0, 0, 0, 0],
            "label": f"pump_pwm_{state_name.lower()}",
        },
        {
            "command": MAV_CMD_DO_SET_RELAY,
            "frame": MAV_FRAME_MISSION,
            "params": [commands["left_spray_valve"]["relay_number"], state["left_valve"], 0, 0, 0, 0, 0],
            "label": f"left_valve_{state_name.lower()}",
        },
        {
            "command": MAV_CMD_DO_SET_RELAY,
            "frame": MAV_FRAME_MISSION,
            "params": [commands["right_spray_valve"]["relay_number"], state["right_valve"], 0, 0, 0, 0, 0],
            "label": f"right_valve_{state_name.lower()}",
        },
        {
            "command": MAV_CMD_DO_SET_RELAY,
            "frame": MAV_FRAME_MISSION,
            "params": [commands["agitation"]["relay_number"], state["agitation"], 0, 0, 0, 0, 0],
            "label": f"agitation_{state_name.lower()}",
        },
    ]


def mission_sequence(source: dict[str, Any]) -> list[dict[str, Any]]:
    transitions = transition_by_item(source)
    sequence: list[dict[str, Any]] = []
    for item in source["mission_items"]:
        if item["type"] == "home":
            continue
        if item["id"] in transitions:
            for command in command_rows_for_state(source, transitions[item["id"]]):
                sequence.append({"kind": "actuator", "at_item_id": item["id"], **command})
        sequence.append(
            {
                "kind": "speed",
                "at_item_id": item["id"],
                "command": MAV_CMD_DO_CHANGE_SPEED,
                "frame": MAV_FRAME_MISSION,
                "params": [1, item["target_speed_mps"], -1, 0, 0, 0, 0],
            }
        )
        sequence.append(
            {
                "kind": "waypoint",
                "item_id": item["id"],
                "row_label": item["row_label"],
                "spray_state": item["spray_state"],
                "command": MAV_CMD_NAV_WAYPOINT,
                "frame": MAV_FRAME_GLOBAL_RELATIVE_ALT,
                "params": [0, source["vehicle"]["acceptance_radius_m"], 0, 0, item["lat"], item["lon"], item["alt_m"]],
            }
        )
    return sequence


def plan_item(seq: int, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "AMSLAltAboveTerrain": None,
        "Altitude": entry["params"][6],
        "AltitudeMode": 1,
        "autoContinue": True,
        "command": entry["command"],
        "doJumpId": seq + 1,
        "frame": entry["frame"],
        "params": entry["params"],
        "type": "SimpleItem",
    }


def export_plan(source: dict[str, Any], sequence: list[dict[str, Any]], path: Path) -> None:
    home = source["mission_items"][0]
    data = {
        "fileType": "Plan",
        "geoFence": {"circles": [], "polygons": [], "version": 2},
        "groundStation": "QGroundControl",
        "mission": {
            "cruiseSpeed": 0.35,
            "firmwareType": 3,
            "globalPlanAltitudeMode": 1,
            "hoverSpeed": 0,
            "items": [plan_item(seq, entry) for seq, entry in enumerate(sequence)],
            "plannedHomePosition": [home["lat"], home["lon"], home["alt_m"]],
            "vehicleType": 10,
            "version": 2,
        },
        "rallyPoints": {"points": [], "version": 2},
        "version": 1,
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_number(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.7f}".rstrip("0").rstrip(".") if value else "0"
    return str(value)


def export_waypoints(sequence: list[dict[str, Any]], path: Path) -> None:
    lines = ["QGC WPL 110"]
    for seq, entry in enumerate(sequence):
        current = 1 if seq == 0 else 0
        fields = [seq, current, entry["frame"], entry["command"], *entry["params"], 1]
        lines.append("\t".join(format_number(value) for value in fields))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    source = load_json(SOURCE)
    mapping = load_json(MAPPING)
    assert_mapping_matches_source(source, mapping)
    sequence = mission_sequence(source)

    plan_path = ROOT / source["required_exports"]["qgc_plan"]
    wpl_path = ROOT / source["required_exports"]["ardupilot_wpl110"]
    plan_path.parent.mkdir(parents=True, exist_ok=True)

    export_plan(source, sequence, plan_path)
    export_waypoints(sequence, wpl_path)

    actuator_count = sum(1 for item in sequence if item["kind"] == "actuator")
    waypoint_count = sum(1 for item in sequence if item["kind"] == "waypoint")
    print(f"EXPORTED_QGC_PLAN={plan_path.relative_to(ROOT)}")
    print(f"EXPORTED_ARDUPILOT_WPL110={wpl_path.relative_to(ROOT)}")
    print(f"MISSION_EXPORT_ITEMS={len(sequence)} WAYPOINTS={waypoint_count} ACTUATOR_COMMANDS={actuator_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
