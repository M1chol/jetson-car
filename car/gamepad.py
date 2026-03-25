import evdev
from time import sleep
import os
import json
from threading import Thread, Event


class Gamepad:
    def __init__(self, carStopEvent, startCollectionEvent, config, debug: bool = False) -> None:
        self.__buttonMap = {304: "A", 305: "B", 307: "X", 308: "Y"}
        self.__buttonState = {"A": False, "B": False, "X": False, "Y": False}
        self.__gamepad = None
        self.currentAngle = 0
        self.currentSpeed = 0
        self.currentBrake = 0
        self.currentGas = 0
        self.__config = config
        self.__DEBUG = debug
        self.__startDataCollection = startCollectionEvent
        self.__carStopEvent = carStopEvent

    def getGamePad(self) -> bool:
        device_paths = evdev.list_devices()
        timeout = 0
        sleep_time = 5
        while not device_paths:
            print(
                f"[STEER] Failed to find gamepad... try {timeout // sleep_time}/{self.__config['PAD_TIMEOUT'] // sleep_time}"
            )
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

    def updateGamepad(self) -> bool:
        print("[GAMEPAD] updateGamepad worker started")
        if not self.__gamepad:
            print("[GAMEPAD] updateGamepad failed, gamepad is None")
            return False
        for event in self.__gamepad.read_loop():
            if abs(self.currentAngle) > abs(self.__config["MAX_ANGLE"]):
                self.currentAngle = 0
                raise ValueError("Angle exceeds maximum limit")
            if event.type == evdev.ecodes.EV_KEY:
                button_name = self.__buttonMap.get(event.code)
                if button_name:
                    self.__buttonState[button_name] = event.value == 1
                    if button_name == "B" and event.value == 1:
                        print("[GAMEPAD] Close button pressed, quiting...")
                        self.currentAngle = 0
                        self.currentSpeed = 0
                        sleep(.5)
                        self.__carStopEvent.set()
                    if button_name == "A" and event.value == 1:
                        if not self.__startDataCollection.is_set():
                            print("[GAMEPAD] Data collection started")
                            self.__startDataCollection.set()
                        else:
                            print("[GAMEPAD] Data collection stopped")
                            self.__startDataCollection.clear()
            elif event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_X:
                    angle = (event.value / self.__config["PAD_READ_TURN"] - 0.5) * 2 * self.__config["MAX_ANGLE"]
                    if abs(angle) > self.__config["PAD_DEADZONE_DEG"]:
                        self.currentAngle = angle
                    else:
                        self.currentAngle = 0
                if event.code == evdev.ecodes.ABS_BRAKE:
                    self.currentBrake = (
                        event.value
                        / self.__config["PAD_READ_SPEED"]
                        * self.__config["MAX_SPEED"]
                    )
                    self.currentSpeed = self.currentGas - self.currentBrake
                if event.code == evdev.ecodes.ABS_GAS:
                    self.currentGas = (
                        event.value
                        / self.__config["PAD_READ_SPEED"]
                        * self.__config["MAX_SPEED"]
                    )
                    self.currentSpeed = self.currentGas - self.currentBrake
            if self.__carStopEvent.is_set():
                break
        return True

    def printData(self) -> None:
        print("PrintData started sleeping 2 seconds...")
        sleep(2)
        while not self.__carStopEvent.is_set():
            os.system("clear")
            print(
                f"Gas/Brake: {self.currentSpeed:.2f}\n Angle: {self.currentAngle:.2f}"
            )
            print(
                f"A: {self.__buttonState['A']}\nB: {self.__buttonState['B']}\nX: {self.__buttonState['X']}\nY: {self.__buttonState['Y']}"
            )
        os.system("clear")

    def stop(self) -> None:
        self.__carStopEvent.set()
        
if __name__ == "__main__":
    config_f = open("config.json")
    config = json.load(config_f)
    event = Event()
    pad = Gamepad(event, config, False)
    pad.getGamePad()
    thread = Thread(target=pad.updateGamepad)
    thread.start()
    pad.printData()
    thread.join()
