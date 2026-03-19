import cv2
from pathlib import Path
import re

# GStreamer pipeline for single-frame capture
gst_pipeline = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM),width=3280,height=2464,framerate=15/1,format=NV12 ! "
    "nvvidconv ! "
    "video/x-raw,format=BGRx ! "
    "videoconvert ! "
    "video/x-raw,format=BGR ! "
    "appsink drop=true max-buffers=1 sync=false"
)

WARMUP_FRAMES = 100  # skip first N frames

output_dir = Path("results/temp/single_frame")
output_dir.mkdir(parents=True, exist_ok=True)


def get_next_index() -> int:
    """Find next frame index based on existing files in output_dir."""
    pattern = re.compile(r"frame_(\d{4})\.jpg$")
    max_idx = -1

    for f in output_dir.glob("frame_*.jpg"):
        m = pattern.match(f.name)
        if m:
            idx = int(m.group(1))
            if idx > max_idx:
                max_idx = idx

    return max_idx + 1  # start at 0 if none found


def main():
    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        raise RuntimeError("Failed to open camera with GStreamer pipeline")

    # Discard the first N frames (warmup)
    for _ in range(WARMUP_FRAMES):
        cap.read()

    # Grab the frame
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.release()
        raise RuntimeError("Failed to grab a frame from the camera")

    # Compute next filename without overwriting existing frames
    idx = get_next_index()
    output_path = output_dir / f"frame_{idx:04d}.jpg"

    cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    cap.release()

    print(f"Saved single frame to: {output_path}")


if __name__ == "__main__":
    main()
