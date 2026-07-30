# SITL Fault Recovery, Resume Policy, and Telemetry Log

## Scope

FEAT-010 defines the deterministic fault-recovery and black-box telemetry contract for the cucumber-row AGV sprayer mission. It is a SITL/companion-control validation artifact only: it must not energize pumps, valves, relays, servos, or field hardware.

The machine-readable contract lives at `sitl/fault-recovery-telemetry.v0.json`; the deterministic validator is `scripts/validate-fault-recovery-telemetry.py`.

## Source Contracts

FEAT-010 cross-checks the recovery contract against earlier validated artifacts:

| Source | Contract | Purpose |
| --- | --- | --- |
| FEAT-006 | `hardware/pixhawk-actuator-mapping.v0.json` | Confirms pump/valve/agitation safe outputs match Pixhawk actuator mapping. |
| FEAT-007 | `missions/cucumber-row-mission.v0.json` | Supplies mission IDs, waypoint IDs, spray states, and spray segment references. |
| FEAT-008 | `sitl/preflight-dosing.v0.json` | Confirms pump-off PWM matches preflight/dosing safety assumptions. |
| FEAT-009 | `sitl/position-confidence.v0.json` | Supplies bounded dead-reckoning duration/distance thresholds for canopy fallback. |

## Recovery State Machine

| State | Meaning |
| --- | --- |
| `MISSION_RUNNING` | Navigation, dosing, preflight, and position confidence are safe enough to continue the mission. |
| `HOLD_FAULT_ACTIVE` | A fault or unsafe confidence state requires HOLD mode with all sprayer outputs off. |
| `RECOVERY_READY` | Fault-clear telemetry is fresh, required acknowledgement is present, and position confidence is acceptable for resume. |
| `RECOVERY_BLOCKED` | A recovery attempt is rejected because policy inputs are stale, incomplete, unsafe, or would duplicate spraying. |
| `MISSION_RESUMED` | Mission execution restarts at the first unsprayed spray-ledger work unit or at the next non-spray mission item. |
| `MISSION_COMPLETE` | Mission ended with required spray work units sprayed once or intentionally skipped with a logged reason. |
| `MISSION_ABORTED` | Mission cannot safely recover within policy and remains safe/off. |

Allowed transitions are deliberately narrow: running can enter fault hold, complete, or abort; hold can become ready, blocked, or aborted; ready can resume; blocked returns to hold; resumed returns to running.

## Fault Classes and Resume Policy

Recoverable fault types are:

- `FRONT_OBSTACLE` — enters HOLD, requires a fresh clear event, operator acknowledgement, and `RTK_CONFIDENT` or bounded `DEAD_RECKONING_ACTIVE` position confidence before resume.
- `CANOPY_RTK_DROP` — may continue in bounded dead reckoning without HOLD when FEAT-009 duration and distance budgets are still valid and local sensors agree.
- `ULTRASONIC_CANOPY_SHADOW` — enters HOLD, requires operator acknowledgement, and resumes only after fresh clear telemetry with `RTK_CONFIDENT` position confidence.

Unrecoverable-for-auto-resume fault types are:

- `ESTOP_ACTIVE`
- `LOW_LIQUID`
- `ODOMETER_IMU_DIVERGENCE`
- `PUMP_FEEDBACK_MISMATCH`

Policy thresholds in the current contract:

| Policy | Value | Effect |
| --- | ---: | --- |
| `max_fault_clear_age_s` | `2.0 s` | Older fault-clear telemetry blocks resume. |
| `max_hold_duration_s` | `15.0 s` | Longer unrecovered HOLD produces `HOLD_TIMEOUT` and aborts. |
| `max_actuator_safe_latency_ms` | `200 ms` | HOLD and actuator-safe events must switch outputs off within this latency after a hold-requiring fault. |
| `resume_start_policy` | `FIRST_UNSPRAYED_LEDGER_UNIT` | Resume scans the spray ledger and starts at the first unit not already sprayed. |
| `duplicate_spray_action` | `SUPPRESS_COMMAND_LOG_EVENT_KEEP_OUTPUTS_SAFE` | Duplicate replay commands are logged and not applied to pump or valves. |

A recoverable resume is allowed only when all required conditions are true: fault clear is fresh, acknowledgement is present when required, position confidence is accepted, FEAT-009 fallback budgets are not exceeded, and at least one unsprayed ledger unit remains.

## Spray Ledger and Duplicate-Spray Suppression

The spray ledger is the guard against duplicate chemical/fertilizer application after a mission replay or resume. Each logical spray work unit is identified by:

- `mission_id`
- `spray_unit_id`
- `row_label`
- `spray_zone`
- `pass_id`

The current cucumber-row mission splits the left-row spray pass into two work units:

| Spray unit | Mission items | Progress range | Zone |
| --- | --- | ---: | --- |
| `row_01_left_spray_head` | `WP003` to `WP004` | `0.00–0.45` | `LEFT` |
| `row_01_left_spray_tail` | `WP003` to `WP004` | `0.45–1.00` | `LEFT` |

