import queue
import threading
from pathlib import Path
import json

class FileHandler:
    def __init__(self, path : Path) -> None:
        self.path = path
        self.encoding = "utf-8"
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.file = None

    def setup(self):
        self.file = self.path.open()
        print(f"[WRITER] File writer for {self.filename} is ready")
        return self

    def write(self, data: str) -> None:
        self.queue.put(data)

    def writeWorker(self) -> None:
        print("[WRITER] File writer worker started")
        while not self.stop_event.is_set() or self.queue.qsize > 0:
            try:
                item = self.queue.get(timeout=0.1)
                if item.split()[0] == "SERVO":
                    feedback = item[2].split(";")
                    if feedback[0] == "FBK_ERR":
                        raise ValueError("Servo responded with FBK_ERR")
                    line = {
                        "type": "SERVO",
                        "time": item[1],
                        "data": {
                            "setAngle": item[3],
                            "servo_1": feedback[1],
                            "servo_2": feedback[2],
                            "feedback_type": feedback[0]
                        }
                    }
                elif item.split()[0] == "MOTOR":
                    try:
                        line = {
                            "type": "MOTOR",
                            "time": item[1],
                            "data": json.loads(item[2])
                        }
                    except json.JSONDecodeError:
                        print("[WRITER] Warning: Motor returned non json object")
                self.file.writelines(json.dumps(line, ensure_ascii=False) + "\n")
            except queue.Empty:
                pass

    def startWorker(self, executor):
        executor.submit(self.writeWorker)

    def getStatus(self):
        return self.stop_event

    def stop(self) -> None:
        print("[WRITER] File writer worker closing")
        self.stop_event.set()
