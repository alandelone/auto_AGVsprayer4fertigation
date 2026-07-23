# Safety Contract

## Purpose

Define the minimum Phase 1 safety behaviors for autonomous cucumber-row spraying/fertigation.

## Default Safe State

- Rover stopped or held.
- Pump off.
- Left valve off.
- Right valve off.
- Manual operator review before resuming spray.

## Required Faults & Interlocks

- `front_obstacle`: stop/HOLD, spray off, wait for operator decision.
- `invalid_side_sensor`: reduce speed or stop; never steer into side planting beds.
- `low_liquid`: pump off, valves off, alert operator, no automatic resume.
- `pressure_low`: pump off; inspect for dry-run, leak, empty tank, or disconnected line.
- `pressure_high`: pump off; inspect for blocked nozzle or closed valve.
- `low_battery`: spray off and stop/return according to selected ArduRover failsafe.
- `rc_loss`: spray off and stop/return according to selected ArduRover failsafe.
- `telemetry_loss`: continue only if RC/manual failsafe remains available; otherwise stop/return with spray off.
- `position_confidence_low`: RTK fix loss + ultrasonic/odometer disagreement exceeding threshold; reduce speed, switch to IMU/wheel odometer dead reckoning, or HOLD.
- `preflight_check_failed`: hardware disarmed, prevent AUTO mode entry until all sensor, power, E-stop, and telemetry checks pass.
- `emergency_stop`: physical circuit cuts motor and pump power independently of Pixhawk/software.

## Position Confidence Gate & Navigation Fallback

- **Cross-Sensor Validation:** System continuously compares RTK GPS positioning against ultrasonic wall-following and wheel odometer speed/distance.
- **Dead Reckoning Fallback:** When RTK GPS drops under dense leaf canopy, the controller seamlessly falls back to IMU + Wheel Odometer dead reckoning for short-distance row traversal.
- **Confidence Gate:** If fused position variance exceeds safety limits (> 0.3 m sideways drift from row centerline), autonomous motion stops immediately with spray disabled.

## Preflight Verification Policy

Before allowing vehicle arming or transition to `AUTO` mode, the controller must execute a hardware Preflight Gate:
1. E-stop physical circuit closed (active high safety signal).
2. Battery voltage within nominal operating range.
3. Pressure sensor at normal idle reading (0 Bar / 0 PSI).
4. Liquid level sensor reporting adequate fluid level.
5. Telemetry link RSSI > 50%.
6. All Pixhawk actuators (pump, left valve, right valve, agitation) responding to signal checks.

## Recovery & Resume Policy

Following an abort, emergency stop, or fault HOLD state:
1. Operator must acknowledge and clear the fault manually.
2. System requires re-execution of the Preflight Check.
3. Operator selects:
   - **Resume Mission:** Vehicle navigates to the last uncompleted waypoint, re-primes pump, verifies position confidence, and resumes spraying.
   - **Return to Base:** Vehicle navigates safely out of the crop row with spray disabled.
4. Duplicate-spray protection: Spray is kept OFF until vehicle reaches the exact uncompleted route boundary.

## Manual Override

RC/manual control has priority over autonomous mission control. The operator must be able to stop motion and disable spraying immediately.

## Sensor Degradation & Logging

- Invalid ultrasonic readings, large left/right disagreement, or unstable wet-leaf readings are safety degradation events. The rover should slow, stop, or abort rather than use questionable data to steer near crop beds.
- All position confidence drops, sensor anomalies, preflight failures, and recovery events are recorded to the **Mission Telemetry Log** for post-mission diagnostics.
