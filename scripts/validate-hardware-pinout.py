#!/usr/bin/env python3
"""Validate FEAT-003 hardware BOM and pinout contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "bom-pinout.v0.json"
REQUIRED_BOM = {
    "flight_controller", "telemetry", "rc_control", "rangefinder", "liquid_sensing",
    "pressure_sensing", "pump", "valves", "actuator_drivers", "power", "safety", "spray_hardware",
}
REQUIRED_SIGNALS = {
    "RC_INPUT", "TELEM1", "I2C_GPS_COMPASS", "RANGE_FRONT", "RANGE_LEFT", "RANGE_RIGHT",
    "PUMP_ENABLE", "LEFT_VALVE_ENABLE", "RIGHT_VALVE_ENABLE", "LOW_LIQUID",
    "PRESSURE_SENSOR", "ESTOP_POWER_CUT",
}
FORBIDDEN_TEXT = ["directly powering pump", "changing ArduRover firmware"]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    if not CONTRACT.is_file():
        fail(errors, f"missing contract: {CONTRACT.relative_to(ROOT)}")
    else:
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        if data.get("scope") != "hardware reference only; no ArduRover firmware changes":
            fail(errors, "scope must explicitly avoid ArduRover firmware changes")
        categories = {item.get("category") for item in data.get("bom", [])}
        missing_bom = sorted(REQUIRED_BOM - categories)
        if missing_bom:
            fail(errors, f"missing BOM categories: {missing_bom}")
        signals = {item.get("signal") for item in data.get("pinout", [])}
        missing_signals = sorted(REQUIRED_SIGNALS - signals)
        if missing_signals:
            fail(errors, f"missing pinout signals: {missing_signals}")
        forbidden = "\n".join(data.get("forbidden", []))
        for text in FORBIDDEN_TEXT:
            if text not in forbidden:
                fail(errors, f"forbidden rules must mention: {text}")

    for doc in [ROOT / "docs" / "hardware-bom.md", ROOT / "docs" / "pixhawk-rpi-pump-valve-pinout.md"]:
        if not doc.is_file():
            fail(errors, f"missing doc: {doc.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"Validated hardware BOM/pinout contract: {CONTRACT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
