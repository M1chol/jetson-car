import threading
from concurrent.futures import wait
import serial
import serial.tools.list_ports
import json
from time import sleep
import time
import math

from car.fileHandler import FileHandler
from car.gamepad import Gamepad
from car.virtualFileHandler import VirtualFileHandler


class Steering:
    def __init__(self, config, debug: bool = False, *, VIRTUAL_GAMEPAD=None) -> None:
        self.__serialServo = None
        self.__serialMotor = None
        self.stopEvent = threading.Event()
        self.__config = config
        self.fileWriter: FileHandler | VirtualFileHandler | None = None
        self.__gamepad = (
            Gamepad(self.stopEvent, config, debug)
            if not VIRTUAL_GAMEPAD
            else VIRTUAL_GAMEPAD
        )
        self.DEBUG = debug
        self.DEBUG_CONTROLLER = bool(False)
        self.STEER_MANUAL = bool(False)
        """Setting this flag pauses motorWriter loop"""

    def __openSerial(self) -> bool:
        servoPort = None
        motorPort = None
        ports = serial.tools.list_ports.comports()
        for _port in ports:
            if (
                _port.vid == self.__config["SERVO_VID"]
                and _port.pid == self.__config["SERVO_PID"]
            ):
                servoPort = _port.device
            elif (
                _port.vid == self.__config["MOTOR_VID"]
                and _port.pid == self.__config["MOTOR_PID"]
            ):
                motorPort = _port.device
        if not all([servoPort, motorPort]):
            print(
                f"[STEER] failed to find some hardware{' (motor driver)' if not motorPort else ''}{' (servo driver)' if not servoPort else ''}"
            )
            return False
        self.__serialServo = serial.Serial(
            servoPort, baudrate=115200, timeout=1, dsrdtr=False, rtscts=False
        )
        self.__serialMotor = serial.Serial(
            motorPort, baudrate=115200, timeout=1, dsrdtr=False, rtscts=False
        )
        #TODO: Check if this is needed
        self.__serialServo.setRTS(False)
        self.__serialServo.setDTR(False)
        self.__serialMotor.setRTS(False)
        self.__serialMotor.setDTR(False)
        print(
            f"[STEER] Serial connected\n[STEER]\t- motor driver on {motorPort}\n[STEER]\t- servo driver on {servoPort}"
        )
        return True

    def __writeMotor(self, command: str) -> None:
        if self.DEBUG:
            print(f"[STEER -> MOTOR] {command}")
        if self.__serialMotor:
            self.__serialMotor.write(command.encode() + b"\n")

    def __motorSetup(self) -> bool:
        print("[STEER] Starting motor setup")
        if not self.__serialMotor:
            print("[STEER] Serial connection is not established (motor)")
            return False
        self.__serialMotor.reset_input_buffer()
        self.__serialMotor.reset_output_buffer()
        for i in range(4):
            # Check motor status
            self.__writeMotor(self.__generateMotorCommand("CMD_DDSM_INFO", id=i + 1))
            if self.__serialMotor.readline():
                print(f"[STEER] Motor {i + 1} ok")
            else:
                print(f"[STEER] Motor {i + 1} failed to respond")
                return False
            # Enable motor
            self.__writeMotor(
                self.__generateMotorCommand("CMD_CHANGE_Enable", id=i + 1)
            )
            self.__serialMotor.readline()
            # Change mode default mode
            self.__writeMotor(
                self.__generateMotorCommand(
                    "CMD_CHANGE_MODE",
                    id=i + 1,
                    mode=self.__config["MOTOR_MODES"][
                        self.__config["MOTOR_DEFAULT_MODE"]
                    ],
                )
            )
            self.__serialMotor.readline()
        print("[STEER] Finished motor setup")
        return True

    def __servoSetup(self) -> bool:
        print("[STEER] Starting servo setup")
        if not self.__serialServo:
            print("[STEER] Serial connection is not established (servo)")
            return False
        self.__serialServo.reset_input_buffer()
        self.__serialServo.reset_output_buffer()
        command = "BEG" + str(self.__config["SERVO_FBK_FREQ_MS"])
        self.__serialServo.write(command.encode() + b"\n")
        if not self.__serialServo.readline():
            print("[STEER] Servo setup failed")
            return False
        print("[STEER] Finished servo setup")
        return True

    def setup(self, fileWriterFuture):
        if not self.__gamepad:
            raise ValueError("[STEER] Gamepad is None")
        if not self.__gamepad.getGamePad():
            raise ValueError("[STEER] Gamepad setup failed")
        if not self.__openSerial():
            raise ValueError("[STEER] Serial connection failed")
        if not self.__motorSetup():
            raise ValueError("[STEER] Motor setup failed")
        if not self.__servoSetup():
            raise ValueError("[STEER] Servo setup failed")
        wait([fileWriterFuture])
        self.fileWriter = fileWriterFuture.result()
        return self

    def __setMotors(self, vals) -> None:
        """Set motor values [FR, RR, RL, FL]"""
        for i in range(4):
            self.__writeMotor(
                self.__generateMotorCommand(
                    "CMD_DDSM_CTRL", id=self.__config["MOTOR_IDS_MAP"][i], cmd=vals[i]
                )
            )
            sleep(0.01)

    def __getDiferentialforWheels(self, angle: float):
        if angle == 0 or not self.__config["DIFF_ENABLED"]:
            return [1, 1, 1, 1]
        delta = math.radians(angle)

        L = self.__config["DIFF_LENGTH"]
        D = self.__config["DIFF_WIDTH"]

        Rc = L / (2 * math.tan(delta))

        Rin = math.sqrt((Rc - D / 2)**2 + (L / 2)**2)
        Rout = math.sqrt((Rc + D / 2)**2 + (L / 2)**2)

        k_in = abs(Rin / Rc)
        k_out = abs(Rout / Rc)
        if self.__gamepad.currentAngle > 0:
            return [k_in, k_in, k_out, k_out]
        else:
            return [k_out, k_out, k_in, k_in]

    def __writeSerialMotor(self) -> bool:
        print("[STEER] writeSerialMotor worker started")
        if not self.__serialMotor:
            print("[STEER] writeSerialMotor failed, serial connection is not established")
            return False
        # Set heartbeat
        self.__writeMotor(
            self.__generateMotorCommand(
                "CMD_HEARTBEAT_TIME", time=str(self.__config["MOTOR_HEARTBEAT_TIME"])
            )
        )
        self.__serialMotor.readline().decode("utf-8").strip()
        while not self.stopEvent.is_set():
            if self.STEER_MANUAL:
                continue
            speed = self.__gamepad.currentSpeed
            angle = self.__gamepad.currentAngle
            diff = self.__getDiferentialforWheels(angle)
            values = [
                int(round(speed)) * self.__config["MOTOR_INVERT"][idx] * diff[idx]
                for idx in range(4)
            ]
            self.__setMotors(values)
        return True

    def __writeSerialServo(self) -> bool:
        print("[STEER] writeSerialServo worker started")
        lastAngle = self.__gamepad.currentAngle
        if not self.__serialServo:
            print("[STEER] Serial connection is not established (servo)")
            return False
        while not self.stopEvent.is_set():
            if self.__gamepad.currentAngle != lastAngle:
                command = f"CMD{self.__gamepad.currentAngle:.2f};{-self.__gamepad.currentAngle:.2f}"
                self.__serialServo.write(command.encode() + b"\n")
            lastAngle = self.__gamepad.currentAngle
            sleep(0.1)
        return True

    def __readSerialMotor(self) -> bool:
        print("[STEER] readSerialMotor worker started")
        if not self.__serialMotor:
            print("[STEER] Serial connection is not established (servo)")
            return False
        if not self.fileWriter:
            print("[STEER] File writer is None")
            return False
        count = 0
        timer = time.monotonic()
        while not self.stopEvent.is_set():
            try:
                if time.monotonic() - timer >= 10:
                    freq = count / 40
                    print(f"[STEER] readSerialMotor operating at {freq}Hz")
                    count = 0
                    timer = time.monotonic()
                line = self.__serialMotor.readline()
                if not line:
                    continue
                msg = line.decode("utf-8", errors="ignore").strip()
                if not msg:
                    continue
                line = (
                    "MOTOR "
                    + str(time.monotonic())
                    + " "
                    + msg
                    + " "
                    + str(self.__gamepad.currentSpeed)
                )
                self.fileWriter.write(line)
                if self.DEBUG:
                    print(f"[STEER <- MOTOR] {msg}")
                    print(f"[STEER -> WRITER] {line}")
                count += 1
            except Exception as e:
                if self.DEBUG:
                    print(f"[MOTOR READ ERR] {e}")
        return True

    def __readSerialServo(self) -> bool:
        print("[STEER] readSerialServo worker started")
        if not self.__serialServo:
            print("[STEER] Serial connection is not established (servo)")
            return False
        if not self.fileWriter:
            print("[STEER] File writer is None - readSerialServo")
            return False
        count = 0
        timer = time.monotonic()
        while not self.stopEvent.is_set():
            try:
                if time.monotonic() - timer >= 10:
                    freq = count / 10
                    print(f"[STEER] readSerial operating at {freq}Hz")
                    count = 0
                    timer = time.monotonic()
                line = self.__serialServo.readline()
                if not line:
                    continue
                msg = line.decode("utf-8", errors="ignore").strip()
                if not msg:
                    continue
                line = (
                    "SERVO "
                    + str(time.monotonic())
                    + " "
                    + msg
                    + " "
                    + str(self.__gamepad.currentAngle)
                )
                self.fileWriter.write(line)
                if self.DEBUG:
                    print(f"[STEER <- SERVO] {msg}")
                    print(f"[STEER -> WRITER] {line}")
                count += 1
            except Exception as e:
                if self.DEBUG:
                    print(f"[SERVO READ ERR] {e}")
        return True

    def startWorker(self, executor) -> None:
        executor.submit(self.__writeSerialServo)
        executor.submit(self.__writeSerialMotor)
        executor.submit(self.__readSerialMotor)
        executor.submit(self.__readSerialServo)
        executor.submit(self.__gamepad.updateGamepad)
        if self.DEBUG_CONTROLLER:
            executor.submit(self.__gamepad.printData)

    def stop(self) -> bool:
        if not self.__serialMotor:
            print("[STEER] Stop failed serial motor connection is Null")
            return False
        command = "CMD90;90"
        self.__setMotors([0, 0, 0, 0])
        for i in range(4):
            self.__generateMotorCommand("CMD_CHANGE_Disable", id=i + 1)
            self.__serialMotor.write(command.encode() + b"\n")
        self.stopEvent.set()
        print("[STEER] requested thread close")
        return True

    def __generateMotorCommand(self, cmd_name: str, **kwargs) -> str:
        if cmd_name not in self.__config["command_map"]:
            raise ValueError(f"Unknown command: {cmd_name}")
        command = self.__config["command_map"][cmd_name].copy()
        command.update(kwargs)
        return json.dumps(command)

    def getStatus(self):
        return self.stopEvent.is_set()


if __name__ == "__main__":
    print("This file should not be run directly. Please run main.py")
