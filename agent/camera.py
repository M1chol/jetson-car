from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2


@dataclass(frozen=True)
class CameraFrame:
    jpeg_bytes: bytes
    width: int
    height: int
    saved_path: str | None = None


def capture_jpeg_frame(
    pipeline: str,
    warmup_frames: int = 0,
    jpeg_quality: int = 90,
    save_dir: str | Path | None = Path("results/temp/agent"),
) -> CameraFrame:
    if not pipeline:
        raise ValueError("Brak skonfigurowanego pipeline kamery.")

    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    try:
        if not cap.isOpened():
            raise RuntimeError("Nie udalo sie otworzyc kamery przez GStreamer.")

        for _ in range(max(0, warmup_frames)):
            cap.read()

        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError("Nie udalo sie pobrac klatki z kamery.")

        encode_params = [cv2.IMWRITE_JPEG_QUALITY, int(jpeg_quality)]
        ok, encoded = cv2.imencode(".jpg", frame, encode_params)
        if not ok:
            raise RuntimeError("Nie udalo sie zakodowac klatki jako JPEG.")

        jpeg_bytes = encoded.tobytes()
        saved_path = None
        if save_dir is not None:
            output_dir = Path(save_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            output_path = output_dir / f"camera_{timestamp}.jpg"
            output_path.write_bytes(jpeg_bytes)
            saved_path = str(output_path)

        height, width = frame.shape[:2]
        return CameraFrame(
            jpeg_bytes=jpeg_bytes,
            width=width,
            height=height,
            saved_path=saved_path,
        )
    finally:
        cap.release()
