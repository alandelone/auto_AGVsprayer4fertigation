# SITL Position Confidence and Canopy Fallback

## Scope

FEAT-009 defines a deterministic ArduRover SITL-style navigation safety contract for cucumber-row sprayer missions. The contract cross-checks RTK GPS, IMU heading, wheel odometry, and ultrasonic row-distance cues before allowing spray logic to continue. It is a software/SITL validation artifact only: it must not energize pumps, valves, relays, servos, or field hardware.

The machine-readable contract lives at `sitl/position-confidence.v0.json`; the deterministic validator is `scripts/validate-position-confidence.py`.

## Inputs and Units

| Signal | Unit | Purpose |
| --- | --- | --- |
| `gps.fix_type` | enum | Classifies RTK confidence (`RTK_FIXED` / `RTK_FLOAT` are accepted for confident operation). |
| `gps.hdop` | dimensionless | Rejects poor dilution of precision above the configured RTK threshold. |
| `gps.age_s` | seconds | Rejects stale position samples before any fallback decision. |
| `imu.heading_deg` | degrees | Cross-checks rover heading against wheel odometry during fallback. |
| `odometer.heading_deg` | degrees | Confirms local heading agreement for dead reckoning. |
| `odometer.distance_into_segment_m` | meters | Detects drift from the mission segment distance. |
| `ultrasonic.left_m` / `ultrasonic.right_m` | meters | Confirms the rover remains centered between row/canopy cues. |
| `fallback.duration_s` | seconds | Bounds dead-reckoning time under canopy GPS degradation. |
| `fallback.distance_m` | meters | Bounds dead-reckoning travel distance under canopy GPS degradation. |
| `speed_mps` | meters per second | Preserves mission context for future SITL/companion integration. |

## Configured Thresholds

The FEAT-009 contract currently uses these conservative dry-run thresholds:

| Threshold | Value | Effect |
| --- | ---: | --- |
| Accepted RTK fix types | `RTK_FIXED`, `RTK_FLOAT` | Required for `RTK_CONFIDENT` decisions. |
| Maximum HDOP | `1.2` | Higher HDOP is treated as degraded GPS. |
| Maximum GPS age | `1.5 s` | Older samples force `SAFE_HOLD` with reason `gps_stale`. |
| Maximum odometer-vs-mission drift | `0.35 m` | Larger drift blocks fallback with `odometer_mission_drift`. |
| Maximum IMU/odometer heading divergence | `8 deg` | Larger divergence blocks fallback with `imu_odom_heading_disagreement`. |
| Ultrasonic valid range | `0.18–1.20 m` | Out-of-range row cues block fallback with `ultrasonic_invalid`. |
| Row width target | `1.20 m` | Left+right ultrasonic readings should match the cucumber-row corridor. |
| Maximum row-width error | `0.25 m` | Larger row-width mismatch blocks fallback with `ultrasonic_row_width_error`. |
| Maximum fallback duration | `6.0 s` | Longer fallback forces `SAFE_HOLD`. |
| Maximum fallback distance | `1.5 m` | Longer fallback travel forces `SAFE_HOLD`. |

## Decision States

### `RTK_CONFIDENT`

The rover may remain in `AUTO` when GPS is fresh, fix type is accepted, HDOP is within threshold, and IMU/odometer/ultrasonic cues agree with the active mission segment. Spraying is allowed only if the mission segment spray zone is active.

### `DEAD_RECKONING_ACTIVE`

The rover may continue briefly in `AUTO` when GPS is degraded under canopy conditions, but only if fallback is already active, GPS is not stale, IMU and wheel odometry agree, odometer distance is close to mission distance, ultrasonic row cues are valid, and both fallback duration and distance remain within budget.

This state is intentionally bounded. It is not permission for indefinite blind navigation or chemical operation.

### `SAFE_HOLD`

The rover must enter `HOLD` and stop spraying whenever position confidence is unsafe. The validator requires this state for stale GPS, local-sensor disagreement, odometer drift, invalid ultrasonic readings, row-width mismatch, degraded GPS without active fallback, and expired fallback time/distance budgets.

## Actuator Safety Behavior

FEAT-009 inherits the FEAT-006 actuator mapping and FEAT-008 preflight/dosing safety semantics. Any `SAFE_HOLD` decision must require the configured safe outputs:

```text
pump_pwm_us=1000
left_spray_valve=0
right_spray_valve=0
```

The validator cross-checks those values against `hardware/pixhawk-actuator-mapping.v0.json` and `sitl/preflight-dosing.v0.json`. If a scenario enters `SAFE_HOLD` without safe pump/valve expectations, validation fails.

## SITL / Companion Integration Path

1. Run `python scripts/validate-position-confidence.py sitl/position-confidence.v0.json` from the repository root to verify the deterministic contract.
2. Wire the validator into `bash scripts/check-gate.sh` so FEAT-009 participates in the repo-level gate.
3. Map SITL or companion telemetry into the contract fields:
   - RTK fix, HDOP, and sample age from GPS telemetry,
   - IMU heading from attitude/heading telemetry,
   - wheel odometer heading and segment distance from local odometry,
   - left/right ultrasonic row distance from rangefinder inputs,
   - fallback timer/distance from companion-side state.
4. Treat `RTK_CONFIDENT` and bounded `DEAD_RECKONING_ACTIVE` as software permission to continue the current dry-run mission segment.
5. Treat `SAFE_HOLD` as a failsafe command: switch to `HOLD`, set pump PWM to off, close spray valves, and require operator review before any future resume policy.

Full recovery, resume behavior, and black-box mission telemetry belong to FEAT-010, not FEAT-009.

## Operator Notes

- Keep physical actuator power disconnected for FEAT-009 dry-run validation.
- Do not widen thresholds just to make scenarios pass; threshold changes must be reflected in both the JSON contract and validator output evidence.
- Do not use dead reckoning when ultrasonic cues are missing, stale, out of range, or inconsistent with expected row width.
- Do not manually edit `feature-list.json` pass flags; use `python scripts/update-feature.py feature-list.json` only after the full gate succeeds.
- Preserve actual terminal output in `stage-gates/active/FEAT-009/04-verification.md` before changing the verification status to PASS.
