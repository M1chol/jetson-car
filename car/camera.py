import queue
import time
from threading import Event
from concurrent.futures import wait

from car.fileHandler import FileHandler
from car.virtualFileHandler import VirtualFileHandler
import cv2

class Camera:
    def __init__(self, config, location, stream: bool, debug=False):
        self.config = config
        self.location = location
        self.fileWriter: FileHandler | VirtualFileHandler | None = None
        self.debug = debug 
        self.streamEnabled = stream
        self.pipeline = self.config["CAMERA"]["PIPELINES"]["GST_STREAM" if stream else "GST_BASIC"]
        self.frameQueue = queue.Queue(maxsize=30)
        self.capture = None
        self.stop_event = Event()

    def setup(self, fileWriterFuture):
        if self.streamEnabled:
            import subprocess
            def is_mediamtx_running():
                result = subprocess.run(["pgrep", "-f", "mediamtx"],stdout=subprocess.DEVNULL        )
                return result.returncode == 0
            print("[CAMERA] Connecting pipeline to mediamtx")
            retry_count = 0
            while retry_count < 6 and not is_mediamtx_running():
                retry_count += 1
                print(f"[CAMERA] Waiting for mediamtx server {retry_count}/6...")
                time.sleep(1)
        self.capture = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        wait([fileWriterFuture])
        self.fileWriter = fileWriterFuture.result()
        if not self.capture.isOpened():
            print("[CAMERA] Failed to open camera device")
            return None
        print(f"[CAMERA] Pipeline connected")
        return self

    def capture_worker(self):
        if not self.fileWriter:
            print("[CAMERA] No file writer available, capture worker exiting")
            return
        if not self.capture or not self.capture.isOpened():
            print("[CAMERA] Capture device not opened, capture worker exiting")
            return
        if isinstance(self.fileWriter, VirtualFileHandler):
            return
        frame_count = 0
        while not self.stop_event.is_set():
            ret, frame = self.capture.read()
            if ret:
                if not self.frameQueue.full():
                    self.fileWriter.write(f"{frame_count};{time.monotonic()}")
                    self.frameQueue.put(frame.copy())
                    frame_count += 1
            else:
                break

    def save_worker(self):
        frame_count = 0
        def _save_one_frame(self, frame, frame_count):
            filename = self.location / f"frame_{frame_count:04d}.jpg"
            cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

        while not self.stop_event.is_set():
            try:
                frame = self.frameQueue.get(timeout=1)
            except queue.Empty:
                continue
            _save_one_frame(self, frame, frame_count)
            frame_count += 1

        while not self.frameQueue.empty():
            try:
                frame = self.frameQueue.get(timeout=1)
            except queue.Empty:
                continue
            _save_one_frame(self, frame, frame_count)
            frame_count += 1
        print(f"[CAMERA] Save worker exiting, saved {frame_count} frames")

    def startWorker(self, executor):
        executor.submit(self.capture_worker)
        executor.submit(self.save_worker)

    def stop(self):
        self.stop_event.set()
        if self.capture:
            self.capture.release()

    def getStatus(self):
        return self.stop_event.is_set()
