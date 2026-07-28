# 02 Tech Design — FEAT-009 SITL Position Confidence + Canopy Fallback

## Goal

Define the implementation approach for deterministic position-confidence checks and bounded canopy dead-reckoning fallback.

## Module boundaries

- `sitl/position-confidence.v0.json`: scenario contract with nominal RTK, canopy fallback, sensor disagreement, stale GPS, odometry drift, ultrasonic invalid, and fallback-expired cases.
- `scripts/validate-position-confidence.py`: deterministic validator that evaluates each scenario and prints concise pass/fail evidence.
- `docs/position-confidence-fallback.md`: operator/developer reference for thresholds, states, and safety actions.
- `scripts/check-gate.sh`: add the validator to the repo gate once implementation artifacts exist.
- `stage-gates/active/FEAT-009/04-verification.md`: capture actual command/output evidence before marking PASS.

## Data flow and API contracts

1. Scenario input provides a mission segment, current navigation mode, telemetry samples, threshold config, expected decision, and expected actuator safety state.
2. Validator derives a confidence state:
   - `RTK_CONFIDENT` when RTK quality, freshness, and sensor cross-checks are within threshold.
   - `DEAD_RECKONING_ACTIVE` when GPS is degraded but IMU, odometer, and ultrasonic row cues agree within bounded fallback limits.
   - `SAFE_HOLD` when confidence is unsafe or fallback limits expire.
3. Validator enforces sprayer safety: any `SAFE_HOLD` decision requires pump and valves off.
4. Output must include scenario counts and decision counts for gate evidence.

## Configuration strategy

Thresholds must be explicit in the JSON contract, including at minimum:

- maximum GPS age before stale classification,
- acceptable RTK fix types,
- maximum HDOP,
- maximum odometry-vs-mission drift,
- maximum IMU/odometer heading divergence,
- ultrasonic valid range and left/right row-width tolerance,
- maximum fallback duration and distance.

## Test strategy

- Start with fixture-level deterministic tests; no simulator process or hardware dependency.
- Include positive and negative scenarios for every state transition.
- Compile the validator with `python -m py_compile` and run it directly.
- Full gate must run through `bash init.sh && bash scripts/check-gate.sh` before feature completion.

## Safety and failure-mode handling

- Default unsafe: missing required telemetry, unknown mode, stale samples, or invalid thresholds must fail validation or produce `SAFE_HOLD` in scenarios.
- Dead reckoning is allowed only with bounded duration/distance and agreement between IMU, wheel odometer, and ultrasonic row cues.
- Any stop/fault mode must inherit FEAT-008 actuator safety: pump off, left valve off, right valve off.
