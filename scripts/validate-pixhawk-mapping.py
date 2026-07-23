#!/usr/bin/env python3
"""Validate FEAT-006 Pixhawk actuator mapping and ArduRover parameter export."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "hardware" / "pixhawk-actuator-mapping.v0.json"
PARAM_FILE = ROOT / "hardware" / "pixhawk-ardurover-sprayer.param"

EXPECTED_FEATURE = "FEAT-006"
EXPECTED_FIRMWARE = "ArduRover"
EXPECTED_OUTPUTS = {
    "pump_pwm",
    "left_spray_valve",
    "right_spray_valve",
    "agitation",
    "estop_cutoff",
}
EXPECTED_AUX = {"AUX1", "AUX2", "AUX3", "AUX4", "AUX5"}
REQUIRED_PARAMETERS = {
    "BRD_PWM_COUNT",
    "SERVO9_FUNCTION",
    "SERVO9_MIN",
    "SERVO9_MAX",
    "RELAY1_PIN",
    "RELAY1_DEFAULT",
    "RELAY2_PIN",
    "RELAY2_DEFAULT",
    "RELAY3_PIN",
    "RELAY3_DEFAULT",
    "RELAY4_PIN",
    "RELAY4_DEFAULT",
}
FORBIDDEN_RULES = {
    "direct Pixhawk power drive for pump or solenoid loads",
    "software-only emergency stop",
    "shared GPIO pin assignments across independent actuator roles",
    "chemical/fertilizer testing before water-only bench acceptance passes",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_mapping(errors: list[str]) -> dict[str, Any]:
    if not MAPPING.is_file():
        fail(errors, f"missing mapping contract: {MAPPING.relative_to(ROOT)}")
        return {}
    try:
        return json.loads(MAPPING.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(errors, f"invalid JSON in {MAPPING.relative_to(ROOT)}: {exc}")
        return {}


def load_params(errors: list[str]) -> dict[str, int]:
    if not PARAM_FILE.is_file():
        fail(errors, f"missing parameter export: {PARAM_FILE.relative_to(ROOT)}")
        return {}

    params: dict[str, int] = {}
    for line_number, raw_line in enumerate(PARAM_FILE.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            fail(errors, f"{PARAM_FILE.relative_to(ROOT)}:{line_number} must use PARAM_NAME,VALUE format")
            continue
        name, value = [part.strip() for part in line.split(",", 1)]
        if name in params:
            fail(errors, f"duplicate parameter in export: {name}")
        if not name or not value:
            fail(errors, f"{PARAM_FILE.relative_to(ROOT)}:{line_number} has empty parameter name or value")
            continue
        try:
            params[name] = int(value)
        except ValueError:
            fail(errors, f"{PARAM_FILE.relative_to(ROOT)}:{line_number} value for {name} must be an integer")
    return params


def validate_outputs(data: dict[str, Any], errors: list[str]) -> None:
    outputs = data.get("outputs")
    if not isinstance(outputs, list):
        fail(errors, "outputs must be a list")
        return

    ids = [item.get("id") for item in outputs if isinstance(item, dict)]
    if set(ids) != EXPECTED_OUTPUTS:
        fail(errors, f"outputs must contain exactly: {sorted(EXPECTED_OUTPUTS)}")
    if len(ids) != len(set(ids)):
        fail(errors, "output ids must be unique")

    aux_values = [item.get("pixhawk_output") for item in outputs if isinstance(item, dict)]
    if set(aux_values) != EXPECTED_AUX:
        fail(errors, f"pixhawk outputs must map exactly AUX1-AUX5, got: {sorted(set(aux_values))}")
    if len(aux_values) != len(set(aux_values)):
        fail(errors, "pixhawk outputs must be unique")

    servo_channels = [item.get("servo_channel") for item in outputs if isinstance(item, dict) and "servo_channel" in item]
    if servo_channels != [9]:
        fail(errors, "exactly one PWM servo output must be SERVO9 on AUX1")

    relay_numbers = [item.get("relay_number") for item in outputs if isinstance(item, dict) and "relay_number" in item]
    if set(relay_numbers) != {1, 2, 3, 4} or len(relay_numbers) != len(set(relay_numbers)):
        fail(errors, "relay outputs must uniquely use RELAY1-RELAY4")

    gpio_pins = [item.get("gpio_pin") for item in outputs if isinstance(item, dict) and "gpio_pin" in item]
    if set(gpio_pins) != {51, 52, 53, 54} or len(gpio_pins) != len(set(gpio_pins)):
        fail(errors, "relay GPIO pins must uniquely use 51-54")

    for item in outputs:
        if not isinstance(item, dict):
            fail(errors, "each output entry must be an object")
            continue
        if item.get("driver_required") is not True:
            fail(errors, f"{item.get('id', '<unknown>')} must require an external driver")
        if item.get("default_state") not in (None, 0, 1):
            fail(errors, f"{item.get('id', '<unknown>')} default_state must be 0 or 1")
        if item.get("active_state") not in (None, 0, 1):
            fail(errors, f"{item.get('id', '<unknown>')} active_state must be 0 or 1")


def expected_params_from_outputs(data: dict[str, Any]) -> dict[str, int]:
    expected = dict(data.get("parameters", {}))
    for item in data.get("outputs", []):
        if not isinstance(item, dict):
            continue
        if item.get("id") == "pump_pwm":
            expected[item["function_parameter"]] = item["function_value"]
            expected["SERVO9_MIN"] = item["min_pwm_us"]
            expected["SERVO9_MAX"] = item["max_pwm_us"]
        if "relay_number" in item:
            relay = item["relay_number"]
            expected[f"RELAY{relay}_PIN"] = item["gpio_pin"]
            expected[f"RELAY{relay}_DEFAULT"] = item["default_state"]
    return expected


def main() -> int:
    errors: list[str] = []
    data = load_mapping(errors)
    params = load_params(errors)

    if data:
        if data.get("feature_id") != EXPECTED_FEATURE:
            fail(errors, f"feature_id must be {EXPECTED_FEATURE}")
        if data.get("firmware") != EXPECTED_FIRMWARE:
            fail(errors, f"firmware must be {EXPECTED_FIRMWARE}")
        validate_outputs(data, errors)
        forbidden = set(data.get("forbidden", []))
        missing_forbidden = sorted(FORBIDDEN_RULES - forbidden)
        if missing_forbidden:
            fail(errors, f"missing forbidden safety rules: {missing_forbidden}")

        declared_params = data.get("parameters")
        if not isinstance(declared_params, dict):
            fail(errors, "parameters must be an object")
        else:
            missing = sorted(REQUIRED_PARAMETERS - set(declared_params))
            extra = sorted(set(declared_params) - REQUIRED_PARAMETERS)
            if missing:
                fail(errors, f"missing required parameters: {missing}")
            if extra:
                fail(errors, f"unexpected parameters: {extra}")
            derived = expected_params_from_outputs(data)
            if declared_params != derived:
                fail(errors, "parameters must match values derived from output mapping")

        if params and declared_params != params:
            fail(errors, "parameter export must exactly match mapping parameters")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(f"Validated Pixhawk actuator mapping: {MAPPING.relative_to(ROOT)}")
    print(f"Validated ArduRover parameter export: {PARAM_FILE.relative_to(ROOT)}")
    print("ACTUATOR_OUTPUTS=AUX1,AUX2,AUX3,AUX4,AUX5")
    print("PARAMETERS=BRD_PWM_COUNT,SERVO9_FUNCTION,SERVO9_MIN,SERVO9_MAX,RELAY1_PIN,RELAY1_DEFAULT,RELAY2_PIN,RELAY2_DEFAULT,RELAY3_PIN,RELAY3_DEFAULT,RELAY4_PIN,RELAY4_DEFAULT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
