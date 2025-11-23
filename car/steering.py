import threading
from concurrent.futures import wait
import serial
import serial.tools.list_ports
import json
from time import sleep
import time
from car.gamepad import Gamepad


class Steering:
    def __init__(self, config, debug: bool = False, *, VIRTUAL_GAMEPAD = None) -> None:
        self.__serialServo = None
        self.__serialMotor = None
        self.stopEvent = threading.Event()
        self.__config = config
        self.__fileWriterMotor = None
        self.__fileWriterServo = None
        self.__gamepad = Gamepad(self.stopEvent, config, debug) if not VIRTUAL_GAMEPAD else VIRTUAL_GAMEPAD
        self.DEBUG = debug
        self.DEBUG_CONTROLLER = False
        self.STEER_MANUAL = False

    def __openSerial(self) -> str:
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
        self.__serialMotor.write(command.encode() + b"\n")

    def __motorSetup(self) -> bool:
        print("[STEER] Starting motor setup")
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
            self.__writeMotor(self.__generateMotorCommand("CMD_CHANGE_Enable", id=i + 1))
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
        self.__serialServo.reset_input_buffer()
        self.__serialServo.reset_output_buffer()
        command = "BEG" + str(self.__config["SERVO_FBK_FREQ_MS"])
        self.__serialServo.write(command.encode() + b"\n")
        if not self.__serialServo.readline():
            print("[STEER] Servo setup failed")
            return False
        print("[STEER] Finished servo setup")
        return True

    def setup(self, fileWriterMotorFuture, fileWriterServoFuture):
        if not self.__gamepad:
            return None
        if not self.__gamepad.getGamePad():
            return None
        if not self.__openSerial():
            return None
        if not self.__motorSetup():
            return None
        if not self.__servoSetup():
            return None
        wait([fileWriterMotorFuture, fileWriterServoFuture])
        self.__fileWriterMotor = fileWriterMotorFuture.result()
        self.__fileWriterServo = fileWriterServoFuture.result()
        return self

    def __setMotors(self, FR : float, RR : float, RL : float, FL : float) -> None:
        sleepTime = 0.01
        self.__writeMotor(self.__generateMotorCommand("CMD_DDSM_CTRL", id=1, cmd=FR))        
        sleep(sleepTime)
        self.__writeMotor(self.__generateMotorCommand("CMD_DDSM_CTRL", id=2, cmd=RR))        
        sleep(sleepTime)
        self.__writeMotor(self.__generateMotorCommand("CMD_DDSM_CTRL", id=3, cmd=RL))        
        sleep(sleepTime)
        self.__writeMotor(self.__generateMotorCommand("CMD_DDSM_CTRL", id=4, cmd=FL))        
        sleep(sleepTime)

    def __writeSerialMotor(self) -> None:
        print("[STEER] writeSerialMotor worker started")
        # Set heartbeat
        self.__writeMotor(self.__generateMotorCommand("CMD_HEARTBEAT_TIME", time="600"))
        self.__serialMotor.readline().decode("utf-8").strip()
        if self.__config["STEER_WITH_DIFFERENTIAL"]:
            pass
        else:
            while not self.stopEvent.is_set():
                if self.STEER_MANUAL:
                    continue
                values = [int(round(self.__gamepad.currentSpeed)) * direction for direction in self.__config["MOTOR_INVERT"]]
                self.__setMotors(*values)

    def __writeSerialServo(self) -> None:
        print("[STEER] writeSerialServo worker started")
        lastAngle = self.__gamepad.currentAngle
        while not self.stopEvent.is_set():
            if self.__gamepad.currentAngle != lastAngle:
                command = f"CMD{self.__gamepad.currentAngle:.2f};{-self.__gamepad.currentAngle:.2f}"
                self.__serialServo.write(command.encode() + b"\n")
            lastAngle = self.__gamepad.currentAngle
            sleep(0.1)

    def __readSerialMotor(self) -> None:
        print("[STEER] readSerialMotor worker started")
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
                self.__fileWriterMotor.write(str(time.monotonic()) + ";" + msg)
                if self.DEBUG:
                    print(f"[STEER <- MOTOR] {msg}")
                count += 1
            except Exception as e:
                if self.DEBUG:
                    print(f"[MOTOR READ ERR] {e}")

    def __readSerialServo(self) -> None:
        print("[STEER] readSerialServo worker started")
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
                self.__fileWriterServo.write(
                    str(time.monotonic()) + ";" + msg + ";" + str(self.__gamepad.currentAngle)
                )
                if self.DEBUG:
                    print(f"[STEER <- SERVO] {msg}")
                count += 1
            except Exception as e:
                if self.DEBUG:
                    print(f"[SERVO READ ERR] {e}")

    def startWorker(self, executor) -> None:
        executor.submit(self.__writeSerialServo)
        executor.submit(self.__writeSerialMotor)
        executor.submit(self.__readSerialMotor)
        executor.submit(self.__readSerialServo)
        executor.submit(self.__gamepad.updateGamepad)
        if self.DEBUG_CONTROLLER:
            executor.submit(self.__gamepad.printData)

    def stop(self) -> None:
        command = "CMD90;90"
        self.__setMotors(0, 0, 0, 0)
        for i in range(4):
            self.__generateMotorCommand("CMD_CHANGE_Disable", id=i + 1)
            self.__serialMotor.write(command.encode() + b"\n")
        self.stopEvent.set()
        print("[STEER] requested thread close")

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
