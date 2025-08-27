# Jetson-Powered Autonomous Car
> [!WARNING]
> This repository is under active development! This file explains the overall idea of the project and may include information about systems that are not yet implemented. See the “Goals of the project” section below for the current implementation status.

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
- [ ] Course mapping
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
- 12V battery (see power layout section)

### Optional but recommended
- [4x Suspension for DDSM400](https://www.waveshare.com/UGV-Suspension-B.htm)
- 512GB M.2 NVMe SSD

### Power layout
The use of driver boards simplifies the power layout, but appropriate connectors are needed. The Jetson can be safely powered from the same battery as the rest of the components, but requires a high-quality regulator in between. Currently considering [DFRobot](https://www.dfrobot.com/product-752.html) (this section will be expanded).

Device  | Voltage range | Max current | Connector
------- | ------------- | ----------- | ---------
Servo (single) | 6–12.6V | 2.4A | PH2.0×3P
Servo driver board | DC 6–12V | 4.8A[^1] | 5.5×2.1 mm DC power jack
DDSM400 (single) | DC 9–28V | 2.4A | PH2.0×4P
DDSM400 driver board | DC 9–28V | 9.6A[^1] | 5.5×2.5 mm DC power jack or XT60
Jetson Orin Nano | DC 9–20V | ~2.3A | 5.5×2.5 mm DC power jack

![image](https://github.com/M1chol/jetson-car/blob/main/images/power.svg)

[^1]: Calculated by multiplying the maximum current by the number of devices.

## Software
> This section will be expanded

There are two main parts of the software:
1. Arduino code for the driver boards
2. Python code for the Jetson

## Getting started
> This section will be expanded

To set up the Jetson, please follow the [official guide](https://developer.nvidia.com/embedded/learn/get-started-jetson-orin-nano-devkit).
Then use the Arduino IDE to flash the driver boards with the provided code. The last step is to set up the Python code on your Jetson device:
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
