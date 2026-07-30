# 01 Discovery — FEAT-009 SITL Position Confidence + Canopy Fallback

## Goal

Implement a deterministic SITL navigation safety layer that cross-checks RTK GPS, IMU, wheel odometer, and ultrasonic row/canopy distance signals before and during autonomous spraying. The feature must detect degraded position confidence under canopy-like GPS loss, switch to bounded dead reckoning only when local sensors agree, and command safe HOLD with sprayer outputs off when confidence is unsafe.

## User goal and success criteria

- Prevent mission logic crashes when GPS quality degrades in cucumber-row canopy conditions.
- Keep spraying only when position confidence is high enough or dead-reckoning fallback is explicitly safe and bounded.
- Enter HOLD and disable pump/valves when sensors disagree, odometry drift exceeds limits, ultrasonic row/canopy cues are invalid, or fallback time/distance budget expires.
- Produce machine-checkable scenario data and a validator that can run without real hardware.

## Hardware and software assumptions

- Vehicle stack target remains ArduRover/Pixhawk with companion-side logic validated first in deterministic SITL-style fixtures.
- Available signals for this feature: RTK fix type/HDOP/age, IMU yaw rate or heading consistency, wheel odometer delta, ultrasonic left/right row distance, mission segment context, and sprayer actuator state.
- FEAT-006 actuator mapping and FEAT-008 preflight/dosing safety semantics remain authoritative: any navigation safety stop must command pump and valves off.

## External dependencies

- No live ArduPilot SITL instance is required for the first deterministic gate; fixtures and validators must run with Python only.
- Later integration may map these contracts to MAVLink telemetry fields and Mission Planner/QGC replay outputs.

## Risks, unknowns, and blockers

- Exact RTK and odometer noise characteristics are not yet measured on the physical rover; thresholds must be conservative and explicit.
- Ultrasonic readings can be noisy near leaves, trellis posts, row ends, and angled canopy surfaces.
- Dead reckoning must be time/distance bounded; indefinite fallback is not acceptable for chemical/fertigation safety.
- Physical-field validation is out of scope until deterministic SITL-style checks pass.

## Feature IDs in scope

- In scope: FEAT-009.
- Upstream dependencies: FEAT-006 actuator mapping, FEAT-007 mission trigger semantics, FEAT-008 preflight/dosing gate.
- Out of scope: FEAT-010 full recovery/resume telemetry, real chemical operation, firmware flashing, and hardware procurement.
