#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "bench-test-ratings.v0.json"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    ratings = data.get("selected_ratings", {})
    pump = ratings.get("pump", {})
    nozzles = ratings.get("nozzles", {})
    valves = ratings.get("valves", {})
    pressure = ratings.get("pressure_sensor", {})
    drivers = ratings.get("drivers", {})
    power = ratings.get("power", {})
    fit = data.get("fit_check", {})
    errors: list[str] = []

    require(data.get("feature_id") == "FEAT-004", "feature_id must be FEAT-004", errors)
    require(pump.get("rated_flow_lpm_min", 0) >= 5.0, "pump flow must be at least 5 L/min", errors)
    require(pump.get("rated_pressure_psi_min", 0) >= 60, "pump pressure must be at least 60 PSI", errors)
    require(nozzles.get("qty") == 2, "bench selection must define two nozzles", errors)
    require(nozzles.get("per_nozzle_flow_gpm_at_40psi", 0) > 0, "nozzle flow must be positive", errors)
    require(fit.get("pump_to_two_nozzle_flow_margin_x", 0) >= 3.0, "pump/nozzle flow margin must be >= 3x", errors)
    require("normally-closed" in valves.get("type", "").lower(), "valves must be normally closed", errors)
    require(valves.get("pressure_rating_psi_min", 0) >= 100, "valves need >=100 PSI rating", errors)
    require(pressure.get("range_mpa", [0, 0])[1] >= 1.0, "pressure sensor range must cover >=1.0 MPa", errors)
    require(drivers.get("channels_min", 0) >= 3, "driver board needs at least 3 channels", errors)
    require(drivers.get("channel_current_a_min", 0) >= pump.get("current_a_max_design", 999), "driver current rating must cover pump current", errors)
    require(power.get("pump_fuse_a", 0) >= pump.get("current_a_max_design", 999), "pump fuse must cover pump design current", errors)
    require(len(data.get("bench_acceptance", [])) >= 4, "bench acceptance criteria are incomplete", errors)
    require(len(data.get("sources", [])) >= 2, "rating contract must include at least two evidence sources", errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(
        "Validated bench ratings contract: "
        f"{CONTRACT.relative_to(ROOT)} "
        f"margin={fit.get('pump_to_two_nozzle_flow_margin_x')}x"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
