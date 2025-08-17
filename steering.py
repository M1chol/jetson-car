import glob
import evdev
import threading
import serial
import serial.tools.list_ports
import os
import json


class Steering:
    def __init__(self):
        self._serial = None
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
        port = None
        ports = serial.tools.list_ports.comports()
        for _port in ports:
            if (
                _port.vid == self._config["SERVO_VID"]
                and _port.pid == self._config["SERVO_PID"]
            ):
                port = _port.device
        if not port:
            print("[STEER] Servo driver not found")
            return False
        self.serial = serial.Serial(
            port, baudrate=115200, timeout=1, dsrdtr=False, rtscts=False
        )
        self.serial.setRTS(False)
        self.serial.setDTR(False)
        print(f"[STEER] Serial connected to {port}")
        return True

    def getGamePad(self) -> evdev.InputDevice:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for i, dev in enumerate(devices):
            print(f"[STEER] Urządzenie {i}: {dev.name} na {dev.path}")
        selectedDevice = None
        if not devices:
            print("[STEER] Nie znaleziono poprawnego kontrolera...")
            return False
        elif len(devices) > 1:
            selectedDevice = evdev.list_devices[
                int(input("[STEER] Wybierz urzadzenie: "))
            ]
        else:
            selectedDevice = evdev.list_devices()[0]

        self.gamepad = evdev.InputDevice(selectedDevice)
        return True

    def setup(self):
        print("[STEER] Starting steering setup")
        serialStatus = self.openSerial()
        gamepadStatus = self.getGamePad()
        if not serialStatus or not gamepadStatus:
            print("[STEER] Setup not completed quiting")
            self._stopEvent.set()
            return None
        return self

    def updateGamepad(self):
        for event in self.gamepad.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                button_name = self._buttonMap.get(event.code)
                if button_name:
                    self._buttonState[button_name] = event.value == 1
                    if button_name == "B" and event.value == 1:
                        print("[STEER] Close button pressed, quiting...")
                        # TODO: set the defaoult angle and speed for car
                        self._stopEvent.set()
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

    def writeSerial(self):
        # TODO: Write commands to the device
        pass

    def printData(self):
        while not self._stopEvent.is_set():
            os.system("clear")
            print(f"Gas/Brake: {self._currentSpeed}\n Angle: {self._currentAngle}")
            print(
                f"A: {self._buttonState['A']}\nB: {self._buttonState['B']}\nX: {self._buttonState['X']}\nY: {self._buttonState['Y']}"
            )
        os.system("clear")

    def startWorker(self, executor):
        # executor.submit(self.writeSerial)
        executor.submit(self.updateGamepad)
        if self.DEBUG:
            executor.submit(self.printData)

    def stop(self):
        self._stopEvent.set()
        print("[STEER] Thread closed")


if __name__ == "__main__":
    print("This file should not be run directly. Please run main.py")
