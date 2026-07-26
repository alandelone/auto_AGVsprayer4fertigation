# 01 Discovery — FEAT-008

## Goal

Implement an ArduRover SITL preflight gate and dosing calibration script so the sprayer mission cannot start unless simulated safety, tank, pressure, actuator, and mission-export prerequisites are healthy, and so flow-rate dosing can be calculated from rover speed without logic crashes.

## User goal and success criteria

- Validate preflight readiness before mission execution in SITL or deterministic dry-run mode.
- Verify speed-synchronized dosing calculations for the cucumber-row mission source/export artifacts from FEAT-007.
- Fail safely when required sensor/actuator inputs are missing, out of range, or inconsistent.
- Produce deterministic command-line evidence suitable for `bash scripts/check-gate.sh`.

## Hardware and software assumptions

- Pixhawk/ArduRover actuator mapping from FEAT-006 remains the actuator source of truth.
- Mission Planner / QGC mission exports from FEAT-007 remain the route source of truth.
- SITL may be unavailable on the host; therefore validators must support deterministic fixture-backed validation that can later be connected to live SITL telemetry.
- No chemical/fertilizer operation is in scope; this is simulation/preflight logic only.

## External dependencies

- Python 3 standard library only unless a later gate explicitly justifies additional dependencies.
- Existing repo scripts: `scripts/check-gate.sh`, `scripts/validate-mission-exports.py`, and deterministic contracts under `hardware/`, `missions/`, and `routes/`.

## Risks, unknowns, and blockers

- Real ArduPilot SITL binaries may not be installed in this environment.
- MAVLink telemetry schemas must be represented deterministically before live SITL integration.
- Dosing formulas must avoid commanding pump/valve outputs outside the FEAT-006 actuator safety mapping.

## Feature IDs in scope

- In scope: FEAT-008 only.
- Out of scope: FEAT-009 navigation confidence/dead-reckoning fallback and FEAT-010 fault recovery/telemetry replay.
