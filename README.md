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
5. [Demos](#demos)
6. [License](#license)

## Goals of the project
- [x] Manual steering
- [x] Course mapping
- [ ] Simple course following
- [ ] Course mapping with camera
- [ ] Advanced course following with camera
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
- [Small 4-pin I2C Oled screen](https://www.electronicscomp.com/0.91-inch-i2c-iic-128x32-serial-4-pin-oled-display-module-white)

### Power layout
Using driver boards simplifies the power layout, but appropriate connectors are needed. The Jetson could be  powered from the same battery as the rest of the components, but voltage fluctuations could cause instability. High-quality 12V voltage regulator was used to omit potential problems. As maximum voltage of the servo driver is 12V it also needs to be stepped-down in some way. Here is our full power layout:

![image](https://github.com/M1chol/jetson-car/blob/main/images/power.svg)

Circuit breakers were also used for increased safety, marked `BG`, `B1`, `B2`, `B3`. Additionally main power switch was added - marked `O1`.

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

Each section will be expanded on below.

[^2]: DDSM400 Motor driver board code is not provided in the repo. See more below

### Servo driver
The provided code - `servoDriver.ino` implements a simple communication protocol.
1. Feedback enable command `BEG` - `BEG20` enables a  feedback loop with 20 ms interval. Driver will respond with `ACK BEG 20`, and then continuously write `FBK;<x>;<y>` commands containing current angles of both servos.
2. Steering command `CMD<x>;<y>` - `CMD90;90` steers both servos to 90°. Driver will respond with `ACK;90;90` command.
3. Feedback stop command `STP` - pauses the feedback loop. Driver will respond with `ACK STP`
4. Calibration command `CAL` - sets the current position of the servos as the internal 0°. Driver will respond with `ACK CAL`

When the feedback read from servo fails driver will write `FBK_ERR` command (unlikely). This protocol can be tested using `tools/directCom.py` from the Jetson side (see tools section).

### Code that drives the car
> This section will be updated when new modules are implemented.

This section will describe how the `car` package operates. It is responsible for steering and collecting data. Code is built in modules, which are then imported into the `setup.py` file that orchestrates the execution. The flow is separated into two parts:

1. Setup stage
2. Launching workers

Modules implement a class with two public methods, `setup()` and `startWorker()`, corresponding to the two stages of execution.  
- `setup()` launches tasks that prepare the module for actual work. This may include checking if devices are connected, creating files for writing, or opening serial connections. This step is crucial for synchronizing all devices.
- `startWorker()` launches all tasks that need to be parallelized within the module.

Two modules are implemented:

- `steering.py` which handles communication with motor and servo drivers
- `fileHandler.py` which handles saving and parsing streamed data  from the devices to a `NDJSON` format (see `out.txt` in results).

To abstract thread creation, I use Python’s `ThreadPoolExecutor` from `concurrent.futures`.    
Setup schematic:    
    
![image](https://github.com/M1chol/jetson-car/blob/main/images/setup.svg)
    

---
Worker launching schematic; each oval represents a thread inside `ThreadPoolExecutor`:    
    
![image](https://github.com/M1chol/jetson-car/blob/main/images/workers.svg)

In addition to 2 modules `Gamepad` and `VirtualGamepad` classes were implemented. `Gamepad` class handles connecting and reading data from standard X-box game-pad. `VirtualGamepad` class inherits from the `Gamepad` class and was created for autonomous steering commands execution.

### Tools

Tools are small independent programs that were created for testing purposes.

- `directCom.py` - this can be used to manually send commands to both the servos and the motors.
- `testCar.py` - an initialization and small test of steering systems.
- `testMotor.py` - test of each motor independently.
- `screen.py` - script for displaying IP address on small OLED screen connected to pins `3, 4, 5, 6` of the GPIO

### DDSM400 Driver

> This could be changed in the future to simplify the communication protocol.

Right now default factory flashed code provided by Waveshare is being used. It comes with a lot of features, but this project uses only JSON communication over UART. Code can be found on the [Waveshare Wiki](https://www.waveshare.com/wiki/DDSM_Driver_HAT_(B))

## Getting started

```bash
git clone https://github.com/M1chol/jetson-car
cd jetson-car
```

To set up the Jetson, follow the [official](https://developer.nvidia.com/embedded/learn/get-started-jetson-orin-nano-devkit) or [my guide](https://m1chol.github.io/m1/2025-09-22/jetson).
Then use the Arduino IDE to flash the servo driver board with the provided code (`servoDriver.ino`). If you wish that the car should launch automatically you should consider creating a `systemmd` service. To do so you can launch `autostart.sh` script.

```bash
./autostart.sh
```

`autostart.sh`:

- creates a `.venv` and installs the dependencies
- creates `jetson-car-autostart` service file that
  - launches `screen.py` script to display the IP on the screen
  - launches `main.py` to launch the car steering system
- enables the service and reloads the `systemd`

To launch the car manually simply:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Keep in mind that if you do not have a screen connected `jetson-car-autostart` could start error loop. You can also see the logs from the run using `journalctl` command with `-u` flag:

```bash
journalctl -u jetson-car-autostart
```

## Demos

Course mapping:

![image](https://github.com/M1chol/jetson-car/blob/main/images/path_v1.png?raw=true)

In blue driven path reconstructed from sensor data using bicycle model for 2 turning axis. Black labels are speed in m/s at the given point.

## License

This project is licensed under the Apache License, Version 2.0, modified with the Commons Clause. See https://commonsclause.com/ for more information.

[^2]: 
