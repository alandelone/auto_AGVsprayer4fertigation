# Spray Output Contract

## Purpose

Define the Phase 1 pump and valve output behavior for route-defined cucumber spraying/fertigation.

## Output Channels

Recommended logical outputs:

- `pump`: enables pump driver.
- `left_valve`: opens left-side spray/fertigation valve.
- `right_valve`: opens right-side spray/fertigation valve.

Pixhawk relay/servo/PWM pins must only drive an external relay, MOSFET, ESC, or valve driver input. Do not power pump or valve loads directly from Pixhawk GPIO/servo pins.

## Spray Mode Mapping

- `OFF`: pump off, left valve off, right valve off.
- `LEFT`: pump on, left valve on, right valve off.
- `RIGHT`: pump on, left valve off, right valve on.
- `BOTH`: pump on, left valve on, right valve on.

## Segment Boundary Rule

Every route segment must explicitly set its spray state. Do not rely on previous output state.

## Fault Override Rule

Any fault state must force:

- pump off.
- left valve off.
- right valve off.
- operator alert or manual recovery procedure.

## Manual Trigger

Manual fixed-point spraying may be provided by an RC auxiliary switch or Mission Planner relay/servo control, but emergency stop and safety faults still override it.
