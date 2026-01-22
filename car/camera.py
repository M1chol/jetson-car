import queue
from threading import Event

class Camera:
    def __init__(self, config, location, debug=False):
        self.config = config
        self.location = location
        self.debug = debug 
        self.pipeline = self.config["CAMERA"]["PIPELINES"][self.config["CAMERA"]["PIPELINE"]]
        self.frameQueue = queue.Queue(maxsize=30)
        self.capture = None
        self.stop_event = Event()

    def setup(self):
        # Moved here to stop VirtualCamera from loading cv2
        import cv2
        self.capture = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        return self

    def save_worker(self):
        frame_count = 0
        while not self.stop_event.is_set():
            try:
                frame = self.frameQueue.get(timeout=1)
                filename = self.location / f"frame_{frame_count:04d}.jpg"
                cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                frame_count += 1
            except queue.Empty:
                continue

    def startWorker(self, executor):
        executor.submit(self.save_worker)

    def stop(self):
        self.stop_event.set()
        if self.capture:
            self.capture.release()

    def getStatus(self):
        return self.stop_event.is_set()