import queue
import time
import os
from threading import Event
from concurrent.futures import wait

os.environ["GST_DEBUG"] = "0"
from car.fileHandler import FileHandler
from car.virtualFileHandler import VirtualFileHandler
import cv2

class Camera:
    def __init__(self, config, location, debug=False):
        self.config = config
        self.location = location
        self.fileWriter: FileHandler | VirtualFileHandler | None = None
        self.debug = debug 
        self.pipeline = self.config["CAMERA"]["PIPELINES"][self.config["CAMERA"]["PIPELINE"]]
        self.frameQueue = queue.Queue(maxsize=30)
        self.capture = None
        self.stop_event = Event()

    def setup(self, fileWriterFuture):
        self.capture = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        wait([fileWriterFuture])
        self.fileWriter = fileWriterFuture.result()
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