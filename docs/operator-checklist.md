# Operator Checklist

## Pre-Run

- Confirm physical E-stop cuts motor and pump power.
- Confirm RC/manual override works before AUTO mode.
- Confirm pump power is disabled until route/spray checks pass.
- Confirm tank/liquid level is above minimum.
- Confirm pressure sensor/switch reports normal idle state.
- Confirm nozzles and hoses are not blocked or leaking.
- Confirm left, right, and front ultrasonic readings are plausible.
- Confirm RTK/GPS status is acceptable for row entry.
- Confirm telemetry link is stable on selected 433/915 MHz radio.
- Confirm route uses fake/test coordinates in simulation and real coordinates only on the operator device, not committed to repository.

## Start Mission

- Start in manual/HOLD-safe condition.
- Arm only after E-stop, RC override, liquid, pressure, and sensor checks pass.
- Enter AUTO only with operator watching the row entry.
- Keep spray disabled until the intended segment boundary.

## During Mission

- Watch front obstacle distance and row-centering behavior.
- Stop if the rover approaches trellis posts, hoses, grow bags, or workers.
- Stop if spray appears on a transit-only segment.
- Stop on abnormal pressure, low liquid, or unstable ultrasonic readings.

## End / Abort

- Force spray `OFF` before row exit, RTL, abort, or mission end.
- Disarm before servicing pump, valves, tank, or nozzles.
- Record failures and command output in `stage-gates/active/FEAT-002/04-verification.md`.
