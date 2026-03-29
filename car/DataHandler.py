import queue
import threading
from pathlib import Path
import json


class DataHandler:
    def __init__(
        self, 
        path: Path, 
        startEvent: threading.Event, 
        debug: bool = False,
        pipeline: Optional[RealtimePathPipeline] = None  # NEW: Optional pipeline
    ) -> None:
        self.path = path
        self.encoding = "utf-8"
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.file = None
        self.countServo = 0
        self.countMotor = 0
        self.countSimple = 0
        self.countMiss = 0
        self.DEBUG = debug
        self.startEvent: threading.Event = startEvent
        self.pipeline = pipeline  # NEW: Store pipeline reference

    def setup(self):
        self.file = self.path.open("w")
        print(f"[WRITER] File writer for {self.path} is ready")
        return self

    def write(self, data: str) -> None:
        if self.startEvent.is_set():
            self.queue.put(data)

    def writeWorker(self) -> bool:
        if not self.file:
            print("[WRITER] File not opened cannot start worker")
            return False
        print("[WRITER] File writer worker started")
        
        try:
            while not self.stop_event.is_set() or not self.queue.empty():
                try:
                    item = self.queue.get(timeout=0.2)
                    item = item.split()
                    
                    if self.DEBUG:
                        print("[WRITER]", item)
                    
                    # Parse based on type
                    if item[0] == "SERVO":
                        self.countServo += 1
                        line = self._parse_servo(item)
                    elif item[0] == "MOTOR":
                        self.countMotor += 1
                        line = self._parse_motor(item)
                    else:
                        self.countMiss += 1
                        line = {"ERROR": "unknown source"}
                        print("[WRITER] WARN missed line: unknown source")
                    
                    # Write to file (existing behavior)
                    if "ERROR" not in line:
                        self.file.write(json.dumps(line, ensure_ascii=False) + "\n")
                        
                        # NEW: Send to pipeline if available
                        if self.pipeline:
                            self.pipeline.process_record(line)
                            
                except queue.Empty:
                    pass
        finally:
            self.file.close()
            # NEW: Close pipeline to flush remaining data
            if self.pipeline:
                self.pipeline.close()
                
        return True

    def _parse_servo(self, item: list) -> dict:
        try:
            feedback = item[2].split(";")
            if feedback[0] == "FBK_ERR":
                raise ValueError("Servo responded with FBK_ERR")
                
            return {
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
            print("[WRITER] WARN failed parsing servo message", e)
            return {"ERROR": str(e)}

    def _parse_motor(self, item: list) -> dict:
        try:
            return {
                "type": "MOTOR",
                "time": float(item[1]),
                "data": json.loads(item[2]),
            }
        except Exception as e:
            print("[WRITER] WARN failed parsing motor message", e)
            return {"ERROR": str(e)}

    def writeWorkerSimple(self) -> bool:
        # Unchanged from your original
        if not self.file:
            print("[WRITER] File not opened cannot start worker")
            return False
        print("[WRITER] Simple file writer worker started")
        while not self.stop_event.is_set() or not self.queue.empty():
            try:
                item = self.queue.get(timeout=0.2)
                if self.DEBUG:
                    print("[WRITER]", item)
                self.file.writelines(item + "\n")
                self.countSimple += 1
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
            f"[WRITER] File writer worker closing. Wrote {self.countServo + self.countMotor}",
            f"(missed {self.countMiss}) advanced lines and {self.countSimple} simple lines",
        )
        self.stop_event.set()