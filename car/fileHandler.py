import queue
import threading
from pathlib import Path
import json


class FileHandler:
    def __init__(self, path: Path, *, debug=False) -> None:
        self.path = path
        self.encoding = "utf-8"
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.file = None
        self.countServo = 0
        self.countMotor = 0
        self.countMiss = 0
        self.DEBUG = debug

    def setup(self):
        self.file = self.path.open("w")
        print(f"[WRITER] File writer for {self.path} is ready")
        return self

    def write(self, data: str) -> None:
        self.queue.put(data)

    def writeWorker(self) -> bool:
        if not self.file:
            print("[WRITER] File not opened cannot start worker")
            return False
        print("[WRITER] File writer worker started")
        while not self.stop_event.is_set() or not self.queue.empty:
            try:
                item = self.queue.get(timeout=0.1)
                item = item.split()
                if self.DEBUG:
                    print("[WRITER]", item)
                if item[0] == "SERVO":
                    self.countServo += 1
                    try:
                        feedback = item[2].split(";")
                        if feedback[0] == "FBK_ERR":
                            raise ValueError("Servo responded with FBK_ERR")
                        # SERVO 2823.037912669 FBK;0.35;-0.53 -21.978607177734375
                        line = {
                            "type": "SERVO",
                            "time": float(item[1]),
                            "data": {
                                "setAngle": float(item[3]),
                                "servo_1": float(feedback[1]),
                                "servo_2": float(feedback[2]),
                                "feedback_type": feedback[0],
                            },
                        }
                    except Exception as e:
                        line = {"ERROR": e}
                        print("[WRITER] WARN failed parsing servo message", e)
                elif item[0] == "MOTOR":
                    self.countMotor += 1
                    try:
                        line = {
                            "type": "MOTOR",
                            "time": float(item[1]),
                            "data": json.loads(item[2]),
                        }
                    except Exception as e:
                        line = {"ERROR": e}
                        print("[WRITER] WARN failed parsing motor message", e)
                else:
                    self.countMiss += 1
                    line = {"ERROR": "unknown source"}
                    print("[WRITER] WARN missed line: unnown source")
                self.file.writelines(json.dumps(line, ensure_ascii=False) + "\n")
            except queue.Empty:
                pass
        self.file.close()
        return True

    def writeWorkerSimple(self) -> bool:
        if not self.file:
            print("[WRITER] File not opened cannot start worker")
            return False
        print("[WRITER] File writer worker started")
        while not self.stop_event.is_set() or not self.queue.empty:
            try:
                item = self.queue.get(timeout=0.1)
                if self.DEBUG:
                    print("[WRITER]", item)
                self.file.writelines(item + "\n")
            except queue.Empty:
                pass
        self.file.close()
        return True

    def startWorker(self, executor, simple=False) -> None:
        if simple:
            executor.submit(self.writeWorkerSimple)
        else:
            executor.submit(self.writeWorker)

    def getStatus(self):
        return self.stop_event

    def stop(self) -> None:
        print(
            f"[WRITER] File writer worker closing wrote {self.countServo} servo lines,",
            f"{self.countMotor} motor lines and missed {self.countMiss} lines",
        )
        self.stop_event.set()
