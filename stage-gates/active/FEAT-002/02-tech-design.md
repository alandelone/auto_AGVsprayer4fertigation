# 02 Tech Design

## Goal

Define a Phase 1 technical design for a practical cucumber-farm AGV sprayer/fertigation rover using Pixhawk + ArduRover, RTK waypoint navigation, ultrasonic row-following, and route-segment spray control.

## Design Status

STATUS: READY FOR OWNER REVIEW

This design intentionally avoids Raspberry Pi, Jetson, ROS2, AI vision, and custom real-time Linux robotics code in Phase 1. It uses ArduRover, Mission Planner, Pixhawk-compatible I/O, and deterministic simulation/bench tests first.

## Source Inputs

- Discovery contract: `stage-gates/active/FEAT-002/01-discovery.md`
- Field/hardware reference: `docs/field-reference.md`
- Extracted PDF reference: `docs/pdf-extract-3d-agv-sprayer.txt`
- ArduPilot Rover documentation checked during design:
  - Rover object avoidance supports rangefinders/proximity sensors and can stop/re-route depending mode/configuration.
  - Rover rangefinder setup supports multiple rangefinders around the vehicle; forward rangefinder is the minimum for obstacle avoidance.
  - ArduPilot relay outputs can be controlled by mission commands and RC auxiliary options, but GPIO relay pins have limited current and must drive an external relay/MOSFET/driver, not pump load directly.
  - MAVLink mission commands include `DO_SET_RELAY`, `DO_REPEAT_RELAY`, `DO_SET_SERVO`, and waypoint/navigation commands usable for spray segment enable/disable.

## Phase 1 System Boundary

### In Scope

- Pixhawk-class controller running ArduRover.
- Mission Planner configuration and mission planning.
- RTK-GPS waypoint navigation for row entry, row exits, and inter-row movement.
- Ultrasonic distance sensing for local row alignment and frontal stop behavior.
- Pixhawk-controlled spray/fertigation actuator outputs by relay/servo/PWM channel.
- Manual override, emergency stop, low-liquid detection, and pump-pressure abnormal detection.
- Simulation-first validation using ArduPilot SITL, with bench/hardware validation later.

### Out Of Scope

- ROS2 navigation stack.
- Companion computer dependency.
- AI/depth-camera autonomy.
- Automatic crop health diagnosis, cucumber counting, or harvesting.
- Final mechanical CAD, tank sizing, pump sizing, or nozzle calibration until dimensions and parts are selected.

## Module Boundaries

### 1. Vehicle Control Layer

Owner: Pixhawk + ArduRover firmware.

Responsibilities:

- Steering/throttle control.
- Flight mode management: MANUAL/HOLD/AUTO/RTL or equivalent rover modes.
- Geofence and mission execution.
- Failsafe behavior for RC/GCS/GPS/battery where available.
- Rangefinder/proximity input handling for obstacle stop/avoidance.

Configuration artifacts:

- Mission Planner parameter file, later stored as sanitized `config/ardurover-phase1.param`.
- SITL parameter overlay, later stored as `simulation/ardurover-sitl.param`.

### 2. Navigation Contract Layer

Owner: route/mission definition files and operator workflow.

Responsibilities:

- Define field routes as row-entry, in-row travel, row-exit, turn/transition, and return-home segments.
- Assign each route segment a spray mode: `OFF`, `LEFT`, `RIGHT`, or `BOTH`.
- Keep GPS/RTK responsible for macro-positioning only.
- Use ultrasonic side distances as local row-centering references inside rows.

Data model candidate:

```json
{
  "route_id": "cucumber_block_a_row_01",
  "segments": [
    {
      "id": "entry",
      "type": "TRANSIT",
      "spray": "OFF",
      "waypoints": ["WP001", "WP002"]
    },
    {
      "id": "row_01_spray_left",
      "type": "IN_ROW",
      "spray": "LEFT",
      "target_speed_mps": 0.25,
      "waypoints": ["WP003", "WP004"]
    }
  ]
}
```

