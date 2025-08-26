import queue
import threading


class FileHandler:
    def __init__(self, filename: str, mode: str = "w") -> None:
        self.filename = filename
        self.mode = mode
        self.bufferSize = 100
        self.encoding = "utf-8"
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.buffer = []
        self.file = None

    def setup(self):
        self.file = open(self.filename, self.mode, encoding=self.encoding)
        print(f"[WRITER] File writer for {self.filename} is ready")
        return self

    def write(self, data: str) -> None:
        self.queue.put(data)

    def writeWorker(self) -> None:
        print("[WRITER] File writer worker started")
        while not self.stop_event.is_set():
            try:
                item = self.queue.get(timeout=0.1)
                self.buffer.append(item.strip() + "\n")
                if len(self.buffer) >= self.bufferSize:
                    self.file.writelines(self.buffer)
                    self.buffer.clear()
            except queue.Empty:
                pass
        if self.buffer:
            self.file.writelines(self.buffer)

    def startWorker(self, executor):
        executor.submit(self.writeWorker)

    def getStatus(self):
        return self.stop_event

    def stop(self) -> None:
        print("[WRITER] File writer worker closing")
        self.stop_event.set()
