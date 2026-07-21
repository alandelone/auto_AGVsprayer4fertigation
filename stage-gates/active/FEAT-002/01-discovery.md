# 01 Discovery

## Feature

FEAT-002: Define autonomous spraying and fertigation requirements.

## Source Material

- `C:\Users\Ling's\Downloads\3D打印无人车自动打药系统.pdf`
- Extracted reference text: `docs/pdf-extract-3d-agv-sprayer.txt`
- Field and hardware reference: `docs/field-reference.md`
- Field image: `docs/images/cucumber-field-row-entrance.jpg`
- Field image: `docs/images/cucumber-field-under-canopy.jpg`

## User Goal

Build a practical, low-cost first-stage autonomous cucumber-farm AGV for automatic spraying/fertigation. The first release should prioritize stable field operation over advanced AI vision.

## Phase 1 Target Architecture

- Use a single Pixhawk flight controller running ArduRover.
- Avoid Raspberry Pi, Jetson, ROS2, and AI vision in Phase 1.
- Use Mission Planner / ArduRover configuration instead of custom Linux robotics code where possible.
- Keep the platform upgradeable for future AI vision, crop scouting, disease detection, or cucumber counting.

## Field Scenario

- Crop: cucumber.
- Environment: outdoor trellis farm with dense overhead vine canopy.
- Travel corridor: center lane between blue trellis frames and side grow bags/planting beds.
- Practical obstacles include trellis posts, irrigation hoses, uneven soil, grass, debris, and low-hanging vines.
- Vehicle should stay inside the center row corridor and avoid damaging side planting areas.

## Hardware Assumptions

- Chassis may use 3D-printed parts where practical.
- Controller: Pixhawk 2.4.8 / PIX 32-bit APM-compatible STM32 flight controller kit.
- Firmware: ArduRover, preferred over PX4 for ground-vehicle support.
- Telemetry: 3DR LoRa 433/915 MHz data radio, with 433 MHz 500 mW candidate module.
- Sensors: 3 to 5 waterproof JSN-SR04T-style ultrasonic sensors.
- Alternative ultrasonic option: GY-US42 I2C Pixhawk/APM ultrasonic ranging module, pending waterproofing check.
- Interface support: 2-channel MOSFET level converter for I2C/serial voltage conversion where required.
- Sensor placement: 1 to 2 left, 1 to 2 right, and 1 front-facing obstacle sensor.
- Navigation: RTK-GPS for macro positioning, ultrasonic row following for local alignment.
- Communication: prefer 915 MHz or 433 MHz telemetry/remote control.
- Avoid 2.4 GHz Wi-Fi, 5.8 GHz video links, and low-mounted UWB in wet dense crop canopy unless antennas are physically elevated.

## Navigation Requirements

- Vehicle should enter cucumber rows using GPS/RTK waypoints.
- Once inside rows, vehicle should maintain centerline using wall-following behavior from left/right ultrasonic distances.
- Cucumber trellis/vegetation is treated as a natural wall.
- Front ultrasonic sensor should detect dead ends, workers, or unexpected obstacles and trigger stop/brake behavior.
- GPS drift under wet canopy must not cause the vehicle to crush plants.

## Spraying/Fertigation Requirements

- Spraying/fertigation output should be controllable by Pixhawk-compatible relay, servo, or pump-control channel.
- System should support manual remote trigger for fixed-point spraying.
- Spraying is route-defined, not continuous, and not automatically applied to every plant.
- Some routes may require single-side spraying only.
- Vehicle may travel through a row without spraying when the route definition marks that segment as transit-only.
- Technical design must support waypoint or route-segment based spray enable/disable commands.
- Future execution design must define pump, valve, nozzle, tank, pressure, flow-rate, and dosing details.
- Low liquid level, pump fault, or blocked nozzle behavior remains open and must be specified before implementation.

## Communication Constraints

- Wet cucumber leaves and spray mist strongly attenuate high-frequency signals.
- 915 MHz or 433 MHz is preferred because lower frequency signals diffract better around wet vegetation.
- High-frequency systems such as UWB, 2.4 GHz, and 5.8 GHz should only be used with elevated antennas or clear line-of-sight.

## Safety Requirements

- Obstacle avoidance is mandatory.
- Low liquid level detection is required.
- Pump pressure abnormal detection is required.
- Manual override and emergency stop should be specified in technical design.

## Explicit Non-Goals For Phase 1

- No ROS2 autonomy stack.
- No Raspberry Pi or Jetson dependency.
- No depth camera requirement.
- No AI disease detection, cucumber counting, or robotic harvesting.
- No custom real-time stereo vision pipeline.

## Future Phase Candidates

- Add Raspberry Pi 5 or NVIDIA Jetson as an edge AI computer.
- Add stereo depth camera such as OAK-D or Intel RealSense D435/D455 for crop scouting.
- Use MAVLink to let the AI computer send high-level commands to Pixhawk.
- Train YOLO-style models for cucumber counting or disease detection.

## Risks And Unknowns

- Exact crop row width, plant height, trellis geometry, and ground conditions are unknown.
- Actual motor driver, steering type, pump, tank, nozzle, and power system are not selected.
- ArduRover ultrasonic wall-following parameter support must be confirmed for the chosen firmware version.
- Waterproof ultrasonic performance must be tested against leaves, mist, mud, and angled trellis surfaces.
- Safety interlocks for emergency stop, manual override, low battery, low liquid, and pump failure are not yet fully defined.
- Pump pressure abnormal detection method is not selected.
- Simulation environment is not selected; candidates include ArduPilot SITL, Gazebo, Webots, or AirSim.

## Success Criteria

- Phase 1 requirements are accepted by the human owner.
- Hardware bill-of-material direction is clear enough for technical design.
- Navigation strategy is fixed as Pixhawk + ArduRover + RTK macro navigation + ultrasonic row following.
- Phase 1 non-goals are explicitly excluded to prevent scope creep.
- Custom ArduRover behavior can pass in a simulation environment such as ArduPilot SITL, Gazebo, Webots, or AirSim.
