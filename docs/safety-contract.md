# Safety Contract

## Purpose

Define the minimum Phase 1 safety behaviors for autonomous cucumber-row spraying/fertigation.

## Default Safe State

- Rover stopped or held.
- Pump off.
- Left valve off.
- Right valve off.
- Manual operator review before resuming spray.

## Required Faults

- `front_obstacle`: stop/HOLD, spray off, wait for operator decision.
- `invalid_side_sensor`: reduce speed or stop; never steer into side planting beds.
- `low_liquid`: pump off, valves off, alert operator, no automatic resume.
- `pressure_low`: pump off; inspect for dry-run, leak, empty tank, or disconnected line.
- `pressure_high`: pump off; inspect for blocked nozzle or closed valve.
- `low_battery`: spray off and stop/return according to selected ArduRover failsafe.
- `rc_loss`: spray off and stop/return according to selected ArduRover failsafe.
- `telemetry_loss`: continue only if RC/manual failsafe remains available; otherwise stop/return with spray off.
- `emergency_stop`: physical circuit cuts motor and pump power independently of Pixhawk/software.

## Manual Override

RC/manual control has priority over autonomous mission control. The operator must be able to stop motion and disable spraying immediately.

## Sensor Degradation

Invalid ultrasonic readings, large left/right disagreement, or unstable wet-leaf readings are safety degradation events. The rover should slow, stop, or abort rather than use questionable data to steer near crop beds.
