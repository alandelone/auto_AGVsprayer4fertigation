# Route Contract

## Purpose

Define how a cucumber-row mission expresses movement and route-defined spraying/fertigation without requiring a companion computer in Phase 1.

## Route File

Example: `routes/examples/cucumber-row-route.example.json`

A route has:

- `route_id`: stable identifier.
- `waypoints`: named waypoint references. Repository examples must use fake/sanitized coordinates.
- `segments`: ordered movement sections.
- `mission_output_mapping`: spray mode to actuator output state.
- `required_faults`: safety conditions that must force safe behavior.

## Segment Fields

Required:

- `id`: unique segment ID.
- `type`: one of `TRANSIT`, `IN_ROW`, `TURN`, `RTL`, `ABORT`, `MISSION_END`.
- `spray`: one of `OFF`, `LEFT`, `RIGHT`, `BOTH`.
- `target_speed_mps`: positive rover speed for the segment.
- `waypoints`: at least two waypoint IDs.

## Spray Rules

- Spraying is route-defined, not continuous.
- Every segment must explicitly set `spray`.
- `TRANSIT`, `TURN`, `RTL`, `ABORT`, and `MISSION_END` must use `OFF`.
- Only `IN_ROW` segments may use `LEFT`, `RIGHT`, or `BOTH`.
- Every segment boundary that starts, changes, or stops spraying must map to Mission Planner/MAVLink DO commands.

## Mission Planner Mapping

Phase 1 may encode route segments directly in Mission Planner:

- Navigation waypoints represent segment start/end.
- `DO_SET_RELAY` or `DO_SET_SERVO` commands set pump/valve outputs.
- Each non-spray segment explicitly sends spray `OFF` commands.
- Mission end and abort procedures must force spray `OFF` before return or hold.

## Safety Rule

Any safety fault overrides route state and forces spray `OFF`.
