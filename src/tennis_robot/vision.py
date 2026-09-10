from __future__ import annotations

from abc import ABC, abstractmethod

import cv2
import numpy as np

from .config import DetectorConfig
from .models import Detection


class BallDetector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray) -> tuple[list[Detection], np.ndarray]:
        raise NotImplementedError


class HSVBallDetector(BallDetector):
    """Fast CPU baseline using illumination-tolerant HSV segmentation."""

    def __init__(self, config: DetectorConfig):
        self.config = config

    def detect(self, frame: np.ndarray) -> tuple[list[Detection], np.ndarray]:
        blurred = cv2.GaussianBlur(frame, (7, 7), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv,
            np.asarray(self.config.hsv_lower, dtype=np.uint8),
            np.asarray(self.config.hsv_upper, dtype=np.uint8),
        )
        kernel_size = max(3, self.config.morph_kernel | 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: list[Detection] = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if not self.config.min_area <= area <= self.config.max_area:
                continue
            perimeter = float(cv2.arcLength(contour, True))
            if perimeter <= 0:
                continue
            circularity = 4.0 * np.pi * area / (perimeter * perimeter)
            if circularity < self.config.min_circularity:
                continue
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            x, y, w, h = cv2.boundingRect(contour)
            fill_ratio = min(1.0, area / max(np.pi * radius * radius, 1.0))
            confidence = float(np.clip(0.55 * circularity + 0.45 * fill_ratio, 0.0, 1.0))
            detections.append(Detection((cx, cy), radius, confidence, (x, y, w, h)))
        detections.sort(key=lambda item: item.confidence, reverse=True)
        return detections, mask


class YOLOBallDetector(BallDetector):
    """Optional Ultralytics backend for a fine-tuned tennis-ball model."""

    def __init__(self, config: DetectorConfig):
        if not config.model_path:
            raise ValueError("detector.model_path is required for the YOLO backend")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Install the 'ai' extra to use YOLO") from exc
        self.config = config
        self.model = YOLO(config.model_path)

    def detect(self, frame: np.ndarray) -> tuple[list[Detection], np.ndarray]:
        result = self.model.predict(frame, conf=self.config.confidence, verbose=False)[0]
        detections: list[Detection] = []
        for xyxy, confidence in zip(result.boxes.xyxy.cpu().numpy(), result.boxes.conf.cpu().numpy()):
            x1, y1, x2, y2 = (float(value) for value in xyxy)
            width, height = x2 - x1, y2 - y1
            detections.append(
                Detection(
                    center=((x1 + x2) / 2, (y1 + y2) / 2),
                    radius=max(width, height) / 2,
                    confidence=float(confidence),
                    bbox=(int(x1), int(y1), int(width), int(height)),
                )
            )
        return detections, np.zeros(frame.shape[:2], dtype=np.uint8)


def build_detector(config: DetectorConfig) -> BallDetector:
    if config.backend.lower() == "yolo":
        return YOLOBallDetector(config)
    if config.backend.lower() == "hsv":
        return HSVBallDetector(config)
    raise ValueError(f"Unsupported detector backend: {config.backend}")