Phase 1 implementation may encode this directly as Mission Planner waypoints plus DO commands instead of custom route JSON, but the above contract prevents ambiguity.

### 3. Sensor Layer

Owner: hardware wiring + ArduRover rangefinder parameters.

Candidate sensors:

- Left row distance: 1 or 2 waterproof JSN-SR04T-style ultrasonic modules.
- Right row distance: 1 or 2 waterproof JSN-SR04T-style ultrasonic modules.
- Front obstacle/dead-end detection: 1 waterproof ultrasonic module.
- Optional alternative: GY-US42 I2C-compatible ultrasonic module if waterproofing is solved.

Responsibilities:

- Provide bounded distance readings to ArduRover/Mission Planner.
- Reject invalid readings outside physical min/max range.
- Detect frontal obstacle threshold breach and force stop/HOLD behavior.
- Support local row-centering by comparing left/right distances.

Open engineering decision:

- Exact ArduRover parameter mapping for 3-5 ultrasonic sensors must be validated against the selected firmware build and Pixhawk I/O limits.

### 4. Sprayer/Fertigation Actuator Layer

Owner: Pixhawk output + external driver board + pump/valve hardware.

Responsibilities:

- Turn pump/valves on/off from Pixhawk relay/servo/PWM outputs.
- Support independent side selection: `LEFT`, `RIGHT`, `BOTH`, `OFF`.
- Support fixed-point/manual trigger from RC auxiliary switch or Mission Planner servo/relay control.
- Keep pump current off Pixhawk pins; Pixhawk output only drives relay/MOSFET/ESC/driver signal.

Recommended Phase 1 actuator model:

- `RELAY0` or servo/PWM output: pump enable.
- `RELAY1` or servo/PWM output: left valve enable.
- `RELAY2` or servo/PWM output: right valve enable.
- Mission commands toggle outputs at segment boundaries.

### 5. Safety Interlock Layer

Owner: ArduRover failsafes + discrete sensors + operator procedure.

Mandatory interlocks:

- Manual override: RC transmitter can take control immediately.
- Emergency stop: physical E-stop breaks motor power and pump power independently of software.
- Front obstacle stop: forward sensor threshold triggers stop/HOLD or mission abort.
- Low-liquid: float switch or level sensor disables pump and raises operator alert.
- Pump pressure abnormal: pressure switch/sensor detects blocked nozzle, dry run, leak, or overpressure.
- Low battery: rover returns or stops with pump disabled.
- Lost RC/GCS/telemetry: rover stops or returns according to selected operating policy.

Default safe state:

- Vehicle stopped.
- Pump off.
- Left/right valves closed/off.
- Manual recovery required before spraying resumes.

## Data Flow

1. Operator surveys row boundaries and creates RTK waypoints.
2. Operator defines route segments and spray mode per segment.
3. Mission Planner uploads mission and parameters to Pixhawk.
4. Rover enters row using RTK/GPS waypoints.
5. In-row movement uses side ultrasonic distance balance as local alignment input/guard.
6. Mission segment boundary issues spray output commands.
7. Front ultrasonic, low-liquid, pressure, E-stop, RC override, and failsafe states can interrupt mission.
8. Telemetry radio returns vehicle state, mode, GPS, rangefinder, and actuator status to operator.
9. Verification logs are saved into `stage-gates/active/FEAT-002/04-verification.md`.

## API / Mission Contracts

### Spray Mode Contract

- `OFF`: pump off; both side valves off.
- `LEFT`: pump on; left valve on; right valve off.
- `RIGHT`: pump on; left valve off; right valve on.
- `BOTH`: pump on; left valve on; right valve on.

### Segment Transition Contract

- Every in-row spray segment must explicitly set spray state at entry.
- Every transit, turn, pause, RTL, abort, or mission-end segment must explicitly set `OFF`.
- Mission must never assume previous actuator state is safe.

