#!/usr/bin/env python3
"""Validate the FEAT-008 SITL preflight/dosing contract.

This validator is intentionally deterministic and uses only the Python standard
library so it can run in lightweight cron/CI environments before SITL is wired.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "sitl" / "preflight-dosing.v0.json"
MAPPING_PATH = ROOT / "hardware" / "pixhawk-actuator-mapping.v0.json"
MISSION_PATH = ROOT / "missions" / "cucumber-row-mission.v0.json"

REQUIRED_OUTPUT_IDS = {
    "pump_pwm",
    "left_spray_valve",
    "right_spray_valve",
    "agitation",
    "estop_cutoff",
}
REQUIRED_UNITS = {
    "speed_mps": "meters_per_second",
    "pressure_psi": "pounds_per_square_inch",
    "flow_lpm": "liters_per_minute",
    "application_rate_l_per_m2": "liters_per_square_meter",
    "swath_width_m": "meters",
}


class ValidationError(Exception):
    """Contract validation failed."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


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


def validate_units(contract: dict[str, Any]) -> None:
    units = contract.get("units")
    require(isinstance(units, dict), "units must be an object")
    for key, expected in REQUIRED_UNITS.items():
        require(units.get(key) == expected, f"units.{key} must be {expected!r}")


def validate_mapping(contract: dict[str, Any], mapping: dict[str, Any]) -> None:
    outputs = mapping.get("outputs")
    require(isinstance(outputs, list), "actuator mapping outputs must be a list")
    output_ids = {item.get("id") for item in outputs if isinstance(item, dict)}
    missing = sorted(REQUIRED_OUTPUT_IDS - output_ids)
    require(not missing, f"actuator mapping missing required outputs: {', '.join(missing)}")

    requirements = contract.get("preflight_requirements")
    require(isinstance(requirements, list) and requirements, "preflight_requirements must be a non-empty list")
    by_id = {item.get("id"): item for item in requirements if isinstance(item, dict)}
    mapping_req = by_id.get("actuator_mapping_present")
    require(isinstance(mapping_req, dict), "preflight requirement actuator_mapping_present is required")
    declared = mapping_req.get("required_output_ids")
    require(isinstance(declared, list), "actuator_mapping_present.required_output_ids must be a list")
    declared_ids = set(declared)
    require(declared_ids == REQUIRED_OUTPUT_IDS, "actuator_mapping_present.required_output_ids must match required sprayer outputs")


def validate_mission_has_spray_segments(contract: dict[str, Any], mission: dict[str, Any]) -> int:
    mission_items = mission.get("mission_items")
    require(isinstance(mission_items, list), "mission mission_items must be a list")
    spray_items = [
        item
        for item in mission_items
        if isinstance(item, dict) and item.get("spray_state") in {"LEFT", "RIGHT", "BOTH"}
    ]
    requirements = contract.get("preflight_requirements")
    by_id = {item.get("id"): item for item in requirements if isinstance(item, dict)}
    spray_req = by_id.get("mission_has_spray_segments")
    require(isinstance(spray_req, dict), "preflight requirement mission_has_spray_segments is required")
    minimum = int(require_number(spray_req.get("minimum_spray_segments"), "minimum_spray_segments", minimum=1))
    require(len(spray_items) >= minimum, f"mission has {len(spray_items)} spray segments; required {minimum}")
    return len(spray_items)


def validate_dosing_model(contract: dict[str, Any]) -> dict[str, float]:
    model = contract.get("dosing_model")
    require(isinstance(model, dict), "dosing_model must be an object")
    swath = require_number(model.get("swath_width_m"), "dosing_model.swath_width_m", minimum=0.01)
    rate = require_number(model.get("application_rate_l_per_m2"), "dosing_model.application_rate_l_per_m2", minimum=0.001)
    speed = require_number(model.get("speed_reference_mps"), "dosing_model.speed_reference_mps", minimum=0.01)
    expected = require_number(model.get("expected_target_flow_lpm"), "dosing_model.expected_target_flow_lpm", minimum=0.001)
    calculated = speed * swath * rate * 60
    require(math.isclose(calculated, expected, rel_tol=1e-9, abs_tol=1e-9), f"expected_target_flow_lpm {expected} does not match formula result {calculated:.6f}")

    allowed = model.get("allowed_target_flow_lpm")
    require(isinstance(allowed, dict), "dosing_model.allowed_target_flow_lpm must be an object")
    min_flow = require_number(allowed.get("min"), "allowed_target_flow_lpm.min", minimum=0)
    max_flow = require_number(allowed.get("max"), "allowed_target_flow_lpm.max", minimum=min_flow)
    require(min_flow <= calculated <= max_flow, "reference target flow must be inside allowed_target_flow_lpm range")

    pwm = model.get("pump_pwm_us")
    require(isinstance(pwm, dict), "dosing_model.pump_pwm_us must be an object")
    off = require_number(pwm.get("off"), "pump_pwm_us.off", minimum=0)
    min_cal = require_number(pwm.get("min_calibrated"), "pump_pwm_us.min_calibrated", minimum=off)
    max_cal = require_number(pwm.get("max_calibrated"), "pump_pwm_us.max_calibrated", minimum=min_cal)
    return {"swath": swath, "rate": rate, "min_flow": min_flow, "max_flow": max_flow, "off_pwm": off, "min_pwm": min_cal, "max_pwm": max_cal}


