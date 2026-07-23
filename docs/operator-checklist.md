# Operator Checklist & Field Protocol

## Preflight Hardware Checklist (Automated & Human)

Prevent execution if hardware, power, sensors, or communications are unverified:
- [ ] **E-Stop Cutoff:** Confirm physical E-stop cuts motor and pump power independently.
- [ ] **RC Override:** Confirm RC/manual override has control authority over AUTO mode.
- [ ] **Tank & Liquid Level:** Confirm liquid level sensor reports adequate fluid (above minimum threshold).
- [ ] **Pressure Sensor Idle State:** Confirm pressure sensor reports normal idle reading (0 Bar / 0 PSI).
- [ ] **Nozzles & Hoses:** Confirm nozzles and hoses are clean, unblocked, and leak-free.
- [ ] **Ultrasonic Distance Sensors:** Confirm left, right, and front ultrasonic distance readings are plausible.
- [ ] **Positioning & Navigation:** Confirm RTK/GPS fix status (3D/Float/Fixed) and verify IMU + Wheel Odometer health.
- [ ] **Telemetry Link:** Confirm 433/915 MHz telemetry radio RSSI is stable (> 50%).
- [ ] **Preflight Automated Gate:** Verify that software preflight checklist returns `STATUS: OK` before arming.

## Dosing Calibration Verification

Ensure precise application (L/m² or L/m) rather than uncalibrated water output:
- [ ] **Catch-Cup Catch Test:** Run 60-second pump calibration test into catch cups; verify flow rate matches rated 0.20 GPM @ 40 PSI within ±5%.
- [ ] **Pressure-Flow Curve Match:** Confirm operating pressure matches target nozzle operating pressure.
- [ ] **Speed-Synchronized Dosing:** Verify pump PWM / valve timing scales dynamically with AGV forward ground speed.

## Start Mission & Position Confidence Gate

- [ ] **Safe Start State:** Start in manual/HOLD-safe condition with pump power disabled.
- [ ] **Arming Gate:** Arm only after all preflight, calibration, and safety checks pass.
- [ ] **Position Confidence Verification:** Verify that RTK GPS, ultrasonic row-following, and wheel odometer agree on row entry coordinates before entering `AUTO` mode.
- [ ] **Row Entry Monitoring:** Enter `AUTO` mode only with operator actively watching row entrance. Keep spray disabled until designated row spray segment boundary.

## During Mission & Active Failsafes

- [ ] Watch front obstacle distance and row-centering behavior.
- [ ] Monitor **Position Confidence Gate**: if RTK fix drops under dense leaf canopy, ensure system switches smoothly to IMU + Wheel Odometer dead reckoning.
- [ ] Abort immediately if position variance exceeds 0.3 m sideways drift.
- [ ] Stop immediately if the rover approaches trellis posts, ground hoses, grow bags, or field workers.
- [ ] Stop on abnormal pressure, low liquid level, or sensor degradation.

## Recovery & Resume Protocol (Post-Fault / Post-Pause)

- [ ] Clear fault state and verify root cause on operator Ground Control Station (GCS).
- [ ] Re-run Preflight Hardware Checklist.
- [ ] Re-prime pump and bleed air if system ran dry or was serviced.
- [ ] Select **Resume Mission**: Vehicle navigates to last uncompleted waypoint, verifies position confidence, and resumes spraying at exact row segment boundary (duplicate-spray protection enabled).

## End of Mission & Telemetry Log Archive

- [ ] Force spray `OFF` before row exit, RTL, abort, or mission end.
- [ ] Disarm vehicle before servicing pump, valves, tank, or nozzles.
- [ ] **Download Complete Mission Telemetry Log:** Export and archive `.tlog` / `.bin` black-box telemetry file detailing RTK fix status, position confidence metrics, pressure, valve actions, and fault occurrences for review.