Ledger statuses are `unsprayed`, `sprayed`, and `skipped_duplicate_suppressed`. On resume, the companion logic scans `resume_scan_order` and selects the first unit whose status is not `sprayed`. If a replay tries to energize a spray unit already marked `sprayed`, the validator requires:

1. no pump/valve command is applied,
2. `DUPLICATE_SPRAY_SUPPRESSED` is logged,
3. reason code `ledger_unit_already_sprayed` is present, and
4. actuator outputs remain safe/off.

## Actuator Safety Rules

Safe/off outputs for FEAT-010 are:

```text
pump_pwm_us=1000
left_spray_valve=0
right_spray_valve=0
agitation=0
```

The validator cross-checks these values against FEAT-006, FEAT-007, and FEAT-008. HOLD-mode events, blocked recovery, timeout, abort, duplicate suppression, mission resume handoff, spray-off, and mission completion must carry safe/off actuator states. A `SPRAY_ON` event is allowed only for an unsprayed unit and must match the declared spray output for its zone.

## Black-Box Telemetry Schema

Telemetry sequence numbers must be strictly increasing and timestamps must be nondecreasing within each scenario. Every event requires:

- `seq`
- `timestamp_s`
- `event_type`
- `state`
- `mode`
- `mission_item_id`
- `actuator_state`

Event-specific required fields make the log reconstructable after a fault. Examples:

| Event type | Required fields |
| --- | --- |
| `MISSION_START` | `mission_id` |
| `SPRAY_ON` | `spray_unit_id`, `spray_zone` |
| `SPRAY_LEDGER_RECORD` | `spray_unit_id`, `ledger_status` |
| `FAULT_DETECTED` | `fault_id`, `fault_type`, `recovery_class`, `position_confidence_state` |
| `HOLD_ENTERED` | `fault_id`, `reason_codes` |
| `ACTUATORS_SAFE` | `fault_id`, `safe_output_verified` |
| `FAULT_CLEAR` | `fault_id`, `clear_event_age_s`, `clear_source` |
| `RESUME_ACK` | `fault_id`, `ack_source`, `acknowledgement` |
| `POSITION_CONFIDENCE` | `position_confidence_state`, `confidence_inputs` |
| `RECOVERY_DECISION` | `fault_id`, `recovery_decision`, `resume_allowed`, `reason_codes` |
| `MISSION_RESUMED` | `resume_policy`, `resume_unit_id` |
| `SPRAY_REPLAY_ATTEMPT` | `spray_unit_id`, `requested_actuator_state` |
| `DUPLICATE_SPRAY_SUPPRESSED` | `spray_unit_id`, `reason_codes` |
| `HOLD_TIMEOUT` | `fault_id`, `hold_duration_s`, `reason_codes` |
| `MISSION_ABORTED` | `fault_id`, `reason_codes` |
| `MISSION_COMPLETE` | `outcome` |

The contract requires outcome-specific event sequences for completed recovery, bounded dead-reckoning completion, duplicate-suppressed completion, aborted missions, and blocked resume attempts.

## Negative Completeness Checks

The validator intentionally mutates the successful recovery scenario to prove the telemetry schema fails closed:

- dropping `fault_id` from a fault record must fail with `missing_required_field:fault_id`,
- dropping `RECOVERY_DECISION` from a recovered mission must fail with `missing_required_event:RECOVERY_DECISION`.

These negative checks prevent a sparse or ambiguous black-box log from passing the feature gate.

## SITL / Companion Integration Path

1. Keep actuator power disconnected for FEAT-010 dry-run validation.
2. Run `python scripts/validate-fault-recovery-telemetry.py sitl/fault-recovery-telemetry.v0.json` from the repository root to validate the deterministic contract.
3. Map ArduRover/SITL telemetry into the contract fields:
   - mission item and mode from mission/vehicle state,
   - actuator output echo from servo/relay command state,
   - obstacle and ultrasonic clear events from simulated rangefinder or virtual bumper data,
   - RTK/dead-reckoning confidence from FEAT-009 position-confidence evaluation,
   - operator acknowledgement from the companion console or test harness.
4. On any hold-requiring fault, command HOLD and safe/off outputs before considering resume.
5. Before resuming, evaluate clear freshness, acknowledgement, position confidence, FEAT-009 fallback budget, and the spray ledger.
6. Resume at `FIRST_UNSPRAYED_LEDGER_UNIT`; suppress and log any duplicate spray replay instead of energizing pump/valves.
7. Preserve the telemetry log as the black-box artifact for SITL regression review before any physical prototype control code is connected.

## Operator Notes

- Do not use FEAT-010 evidence to justify chemical/fertilizer field operation; it is SITL-only.
- Do not widen recovery thresholds just to make scenarios pass; threshold changes must be reflected in the JSON contract, validator, and verification evidence.
- Do not manually edit `feature-list.json` pass flags; use `python scripts/update-feature.py feature-list.json` only after the full gate succeeds.
- Preserve actual terminal output in `stage-gates/active/FEAT-010/04-verification.md` before changing the verification status to PASS.
