import evdev
import threading
from concurrent.futures import wait
import serial
import serial.tools.list_ports
import os
import json
from time import sleep
import time
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
        self._fileWriter = None
        with open("config.json") as file:
            self._config = json.load(file)
        if not self._config:
            print("[STEER] Config file faild to load")
            raise Exception()
        self.DEBUG = False
        self.CONTROLLER = False
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

    def getGamePad(self) -> bool:
        device_paths = evdev.list_devices()

        if not device_paths:
            print("[STEER] Failed to find gamepad...")
            return False

        for i, path in enumerate(device_paths):
            dev = evdev.InputDevice(path)
            print(f"[STEER] Device {i}: {dev.name} at {dev.path}")

        if len(device_paths) > 1:
            try:
                idx = int(input("[STEER] Multiple gamepads, select index: "))
                selected_path = device_paths[idx]
            except Exception:
                print("[STEER] Invalid selection")
                return False
        else:
            selected_path = device_paths[0]

        self.gamepad = evdev.InputDevice(selected_path)
        return True

    def writeMotor(self, command: str) -> None:
        if self.DEBUG:
            print(f"[STEER -> MOTOR] {command}")
        self._serialMotor.write(command.encode() + b"\n")

    def _motorSetup(self) -> bool:
        print("[STEER] Starting motor setup")
        self._serialMotor.reset_input_buffer()
        self._serialMotor.reset_output_buffer()
        for i in range(4):
            # Check motor status
            self.writeMotor(self.generateMotorCommand("CMD_DDSM_INFO", id=i + 1))
            if self._serialMotor.readline().decode("utf-8").strip():
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

    def setup(self, fileWriterFuture):
        if not self.getGamePad():
            return None
        if not self.openSerial():
            return None
        if not self._motorSetup():
            return None
        wait([fileWriterFuture])
        self._fileWriter = fileWriterFuture.result()
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
        # Set heartbeat
        self.writeMotor(self.generateMotorCommand("CMD_HEARTBEAT_TIME", time="600"))
        self._serialMotor.readline().decode("utf-8").strip()
        while not self._stopEvent.is_set():
            value = int(round(self._currentSpeed))
            for i in range(4):
                cmd_val = value * self._config["MOTOR_INVERT"][i]
                self.writeMotor(
                    self.generateMotorCommand("CMD_DDSM_CTRL", id=i + 1, cmd=cmd_val)
                )
                sleep(0.01)

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
        count = 0
        timer = time.monotonic()
        while not self._stopEvent.is_set():
            try:
                if time.monotonic() - timer >= 10:
                    freq = count / 40
                    print(f"[STEER] readSerial operating at {freq}Hz")
                    count = 0
                    timer = time.monotonic()
                line = self._serialMotor.readline()
                if not line:
                    continue
                msg = line.decode("utf-8", errors="ignore").strip()
                if not msg:
                    continue
                self._fileWriter.write(str(time.monotonic()) + ";" + msg)
                if self.DEBUG:
                    print(f"[STEER <- MOTOR] {msg}")
                count += 1
            except Exception as e:
                if self.DEBUG:
                    print(f"[MOTOR READ ERR] {e}")

    def printData(self) -> None:
        while not self._stopEvent.is_set():
            os.system("clear")
            print(
                f"Gas/Brake: {self._currentSpeed:2.f}\n Angle: {self._currentAngle:.2f}"
            )
            print(
                f"A: {self._buttonState['A']}\nB: {self._buttonState['B']}\nX: {self._buttonState['X']}\nY: {self._buttonState['Y']}"
            )
        os.system("clear")

    def startWorker(self, executor) -> None:
        executor.submit(self.writeSerialServo)
        executor.submit(self.writeSerialMotor)
        executor.submit(self.readSerial)
        executor.submit(self.updateGamepad)
        if self.CONTROLLER:
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
