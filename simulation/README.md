# ArduRover SITL Simulation Plan

## Purpose

Provide the first simulation path for FEAT-002 without adding ROS2, Raspberry Pi, Jetson, or AI vision to Phase 1.

## Current Status

STATUS: INSTALLED AND BUILT LOCALLY

Checked local commands:

```bash
command -v sim_vehicle.py
command -v ardupilot
command -v mavproxy.py
```

Current result: ArduPilot SITL was cloned under the ignored path `simulation/ardupilot/`, prerequisites were installed, Rover configured for `sitl`, and `build/sitl/bin/ardurover` was built and launched successfully. `mavproxy.py` is not required for the headless proof run.

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

## Proven Setup Commands

These commands were executed successfully in this workspace:

```bash
git clone --depth 1 --recurse-submodules --shallow-submodules https://github.com/ArduPilot/ardupilot.git simulation/ardupilot
cd simulation/ardupilot
Tools/environment_install/install-prereqs-ubuntu.sh -y
sudo apt-get install -y python3-empy python3-pexpect python3-future python3-lxml python3-numpy python3-pyparsing
PYTHONNOUSERSITE=1 /usr/bin/python3 ./waf configure --board sitl
PYTHONNOUSERSITE=1 /usr/bin/python3 ./waf rover
```

Headless launch proof:

```bash
timeout 8s build/sitl/bin/ardurover --model rover --speedup 1 --sim-address=127.0.0.1 -I1 --home -35.363261,149.16523,584.0,353.0
```

Observed output:

```text
Setting SIM_SPEEDUP=1.000000
Home: -35.363261 149.165230 alt=584.000000m hdg=353.000000
Starting sketch 'Rover'
Starting SITL input
Using Irlock at port : 9015
Using \clock topic for DDS timing: disabled
bind port 5770 for SERIAL0
SERIAL0 on TCP port 5770
Waiting for connection ....
ARDUROVER_EXIT=124
```

`ARDUROVER_EXIT=124` is expected for this proof because `timeout` stopped the long-running simulator after startup was confirmed.

## Repository Rule

Do not commit the full ArduPilot source tree, build outputs, real farm coordinates, telemetry credentials, or hardware secrets into this repository.

If SITL is cloned locally, add it under an ignored path or external workspace after owner approval if outside this repository.
