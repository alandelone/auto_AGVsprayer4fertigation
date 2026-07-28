#!/usr/bin/env python3
"""Validate the FEAT-009 SITL position-confidence fallback contract.

The validator is deterministic and standard-library only so heartbeat/CI runs can
exercise the canopy dead-reckoning decision logic before a live SITL process is
introduced.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = ROOT / "sitl" / "position-confidence.v0.json"

REQUIRED_UNITS = {
    "gps_age_s": "seconds",
    "hdop": "dimensionless",
    "distance_m": "meters",
    "heading_deg": "degrees",
    "duration_s": "seconds",
    "speed_mps": "meters_per_second",
}
REQUIRED_SOURCE_KEYS = {
    "mission_export": "FEAT-007",
    "actuator_mapping": "FEAT-006",
    "preflight_dosing": "FEAT-008",
}
DECISIONS = ("RTK_CONFIDENT", "DEAD_RECKONING_ACTIVE", "SAFE_HOLD")
SPRAY_ZONES = {"OFF", "LEFT", "RIGHT", "BOTH"}


class ValidationError(Exception):
    """Contract validation failed."""


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_number(value: Any, field: str, *, minimum: float | None = None) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    numeric = float(value)
    require(math.isfinite(numeric), f"{field} must be finite")
    if minimum is not None:
        require(numeric >= minimum, f"{field} must be >= {minimum}")
    return numeric


def require_string(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a non-empty string")
    return value


def require_bool(value: Any, field: str) -> bool:
    require(isinstance(value, bool), f"{field} must be boolean")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {display_path(path)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {display_path(path)}: {exc}") from exc
    require(isinstance(data, dict), f"{display_path(path)} must contain a JSON object")
    return data


def resolve_repo_path(value: Any, field: str) -> Path:
    raw = require_string(value, field)
    rel = Path(raw)
    require(not rel.is_absolute(), f"{field} must be repository-relative")
    resolved = (ROOT / rel).resolve()
    require(resolved == ROOT or ROOT in resolved.parents, f"{field} must stay inside repository")
    return resolved


def resolve_contract_path(raw: str | None) -> Path:
    if raw is None:
        return DEFAULT_CONTRACT_PATH
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    require(resolved == ROOT or ROOT in resolved.parents, "contract path must stay inside repository")
    return resolved


def validate_units(contract: dict[str, Any]) -> None:
    units = contract.get("units")
    require(isinstance(units, dict), "units must be an object")
    for key, expected in REQUIRED_UNITS.items():
        require(units.get(key) == expected, f"units.{key} must be {expected!r}")


def validate_thresholds(contract: dict[str, Any]) -> dict[str, Any]:
    thresholds = contract.get("thresholds")
    require(isinstance(thresholds, dict), "thresholds must be an object")

    accepted = thresholds.get("accepted_rtk_fix_types")
    require(isinstance(accepted, list) and accepted, "thresholds.accepted_rtk_fix_types must be a non-empty list")
    accepted_set = {require_string(item, "accepted_rtk_fix_types item") for item in accepted}
    require("RTK_FIXED" in accepted_set, "accepted_rtk_fix_types must include RTK_FIXED")

    ultrasonic = thresholds.get("ultrasonic_valid_range_m")
    require(isinstance(ultrasonic, dict), "thresholds.ultrasonic_valid_range_m must be an object")
    ultrasonic_min = require_number(ultrasonic.get("min"), "ultrasonic_valid_range_m.min", minimum=0.0)
    ultrasonic_max = require_number(ultrasonic.get("max"), "ultrasonic_valid_range_m.max", minimum=ultrasonic_min)

    parsed = {
        "accepted_rtk_fix_types": accepted_set,
        "max_hdop": require_number(thresholds.get("max_hdop"), "thresholds.max_hdop", minimum=0.0),
        "max_gps_age_s": require_number(thresholds.get("max_gps_age_s"), "thresholds.max_gps_age_s", minimum=0.0),
        "max_odom_vs_mission_drift_m": require_number(
            thresholds.get("max_odom_vs_mission_drift_m"),
            "thresholds.max_odom_vs_mission_drift_m",
            minimum=0.0,
        ),
        "max_imu_odom_heading_divergence_deg": require_number(
            thresholds.get("max_imu_odom_heading_divergence_deg"),
            "thresholds.max_imu_odom_heading_divergence_deg",
            minimum=0.0,
        ),
        "ultrasonic_min_m": ultrasonic_min,
        "ultrasonic_max_m": ultrasonic_max,
        "row_width_m": require_number(thresholds.get("row_width_m"), "thresholds.row_width_m", minimum=0.01),
        "max_ultrasonic_row_width_error_m": require_number(
            thresholds.get("max_ultrasonic_row_width_error_m"),
            "thresholds.max_ultrasonic_row_width_error_m",
            minimum=0.0,
        ),
        "max_fallback_duration_s": require_number(
            thresholds.get("max_fallback_duration_s"),
            "thresholds.max_fallback_duration_s",
            minimum=0.0,
        ),
        "max_fallback_distance_m": require_number(
            thresholds.get("max_fallback_distance_m"),
            "thresholds.max_fallback_distance_m",
            minimum=0.0,
        ),
    }
    require(parsed["max_imu_odom_heading_divergence_deg"] <= 180.0, "heading divergence threshold must be <= 180")
    return parsed


def validate_sources(contract: dict[str, Any], safe_outputs: dict[str, Any]) -> int:
    sources = contract.get("sources")
    require(isinstance(sources, dict), "sources must be an object")
    for key in REQUIRED_SOURCE_KEYS:
        require(key in sources, f"sources.{key} is required")

    mission = load_json(resolve_repo_path(sources["mission_export"], "sources.mission_export"))
    mapping = load_json(resolve_repo_path(sources["actuator_mapping"], "sources.actuator_mapping"))
    preflight = load_json(resolve_repo_path(sources["preflight_dosing"], "sources.preflight_dosing"))

    require(mission.get("feature_id") == REQUIRED_SOURCE_KEYS["mission_export"], "mission_export must reference FEAT-007")
    require(mapping.get("feature_id") == REQUIRED_SOURCE_KEYS["actuator_mapping"], "actuator_mapping must reference FEAT-006")
    require(preflight.get("feature_id") == REQUIRED_SOURCE_KEYS["preflight_dosing"], "preflight_dosing must reference FEAT-008")

    mission_items = mission.get("mission_items")
    require(isinstance(mission_items, list), "mission_export.mission_items must be a list")
    spray_segments = [
        item
        for item in mission_items
        if isinstance(item, dict) and item.get("spray_state") in {"LEFT", "RIGHT", "BOTH"}
    ]
    require(spray_segments, "mission_export must include at least one spray segment")

    outputs = mapping.get("outputs")
    require(isinstance(outputs, list), "actuator_mapping.outputs must be a list")
    by_output = {item.get("id"): item for item in outputs if isinstance(item, dict)}
    pump = by_output.get("pump_pwm")
    left = by_output.get("left_spray_valve")
    right = by_output.get("right_spray_valve")
    require(isinstance(pump, dict), "actuator_mapping.outputs must include pump_pwm")
    require(isinstance(left, dict), "actuator_mapping.outputs must include left_spray_valve")
    require(isinstance(right, dict), "actuator_mapping.outputs must include right_spray_valve")
    require(pump.get("safe_pwm_us") == safe_outputs.get("pump_pwm_us"), "contract pump safe output must match actuator mapping")
    require(left.get("default_state") == safe_outputs.get("left_spray_valve"), "contract left valve safe output must match actuator mapping")
    require(right.get("default_state") == safe_outputs.get("right_spray_valve"), "contract right valve safe output must match actuator mapping")

    dosing_model = preflight.get("dosing_model")
    require(isinstance(dosing_model, dict), "preflight_dosing.dosing_model must be an object")
    pump_pwm = dosing_model.get("pump_pwm_us")
    require(isinstance(pump_pwm, dict), "preflight_dosing.dosing_model.pump_pwm_us must be an object")
    require(pump_pwm.get("off") == safe_outputs.get("pump_pwm_us"), "contract pump safe output must match FEAT-008 pump off PWM")
    return len(spray_segments)


def validate_states(contract: dict[str, Any]) -> None:
    states = contract.get("states")
    require(isinstance(states, dict), "states must be an object")
    for decision in DECISIONS:
        require_string(states.get(decision), f"states.{decision}")


def validate_safe_outputs(contract: dict[str, Any]) -> dict[str, Any]:
    safe_outputs = contract.get("safe_outputs")
    require(isinstance(safe_outputs, dict), "safe_outputs must be an object")
    require(safe_outputs.get("pump_pwm_us") == 1000, "safe_outputs.pump_pwm_us must be 1000")
    require(safe_outputs.get("left_spray_valve") == 0, "safe_outputs.left_spray_valve must be 0")
    require(safe_outputs.get("right_spray_valve") == 0, "safe_outputs.right_spray_valve must be 0")
    return safe_outputs


def angular_difference_deg(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


def require_object(parent: dict[str, Any], key: str, field: str) -> dict[str, Any]:
    value = parent.get(key)
    require(isinstance(value, dict), f"{field}.{key} must be an object")
    return value


def evaluate_scenario(scenario: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    scenario_id = require_string(scenario.get("id"), "scenario.id")
    mission = require_object(scenario, "mission_segment", scenario_id)
    telemetry = require_object(scenario, "telemetry", scenario_id)

    spray_zone = require_string(mission.get("spray_zone"), f"{scenario_id}.mission_segment.spray_zone")
    require(spray_zone in SPRAY_ZONES, f"{scenario_id}.mission_segment.spray_zone must be one of {sorted(SPRAY_ZONES)}")
    require_number(mission.get("expected_heading_deg"), f"{scenario_id}.mission_segment.expected_heading_deg")
    mission_distance = require_number(
        mission.get("distance_into_segment_m"),
        f"{scenario_id}.mission_segment.distance_into_segment_m",
        minimum=0.0,
    )

    gps = require_object(telemetry, "gps", f"{scenario_id}.telemetry")
    imu = require_object(telemetry, "imu", f"{scenario_id}.telemetry")
    odometer = require_object(telemetry, "odometer", f"{scenario_id}.telemetry")
    ultrasonic = require_object(telemetry, "ultrasonic", f"{scenario_id}.telemetry")
    fallback = require_object(telemetry, "fallback", f"{scenario_id}.telemetry")

    gps_fix_type = require_string(gps.get("fix_type"), f"{scenario_id}.telemetry.gps.fix_type")
    gps_hdop = require_number(gps.get("hdop"), f"{scenario_id}.telemetry.gps.hdop", minimum=0.0)
    gps_age_s = require_number(gps.get("age_s"), f"{scenario_id}.telemetry.gps.age_s", minimum=0.0)
    imu_heading = require_number(imu.get("heading_deg"), f"{scenario_id}.telemetry.imu.heading_deg")
    odom_heading = require_number(odometer.get("heading_deg"), f"{scenario_id}.telemetry.odometer.heading_deg")
    odom_distance = require_number(
        odometer.get("distance_into_segment_m"),
        f"{scenario_id}.telemetry.odometer.distance_into_segment_m",
        minimum=0.0,
    )
    ultrasonic_left = require_number(ultrasonic.get("left_m"), f"{scenario_id}.telemetry.ultrasonic.left_m", minimum=0.0)
    ultrasonic_right = require_number(ultrasonic.get("right_m"), f"{scenario_id}.telemetry.ultrasonic.right_m", minimum=0.0)
    fallback_active = require_bool(fallback.get("active"), f"{scenario_id}.telemetry.fallback.active")
    fallback_duration = require_number(fallback.get("duration_s"), f"{scenario_id}.telemetry.fallback.duration_s", minimum=0.0)
    fallback_distance = require_number(fallback.get("distance_m"), f"{scenario_id}.telemetry.fallback.distance_m", minimum=0.0)
    require_number(telemetry.get("speed_mps"), f"{scenario_id}.telemetry.speed_mps", minimum=0.0)

    if gps_age_s > thresholds["max_gps_age_s"]:
        return {
            "decision": "SAFE_HOLD",
            "mode": "HOLD",
            "spray_allowed": False,
            "safe_outputs_required": True,
            "reason_codes": ["gps_stale"],
        }

    local_reasons: list[str] = []
    if angular_difference_deg(imu_heading, odom_heading) > thresholds["max_imu_odom_heading_divergence_deg"]:
        local_reasons.append("imu_odom_heading_disagreement")
    if abs(odom_distance - mission_distance) > thresholds["max_odom_vs_mission_drift_m"]:
        local_reasons.append("odometer_mission_drift")

    ultrasonic_valid = (
        thresholds["ultrasonic_min_m"] <= ultrasonic_left <= thresholds["ultrasonic_max_m"]
        and thresholds["ultrasonic_min_m"] <= ultrasonic_right <= thresholds["ultrasonic_max_m"]
    )
    if not ultrasonic_valid:
        local_reasons.append("ultrasonic_invalid")
    elif abs((ultrasonic_left + ultrasonic_right) - thresholds["row_width_m"]) > thresholds["max_ultrasonic_row_width_error_m"]:
        local_reasons.append("ultrasonic_row_width_error")

    budget_reasons: list[str] = []
    if fallback_duration > thresholds["max_fallback_duration_s"]:
        budget_reasons.append("fallback_duration_exceeded")
    if fallback_distance > thresholds["max_fallback_distance_m"]:
        budget_reasons.append("fallback_distance_exceeded")

    rtk_confident = gps_fix_type in thresholds["accepted_rtk_fix_types"] and gps_hdop <= thresholds["max_hdop"]
    if rtk_confident and not local_reasons:
        return {
            "decision": "RTK_CONFIDENT",
            "mode": "AUTO",
            "spray_allowed": spray_zone != "OFF",
            "safe_outputs_required": False,
            "reason_codes": [],
        }

    if not rtk_confident and fallback_active and not local_reasons and not budget_reasons:
        return {
            "decision": "DEAD_RECKONING_ACTIVE",
            "mode": "AUTO",
            "spray_allowed": spray_zone != "OFF",
            "safe_outputs_required": False,
            "reason_codes": ["gps_degraded_local_sensors_agree"],
        }

    reasons = local_reasons + budget_reasons
    if not rtk_confident and not fallback_active and not reasons:
        reasons.append("gps_degraded_without_fallback")
    elif rtk_confident and budget_reasons and not local_reasons:
        reasons = budget_reasons
    elif not reasons:
        reasons.append("position_confidence_unsafe")
    return {
        "decision": "SAFE_HOLD",
        "mode": "HOLD",
        "spray_allowed": False,
        "safe_outputs_required": True,
        "reason_codes": reasons,
    }


def compare_expected(scenario: dict[str, Any], actual: dict[str, Any], safe_outputs: dict[str, Any]) -> None:
    scenario_id = require_string(scenario.get("id"), "scenario.id")
    expected = require_object(scenario, "expected", scenario_id)
    for key in ("decision", "mode", "spray_allowed", "safe_outputs_required"):
        require(expected.get(key) == actual[key], f"{scenario_id}.expected.{key}={expected.get(key)!r} does not match evaluated {actual[key]!r}")

    reason_codes = expected.get("reason_codes")
    require(isinstance(reason_codes, list), f"{scenario_id}.expected.reason_codes must be a list")
    require(
        reason_codes == actual["reason_codes"],
        f"{scenario_id}.expected.reason_codes {reason_codes!r} does not match evaluated {actual['reason_codes']!r}",
    )

    if actual["decision"] == "SAFE_HOLD":
        expected_outputs = expected.get("safe_outputs")
        require(isinstance(expected_outputs, dict), f"{scenario_id}.expected.safe_outputs must be present for SAFE_HOLD")
        require(expected_outputs == safe_outputs, f"{scenario_id}.expected.safe_outputs must match top-level safe_outputs")
    else:
        require(expected.get("safe_outputs") is None, f"{scenario_id}.expected.safe_outputs must be omitted unless SAFE_HOLD")


def validate_scenarios(contract: dict[str, Any], thresholds: dict[str, Any], safe_outputs: dict[str, Any]) -> dict[str, int]:
    scenarios = contract.get("scenarios")
    require(isinstance(scenarios, list) and scenarios, "scenarios must be a non-empty list")
    seen_ids: set[str] = set()
    decision_counts = {decision: 0 for decision in DECISIONS}
    for scenario in scenarios:
        require(isinstance(scenario, dict), "each scenario must be an object")
        scenario_id = require_string(scenario.get("id"), "scenario.id")
        require(scenario_id not in seen_ids, f"duplicate scenario id: {scenario_id}")
        seen_ids.add(scenario_id)
        actual = evaluate_scenario(scenario, thresholds)
        compare_expected(scenario, actual, safe_outputs)
        decision_counts[actual["decision"]] += 1

    require(decision_counts["RTK_CONFIDENT"] >= 1, "at least one RTK_CONFIDENT scenario is required")
    require(decision_counts["DEAD_RECKONING_ACTIVE"] >= 1, "at least one DEAD_RECKONING_ACTIVE scenario is required")
    require(decision_counts["SAFE_HOLD"] >= 1, "at least one SAFE_HOLD scenario is required")
    return decision_counts


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate FEAT-009 position-confidence contract")
    parser.add_argument(
        "contract",
        nargs="?",
        help="Repository-relative contract path (default: sitl/position-confidence.v0.json)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        contract_path = resolve_contract_path(args.contract)
        contract = load_json(contract_path)
        require(contract.get("feature_id") == "FEAT-009", "contract feature_id must be FEAT-009")
        validate_units(contract)
        validate_states(contract)
        safe_outputs = validate_safe_outputs(contract)
        thresholds = validate_thresholds(contract)
        spray_segments = validate_sources(contract, safe_outputs)
        decision_counts = validate_scenarios(contract, thresholds, safe_outputs)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    total = sum(decision_counts.values())
    continuing = decision_counts["RTK_CONFIDENT"] + decision_counts["DEAD_RECKONING_ACTIVE"]
    print("PASS: position confidence contract validated")
    print(f"Validated scenarios: {total} ({continuing} continue, {decision_counts['SAFE_HOLD']} safe_hold)")
    print(
        "Decision counts: "
        f"RTK_CONFIDENT={decision_counts['RTK_CONFIDENT']} "
        f"DEAD_RECKONING_ACTIVE={decision_counts['DEAD_RECKONING_ACTIVE']} "
        f"SAFE_HOLD={decision_counts['SAFE_HOLD']}"
    )
    print(f"Mission spray segments: {spray_segments}")
    print(
        "Fallback budget: "
        f"{thresholds['max_fallback_duration_s']:.1f}s / {thresholds['max_fallback_distance_m']:.3f}m"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
