import evdev
from time import sleep
import os

class Gamepad:

    def __init__(self, config, debug: bool = False) -> None:
        self.__buttonMap = {304: "A", 305: "B", 307: "X", 308: "Y"}
        self.__buttonState = {"A": False, "B": False, "X": False, "Y": False}
        self.__gamepad = None
        self.currentAngle = 0
        self.currentSpeed = 0
        self.currentBreak = 0
        self.currentGas = 0
        self.__config = config
        self.__DEBUG = debug

    def getGamePad(self) -> bool:
        device_paths = evdev.list_devices()
        timeout = 0
        sleep_time = 5
        while not device_paths:
            print(f"[STEER] Failed to find gamepad... try {timeout//sleep_time}/{self.__config["PAD_TIMEOUT"]//sleep_time}")
            if timeout >= self.__config["PAD_TIMEOUT"]:
                return False
            timeout += sleep_time
            sleep(sleep_time)
            device_paths = evdev.list_devices()

        for i, path in enumerate(device_paths):
            dev = evdev.InputDevice(path)
            print(f"[STEER] Device {i}: {dev.name} at {dev.path}")

        if len(device_paths) > 1:
            print("[STEER] More then 1 gamepad detected, choosing first one")
        selected_path = device_paths[0]
        self.__gamepad = evdev.InputDevice(selected_path)
        return True
    
    def updateGamepad(self) -> None:
        print("[STEER] updateGamepad worker started")
        for event in self.__gamepad.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                button_name = self.__buttonMap.get(event.code)
                if button_name:
                    self.__buttonState[button_name] = event.value == 1
                    if button_name == "B" and event.value == 1:
                        print("[STEER] Close button pressed, quiting...")
                        self.stop()
            elif event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_X:
                    self.currentAngle = (
                        event.value
                        / self.__config["PAD_READ_TURN"]
                        * self.__config["MAX_ANGLE"]
                    )
                if event.code == evdev.ecodes.ABS_Z:
                    self.currentBreak = (
                        event.value
                        / self.__config["PAD_READ_SPEED"]
                        * self.__config["MAX_SPEED"]
                    )
                    self.currentSpeed = self.currentGas - self.currentBreak
                if event.code == evdev.ecodes.ABS_RZ:
                    self.currentGas = (
                        event.value
                        / self.__config["PAD_READ_SPEED"]
                        * self.__config["MAX_SPEED"]
                    )
                    self.currentSpeed = self.currentGas - self.currentBreak
            if self._stopEvent.is_set():
                break

    def printData(self) -> None:
        while not self._stopEvent.is_set():
            os.system("clear")
            print(
                f"Gas/Brake: {self.currentSpeed:2.f}\n Angle: {self.currentAngle:.2f}"
            )
            print(
                f"A: {self.__buttonState['A']}\nB: {self.__buttonState['B']}\nX: {self.__buttonState['X']}\nY: {self.__buttonState['Y']}"
            )
        os.system("clear")