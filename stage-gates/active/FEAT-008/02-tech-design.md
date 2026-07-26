# 02 Tech Design — FEAT-008

## Goal

Define a deterministic preflight and dosing-calibration implementation that can run in CI without live hardware and later connect to ArduRover SITL/MAVLink telemetry.

## Module boundaries

- `sitl/preflight-dosing.v0.json`: machine-readable scenario contract for required preflight checks, telemetry ranges, actuator readiness, dosing inputs, and expected safety decisions.
- `scripts/validate-preflight-dosing.py`: deterministic validator/calculator for the scenario contract.
- `docs/preflight-dosing.md`: human operating notes for SITL preflight inputs, fail-safe decisions, and dosing calibration usage.
- `scripts/check-gate.sh`: calls the validator after existing FEAT-001 through FEAT-007 checks.

## Data flow and API contracts

1. Load mission-export summary and actuator mapping already validated by previous feature scripts.
2. Load the FEAT-008 preflight/dosing scenario contract.
3. Validate required preflight sensor ranges:
   - E-stop not active.
   - Low-liquid/tank signal healthy.
   - Pressure within bench-safe range.
   - Pump/valve actuator mapping present.
   - Mission contains spray-triggered segments.
4. Calculate target flow from speed, nozzle width, and application-rate inputs.
5. Emit deterministic PASS/FAIL lines and refuse mission start on any unsafe condition.

## Configuration strategy

- Keep default scenario fixture committed under `sitl/`.
- Use explicit units in JSON keys/values; do not rely on comments in JSON.
- Keep all thresholds traceable to existing bench/prototype contracts where possible.

## Test strategy

- Validator must fail closed for missing fields, invalid units, unsafe ranges, or impossible dosing values.
- Add at least one deterministic happy-path scenario and one unsafe/blocked check in the same contract or fixture set.
- Gate evidence must include actual command output from `bash init.sh && bash scripts/check-gate.sh`.

## Safety and failure-mode handling

- Default decision on malformed telemetry or configuration is `mission_start_allowed=false`.
- The validator must not command actuators; it only verifies readiness and dosing setpoints.
- Outputs must identify which check blocked mission start without exposing secrets or host-private data.
