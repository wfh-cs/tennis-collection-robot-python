import cv2
import numpy as np

from tennis_robot.config import DetectorConfig
from tennis_robot.vision import HSVBallDetector


def test_hsv_detector_finds_synthetic_ball():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.circle(frame, (160, 120), 24, (0, 220, 80), -1)
    detector = HSVBallDetector(DetectorConfig(min_area=200, min_circularity=0.5))
    detections, mask = detector.detect(frame)
    assert mask.shape == (240, 320)
    assert len(detections) == 1
    assert abs(detections[0].center[0] - 160) < 4