def expected_blockers(contract: dict[str, Any], telemetry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for requirement in contract.get("preflight_requirements", []):
        if not isinstance(requirement, dict):
            continue
        req_id = requirement.get("id")
        if req_id == "estop_clear" and telemetry.get("estop_active") is not False:
            blockers.append(req_id)
        elif req_id == "tank_not_low" and telemetry.get("low_liquid") is not False:
            blockers.append(req_id)
        elif req_id == "pressure_in_bench_range":
            pressure = require_number(telemetry.get("pressure_psi"), "scenario.telemetry.pressure_psi")
            min_pressure = require_number(requirement.get("min"), "pressure_in_bench_range.min")
            max_pressure = require_number(requirement.get("max"), "pressure_in_bench_range.max", minimum=min_pressure)
            if not (min_pressure <= pressure <= max_pressure):
                blockers.append(req_id)
    return blockers


def validate_scenarios(contract: dict[str, Any], dosing: dict[str, float]) -> tuple[int, int]:
    scenarios = contract.get("scenarios")
    require(isinstance(scenarios, list) and scenarios, "scenarios must be a non-empty list")
    safe_count = 0
    blocked_count = 0
    seen_ids: set[str] = set()
    for scenario in scenarios:
        require(isinstance(scenario, dict), "each scenario must be an object")
        scenario_id = scenario.get("id")
        require(isinstance(scenario_id, str) and scenario_id, "scenario.id must be a non-empty string")
        require(scenario_id not in seen_ids, f"duplicate scenario id: {scenario_id}")
        seen_ids.add(scenario_id)
        telemetry = scenario.get("telemetry")
        expected = scenario.get("expected")
        require(isinstance(telemetry, dict), f"{scenario_id}.telemetry must be an object")
        require(isinstance(expected, dict), f"{scenario_id}.expected must be an object")

        speed = require_number(telemetry.get("speed_mps"), f"{scenario_id}.telemetry.speed_mps", minimum=0)
        target_flow = speed * dosing["swath"] * dosing["rate"] * 60
        require(dosing["min_flow"] <= target_flow <= dosing["max_flow"], f"{scenario_id} target_flow_lpm {target_flow:.6f} outside allowed range")
        expected_flow = require_number(expected.get("target_flow_lpm"), f"{scenario_id}.expected.target_flow_lpm", minimum=0)
        require(math.isclose(target_flow, expected_flow, rel_tol=1e-9, abs_tol=1e-9), f"{scenario_id} expected target_flow_lpm {expected_flow} does not match formula result {target_flow:.6f}")

        blockers = expected_blockers(contract, telemetry)
        declared_blockers = expected.get("blocked_by")
        require(isinstance(declared_blockers, list), f"{scenario_id}.expected.blocked_by must be a list")
        require(blockers == declared_blockers, f"{scenario_id} blocked_by {declared_blockers!r} does not match evaluated blockers {blockers!r}")
        allowed = expected.get("mission_start_allowed")
        require(isinstance(allowed, bool), f"{scenario_id}.expected.mission_start_allowed must be boolean")
        require(allowed is (not blockers), f"{scenario_id} mission_start_allowed must be false when blockers exist and true otherwise")
        if allowed:
            safe_count += 1
            require(expected.get("actuator_safe_state_required_before_start") is True, f"{scenario_id} must require actuator safe state before start")
            require_number(expected.get("pump_pwm_us_min"), f"{scenario_id}.expected.pump_pwm_us_min", minimum=dosing["min_pwm"])
        else:
            blocked_count += 1
            safe_outputs = expected.get("safe_outputs")
            require(isinstance(safe_outputs, dict), f"{scenario_id}.expected.safe_outputs must be present for blocked scenarios")
            require(safe_outputs.get("pump_pwm_us") == int(dosing["off_pwm"]), f"{scenario_id} must command pump safe/off PWM")
            require(safe_outputs.get("left_spray_valve") == 0, f"{scenario_id} must keep left valve off")
            require(safe_outputs.get("right_spray_valve") == 0, f"{scenario_id} must keep right valve off")
    require(safe_count >= 1, "at least one safe scenario is required")
    require(blocked_count >= 1, "at least one blocked unsafe scenario is required")
    return safe_count, blocked_count


def main() -> int:
    try:
        contract = load_json(CONTRACT_PATH)
        mapping = load_json(MAPPING_PATH)
        mission = load_json(MISSION_PATH)
        require(contract.get("feature_id") == "FEAT-008", "contract feature_id must be FEAT-008")
        validate_units(contract)
        validate_mapping(contract, mapping)
        spray_segments = validate_mission_has_spray_segments(contract, mission)
        dosing = validate_dosing_model(contract)
        safe_count, blocked_count = validate_scenarios(contract, dosing)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    total = safe_count + blocked_count
    print("PASS: preflight dosing contract validated")
    print(f"Validated scenarios: {total} ({safe_count} safe, {blocked_count} blocked)")
    print(f"Mission spray segments: {spray_segments}")
    print("Reference target_flow_lpm: 0.600")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
