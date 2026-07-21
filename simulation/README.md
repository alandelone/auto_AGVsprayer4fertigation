# ArduRover SITL Simulation Plan

## Purpose

Provide the first simulation path for FEAT-002 without adding ROS2, Raspberry Pi, Jetson, or AI vision to Phase 1.

## Current Status

STATUS: NOT YET INSTALLED IN THIS WORKSPACE

Checked local commands:

```bash
command -v sim_vehicle.py
command -v ardupilot
command -v mavproxy.py
```

Current result: none are installed in the active environment.

## Target Simulator

First candidate: ArduPilot SITL for Rover.

Reason:

- It matches the selected Pixhawk + ArduRover firmware path.
- It can validate mission behavior before live hardware.
- It avoids selecting a full robotics simulator before vehicle dimensions and drive layout are confirmed.

## Minimum Scenario

The FEAT-002 simulation should demonstrate:

1. Rover starts in safe state with spray outputs off.
2. Rover follows a representative mission:
   - staging area.
   - row entry.
   - in-row alignment with spray off.
   - in-row spraying segment.
   - row exit with spray off.
   - return/hold.
3. Mission output commands toggle pump/left/right outputs at segment boundaries.
4. Simulated obstacle/fault behavior causes stop/abort and spray off.
5. Command output/log summary is copied into `stage-gates/active/FEAT-002/04-verification.md`.

## Candidate Setup Commands

These commands are not yet proven in this repository and should be executed in a controlled setup step:

```bash
# candidate only; verify package impact before running on production VPS
# git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git simulation/ardupilot
# cd simulation/ardupilot
# Tools/environment_install/install-prereqs-ubuntu.sh -y
# . ~/.profile
# ./waf configure --board sitl
# ./waf rover
# Tools/autotest/sim_vehicle.py -v Rover --console --map
```

## Repository Rule

Do not commit the full ArduPilot source tree, build outputs, real farm coordinates, telemetry credentials, or hardware secrets into this repository.

If SITL is cloned locally, add it under an ignored path or external workspace after owner approval if outside this repository.
