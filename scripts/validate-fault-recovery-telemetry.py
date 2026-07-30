#!/usr/bin/env python3
"""Validate the FEAT-010 SITL fault-recovery telemetry contract.

The validator is deterministic and standard-library only. It evaluates the
fixture-level recovery state machine, actuator safety, duplicate-spray ledger,
and required black-box telemetry fields before a live SITL process is wired.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = ROOT / "sitl" / "fault-recovery-telemetry.v0.json"

REQUIRED_SOURCE_KEYS = {
    "mission_export": "FEAT-007",
    "actuator_mapping": "FEAT-006",
    "preflight_dosing": "FEAT-008",
    "position_confidence": "FEAT-009",
}
REQUIRED_UNITS = {
    "timestamp_s": "seconds from scenario start",
    "hold_duration_s": "seconds",
    "clear_event_age_s": "seconds",
    "fault_clear_age_s": "seconds",
    "fallback_duration_s": "seconds",
    "fallback_distance_m": "meters",
    "pump_pwm_us": "microseconds",
    "spray_progress": "0.0 to 1.0 fraction of logical spray work unit",
}
REQUIRED_SAFE_OUTPUT_KEYS = (
    "pump_pwm_us",
    "left_spray_valve",
    "right_spray_valve",
    "agitation",
)
REQUIRED_STATES = {
    "MISSION_RUNNING",
    "HOLD_FAULT_ACTIVE",
    "RECOVERY_READY",
    "RECOVERY_BLOCKED",
    "MISSION_RESUMED",
    "MISSION_COMPLETE",
    "MISSION_ABORTED",
}
REQUIRED_SCENARIO_IDS = {
    "recoverable_obstacle_resume_tail_and_complete",
    "canopy_degradation_bounded_dead_reckoning_complete",
    "duplicate_spray_replay_attempt_suppressed",
    "unrecoverable_sensor_fault_timeout_aborts_safe",
    "stale_clear_and_missing_ack_blocks_resume",
}
VALID_MODES = {"AUTO", "HOLD"}
VALID_POSITION_STATES = {"RTK_CONFIDENT", "DEAD_RECKONING_ACTIVE", "SAFE_HOLD"}


class ValidationError(Exception):
    """Contract or scenario validation failed."""

    def __init__(self, message: str, reason_code: str | None = None):
        super().__init__(message)
        self.reason_codes = [reason_code or message]


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def require(condition: bool, message: str, reason_code: str | None = None) -> None:
    if not condition:
        raise ValidationError(message, reason_code)


def require_string(value: Any, field: str, reason_code: str | None = None) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a non-empty string", reason_code)
    return value


def require_bool(value: Any, field: str, reason_code: str | None = None) -> bool:
    require(isinstance(value, bool), f"{field} must be boolean", reason_code)
    return value


def require_number(value: Any, field: str, *, minimum: float | None = None, reason_code: str | None = None) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric", reason_code)
    numeric = float(value)
    require(math.isfinite(numeric), f"{field} must be finite", reason_code)
    if minimum is not None:
        require(numeric >= minimum, f"{field} must be >= {minimum}", reason_code)
    return numeric


def require_int(value: Any, field: str, *, minimum: int | None = None, reason_code: str | None = None) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{field} must be integer", reason_code)
    if minimum is not None:
        require(value >= minimum, f"{field} must be >= {minimum}", reason_code)
    return value


def require_object(value: Any, field: str, reason_code: str | None = None) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object", reason_code)
    return value


def require_list(value: Any, field: str, *, non_empty: bool = False, reason_code: str | None = None) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list", reason_code)
    if non_empty:
        require(bool(value), f"{field} must be a non-empty list", reason_code)
    return value


def require_event_field(event: dict[str, Any], field: str, scenario_id: str, event_desc: str) -> None:
    require(
        field in event,
        f"{scenario_id} {event_desc} missing required field: {field}",
        f"missing_required_field:{field}",
    )


def require_event_type_present(event_types: list[str], event_type: str, scenario_id: str) -> None:
    require(
        event_type in event_types,
        f"{scenario_id} missing required event: {event_type}",
        f"missing_required_event:{event_type}",
    )


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
    units = require_object(contract.get("units"), "units")
    for key, expected in REQUIRED_UNITS.items():
        require(units.get(key) == expected, f"units.{key} must be {expected!r}")


def validate_safe_outputs(contract: dict[str, Any]) -> dict[str, int]:
    safe_outputs = require_object(contract.get("safe_outputs"), "safe_outputs")
    parsed = {key: require_int(safe_outputs.get(key), f"safe_outputs.{key}", minimum=0) for key in REQUIRED_SAFE_OUTPUT_KEYS}
    require(parsed["pump_pwm_us"] == 1000, "safe_outputs.pump_pwm_us must be 1000")
    require(parsed["left_spray_valve"] == 0, "safe_outputs.left_spray_valve must be 0")
    require(parsed["right_spray_valve"] == 0, "safe_outputs.right_spray_valve must be 0")
    require(parsed["agitation"] == 0, "safe_outputs.agitation must be 0")
    return parsed


def parse_actuator_template(value: Any, field: str) -> dict[str, int]:
    template = require_object(value, field)
    parsed = {key: require_int(template.get(key), f"{field}.{key}", minimum=0) for key in REQUIRED_SAFE_OUTPUT_KEYS}
    require(parsed["left_spray_valve"] in {0, 1}, f"{field}.left_spray_valve must be 0 or 1")
    require(parsed["right_spray_valve"] in {0, 1}, f"{field}.right_spray_valve must be 0 or 1")
    require(parsed["agitation"] in {0, 1}, f"{field}.agitation must be 0 or 1")
    return parsed


def validate_spray_outputs(contract: dict[str, Any], safe_outputs: dict[str, int]) -> dict[str, dict[str, int]]:
    spray_outputs = require_object(contract.get("spray_outputs"), "spray_outputs")
    parsed: dict[str, dict[str, int]] = {}
    for zone, value in spray_outputs.items():
        zone_name = require_string(zone, "spray_outputs key")
        parsed[zone_name] = parse_actuator_template(value, f"spray_outputs.{zone_name}")
    require("OFF" in parsed, "spray_outputs must include OFF")
    require("LEFT" in parsed, "spray_outputs must include LEFT")
    require(parsed["OFF"] == safe_outputs, "spray_outputs.OFF must match safe_outputs")
    require(parsed["LEFT"]["pump_pwm_us"] > safe_outputs["pump_pwm_us"], "spray_outputs.LEFT must command pump above safe PWM")
    require(parsed["LEFT"]["left_spray_valve"] == 1, "spray_outputs.LEFT must open the left valve")
    require(parsed["LEFT"]["right_spray_valve"] == 0, "spray_outputs.LEFT must keep the right valve closed")
    require(parsed["LEFT"]["agitation"] == 1, "spray_outputs.LEFT must enable agitation during spray")
    return parsed


def validate_sources(
    contract: dict[str, Any],
    safe_outputs: dict[str, int],
    spray_outputs: dict[str, dict[str, int]],
) -> dict[str, Any]:
    sources = require_object(contract.get("sources"), "sources")
    loaded: dict[str, dict[str, Any]] = {}
    for key, feature_id in REQUIRED_SOURCE_KEYS.items():
        require(key in sources, f"sources.{key} is required")
        loaded[key] = load_json(resolve_repo_path(sources[key], f"sources.{key}"))
        require(loaded[key].get("feature_id") == feature_id, f"sources.{key} must reference {feature_id}")

    mission = loaded["mission_export"]
    mission_items = require_list(mission.get("mission_items"), "mission_export.mission_items", non_empty=True)
    mission_item_ids = {require_string(item.get("id"), "mission_item.id") for item in mission_items if isinstance(item, dict)}
    require(mission_item_ids, "mission_export must define mission item ids")
    spray_segments = [
        item for item in mission_items if isinstance(item, dict) and item.get("spray_state") in {"LEFT", "RIGHT", "BOTH"}
    ]
    require(spray_segments, "mission_export must include at least one spray segment")
    mission_id = require_string(mission.get("mission_id"), "mission_export.mission_id")

    mission_spray_states = require_object(mission.get("spray_states"), "mission_export.spray_states")
    mission_off = require_object(mission_spray_states.get("OFF"), "mission_export.spray_states.OFF")
    mission_left = require_object(mission_spray_states.get("LEFT"), "mission_export.spray_states.LEFT")
    require(mission_off.get("pump_pwm_us") == safe_outputs["pump_pwm_us"], "mission OFF pump PWM must match FEAT-010 safe output")
    require(mission_off.get("left_valve") == safe_outputs["left_spray_valve"], "mission OFF left valve must match FEAT-010 safe output")
    require(mission_off.get("right_valve") == safe_outputs["right_spray_valve"], "mission OFF right valve must match FEAT-010 safe output")
    require(mission_off.get("agitation") == safe_outputs["agitation"], "mission OFF agitation must match FEAT-010 safe output")
    require(mission_left.get("pump_pwm_us") == spray_outputs["LEFT"]["pump_pwm_us"], "mission LEFT pump PWM must match FEAT-010 LEFT output")
    require(mission_left.get("left_valve") == spray_outputs["LEFT"]["left_spray_valve"], "mission LEFT valve must match FEAT-010 LEFT output")
    require(mission_left.get("right_valve") == spray_outputs["LEFT"]["right_spray_valve"], "mission RIGHT valve state must match FEAT-010 LEFT output")
    require(mission_left.get("agitation") == spray_outputs["LEFT"]["agitation"], "mission LEFT agitation must match FEAT-010 LEFT output")

    mapping = loaded["actuator_mapping"]
    outputs = require_list(mapping.get("outputs"), "actuator_mapping.outputs", non_empty=True)
    by_output = {item.get("id"): item for item in outputs if isinstance(item, dict)}
    for output_id in ("pump_pwm", "left_spray_valve", "right_spray_valve", "agitation"):
        require(isinstance(by_output.get(output_id), dict), f"actuator_mapping.outputs must include {output_id}")
    require(by_output["pump_pwm"].get("safe_pwm_us") == safe_outputs["pump_pwm_us"], "mapping pump safe PWM must match FEAT-010")
    require(by_output["left_spray_valve"].get("default_state") == safe_outputs["left_spray_valve"], "mapping left valve default must match FEAT-010")
    require(by_output["right_spray_valve"].get("default_state") == safe_outputs["right_spray_valve"], "mapping right valve default must match FEAT-010")
    require(by_output["agitation"].get("default_state") == safe_outputs["agitation"], "mapping agitation default must match FEAT-010")

    preflight = loaded["preflight_dosing"]
    dosing_model = require_object(preflight.get("dosing_model"), "preflight_dosing.dosing_model")
    pump_pwm = require_object(dosing_model.get("pump_pwm_us"), "preflight_dosing.dosing_model.pump_pwm_us")
    require(pump_pwm.get("off") == safe_outputs["pump_pwm_us"], "FEAT-008 pump off PWM must match FEAT-010 safe output")

    position = loaded["position_confidence"]
    thresholds = require_object(position.get("thresholds"), "position_confidence.thresholds")
    position_thresholds = {
        "max_fallback_duration_s": require_number(
            thresholds.get("max_fallback_duration_s"),
            "position_confidence.thresholds.max_fallback_duration_s",
            minimum=0.0,
        ),
        "max_fallback_distance_m": require_number(
            thresholds.get("max_fallback_distance_m"),
            "position_confidence.thresholds.max_fallback_distance_m",
            minimum=0.0,
        ),
    }

    return {
        "mission_id": mission_id,
        "mission_item_ids": mission_item_ids,
        "spray_segments": len(spray_segments),
        "position_thresholds": position_thresholds,
    }


def validate_state_machine(contract: dict[str, Any]) -> tuple[set[str], set[tuple[str, str]]]:
    state_machine = require_object(contract.get("state_machine"), "state_machine")
    states = require_object(state_machine.get("states"), "state_machine.states")
    state_names = {require_string(name, "state_machine.states key") for name in states}
    missing = sorted(REQUIRED_STATES - state_names)
    require(not missing, f"state_machine.states missing required states: {', '.join(missing)}")

    raw_transitions = require_list(state_machine.get("allowed_transitions"), "state_machine.allowed_transitions", non_empty=True)
    transitions: set[tuple[str, str]] = set()
    for index, raw_transition in enumerate(raw_transitions, start=1):
        transition = require_list(raw_transition, f"state_machine.allowed_transitions[{index}]")
        require(len(transition) == 2, f"state_machine.allowed_transitions[{index}] must contain exactly two states")
        src = require_string(transition[0], f"state_machine.allowed_transitions[{index}][0]")
        dst = require_string(transition[1], f"state_machine.allowed_transitions[{index}][1]")
        require(src in state_names and dst in state_names, f"transition {src}->{dst} references an unknown state")
        transitions.add((src, dst))
    return state_names, transitions


def validate_recovery_policy(contract: dict[str, Any]) -> dict[str, Any]:
    policy = require_object(contract.get("recovery_policy"), "recovery_policy")
    recoverable = set(require_string(item, "recoverable_fault_types item") for item in require_list(policy.get("recoverable_fault_types"), "recovery_policy.recoverable_fault_types", non_empty=True))
    unrecoverable = set(require_string(item, "unrecoverable_fault_types item") for item in require_list(policy.get("unrecoverable_fault_types"), "recovery_policy.unrecoverable_fault_types", non_empty=True))
    require(not recoverable & unrecoverable, "recoverable and unrecoverable fault types must not overlap")
    fault_classes = require_object(policy.get("fault_classes"), "recovery_policy.fault_classes")
    for fault_type in sorted(recoverable | unrecoverable):
        fault_class = require_object(fault_classes.get(fault_type), f"recovery_policy.fault_classes.{fault_type}")
        recovery = require_string(fault_class.get("recoverability"), f"fault_classes.{fault_type}.recoverability")
        if fault_type in recoverable:
            require(recovery in {"recoverable_after_clear", "bounded_position_recovery"}, f"{fault_type} must have a recoverable class")
        else:
            require(recovery == "unrecoverable_for_auto_resume", f"{fault_type} must be unrecoverable for auto resume")
            require(fault_class.get("auto_resume_allowed") is False, f"{fault_type} must set auto_resume_allowed false")
        require_bool(fault_class.get("requires_hold_on_detection"), f"fault_classes.{fault_type}.requires_hold_on_detection")
        require_bool(fault_class.get("requires_operator_ack"), f"fault_classes.{fault_type}.requires_operator_ack")

    allowed_resume_states = set(
        require_string(item, "allowed_resume_position_confidence_states item")
        for item in require_list(
            policy.get("allowed_resume_position_confidence_states"),
            "recovery_policy.allowed_resume_position_confidence_states",
            non_empty=True,
        )
    )
    require(allowed_resume_states <= VALID_POSITION_STATES, "allowed resume states must be known position-confidence states")

    parsed = dict(policy)
    parsed["recoverable_fault_types"] = recoverable
    parsed["unrecoverable_fault_types"] = unrecoverable
    parsed["fault_classes"] = fault_classes
    parsed["allowed_resume_position_confidence_states"] = allowed_resume_states
    parsed["max_fault_clear_age_s"] = require_number(policy.get("max_fault_clear_age_s"), "recovery_policy.max_fault_clear_age_s", minimum=0.0)
    parsed["max_hold_duration_s"] = require_number(policy.get("max_hold_duration_s"), "recovery_policy.max_hold_duration_s", minimum=0.0)
    parsed["max_actuator_safe_latency_ms"] = require_number(policy.get("max_actuator_safe_latency_ms"), "recovery_policy.max_actuator_safe_latency_ms", minimum=0.0)
    require(policy.get("resume_start_policy") == "FIRST_UNSPRAYED_LEDGER_UNIT", "resume_start_policy must be FIRST_UNSPRAYED_LEDGER_UNIT")
    require(
        policy.get("duplicate_spray_action") == "SUPPRESS_COMMAND_LOG_EVENT_KEEP_OUTPUTS_SAFE",
        "duplicate_spray_action must suppress commands and keep outputs safe",
    )
    require(policy.get("stale_clear_action") == "BLOCK_RESUME_KEEP_HOLD", "stale_clear_action must block resume")
    require(policy.get("missing_ack_action") == "BLOCK_RESUME_KEEP_HOLD", "missing_ack_action must block resume")
    return parsed


def validate_spray_ledger(contract: dict[str, Any], source_context: dict[str, Any]) -> dict[str, Any]:
    ledger = require_object(contract.get("spray_ledger"), "spray_ledger")
    identity_fields = set(require_string(item, "spray_ledger.identity_fields item") for item in require_list(ledger.get("identity_fields"), "spray_ledger.identity_fields", non_empty=True))
    for required in ("mission_id", "spray_unit_id", "row_label", "spray_zone", "pass_id"):
        require(required in identity_fields, f"spray_ledger.identity_fields must include {required}")
    completion_statuses = set(require_string(item, "spray_ledger.completion_statuses item") for item in require_list(ledger.get("completion_statuses"), "spray_ledger.completion_statuses", non_empty=True))
    require({"unsprayed", "sprayed", "skipped_duplicate_suppressed"} <= completion_statuses, "spray ledger must define required statuses")

    work_units = require_list(ledger.get("spray_work_units"), "spray_ledger.spray_work_units", non_empty=True)
    unit_by_id: dict[str, dict[str, Any]] = {}
    for index, unit in enumerate(work_units, start=1):
        unit_obj = require_object(unit, f"spray_ledger.spray_work_units[{index}]")
        unit_id = require_string(unit_obj.get("spray_unit_id"), f"spray_work_units[{index}].spray_unit_id")
        require(unit_id not in unit_by_id, f"duplicate spray_unit_id: {unit_id}")
        require(unit_obj.get("mission_id") == source_context["mission_id"], f"{unit_id}.mission_id must match mission export")
        require(unit_obj.get("mission_item_start") in source_context["mission_item_ids"], f"{unit_id}.mission_item_start must reference a mission item")
        require(unit_obj.get("mission_item_end") in source_context["mission_item_ids"], f"{unit_id}.mission_item_end must reference a mission item")
        require(require_string(unit_obj.get("spray_zone"), f"{unit_id}.spray_zone") in {"LEFT", "RIGHT", "BOTH"}, f"{unit_id}.spray_zone must be a spray zone")
        progress = require_object(unit_obj.get("progress_range"), f"{unit_id}.progress_range")
        start = require_number(progress.get("start"), f"{unit_id}.progress_range.start", minimum=0.0)
        end = require_number(progress.get("end"), f"{unit_id}.progress_range.end", minimum=start)
        require(start < end <= 1.0, f"{unit_id}.progress_range must satisfy 0 <= start < end <= 1")
        unit_by_id[unit_id] = unit_obj

    scan_order = [require_string(item, "spray_ledger.resume_scan_order item") for item in require_list(ledger.get("resume_scan_order"), "spray_ledger.resume_scan_order", non_empty=True)]
    require(set(scan_order) == set(unit_by_id), "resume_scan_order must include each spray work unit exactly once")
    require(len(scan_order) == len(set(scan_order)), "resume_scan_order must not contain duplicates")
    return {
        "completion_statuses": completion_statuses,
        "unit_by_id": unit_by_id,
        "scan_order": scan_order,
    }


def validate_telemetry_schema(contract: dict[str, Any]) -> dict[str, Any]:
    schema = require_object(contract.get("telemetry_schema"), "telemetry_schema")
    require_string(schema.get("sequence_policy"), "telemetry_schema.sequence_policy")
    common_required = [
        require_string(item, "telemetry_schema.common_required_fields item")
        for item in require_list(schema.get("common_required_fields"), "telemetry_schema.common_required_fields", non_empty=True)
    ]
    for field in ("seq", "timestamp_s", "event_type", "state", "mode", "mission_item_id", "actuator_state"):
        require(field in common_required, f"telemetry_schema.common_required_fields must include {field}")

    required_by_outcome_raw = require_object(
        schema.get("required_event_types_by_expected_outcome"),
        "telemetry_schema.required_event_types_by_expected_outcome",
    )
    required_by_outcome: dict[str, list[str]] = {}
    for outcome, values in required_by_outcome_raw.items():
        required_by_outcome[require_string(outcome, "expected outcome key")] = [
            require_string(item, f"required events for {outcome}") for item in require_list(values, f"required_event_types_by_expected_outcome.{outcome}", non_empty=True)
        ]

    fields_by_event_raw = require_object(schema.get("required_fields_by_event_type"), "telemetry_schema.required_fields_by_event_type")
    fields_by_event: dict[str, list[str]] = {}
    for event_type, values in fields_by_event_raw.items():
        fields_by_event[require_string(event_type, "event type key")] = [
            require_string(item, f"required fields for {event_type}") for item in require_list(values, f"required_fields_by_event_type.{event_type}")
        ]
    return {
        "common_required_fields": common_required,
        "required_event_types_by_expected_outcome": required_by_outcome,
        "required_fields_by_event_type": fields_by_event,
    }


def normalise_actuator_state(value: Any, field: str, reason_code: str | None = None) -> dict[str, int]:
    actuator_state = require_object(value, field, reason_code)
    return {key: require_int(actuator_state.get(key), f"{field}.{key}", minimum=0, reason_code=reason_code) for key in REQUIRED_SAFE_OUTPUT_KEYS}


def actuator_matches(actual: dict[str, int], expected: dict[str, int]) -> bool:
    return all(actual.get(key) == expected.get(key) for key in REQUIRED_SAFE_OUTPUT_KEYS)


def require_safe_actuator(event: dict[str, Any], safe_outputs: dict[str, int], scenario_id: str) -> None:
    actual = normalise_actuator_state(event.get("actuator_state"), f"{scenario_id} seq {event.get('seq')} actuator_state")
    require(
        actuator_matches(actual, safe_outputs),
        f"{scenario_id} seq {event.get('seq')} {event.get('event_type')} must keep sprayer outputs safe/off",
        "actuator_state_not_safe",
    )


def require_spray_actuator(
    event: dict[str, Any],
    spray_outputs: dict[str, dict[str, int]],
    scenario_id: str,
) -> None:
    zone = require_string(event.get("spray_zone"), f"{scenario_id} seq {event.get('seq')} spray_zone")
    require(zone in spray_outputs, f"{scenario_id} seq {event.get('seq')} unknown spray zone {zone}")
    actual = normalise_actuator_state(event.get("actuator_state"), f"{scenario_id} seq {event.get('seq')} actuator_state")
    require(
        actuator_matches(actual, spray_outputs[zone]),
        f"{scenario_id} seq {event.get('seq')} SPRAY_ON actuator_state does not match spray_outputs.{zone}",
        "spray_output_mismatch",
    )


def validate_timeline_shape(
    scenario: dict[str, Any],
    schema: dict[str, Any],
    state_names: set[str],
    allowed_transitions: set[tuple[str, str]],
    source_context: dict[str, Any],
) -> list[dict[str, Any]]:
    scenario_id = require_string(scenario.get("id"), "scenario.id")
    expected_outcome = require_string(scenario.get("expected_outcome_type"), f"{scenario_id}.expected_outcome_type")
    required_by_outcome = schema["required_event_types_by_expected_outcome"]
    require(expected_outcome in required_by_outcome, f"{scenario_id}.expected_outcome_type must be declared in telemetry schema")

    timeline = require_list(scenario.get("timeline"), f"{scenario_id}.timeline", non_empty=True)
    previous_seq: int | None = None
    previous_timestamp: float | None = None
    previous_state: str | None = None
    event_types: list[str] = []
    normalised: list[dict[str, Any]] = []

    for index, raw_event in enumerate(timeline, start=1):
        event = require_object(raw_event, f"{scenario_id}.timeline[{index}]")
        event_desc = f"timeline[{index}]"
        for field in schema["common_required_fields"]:
            require_event_field(event, field, scenario_id, event_desc)

        event_type = require_string(event.get("event_type"), f"{scenario_id}.{event_desc}.event_type")
        event_types.append(event_type)
        for field in schema["required_fields_by_event_type"].get(event_type, []):
            require_event_field(event, field, scenario_id, f"seq {event.get('seq')} {event_type}")

        seq = require_int(event.get("seq"), f"{scenario_id}.{event_desc}.seq")
        if previous_seq is not None:
            require(seq > previous_seq, f"{scenario_id} telemetry seq must be strictly increasing", "sequence_not_strictly_increasing")
        previous_seq = seq

        timestamp = require_number(event.get("timestamp_s"), f"{scenario_id}.{event_desc}.timestamp_s", minimum=0.0)
        if previous_timestamp is not None:
            require(timestamp >= previous_timestamp, f"{scenario_id} telemetry timestamps must be nondecreasing", "timestamp_decreased")
        previous_timestamp = timestamp

        state = require_string(event.get("state"), f"{scenario_id}.{event_desc}.state")
        require(state in state_names, f"{scenario_id} seq {seq} has unknown state {state}")
        if previous_state is not None and state != previous_state:
            require(
                (previous_state, state) in allowed_transitions,
                f"{scenario_id} illegal state transition {previous_state}->{state} at seq {seq}",
                "illegal_state_transition",
            )
        previous_state = state

        mode = require_string(event.get("mode"), f"{scenario_id}.{event_desc}.mode")
        require(mode in VALID_MODES, f"{scenario_id} seq {seq} mode must be AUTO or HOLD")
        mission_item_id = require_string(event.get("mission_item_id"), f"{scenario_id}.{event_desc}.mission_item_id")
        require(mission_item_id in source_context["mission_item_ids"], f"{scenario_id} seq {seq} mission_item_id must reference mission export")
        normalise_actuator_state(event.get("actuator_state"), f"{scenario_id} seq {seq} actuator_state")
        normalised.append(event)

    for required_event_type in required_by_outcome[expected_outcome]:
        require_event_type_present(event_types, required_event_type, scenario_id)
    return normalised


def validate_initial_ledger(scenario: dict[str, Any], ledger_spec: dict[str, Any]) -> dict[str, str]:
    scenario_id = require_string(scenario.get("id"), "scenario.id")
    statuses = {unit_id: "unsprayed" for unit_id in ledger_spec["unit_by_id"]}
    initial = scenario.get("initial_spray_ledger", [])
    require(isinstance(initial, list), f"{scenario_id}.initial_spray_ledger must be a list")
    for index, raw_record in enumerate(initial, start=1):
        record = require_object(raw_record, f"{scenario_id}.initial_spray_ledger[{index}]")
        unit_id = require_string(record.get("spray_unit_id"), f"{scenario_id}.initial_spray_ledger[{index}].spray_unit_id")
        status = require_string(record.get("ledger_status"), f"{scenario_id}.initial_spray_ledger[{index}].ledger_status")
        require(unit_id in ledger_spec["unit_by_id"], f"{scenario_id} initial ledger references unknown spray unit {unit_id}")
        require(status in ledger_spec["completion_statuses"], f"{scenario_id} initial ledger has unknown status {status}")
        statuses[unit_id] = status
    return statuses


def first_unsprayed_unit(ledger_status: dict[str, str], scan_order: list[str]) -> str | None:
    for unit_id in scan_order:
        if ledger_status.get(unit_id) != "sprayed":
            return unit_id
    return None


def event_reason_codes(event: dict[str, Any]) -> list[str]:
    raw_reason_codes = event.get("reason_codes", [])
    if raw_reason_codes is None:
        return []
    require(isinstance(raw_reason_codes, list), f"seq {event.get('seq')} reason_codes must be a list")
    return [require_string(item, f"seq {event.get('seq')} reason code") for item in raw_reason_codes]


def latest_position_within_budget(event: dict[str, Any], source_context: dict[str, Any], scenario_id: str) -> bool:
    state = require_string(event.get("position_confidence_state"), f"{scenario_id} seq {event.get('seq')} position_confidence_state")
    require(state in VALID_POSITION_STATES, f"{scenario_id} seq {event.get('seq')} position_confidence_state is unknown")
    if state != "DEAD_RECKONING_ACTIVE":
        return True
    inputs = require_object(event.get("confidence_inputs"), f"{scenario_id} seq {event.get('seq')} confidence_inputs")
    duration = require_number(inputs.get("fallback_duration_s"), f"{scenario_id} seq {event.get('seq')} confidence_inputs.fallback_duration_s", minimum=0.0)
    distance = require_number(inputs.get("fallback_distance_m"), f"{scenario_id} seq {event.get('seq')} confidence_inputs.fallback_distance_m", minimum=0.0)
    thresholds = source_context["position_thresholds"]
    return duration <= thresholds["max_fallback_duration_s"] and distance <= thresholds["max_fallback_distance_m"]


def validate_recovery_decision(
    event: dict[str, Any],
    faults: dict[str, dict[str, Any]],
    clears: dict[str, float],
    acknowledgements: dict[str, bool],
    latest_position_state: str | None,
    latest_position_budget_ok: bool,
    ledger_status: dict[str, str],
    ledger_spec: dict[str, Any],
    policy: dict[str, Any],
    scenario_id: str,
) -> tuple[bool, str | None]:
    fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {event.get('seq')} fault_id")
    require(fault_id in faults, f"{scenario_id} seq {event.get('seq')} recovery decision references unknown fault {fault_id}", "unknown_fault_id")
    fault = faults[fault_id]
    fault_type = fault["fault_type"]
    fault_class = require_object(policy["fault_classes"].get(fault_type), f"fault_classes.{fault_type}")
    decision = require_string(event.get("recovery_decision"), f"{scenario_id} seq {event.get('seq')} recovery_decision")
    resume_allowed = require_bool(event.get("resume_allowed"), f"{scenario_id} seq {event.get('seq')} resume_allowed")
    reasons = event_reason_codes(event)

    if fault_class.get("recoverability") == "bounded_position_recovery":
        allowed_states = set(fault_class.get("allowed_continue_position_confidence_states", []))
        require(latest_position_state in allowed_states, f"{scenario_id} bounded recovery requires accepted position-confidence state", "position_confidence_not_accepted")
        require(latest_position_budget_ok, f"{scenario_id} bounded recovery exceeds FEAT-009 fallback budget", "fallback_budget_exceeded")
        require(decision == "CONTINUE_WITH_BOUNDED_DEAD_RECKONING", f"{scenario_id} expected bounded dead-reckoning decision")
        require(resume_allowed is True, f"{scenario_id} bounded recovery must allow mission continuation")
        return True, None

    if fault_type in policy["unrecoverable_fault_types"]:
        require(resume_allowed is False, f"{scenario_id} unrecoverable fault must not allow resume", "unrecoverable_resume_allowed")
        return False, None

    clear_age = clears.get(fault_id)
    clear_fresh = clear_age is not None and clear_age <= policy["max_fault_clear_age_s"]
    ack_required = bool(fault_class.get("requires_operator_ack"))
    ack_present = acknowledgements.get(fault_id, False)
    allowed_resume_states = set(fault_class.get("allowed_resume_position_confidence_states", policy["allowed_resume_position_confidence_states"]))
    position_ok = latest_position_state in allowed_resume_states and latest_position_budget_ok
    computed_resume_allowed = clear_fresh and (ack_present or not ack_required) and position_ok

    if computed_resume_allowed:
        require(event.get("state") == "RECOVERY_READY", f"{scenario_id} allowed resume decision must be RECOVERY_READY")
        require(decision == "RESUME_FIRST_UNSPRAYED", f"{scenario_id} resume decision must be RESUME_FIRST_UNSPRAYED")
        require(resume_allowed is True, f"{scenario_id} resume_allowed must be true when policy inputs are safe")
        resume_unit = first_unsprayed_unit(ledger_status, ledger_spec["scan_order"])
        require(resume_unit is not None, f"{scenario_id} resume requested but all ledger units are already sprayed", "no_unsprayed_resume_unit")
        require(event.get("resume_unit_id") == resume_unit, f"{scenario_id} must resume at first unsprayed ledger unit {resume_unit}")
        return True, resume_unit

    require(event.get("state") == "RECOVERY_BLOCKED", f"{scenario_id} blocked resume decision must be RECOVERY_BLOCKED")
    require(decision == "BLOCK_RESUME", f"{scenario_id} blocked policy must emit BLOCK_RESUME")
    require(resume_allowed is False, f"{scenario_id} resume_allowed must be false when policy inputs are unsafe")
    if not clear_fresh:
        require("fault_clear_stale" in reasons or clear_age is None, f"{scenario_id} stale/missing clear must be recorded")
    if ack_required and not ack_present:
        require("operator_ack_missing" in reasons, f"{scenario_id} missing acknowledgement must be recorded")
    if not position_ok:
        require("position_confidence_rejected" in reasons or latest_position_state in allowed_resume_states, f"{scenario_id} rejected confidence must be recorded")
    return False, None


def validate_scenario(
    scenario: dict[str, Any],
    schema: dict[str, Any],
    state_names: set[str],
    allowed_transitions: set[tuple[str, str]],
    source_context: dict[str, Any],
    safe_outputs: dict[str, int],
    spray_outputs: dict[str, dict[str, int]],
    ledger_spec: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    scenario_id = require_string(scenario.get("id"), "scenario.id")
    expected = require_object(scenario.get("expected"), f"{scenario_id}.expected")
    require(expected.get("validation_result") == "PASS", f"{scenario_id}.expected.validation_result must be PASS")
    timeline = validate_timeline_shape(scenario, schema, state_names, allowed_transitions, source_context)

    ledger_status = validate_initial_ledger(scenario, ledger_spec)
    ledger_record_counts = {unit_id: 0 for unit_id in ledger_spec["unit_by_id"]}
    faults: dict[str, dict[str, Any]] = {}
    clears: dict[str, float] = {}
    acknowledgements: dict[str, bool] = {}
    holds_by_fault: set[str] = set()
    safe_events_by_fault: set[str] = set()
    latest_position_state: str | None = None
    latest_position_budget_ok = True
    last_recovery_decision: str | None = None
    last_resume_allowed = False
    last_resume_unit: str | None = None
    duplicate_suppressed = False
    duplicate_commands_applied = 0
    hold_entered = False
    all_reason_codes: list[str] = []
    max_safe_latency_s = policy["max_actuator_safe_latency_ms"] / 1000.0

    for event in timeline:
        seq = event["seq"]
        timestamp = float(event["timestamp_s"])
        event_type = event["event_type"]
        state = event["state"]
        mode = event["mode"]
        actuator_state = normalise_actuator_state(event.get("actuator_state"), f"{scenario_id} seq {seq} actuator_state")
        all_reason_codes.extend(event_reason_codes(event))

        if mode == "HOLD":
            require_safe_actuator(event, safe_outputs, scenario_id)

        if event_type == "MISSION_START":
            require(event.get("mission_id") == source_context["mission_id"], f"{scenario_id} mission_id must match mission export")
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "SPRAY_ON":
            unit_id = require_string(event.get("spray_unit_id"), f"{scenario_id} seq {seq} spray_unit_id")
            require(unit_id in ledger_spec["unit_by_id"], f"{scenario_id} seq {seq} unknown spray unit {unit_id}")
            require(
                ledger_status.get(unit_id) != "sprayed",
                f"{scenario_id} seq {seq} attempted to spray already-complete ledger unit {unit_id}",
                "duplicate_spray_not_suppressed",
            )
            require_spray_actuator(event, spray_outputs, scenario_id)

        elif event_type == "SPRAY_LEDGER_RECORD":
            unit_id = require_string(event.get("spray_unit_id"), f"{scenario_id} seq {seq} spray_unit_id")
            status = require_string(event.get("ledger_status"), f"{scenario_id} seq {seq} ledger_status")
            require(unit_id in ledger_spec["unit_by_id"], f"{scenario_id} seq {seq} unknown spray unit {unit_id}")
            require(status in ledger_spec["completion_statuses"], f"{scenario_id} seq {seq} unknown ledger status {status}")
            if status == "sprayed":
                require(ledger_status.get(unit_id) != "sprayed", f"{scenario_id} seq {seq} duplicate sprayed ledger record for {unit_id}", "duplicate_ledger_record")
                ledger_record_counts[unit_id] += 1
            ledger_status[unit_id] = status

        elif event_type in {"FAULT_DETECTED", "SENSOR_DEGRADED"}:
            fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {seq} fault_id")
            fault_type = require_string(event.get("fault_type"), f"{scenario_id} seq {seq} fault_type")
            require(
                fault_type in policy["recoverable_fault_types"] or fault_type in policy["unrecoverable_fault_types"],
                f"{scenario_id} seq {seq} unknown fault_type {fault_type}",
                "unknown_fault_type",
            )
            fault_class = require_object(policy["fault_classes"].get(fault_type), f"fault_classes.{fault_type}")
            if event_type == "FAULT_DETECTED":
                require(event.get("recovery_class") == fault_class.get("recoverability"), f"{scenario_id} seq {seq} recovery_class must match policy")
            position_state = require_string(event.get("position_confidence_state"), f"{scenario_id} seq {seq} position_confidence_state")
            require(position_state in VALID_POSITION_STATES, f"{scenario_id} seq {seq} unknown position_confidence_state {position_state}")
            faults[fault_id] = {
                "fault_type": fault_type,
                "timestamp_s": timestamp,
                "requires_hold": bool(fault_class.get("requires_hold_on_detection")),
                "event_type": event_type,
            }
            latest_position_state = position_state

        elif event_type == "HOLD_ENTERED":
            hold_entered = True
            fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {seq} fault_id")
            require(fault_id in faults, f"{scenario_id} seq {seq} HOLD_ENTERED references unknown fault {fault_id}", "unknown_fault_id")
            holds_by_fault.add(fault_id)
            require_safe_actuator(event, safe_outputs, scenario_id)
            latency_s = timestamp - faults[fault_id]["timestamp_s"]
            require(0 <= latency_s <= max_safe_latency_s, f"{scenario_id} seq {seq} HOLD safe latency {latency_s:.3f}s exceeds policy", "safe_latency_exceeded")

        elif event_type == "ACTUATORS_SAFE":
            fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {seq} fault_id")
            require(fault_id in faults, f"{scenario_id} seq {seq} ACTUATORS_SAFE references unknown fault {fault_id}", "unknown_fault_id")
            require(event.get("safe_output_verified") is True, f"{scenario_id} seq {seq} ACTUATORS_SAFE must set safe_output_verified true")
            safe_events_by_fault.add(fault_id)
            require_safe_actuator(event, safe_outputs, scenario_id)
            latency_s = timestamp - faults[fault_id]["timestamp_s"]
            require(0 <= latency_s <= max_safe_latency_s, f"{scenario_id} seq {seq} actuator-safe latency {latency_s:.3f}s exceeds policy", "safe_latency_exceeded")

        elif event_type == "FAULT_CLEAR":
            fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {seq} fault_id")
            require(fault_id in faults, f"{scenario_id} seq {seq} FAULT_CLEAR references unknown fault {fault_id}", "unknown_fault_id")
            clears[fault_id] = require_number(event.get("clear_event_age_s"), f"{scenario_id} seq {seq} clear_event_age_s", minimum=0.0)
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "RESUME_ACK":
            fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {seq} fault_id")
            require(fault_id in faults, f"{scenario_id} seq {seq} RESUME_ACK references unknown fault {fault_id}", "unknown_fault_id")
            acknowledgements[fault_id] = event.get("acknowledgement") == "received"
            require(acknowledgements[fault_id], f"{scenario_id} seq {seq} RESUME_ACK must record acknowledgement received")
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "POSITION_CONFIDENCE":
            latest_position_state = require_string(event.get("position_confidence_state"), f"{scenario_id} seq {seq} position_confidence_state")
            latest_position_budget_ok = latest_position_within_budget(event, source_context, scenario_id)

        elif event_type == "RECOVERY_DECISION":
            last_recovery_decision = require_string(event.get("recovery_decision"), f"{scenario_id} seq {seq} recovery_decision")
            last_resume_allowed, last_resume_unit = validate_recovery_decision(
                event,
                faults,
                clears,
                acknowledgements,
                latest_position_state,
                latest_position_budget_ok,
                ledger_status,
                ledger_spec,
                policy,
                scenario_id,
            )

        elif event_type == "MISSION_RESUMED":
            if last_resume_unit is not None:
                require(event.get("resume_unit_id") == last_resume_unit, f"{scenario_id} seq {seq} resumed at {event.get('resume_unit_id')!r}, expected {last_resume_unit!r}")
            require(event.get("resume_policy") == policy["resume_start_policy"], f"{scenario_id} seq {seq} resume policy must match recovery policy")
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "SPRAY_REPLAY_ATTEMPT":
            unit_id = require_string(event.get("spray_unit_id"), f"{scenario_id} seq {seq} spray_unit_id")
            require(unit_id in ledger_spec["unit_by_id"], f"{scenario_id} seq {seq} unknown spray unit {unit_id}")
            require(ledger_status.get(unit_id) == "sprayed", f"{scenario_id} seq {seq} replay attempt must target an already sprayed unit")
            requested = normalise_actuator_state(event.get("requested_actuator_state"), f"{scenario_id} seq {seq} requested_actuator_state")
            require(not actuator_matches(requested, safe_outputs), f"{scenario_id} seq {seq} replay request should represent a duplicate spray command")
            if not actuator_matches(actuator_state, safe_outputs):
                duplicate_commands_applied += 1
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "DUPLICATE_SPRAY_SUPPRESSED":
            unit_id = require_string(event.get("spray_unit_id"), f"{scenario_id} seq {seq} spray_unit_id")
            require(unit_id in ledger_spec["unit_by_id"], f"{scenario_id} seq {seq} unknown spray unit {unit_id}")
            require(ledger_status.get(unit_id) == "sprayed", f"{scenario_id} seq {seq} suppression must reference already sprayed unit")
            duplicate_suppressed = True
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "SPRAY_OFF":
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "HOLD_TIMEOUT":
            fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {seq} fault_id")
            require(fault_id in faults, f"{scenario_id} seq {seq} HOLD_TIMEOUT references unknown fault {fault_id}", "unknown_fault_id")
            hold_duration = require_number(event.get("hold_duration_s"), f"{scenario_id} seq {seq} hold_duration_s", minimum=0.0)
            require(hold_duration > policy["max_hold_duration_s"], f"{scenario_id} seq {seq} HOLD_TIMEOUT must exceed max hold duration")
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "MISSION_ABORTED":
            fault_id = require_string(event.get("fault_id"), f"{scenario_id} seq {seq} fault_id")
            require(fault_id in faults, f"{scenario_id} seq {seq} MISSION_ABORTED references unknown fault {fault_id}", "unknown_fault_id")
            require_safe_actuator(event, safe_outputs, scenario_id)

        elif event_type == "MISSION_COMPLETE":
            require_string(event.get("outcome"), f"{scenario_id} seq {seq} outcome")
            require_safe_actuator(event, safe_outputs, scenario_id)

    for fault_id, fault in faults.items():
        if fault["requires_hold"]:
            require(fault_id in holds_by_fault, f"{scenario_id} fault {fault_id} required HOLD but no HOLD_ENTERED was logged", "missing_required_event:HOLD_ENTERED")
            require(fault_id in safe_events_by_fault, f"{scenario_id} fault {fault_id} required ACTUATORS_SAFE but none was logged", "missing_required_event:ACTUATORS_SAFE")

    safe_event_types = set(expected.get("safe_output_event_types", []))
    require(isinstance(expected.get("safe_output_event_types", []), list), f"{scenario_id}.expected.safe_output_event_types must be a list")
    for event in timeline:
        if event["event_type"] in safe_event_types:
            require_safe_actuator(event, safe_outputs, scenario_id)

    final_state = timeline[-1]["state"]
    mission_complete = final_state == "MISSION_COMPLETE"
    sprayed_once_units = [unit_id for unit_id in ledger_spec["scan_order"] if ledger_record_counts.get(unit_id) == 1]
    duplicate_counts = [unit_id for unit_id, count in ledger_record_counts.items() if count > 1]
    require(not duplicate_counts, f"{scenario_id} ledger contains duplicate sprayed records: {', '.join(duplicate_counts)}")

    if "final_state" in expected:
        require(expected["final_state"] == final_state, f"{scenario_id}.expected.final_state does not match evaluated final state")
    if "mission_complete" in expected:
        require(expected["mission_complete"] is mission_complete, f"{scenario_id}.expected.mission_complete does not match evaluated mission completion")
    if "resume_allowed" in expected:
        require(expected["resume_allowed"] is last_resume_allowed, f"{scenario_id}.expected.resume_allowed does not match recovery policy result")
    if "resume_unit_id" in expected:
        require(expected["resume_unit_id"] == last_resume_unit, f"{scenario_id}.expected.resume_unit_id does not match first-unsprayed ledger result")
    if "recovery_decision" in expected:
        require(expected["recovery_decision"] == last_recovery_decision, f"{scenario_id}.expected.recovery_decision does not match evaluated decision")
    if "hold_entered" in expected:
        require(expected["hold_entered"] is hold_entered, f"{scenario_id}.expected.hold_entered does not match telemetry")
    if "sprayed_once_units" in expected:
        require(expected["sprayed_once_units"] == sprayed_once_units, f"{scenario_id}.expected.sprayed_once_units does not match ledger records")
    if "duplicate_spray_suppressed" in expected:
        require(expected["duplicate_spray_suppressed"] is duplicate_suppressed, f"{scenario_id}.expected.duplicate_spray_suppressed does not match telemetry")
    if "duplicate_spray_commands_applied" in expected:
        require(expected["duplicate_spray_commands_applied"] == duplicate_commands_applied, f"{scenario_id}.expected.duplicate_spray_commands_applied does not match actuator behavior")
    if "required_reason_codes" in expected:
        required_reasons = [require_string(item, f"{scenario_id}.expected.required_reason_codes item") for item in require_list(expected["required_reason_codes"], f"{scenario_id}.expected.required_reason_codes")]
        missing_reasons = [reason for reason in required_reasons if reason not in all_reason_codes]
        require(not missing_reasons, f"{scenario_id} missing expected reason codes: {', '.join(missing_reasons)}")

    return {
        "id": scenario_id,
        "expected_outcome_type": scenario["expected_outcome_type"],
        "final_state": final_state,
        "mission_complete": mission_complete,
        "resume_allowed": last_resume_allowed,
        "duplicate_spray_suppressed": duplicate_suppressed,
        "hold_entered": hold_entered,
        "sprayed_once_units": sprayed_once_units,
    }


def apply_mutation(base_scenario: dict[str, Any], case_id: str, mutation: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(base_scenario)
    mutated["id"] = f"{base_scenario.get('id')}__{case_id}"
    if "drop_fields" in mutation:
        event_seq = mutation.get("event_seq")
        drop_fields = [require_string(item, f"{case_id}.mutation.drop_fields item") for item in require_list(mutation.get("drop_fields"), f"{case_id}.mutation.drop_fields", non_empty=True)]
        for event in mutated.get("timeline", []):
            if isinstance(event, dict) and event.get("seq") == event_seq:
                for field in drop_fields:
                    event.pop(field, None)
    if "drop_event_types" in mutation:
        drop_event_types = set(
            require_string(item, f"{case_id}.mutation.drop_event_types item")
            for item in require_list(mutation.get("drop_event_types"), f"{case_id}.mutation.drop_event_types", non_empty=True)
        )
        mutated["timeline"] = [
            event for event in mutated.get("timeline", []) if not (isinstance(event, dict) and event.get("event_type") in drop_event_types)
        ]
    return mutated


def validate_scenarios(
    contract: dict[str, Any],
    schema: dict[str, Any],
    state_names: set[str],
    allowed_transitions: set[tuple[str, str]],
    source_context: dict[str, Any],
    safe_outputs: dict[str, int],
    spray_outputs: dict[str, dict[str, int]],
    ledger_spec: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    scenarios = require_list(contract.get("scenarios"), "scenarios", non_empty=True)
    scenario_by_id: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for raw_scenario in scenarios:
        scenario = require_object(raw_scenario, "scenario")
        scenario_id = require_string(scenario.get("id"), "scenario.id")
        require(scenario_id not in scenario_by_id, f"duplicate scenario id: {scenario_id}")
        scenario_by_id[scenario_id] = scenario
        results.append(
            validate_scenario(
                scenario,
                schema,
                state_names,
                allowed_transitions,
                source_context,
                safe_outputs,
                spray_outputs,
                ledger_spec,
                policy,
            )
        )
    missing = sorted(REQUIRED_SCENARIO_IDS - set(scenario_by_id))
    require(not missing, f"scenarios missing required ids: {', '.join(missing)}")

    outcome_counts: dict[str, int] = {}
    for result in results:
        outcome = result["expected_outcome_type"]
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    require(outcome_counts.get("MISSION_COMPLETE_AFTER_RECOVERY", 0) >= 1, "at least one successful recovery scenario is required")
    require(outcome_counts.get("BOUNDED_DEAD_RECKONING_COMPLETE", 0) >= 1, "at least one bounded dead-reckoning scenario is required")
    require(outcome_counts.get("DUPLICATE_SUPPRESSED_COMPLETE", 0) >= 1, "at least one duplicate suppression scenario is required")
    require(outcome_counts.get("MISSION_ABORTED", 0) >= 1, "at least one abort scenario is required")
    require(outcome_counts.get("RESUME_BLOCKED", 0) >= 1, "at least one blocked resume scenario is required")

    summary = {
        "total": len(results),
        "mission_complete": sum(1 for result in results if result["mission_complete"]),
        "resume_allowed": sum(1 for result in results if result["resume_allowed"]),
        "duplicate_suppressed": sum(1 for result in results if result["duplicate_spray_suppressed"]),
        "hold_entered": sum(1 for result in results if result["hold_entered"]),
        "outcome_counts": outcome_counts,
    }
    return summary, scenario_by_id


def validate_negative_cases(
    contract: dict[str, Any],
    scenario_by_id: dict[str, dict[str, Any]],
    schema: dict[str, Any],
    state_names: set[str],
    allowed_transitions: set[tuple[str, str]],
    source_context: dict[str, Any],
    safe_outputs: dict[str, int],
    spray_outputs: dict[str, dict[str, int]],
    ledger_spec: dict[str, Any],
    policy: dict[str, Any],
) -> int:
    cases = require_list(contract.get("negative_telemetry_cases"), "negative_telemetry_cases", non_empty=True)
    for raw_case in cases:
        case = require_object(raw_case, "negative_telemetry_case")
        case_id = require_string(case.get("id"), "negative_telemetry_case.id")
        base_id = require_string(case.get("base_scenario_id"), f"{case_id}.base_scenario_id")
        require(base_id in scenario_by_id, f"{case_id} references unknown base scenario {base_id}")
        mutation = require_object(case.get("mutation"), f"{case_id}.mutation")
        expected = require_object(case.get("expected"), f"{case_id}.expected")
        require(expected.get("validation_result") == "FAIL", f"{case_id}.expected.validation_result must be FAIL")
        expected_reason_codes = [
            require_string(item, f"{case_id}.expected.reason_codes item")
            for item in require_list(expected.get("reason_codes"), f"{case_id}.expected.reason_codes", non_empty=True)
        ]
        mutated = apply_mutation(scenario_by_id[base_id], case_id, mutation)
        try:
            validate_scenario(
                mutated,
                schema,
                state_names,
                allowed_transitions,
                source_context,
                safe_outputs,
                spray_outputs,
                ledger_spec,
                policy,
            )
        except ValidationError as exc:
            observed = set(exc.reason_codes)
            missing = [code for code in expected_reason_codes if code not in observed]
            require(not missing, f"{case_id} expected failure codes {missing!r}, observed {exc.reason_codes!r}")
        else:
            raise ValidationError(f"{case_id} mutation unexpectedly passed validation")
    return len(cases)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate FEAT-010 fault-recovery telemetry contract")
    parser.add_argument(
        "contract",
        nargs="?",
        help="Repository-relative contract path (default: sitl/fault-recovery-telemetry.v0.json)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        contract_path = resolve_contract_path(args.contract)
        contract = load_json(contract_path)
        require(contract.get("feature_id") == "FEAT-010", "contract feature_id must be FEAT-010")
        validate_units(contract)
        safe_outputs = validate_safe_outputs(contract)
        spray_outputs = validate_spray_outputs(contract, safe_outputs)
        source_context = validate_sources(contract, safe_outputs, spray_outputs)
        state_names, allowed_transitions = validate_state_machine(contract)
        policy = validate_recovery_policy(contract)
        ledger_spec = validate_spray_ledger(contract, source_context)
        schema = validate_telemetry_schema(contract)
        scenario_summary, scenario_by_id = validate_scenarios(
            contract,
            schema,
            state_names,
            allowed_transitions,
            source_context,
            safe_outputs,
            spray_outputs,
            ledger_spec,
            policy,
        )
        negative_count = validate_negative_cases(
            contract,
            scenario_by_id,
            schema,
            state_names,
            allowed_transitions,
            source_context,
            safe_outputs,
            spray_outputs,
            ledger_spec,
            policy,
        )
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    outcome_counts = scenario_summary["outcome_counts"]
    print("PASS: fault recovery telemetry contract validated")
    print(
        f"Validated scenarios: {scenario_summary['total']} "
        f"({scenario_summary['mission_complete']} complete, {scenario_summary['hold_entered']} hold-entered, "
        f"{scenario_summary['resume_allowed']} resume/continue decisions)"
    )
    print(
        "Outcome counts: "
        f"MISSION_COMPLETE_AFTER_RECOVERY={outcome_counts.get('MISSION_COMPLETE_AFTER_RECOVERY', 0)} "
        f"BOUNDED_DEAD_RECKONING_COMPLETE={outcome_counts.get('BOUNDED_DEAD_RECKONING_COMPLETE', 0)} "
        f"DUPLICATE_SUPPRESSED_COMPLETE={outcome_counts.get('DUPLICATE_SUPPRESSED_COMPLETE', 0)} "
        f"MISSION_ABORTED={outcome_counts.get('MISSION_ABORTED', 0)} "
        f"RESUME_BLOCKED={outcome_counts.get('RESUME_BLOCKED', 0)}"
    )
    print(f"Duplicate suppression events: {scenario_summary['duplicate_suppressed']}")
    print(f"Negative telemetry cases: {negative_count}")
    print(
        "Recovery policy: "
        f"max_clear_age={policy['max_fault_clear_age_s']:.1f}s "
        f"max_hold={policy['max_hold_duration_s']:.1f}s "
        f"safe_latency={policy['max_actuator_safe_latency_ms']:.0f}ms"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