### Safety Contract

- Any safety fault immediately commands `OFF` for spray outputs.
- Any emergency stop cuts motor and pump power outside software.
- Any invalid sensor reading is treated as degraded safety and must reduce speed, stop, or abort according to severity.

## Configuration Strategy

Future config files should be sanitized and hardware-neutral:

- `config/ardurover-phase1.param`: reviewed Mission Planner parameter export with no private farm coordinates.
- `simulation/ardurover-sitl.param`: SITL-safe parameter overlay.
- `routes/examples/cucumber-row-route.example.json`: fake/example route contract.
- `docs/operator-checklist.md`: pre-run checklist for power, E-stop, pump, liquid, pressure, radio, GPS/RTK, and sensor sanity.

Secrets/private data rule:

- Do not commit real farm coordinates, private telemetry IDs, API keys, or hardware credentials.
- Use fake coordinates and example identifiers in repository files.

## Test Strategy

### Deterministic Repository Tests

Before FEAT-002 can pass, add tests or scripts that validate:

- Route segments require explicit spray mode.
- Spray mode maps to correct pump/left/right outputs.
- Transit/turn/abort/RTL segments force spray `OFF`.
- Invalid sensor values are rejected.
- Safety faults force spray `OFF`.
- Simulation evidence exists in `04-verification.md`.

### SITL / Simulation Tests

Use ArduPilot SITL as the first candidate because it matches the selected ArduRover firmware and avoids adding ROS2/AI dependencies.

Minimum simulation evidence:

- Rover can execute a representative row-entry, in-row, row-exit, and return route.
- Mission commands switch spray outputs at correct segment boundaries.
- Obstacle/fault injection causes stop/abort and spray-off behavior.
- Logs or command output are captured in `04-verification.md`.

### Bench Tests Later

- Validate Pixhawk output voltage/current only drives an external control input.
- Verify relay/MOSFET driver switches pump/valves safely.
- Verify low-liquid and pressure sensors trigger pump-off behavior.
- Verify ultrasonic sensors produce stable readings against wet leaves, trellis posts, hoses, and angled foliage.

## Safety And Failure Modes

| Failure | Required Behavior |
| --- | --- |
| Front obstacle below threshold | Stop/HOLD, spray OFF, require operator decision. |
| Left/right ultrasonic disagreement or invalid reading | Reduce speed or stop; do not steer into planting beds. |
| GPS/RTK degraded under canopy | Trust row sensors for local alignment; avoid high-speed operation; stop if position uncertainty exceeds route tolerance. |
| Low liquid level | Pump OFF, valves OFF, alert operator, no automatic resume. |
| Pressure too low | Pump OFF, flag leak/dry-run/no-liquid fault. |
| Pressure too high | Pump OFF, flag blocked nozzle/closed valve fault. |
| RC override | Operator command takes priority; spray OFF unless explicitly held by safe manual control. |
| E-stop pressed | Cut motor and pump power independently of software. |
| Mission end/RTL/abort | Spray OFF before movement continues. |

## Owner Decisions Needed Before Implementation

- Exact row width, trellis spacing, minimum turning area, and vehicle envelope.
- Drive layout: differential drive, Ackermann steering, skid-steer, or tracked.
- Motor driver/ESC, battery voltage, motor current, and pump current.
- Pump type, tank size, nozzle type, expected flow rate, and operating pressure.
- Liquid-level sensor type and pressure sensor/switch type.
- Preferred telemetry frequency: 433 MHz vs 915 MHz for local legality and hardware availability.
- Confirm selected ArduRover firmware version and Pixhawk board variant.

## Definition Of Technical Design Done

- Module boundaries are defined.
- Data flow is defined.
- Spray command contract is defined.
- Safety contract is defined.
- Test/simulation strategy is defined.
- Open hardware decisions are listed for owner confirmation.
