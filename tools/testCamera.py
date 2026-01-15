import cv2
import threading
import queue
from pathlib import Path
import time
import shutil

gst_pipeline = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM),width=1640,height=1232,framerate=15/1,format=NV12 ! "
    "nvvidconv ! "
    "video/x-raw,format=BGRx ! "
    "appsink drop=true max-buffers=1 sync=false"
)

gst_pipeline_stream = (
    "nvarguscamerasrc ! video/x-raw(memory:NVMM),width=1640,height=1232,framerate=20/1,format=NV12 ! "
    "nvvidconv ! video/x-raw,format=I420 ! "
    "tee name=t ! queue ! x264enc bitrate=1000 speed-preset=ultrafast tune=zerolatency ! "
    "h264parse ! flvmux ! rtmpsink location=rtmp://localhost/live t. ! queue !"
    "videoconvert !"
    "video/x-raw,format=BGR !"
    "appsink drop=true max-buffers=1 sync=false"
)

image_location = Path("results/temp/images")
image_location.mkdir(exist_ok=True)
shutil.rmtree(str(image_location))
image_location.mkdir()
timings = open(image_location / "timings.txt", "w")

cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
frame_queue = queue.Queue(maxsize=30)
save_thread_running = True

def save_worker():
    frame_count = 0
    while save_thread_running:
        try:
            frame = frame_queue.get(timeout=1)
            filename = image_location / f"frame_{frame_count:04d}.jpg"
            cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_count += 1
        except queue.Empty:
            continue

save_thread = threading.Thread(target=save_worker, daemon=True)
save_thread.start()

frame_count = 0
try:
    while True:
        ret, frame = cap.read()
        if ret:
            if not frame_queue.full():
                frame_queue.put(frame.copy())
                print(f"{frame_count}/{time.monotonic()}", file=timings)
                frame_count += 1
except KeyboardInterrupt:
    save_thread_running = False
    cap.release()
    save_thread.join()
    timings.close()