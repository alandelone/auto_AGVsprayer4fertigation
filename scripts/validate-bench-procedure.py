#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCEDURE = ROOT / "hardware" / "bench-test-procedure.v0.json"
LOG_TEMPLATE = ROOT / "templates" / "bench-test-log.template.json"
DOC = ROOT / "docs" / "water-only-bench-test-procedure.md"

REQUIRED_TESTS = {
    "T01_DRY_POWER_OFF",
    "T02_ESTOP_CUT",
    "T03_PRIME_LEAK",
    "T04_PRESSURE_LIMITS",
    "T05_LOW_LIQUID",
    "T06_ZONE_VALVES",
    "T07_CATCH_CUP_FLOW",
    "T08_FAULT_SAFE_STATE",
}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    procedure = json.loads(PROCEDURE.read_text(encoding="utf-8"))
    log_template = json.loads(LOG_TEMPLATE.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8").lower()
    errors: list[str] = []

    tests = procedure.get("tests", [])
    test_ids = {test.get("id") for test in tests}
    log_ids = {row.get("id") for row in log_template.get("results", [])}
    forbidden = " ".join(procedure.get("forbidden", [])).lower()
    preconditions = " ".join(procedure.get("preconditions", [])).lower()

    require(procedure.get("feature_id") == "FEAT-005", "procedure feature_id must be FEAT-005", errors)
    require(REQUIRED_TESTS == test_ids, f"procedure test IDs must equal {sorted(REQUIRED_TESTS)}", errors)
    require(REQUIRED_TESTS == log_ids, "log template result IDs must match required tests", errors)
    require("water only" in procedure.get("scope", "").lower() or "water-only" in procedure.get("scope", "").lower(), "scope must require water-only testing", errors)
    require("no fertilizer" in forbidden or "fertilizer" in forbidden, "forbidden actions must block fertilizer/chemical tests", errors)
    require("e-stop" in preconditions, "preconditions must require e-stop", errors)
    require("low-liquid" in preconditions or "low liquid" in preconditions, "preconditions must require low-liquid interlock", errors)
    require("pressure" in preconditions, "preconditions must require pressure interlock or gauge", errors)
    require("all tests must be pass" in procedure.get("pass_rule", "").lower(), "pass rule must require all tests PASS", errors)
    require("0.60-0.90 l/min" in doc or "0.60–0.90 l/min" in doc, "doc must specify catch-cup L/min bounds", errors)
    require("<=20%" in doc, "doc must specify left/right flow difference bound", errors)
    require(log_template.get("overall_status") == "PENDING", "log template must start PENDING", errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(f"Validated bench procedure contract: {PROCEDURE.relative_to(ROOT)} tests={len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
