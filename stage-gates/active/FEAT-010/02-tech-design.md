# 02 Tech Design — FEAT-010 SITL Fault Recovery, Resume Policy, and Telemetry Log

## Goal

Define the implementation approach for deterministic fault recovery, resume safety, duplicate-spray prevention, and black-box telemetry validation.

## Module boundaries

- `sitl/fault-recovery-telemetry.v0.json`: scenario contract covering recoverable and unrecoverable mission faults, resume policy, spray ledger expectations, and required telemetry events.
- `scripts/validate-fault-recovery-telemetry.py`: deterministic validator that evaluates recovery state transitions, actuator safety, duplicate-spray protection, and telemetry completeness.
- `docs/fault-recovery-telemetry.md`: operator/developer reference for state machine behavior, resume rules, spray ledger semantics, and black-box log fields.
- `scripts/check-gate.sh`: add the FEAT-010 validator to the repo gate once implementation artifacts exist.
- `stage-gates/active/FEAT-010/04-verification.md`: capture actual command/output evidence before marking PASS.

## Data flow and API contracts

1. Scenario input provides a mission route reference, ordered timeline events, recovery-policy config, initial spray ledger, and expected mission outcome.
2. Validator derives a recovery state machine:
   - `MISSION_RUNNING` while navigation, dosing, and position confidence are safe.
   - `HOLD_FAULT_ACTIVE` immediately after an obstacle, unsafe sensor drop, timeout, or policy violation.
   - `RECOVERY_READY` only after the fault is clear, telemetry is fresh, position confidence is acceptable, and acknowledgement requirements are met.
   - `MISSION_RESUMED` when replay starts at the first unsprayed mission segment.
   - `MISSION_COMPLETE` or `MISSION_ABORTED` as the final outcome.
3. Validator enforces actuator safety: every hold, abort, and unrecoverable fault requires pump and valves off.
4. Validator enforces spray-ledger semantics: a segment already recorded as sprayed must not receive a second spray-on command after resume.
5. Validator enforces telemetry completeness with monotonic sequence numbers, nondecreasing timestamps, required event types, mission item references, fault IDs, recovery decisions, and actuator states.

## Configuration strategy

The JSON contract must make thresholds and policy choices explicit, including at minimum:

- recoverable fault types and unrecoverable fault types,
- maximum allowed fault-clear age before resume,
- maximum HOLD duration before abort,
- whether operator acknowledgement is required for each recovery class,
- position-confidence states allowed for resume,
- spray-ledger identity fields for duplicate prevention,
- required telemetry event types and required fields per event.

## Test strategy

- Start with fixture-level deterministic tests; no simulator process or hardware dependency.
- Include at least one successful recovery/resume mission, one duplicate-spray replay rejection, one unrecoverable fault HOLD/abort, one stale-clear or missing-ack rejection, and one telemetry-completeness failure path.
- Compile the validator with `python -m py_compile` and run it directly against the contract.
- Add a documentation/index check for the operator/developer reference.
- Run the full repository gate with `bash init.sh && bash scripts/check-gate.sh` before feature completion.

## Safety and failure-mode handling

- Default unsafe: missing telemetry fields, out-of-order event sequence, unknown fault type, stale clear event, missing acknowledgement, or missing position-confidence recheck must fail validation or force HOLD/abort in the scenario.
- Recovery never implies immediate spray-on; the resumed mission must prove the next segment is unsprayed before enabling pump/valves.
- Black-box logs must retain enough information to reconstruct why the rover held, resumed, aborted, or suppressed duplicate spraying.
