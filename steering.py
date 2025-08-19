import evdev
import threading
import serial
import serial.tools.list_ports
import os
import json
from time import sleep
# import time


class Steering:
    def __init__(self) -> None:
        self._serialServo = None
        self._serialMotor = None
        self._gamepad = None
        self._buttonMap = {304: "A", 305: "B", 307: "X", 308: "Y"}
        self._buttonState = {"A": False, "B": False, "X": False, "Y": False}
        self._stopEvent = threading.Event()
        self._currentAngle = 90
        self._currentSpeed = 0
        self._currentBreak = 0
        self._currentGas = 0
        self._config = None
        with open("config.json") as file:
            self._config = json.load(file)
        if not self._config:
            print("[STEER] Config file faild to load")
            raise Exception()
        self.DEBUG = False
        self.MAX_ANGLE = self._config["MAX_ANGLE"]
        self.MAX_SPEED = self._config["MAX_SPEED"]

    def openSerial(self) -> str:
        servoPort = None
        motorPort = None
        ports = serial.tools.list_ports.comports()
        for _port in ports:
            if (
                _port.vid == self._config["SERVO_VID"]
                and _port.pid == self._config["SERVO_PID"]
            ):
                servoPort = _port.device
            elif (
                _port.vid == self._config["MOTOR_VID"]
                and _port.pid == self._config["MOTOR_PID"]
            ):
                motorPort = _port.device
        if not all([servoPort, motorPort]):
            print(
                f"[STEER] failed to find some hardware{' (motor driver)' if not motorPort else ''}{' (servo driver)' if not servoPort else ''}"
            )
            return False
        self._serialServo = serial.Serial(
            servoPort, baudrate=115200, timeout=1, dsrdtr=False, rtscts=False
        )
        self._serialMotor = serial.Serial(
            motorPort, baudrate=115200, timeout=1, dsrdtr=False, rtscts=False
        )
        self._serialServo.setRTS(False)
        self._serialServo.setDTR(False)
        self._serialMotor.setRTS(False)
        self._serialMotor.setDTR(False)
        print(
            f"[STEER] Serial connected\n[STEER]\t- motor driver on {motorPort}\n[STEER]\t- servo driver on {servoPort}"
        )
        return True

    def getGamePad(self) -> evdev.InputDevice:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for i, dev in enumerate(devices):
            print(f"[STEER] Device {i}: {dev.name} na {dev.path}")
        selectedDevice = None
        if not devices:
            print("[STEER] Failed to find gamepad...")
            return False
        elif len(devices) > 1:
            selectedDevice = evdev.list_devices[
                int(input("[STEER] Multiple gamepads select one: "))
            ]
        else:
            selectedDevice = evdev.list_devices()[0]

        self.gamepad = evdev.InputDevice(selectedDevice)
        return True

    def writeMotor(self, command: str) -> None:
        self._serialMotor.write(command.encode() + b"\n")

    def _motorSetup(self) -> bool:
        print("[STEER] Starting motor setup")
        for i in range(4):
            # Check motor status
            self.writeMotor(self.generateMotorCommand("CMD_DDSM_INFO", id=i + 1))
            if t := self._serialMotor.readline().decode("utf-8").strip():
                print(f"[STEER] Motor {i + 1} ok")
            else:
                print(f"[STEER] Motor {i + 1} failed to respond")
                return False
            # Enable motor
            self.writeMotor(self.generateMotorCommand("CMD_CHANGE_Enable", id=i + 1))
            self._serialMotor.readline().decode("utf-8").strip()
            # Change mode to keep speed
            self.writeMotor(
                self.generateMotorCommand("CMD_CHANGE_MODE", id=i + 1, mode=2)
            )
            self._serialMotor.readline().decode("utf-8").strip()
        print("[STEER] Finished motor setup")
        return True

    def setup(self):
        if not self.getGamePad():
            return None
        if not self.openSerial():
            return None
        if not self._motorSetup():
            return None
        return self

    def updateGamepad(self) -> None:
        print("[STEER] updateGamepad worker started")
        for event in self.gamepad.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                button_name = self._buttonMap.get(event.code)
                if button_name:
                    self._buttonState[button_name] = event.value == 1
                    if button_name == "B" and event.value == 1:
                        print("[STEER] Close button pressed, quiting...")
                        self.stop()
            elif event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_X:
                    self._currentAngle = (
                        event.value
                        / self._config["PAD_READ_TURN"]
                        * self._config["MAX_ANGLE"]
                        + 90
                    )
                if event.code == evdev.ecodes.ABS_Z:
                    self._currentBreak = (
                        event.value
                        / self._config["PAD_READ_SPEED"]
                        * self._config["MAX_SPEED"]
                    )
                    self._currentSpeed = self._currentGas - self._currentBreak
                if event.code == evdev.ecodes.ABS_RZ:
                    self._currentGas = (
                        event.value
                        / self._config["PAD_READ_SPEED"]
                        * self._config["MAX_SPEED"]
                    )
                    self._currentSpeed = self._currentGas - self._currentBreak
            if self._stopEvent.is_set():
                break

    def writeSerialMotor(self) -> None:
        print("[STEER] writeSerialMotor worker started")
        lastSpeed = self._currentSpeed
        while not self._stopEvent.is_set():
            if self._currentSpeed != lastSpeed:
                value = self._currentSpeed
                for i in range(4):
                    self.writeMotor(
                        self.generateMotorCommand("CMD_DDSM_CTRL", id=i + 1, cmd=value)
                    )
            lastSpeed = self._currentSpeed
            sleep(0.1)

    def writeSerialServo(self) -> None:
        print("[STEER] writeSerialServo worker started")
        lastAngle = self._currentAngle
        while not self._stopEvent.is_set():
            if self._currentAngle != lastAngle:
                command = f"CMD{self._currentAngle:.2f};{180 - self._currentAngle:.2f}"
                self._serialServo.write(command.encode() + b"\n")
            lastAngle = self._currentAngle
            sleep(0.1)

    def readSerial(self) -> None:
        print("[STEER] readSerial worker started")
        # while self._stopEvent.is_set():
        #     self._serialMotor.readline()

    def printData(self) -> None:
        while not self._stopEvent.is_set():
            os.system("clear")
            print(f"Gas/Brake: {self._currentSpeed}\n Angle: {self._currentAngle}")
            print(
                f"A: {self._buttonState['A']}\nB: {self._buttonState['B']}\nX: {self._buttonState['X']}\nY: {self._buttonState['Y']}"
            )
        os.system("clear")

    def startWorker(self, executor) -> None:
        executor.submit(self.writeSerialServo)
        executor.submit(self.writeSerialMotor)
        executor.submit(self.readSerial)
        executor.submit(self.updateGamepad)
        if self.DEBUG:
            executor.submit(self.printData)

    def stop(self) -> None:
        command = "CMD90;90"
        for i in range(4):
            self.generateMotorCommand("CMD_CHANGE_Disable", id=i + 1)
        self._serialServo.write(command.encode() + b"\n")
        self._stopEvent.set()
        print("[STEER] requested thread close")

    def generateMotorCommand(self, cmd_name: str, **kwargs) -> str:
        if cmd_name not in self._config["command_map"]:
            raise ValueError(f"Unknown command: {cmd_name}")
        command = self._config["command_map"][cmd_name].copy()
        command.update(kwargs)
        return json.dumps(command)

    def getStatus(self):
        return self._stopEvent.is_set()


if __name__ == "__main__":
    print("This file should not be run directly. Please run main.py")
