# SITL Preflight Gate and Dosing Calibration

## Scope

FEAT-008 defines a deterministic ArduRover SITL/dry-run preflight gate and speed-synchronized dosing calculator for cucumber-row sprayer missions. The artifact is a validation contract only: it must not energize pumps, valves, relays, servos, or field hardware.

## Inputs and Units

The contract lives at `sitl/preflight-dosing.v0.json` and uses explicit metric/bench units:

| Field | Unit | Meaning |
| --- | --- | --- |
| `speed_mps` | meters per second | Rover ground speed used for dose synchronization. |
| `pressure_psi` | pounds per square inch | Water-only bench pressure for preflight safety checks. |
| `swath_width_m` | meters | Effective sprayed width for the active row/zone. |
| `application_rate_l_per_m2` | liters per square meter | Desired applied water/fertigation volume per ground area. |
| `target_flow_lpm` | liters per minute | Calculated pump/nozzle flow setpoint. |
| `pump_pwm_us` | PWM microseconds | Pump command range; `off` is the only allowed blocked-state command. |

Reference FEAT-008 calibration:

```text
target_flow_lpm = speed_mps * swath_width_m * application_rate_l_per_m2 * 60
0.600 L/min = 0.25 m/s * 0.50 m * 0.08 L/m² * 60
```

## Dry-Run / SITL Use

1. Keep physical actuator power disconnected for dry-run validation.
2. Run `python scripts/validate-preflight-dosing.py` from the repository root.
3. The validator loads:
   - `sitl/preflight-dosing.v0.json`
   - `hardware/pixhawk-actuator-mapping.v0.json`
   - `missions/cucumber-row-mission.v0.json`
4. Treat a `PASS: preflight dosing contract validated` line as permission to continue software/SITL testing only, not as permission for chemical or powered bench operation.
5. Use `bash init.sh && bash scripts/check-gate.sh` as the repo-level gate before marking FEAT-008 complete.

## Preflight Safety Decisions

The gate fails closed. Mission start is allowed only when every required condition is healthy:

- E-stop/cutoff telemetry reports `estop_active=false`.
- Low-liquid telemetry reports `low_liquid=false`.
- Pressure is inside the water-only bench range: 30–60 PSI.
- Required actuator mappings exist for pump PWM, left valve, right valve, agitation, and E-stop cutoff.
- The mission source includes at least one spray-triggered segment.

Any failed condition sets `mission_start_allowed=false`. Blocked scenarios must keep the pump at the configured off PWM and keep both left/right spray valves closed. A low-liquid event requires operator refill/review; a pressure fault keeps the pump off and requires operator review before any resume decision.

## Calibration Interpretation

The calculated `target_flow_lpm` is the total desired flow for the active spray width at the current speed. If rover speed changes, the target flow changes linearly:

- Higher speed requires higher flow to maintain the same application rate.
- Lower speed requires lower flow to avoid over-application.
- Zero or unsafe speeds must not be used to command actuators directly; this validator only confirms contract consistency.

The configured reference point is 0.600 L/min at 0.25 m/s, 0.50 m swath width, and 0.08 L/m². The allowed target range is 0.10–1.51 L/min, matching the safe deterministic envelope for this SITL/dry-run contract. Pump PWM limits are calibration bounds only; field control code must still enforce safe/off defaults before enabling any output.

## Operator Notes

- Use clean water only for later bench tests; no fertilizer or chemical mix is covered by FEAT-008.
- Do not bypass E-stop, low-liquid, or pressure checks to make a scenario pass.
- Do not manually edit `feature-list.json` pass flags; use `python scripts/update-feature.py feature-list.json` only after the full gate succeeds.
- Preserve the actual terminal output in `stage-gates/active/FEAT-008/04-verification.md` before changing the verification status to PASS.
