# Jetson powered autonomus car
TODO

## Hardware
Here is the list of all the main components used for this project. That is components, that are requiered for the current state of the software. The links are for your convenience only, we are in no way afiliated with the sellers.
- [Jetson Orin Nano Developer Kit](https://kamami.pl/en/jetson-development-kits/1184505-nvidia-jetson-orin-nano-8gb-development-kit-development-kit-with-arm-cortex-a78ae-8gb-ram-5906623468744.html?SubmitCurrency=1&id_currency=1)
- [4x DDSM400 Wheel Servo](https://www.waveshare.com/ddsm400.htm)
- [DDSM Driver Board](https://www.waveshare.com/product/ddsm-driver-hat-b.htm)
- [2x Servo Motor With High Precision Magnetic Encoder](https://www.waveshare.com/product/st3215-hs-servo-motor.htm)
- [Servo Driver Board](https://www.waveshare.com/servo-driver-with-esp32.htm)
- 12V battery (see power layout section)

### Optional but recomanded
- [4x Suspension for DDSM400](https://www.waveshare.com/UGV-Suspension-B.htm)

## Power layout
The use of driver boards simplify the powering layout, but apropriate connectors are needed. Jetson can be safely powered from the same battery as the rest of the components,
but needs a good quality regulator in between. Currently looking into [DFRobot](https://www.dfrobot.com/product-752.html) (this section will be expanded).

Device  | Voltage range | Max current | Connector
------- | ------------- | ----------- | ---------
Servo driver board | DC 6~12V | 2.4A | 5.5*2.1 DC power jack
DDSM400 (single) | DC 9~28V DC [^1] | 2.4A | PH2.0*4P
DDSM400 Driver board | DC 9V~28V | | 5.5x2.5 DC power jack or XT60
Jetson Orin Nano | DC 9~20 V | | 5.5x2.5 DC power jack

[^1]: handled by driver board

## Getting started
TODO

https://developer.nvidia.com/embedded/learn/get-started-jetson-orin-nano-devkit

## Software
TODO

## License
This project is licensed under the Apache License, Version 2.0 modified with Commons Clause. See https://commonsclause.com/ for more info.
