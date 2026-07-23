#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "hardware" / "procurement-checklist.v0.json"
LOG_TEMPLATE = ROOT / "templates" / "procurement-inspection-log.template.json"
DOC = ROOT / "docs" / "bench-prototype-procurement-checklist.md"

REQUIRED_IDS = {
    "P01_PUMP",
    "P02_NOZZLES",
    "P03_VALVES",
    "P04_DRIVER_BOARD",
    "P05_PRESSURE_SENSOR",
    "P06_LOW_LIQUID",
    "P07_ESTOP_POWER",
    "P08_FLUID_PATH",
    "P09_CONTROLLER_TELEMETRY",
}

SAFETY_TERMS = ["e-stop", "normally-closed", "fuse", "pressure", "low"]
PRIVATE_TERMS = ["farm coordinates", "payment", "credentials", "supplier account"]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    data = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    log = json.loads(LOG_TEMPLATE.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8").lower()
    errors: list[str] = []

    items = data.get("items", [])
    item_ids = {item.get("id") for item in items}
    log_ids = {item.get("id") for item in log.get("items", [])}
    forbidden = " ".join(data.get("forbidden", [])).lower()
    all_text = json.dumps(data, ensure_ascii=False).lower()

    require(data.get("feature_id") == "FEAT-006", "checklist feature_id must be FEAT-006", errors)
    require(item_ids == REQUIRED_IDS, f"procurement IDs must equal {sorted(REQUIRED_IDS)}", errors)
    require(log_ids == REQUIRED_IDS, "inspection log IDs must match procurement IDs", errors)
    require(len(items) >= 9, "must define at least nine procurement items", errors)

    for item in items:
        item_id = item.get("id", "UNKNOWN")
        require(item.get("qty", 0) >= 1, f"{item_id} must have qty >= 1", errors)
        require(item.get("required") is True, f"{item_id} must be required", errors)
        require(len(item.get("must_have_specs", [])) >= 3, f"{item_id} needs at least 3 must-have specs", errors)
        require(len(item.get("reject_if", [])) >= 2, f"{item_id} needs reject criteria", errors)

    for term in SAFETY_TERMS:
        require(term in all_text, f"checklist must include safety term: {term}", errors)
    for term in PRIVATE_TERMS:
        require(term in forbidden or term in log.get("private_data_rule", "").lower(), f"private-data rule must mention {term}", errors)

    require("water-only" in forbidden or "water-only" in doc, "must block fertilizer/chemical before water-only PASS", errors)
    require("directly from pixhawk" in forbidden, "must forbid powering loads directly from Pixhawk", errors)
    require("receiving inspection" in doc, "human doc must include receiving inspection section", errors)
    require(log.get("overall_status") == "PENDING", "inspection log template must start PENDING", errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(f"Validated procurement checklist: {CHECKLIST.relative_to(ROOT)} items={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
