# Pixhawk / Raspberry Pi / Pump / Valve Pinout

## Scope Boundary

This pinout is for hardware integration and prototype wiring. It avoids ArduRover firmware edits. Use stock ArduRover outputs, mission relay/servo commands, RC override, and hardwired safety cutoffs.

## Recommended Signal Map

- RC receiver -> Pixhawk RC input: manual override and mode switching.
- Telemetry radio -> Pixhawk TELEM1: Mission Planner/QGC telemetry.
- GPS/compass/RTK -> Pixhawk GPS/I2C: outdoor positioning and heading.
- Front ultrasonic -> Pixhawk compatible rangefinder input/interface: obstacle stop trigger.
- Left ultrasonic -> Pixhawk compatible rangefinder/input/interface: row reference.
- Right ultrasonic -> Pixhawk compatible rangefinder/input/interface: row reference.
- Pump enable -> Pixhawk relay/servo output -> external MOSFET/relay driver -> pump power rail.
- Left valve enable -> Pixhawk relay/servo output -> external MOSFET/relay driver -> left normally-closed valve.
- Right valve enable -> Pixhawk relay/servo output -> external MOSFET/relay driver -> right normally-closed valve.
- Low liquid sensor -> Pixhawk digital/analog input or companion GPIO plus failsafe relay: spray interlock.
- Pressure sensor/switch -> Pixhawk analog input or companion ADC: pressure interlock.
- Physical E-stop -> motor controller and pump/valve power rail: hard power cut independent of Pixhawk/RPi.
- Raspberry Pi optional link -> Pixhawk TELEM2 or USB: later logging/UI/network bridge only.

## Voltage And Isolation Rules

- Pixhawk relay/servo/GPIO pins are signal outputs only. Never power pump or valves directly from Pixhawk.
- Use MOSFET/relay drivers rated for pump/valve current and voltage.
- Add flyback diodes/TVS protection for solenoid valves and pump motor loads.
- Use shared ground only where required by driver input design; prefer opto-isolated driver boards for actuator loads.
- Level-shift 5 V ultrasonic or sensor outputs before any 3.3 V-only input.
- Keep Raspberry Pi powered from a stable buck converter; do not back-power Pixhawk from Pi USB during field wiring unless intentionally designed.

## Failsafe Output Policy

- Default boot state: pump off, left valve off, right valve off.
- TRANSIT / row entry / row exit / mission end: pump off, valves off.
- LEFT spray segment: pump on, left valve on, right valve off.
- RIGHT spray segment: pump on, left valve off, right valve on.
- BOTH spray segment: pump on, left valve on, right valve on.
- Any fault: pump off, left valve off, right valve off, operator review required.

## Firmware Boundary

FEAT-003 must not modify ArduRover firmware. Firmware-facing work later should be limited first to parameter files, mission commands, or companion scripts unless a separate firmware feature is explicitly created.
