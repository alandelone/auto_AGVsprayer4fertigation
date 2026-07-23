# FEAT-007 Discovery: Mission Planner / QGC Waypoint Export

## Goal

Generate deterministic Mission Planner / QGroundControl mission artifacts for cucumber row spraying routes, with spray actuator commands embedded at row entry, row exit, and fault-safe transitions.

## Scope

- Produce a machine-readable mission route contract that can be converted into:
  - QGroundControl `.plan` format.
  - ArduPilot Mission Planner WPL 110 `.waypoints` format.
- Embed ArduPilot mission commands for sprayer actuation:
  - `MAV_CMD_DO_SET_SERVO` for pump PWM speed control on SERVO9 / AUX1.
  - `MAV_CMD_DO_SET_RELAY` for left/right valve relays and optional agitation relay.
- Keep all sample data deterministic and non-private; do not include real farm coordinates.

## Requirements

1. **Route Input Contract**
   - Define a small cucumber-row example route using local/test coordinates or clearly synthetic lat/lon points.
   - Include waypoint IDs, navigation command type, row/spray zone labels, target speed, and spray state.

2. **Exporter**
   - Generate both `.plan` and `.waypoints` outputs from the same source contract.
   - Use stable ordering and formatting so diffs are deterministic.
   - Keep pump/valve command mapping consistent with FEAT-006 Pixhawk actuator mapping.

3. **Safety Behavior**
   - Ensure mission start and mission end commands leave pump and spray valves OFF.
   - Ensure row exit commands turn spray OFF before return/hold segments.
   - Avoid embedding any command that bypasses physical E-stop cutoff behavior.

4. **Validation**
   - Add a deterministic validator that confirms exported mission files exist, parse, and contain required spray ON/OFF command transitions.
