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
| Waterproof ultrasonic | JSN-SR04T integrated waterproof ultrasonic ranging module | Candidate rugged distance sensor for row following and obstacle detection. |
| Level shifting | 2-channel MOSFET level converter for I2C/serial voltage conversion | Needed when sensor/controller logic levels differ. |
| Pixhawk ultrasonic alternative | GY-US42 I2C Pixhawk/APM ultrasonic ranging module | Alternative ultrasonic sensor; check waterproofing before field use. |

## Spraying And Fertigation Rules

- Spraying is route-defined, not continuous and not applied to every row/plant automatically.
- Some routes may require single-side spraying only.
- Vehicle may traverse rows without spraying when the route definition says no spray.
- Spray/fertigation control must support explicit on/off zones or waypoint-triggered actions.
- Future design must define pump, valve, nozzle, flow rate, pressure, tank, and liquid-level sensing.

## Safety Requirements

- Obstacle avoidance is mandatory.
- Low liquid level detection is required.
- Pump pressure abnormal detection is required.
- Manual override and emergency stop should be specified in technical design.

## Simulation Success Standard

The project can pass FEAT-002 only when custom ArduRover behavior is validated in a simulation environment such as ArduPilot SITL, Gazebo, Webots, or AirSim.
