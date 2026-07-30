# 01 Discovery — FEAT-010 SITL Fault Recovery, Resume Policy, and Telemetry Log

## Goal

Define deterministic SITL validation for end-to-end mission fault recovery. FEAT-010 must prove the AGV sprayer can enter a safe HOLD on simulated obstacles or sensor drops, recover only under explicit policy conditions, resume without duplicate spraying, and emit a complete black-box telemetry log for every safety-relevant state transition.

## User goal and success criteria

- Complete a simulated cucumber-row spraying mission after recoverable faults without logic crashes.
- Stop pump and valves immediately whenever an obstacle, unsafe sensor state, or recovery-policy violation requires HOLD.
- Resume only after the fault is cleared, the resume policy is satisfied, and the already-sprayed ledger prevents duplicate spray on replayed mission segments.
- Abort or remain in HOLD when a fault is not recoverable, a timeout expires, telemetry is incomplete, or resume would duplicate spraying.
- Produce machine-checkable scenario data and a validator that run without physical hardware.

## Hardware and software assumptions

- Vehicle target remains ArduRover/Pixhawk with companion-side safety logic validated first in deterministic SITL-style fixtures.
- Upstream actuator safety semantics remain authoritative: pump and all valves are off in HOLD, abort, low-confidence, or e-stop-equivalent states.
- Mission actuation semantics from FEAT-007, preflight/dosing guardrails from FEAT-008, and position-confidence fallback decisions from FEAT-009 are available inputs.
- FEAT-010 inputs include mission item identity, spray zone, fault events, recovery-clear events, operator/autonomy acknowledgement, position-confidence state, sprayer outputs, and telemetry records.

## External dependencies

- No live ArduPilot SITL process is required for the first deterministic gate; fixtures and validators must run with Python only.
- Later integration can map the contract to MAVLink messages, Mission Planner logs, QGroundControl telemetry, or companion black-box logs.
- No secrets, farm-private credentials, or hardware credentials are needed.

## Risks, unknowns, and blockers

- Duplicate spraying can occur if resume replays a previously sprayed segment without a durable spray ledger.
- A recovery path can become unsafe if it trusts stale sensor-clear events or resumes without position-confidence revalidation.
- Telemetry can look complete while missing causality; every fault, hold, clear, resume, spray transition, and mission outcome needs monotonic event ordering.
- Physical-field validation remains out of scope until deterministic SITL-style checks pass.

## Feature IDs in scope

- In scope: FEAT-010.
- Upstream dependencies: FEAT-006 actuator mapping, FEAT-007 mission trigger semantics, FEAT-008 preflight/dosing gate, FEAT-009 position confidence and canopy fallback.
- Out of scope: firmware flashing, real chemical/fertigation operation, hardware procurement, and physical field trials.
