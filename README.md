# Jetson-Powered Autonomous Car
> [!WARNING]
> This repository is under active development. This file explains the overall idea of the project and may include information about systems that are not yet implemented. See the “Goals of the project” section below for the current implementation status.

This repository contains code that enables you to build a model of an autonomous car. The car collects various data such as:
1. Steering angle
2. Current driving speed
3. Camera view

Data collected from wheel encoders and servos, providing real feedback, can be used for systems like PID control, course correction, and machine learning.

**Table of contents**
1. [Goals of the project](#goals-of-the-project)
2. [Hardware](#hardware)
3. [Software](#software)
4. [Getting started](#getting-started)
5. [License](#license)

## Goals of the project
- [x] Manual steering
- [ ] Course mapping (almost here !!!)
- [ ] Simple course following
- [ ] Advanced course following
- [ ] Course navigation

*Implemented functionalities are marked.*

## Hardware
Here is the list of the main components used for this project. These are the components required for the current state of the software. The links are provided for your convenience only; I am in no way affiliated with the sellers.
- [Jetson Orin Nano Developer Kit](https://kamami.pl/en/jetson-development-kits/1184505-nvidia-jetson-orin-nano-8gb-development-kit-development-kit-with-arm-cortex-a78ae-8gb-ram-5906623468744.html?SubmitCurrency=1&id_currency=1)
- [4x DDSM400 Wheel Servo](https://www.waveshare.com/ddsm400.htm)
- [DDSM Driver Board](https://www.waveshare.com/product/ddsm-driver-hat-b.htm)
- [2x Servo Motor with High-Precision Magnetic Encoder](https://www.waveshare.com/product/st3215-hs-servo-motor.htm)
- [Servo Driver Board](https://www.waveshare.com/servo-driver-with-esp32.htm)
- 6S (22.2V) LiPo battery
- [12 V power regulator](https://www.victronenergy.pl/dc-dc-converters/orion-24-12-5-10)

### Optional but recommended
- [4x Suspension for DDSM400](https://www.waveshare.com/UGV-Suspension-B.htm)
- 512 GB M.2 NVMe SSD

### Power layout
Using driver boards simplifies the power layout, but appropriate connectors are needed. The Jetson could be  powered from the same battery as the rest of the components, but voltage fluctuations could cause instability. High-quality 12V voltage regulator was used to omit potential problems. As maximum voltage of the servo driver is 12V it also needs to be stepped-down in some way. Here is our full power layout:

![image](https://github.com/M1chol/jetson-car/blob/main/images/power.svg)

Circuit breakers were also used increased safety, marked `BG`, `B1`, `B2`, `B3`. Additionally main power switch was added - marked `O1`.

Device  | Voltage range | Max current | Connector
------- | ------------- | ----------- | ---------
Servo (single) | DC 6–12.6 V | 2.4 A | PH2.0×3P
Servo driver board | DC 6–12 V | 4.8 A[^1] | 5.5×2.1 mm DC power jack
DDSM400 (single) | DC 9–28 V | 2.4 A | PH2.0×4P
DDSM400 driver board | DC 9–28 V | 9.6 A[^1] | 5.5×2.5 mm DC power jack or XT60
Jetson Orin Nano | DC 9–20 V | ~2.3 A | 5.5×2.5 mm DC power jack

[^1]: Calculated by multiplying the maximum current by the number of devices.

## Software
This repository holds all the software needed to recreate the described project fully[^2]: 

1. Arduino code for servo driver board
2. Python code for running the car
3. Python tooling for testing individual systems
4. Bash script for automating the installation process

Each section will be expanded on bellow.

[^2]: DDSM400 Motor driver board code is not provided in the repo. See more bellow

### Servo driver
The provided code - `servoDriver.ino` implements a simple communication protocol.
1. Feedback enable command `BEG` - `BEG20` enables a  feedback loop with 20 ms interval. Driver will respond with `ACK BEG 20`, and then continuously write `FBK;<x>;<y>` commands containing current angles of both servos.
2. Steering command `CMD<x>;<y>` - `CMD90;90` steers both servos to 90°. Driver will respond with `ACK;90;90` command.
3. Feedback stop command `STP` - pauses the feedback loop. Driver will respond with `ACK STP`
4. Calibration command `CAL` - sets the current position of the servos as the internal 0°. Driver will respond with `ACK CAL`

When the feedback read from servo fails driver will write `FBK_ERR` command (unlikely). This protocol can be tested using `tools/directCom.py` from the Jetson side (see tools section).

### Running the car
> This whole section is out of date and will be updated in the future.
>
> This section will be updated when new modules are implemented.

The Python code is built as modules, which are then imported into the `setup.py` file that orchestrates execution. The flow is separated into two parts:
1. Setup stage
2. Launching workers

Every module implements a class with two methods, `setup()` and `startWorker()`, corresponding to the two stages of execution.  
- `setup()` launches tasks that prepare the module for actual work. This may include checking if devices are connected, creating files for writing, or opening serial connections. This step is crucial for synchronizing all devices.
- `startWorker()` launches all tasks that need to be parallelized within the module.

To abstract thread creation, I use Python’s `ThreadPoolExecutor` from `concurrent.futures`.    
Setup schematic:    
    
![image](https://github.com/M1chol/jetson-car/blob/main/images/setup.svg)
    

---
Worker launching schematic; each oval represents a thread inside `ThreadPoolExecutor`:    
    
![image](https://github.com/M1chol/jetson-car/blob/main/images/workers.svg)

### Tools

> TODO

List of tools:

- directCom.py
- testCar.py
- testMotor.py
- screen.py

### `autostart.sh`

> TODO

`autostart.sh` automates creating service to start the project with the system. 

### DDSM400 Driver

> This could be changed in the future to simplify the communication protocol.

Right now default factory flashed code provided by Waveshare is being used. It comes with a lot of features, but this project uses only JSON communication over UART. Code can be found on the [Waveshare Wiki](https://www.waveshare.com/wiki/DDSM_Driver_HAT_(B))

### 

## Getting started

> This section will be expanded.

To set up the Jetson, follow the [official](https://developer.nvidia.com/embedded/learn/get-started-jetson-orin-nano-devkit) or [my guide](https://m1chol.github.io/m1/2025-09-22/jetson).
Then use the Arduino IDE to flash the servo driver board with the provided code (`servoDriver.ino`). The last step is to set up the Python code on your Jetson device:

```bash
git clone https://github.com/M1chol/jetson-car
cd jetson-car
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## License
This project is licensed under the Apache License, Version 2.0, modified with the Commons Clause. See https://commonsclause.com/ for more information.

*Proofread with AI assistance*

[^2]: 
