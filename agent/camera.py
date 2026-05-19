from __future__ import annotations

from dataclasses import dataclass

import cv2


@dataclass(frozen=True)
class CameraFrame:
    jpeg_bytes: bytes
    width: int
    height: int


def capture_jpeg_frame(
    pipeline: str,
    warmup_frames: int = 0,
    jpeg_quality: int = 90,
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

        height, width = frame.shape[:2]
        return CameraFrame(
            jpeg_bytes=encoded.tobytes(),
            width=width,
            height=height,
        )
    finally:
        cap.release()
