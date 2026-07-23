# Field And Hardware Reference

## Source Images

- `docs/images/cucumber-field-row-entrance.jpg`: cucumber farm row entrance with trellis posts, center grass/dirt lane, side grow bags, and irrigation lines.
- `docs/images/cucumber-field-under-canopy.jpg`: under-canopy view showing dense overhead vines, narrow travel lane, blue trellis frames, ground hose, and side planting beds.

## Field Scenario

- Crop: cucumber.
- Environment: outdoor cucumber farm with trellis frames and dense overhead canopy.
- Travel path: AGV should move through the center lane between rows.
- Navigation challenge: canopy and wet leaves may weaken GPS/high-frequency radio; ground hoses, uneven soil, and trellis posts are practical obstacles.
- Row-following assumption: trellis/plant rows can act as left/right references for ultrasonic wall-following.

## Candidate Hardware

| Component | Candidate Item | Notes |
| --- | --- | --- |
| Telemetry radio | 3DR LoRa data radio 433/915 MHz, 433 MHz 500 mW, claimed 2 km | Preferred low-frequency link for wet crop canopy. |
| Flight controller | Pixhawk 2.4.8 / PIX 32-bit APM-compatible STM32 controller kit | Phase 1 controller running ArduRover. |
| Navigation / Dead Reckoning | Pixhawk internal IMU + Wheel Odometer / Rotary Encoder | Maintains position estimation when RTK GPS is degraded by overhead canopy. |
| Waterproof ultrasonic | JSN-SR04T integrated waterproof ultrasonic ranging module | Candidate rugged distance sensor for row following and obstacle detection. |
| Level shifting | 2-channel MOSFET level converter for I2C/serial voltage conversion | Needed when sensor/controller logic levels differ. |
| Pixhawk ultrasonic alternative | GY-US42 I2C Pixhawk/APM ultrasonic ranging module | Alternative ultrasonic sensor; check waterproofing before field use. |

## Spraying And Fertigation Rules

- Spraying is route-defined, not continuous and not applied to every row/plant automatically.
- Some routes may require single-side spraying only.
- Vehicle may traverse rows without spraying when the route definition says no spray.
- Spray/fertigation control must support explicit on/off zones or waypoint-triggered actions.
- **Dosing Calibration Loop:** Flow-rate vs speed calibration, catch-cup volumetric verification, and pressure-flow curves to guarantee precise application per square meter (L/m² or L/m), preventing uncalibrated over/under spraying.

## Advanced Navigation & Position Confidence

- **IMU / Wheel Odometer Dead Reckoning:** When RTK GPS signal is weakened or temporarily lost under dense cucumber leaf canopy or near metallic trellis posts, the system relies on fused IMU and wheel speed odometry to maintain continuous position estimation.
- **Position Confidence Gate:** Cross-validate RTK GPS, ultrasonic row-following (left/right distance to crop beds), and wheel odometer. If position confidence drops below safety threshold (e.g. RTK fix degrades + ultrasonic disagreement > max tolerance), trigger automatic speed reduction, HOLD mode, or safe mission abort.

## Preflight & Hardware Safeguards

- **Preflight Hardware Checklist:** Automated and manual preflight verification before disarming/starting AUTO mode. Prevent execution if sensors, pressure idle readings, liquid level, battery voltage, relay state, E-stop, or telemetry link are unverified or faulty.

## Operational Recovery & Telemetry Logging

- **Recovery / Resume Policy:** Safe mission resumption protocol following a fault or manual pause. Includes clearing fault state, re-priming pump/valves, verifying position confidence, and resuming from the nearest safe waypoint with duplicate-spray protection.
- **Complete Mission Telemetry Log:** High-frequency black-box logging of all mission events (RTK fix quality, ultrasonic distance, wheel speed, position confidence gate metrics, pump pressure, valve state transitions, obstacle stops, manual overrides) for post-mission playback and failure root-cause analysis.

## Safety Requirements

- Obstacle avoidance is mandatory.
- Low liquid level detection is required.
- Pump pressure abnormal detection is required.
- Manual override and emergency stop should be specified in technical design.

## Simulation Success Standard

The project can pass FEAT-002 only when custom ArduRover behavior is validated in a simulation environment such as ArduPilot SITL, Gazebo, Webots, or AirSim.
