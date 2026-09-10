from __future__ import annotations

import time

import cv2
import numpy as np

from .config import AppConfig
from .models import FrameResult
from .planner import RoutePlanner
from .tracking import CentroidTracker
from .vision import build_detector


class TennisRobotPipeline:
    def __init__(self, config: AppConfig):
        self.config = config
        self.detector = build_detector(config.detector)
        self.tracker = CentroidTracker(config.tracker)
        self.planner = RoutePlanner(config.planner)
        self.homography = np.asarray(config.homography, dtype=np.float32) if config.homography else None

    def process(self, frame: np.ndarray) -> FrameResult:
        started = time.perf_counter()
        detections, mask = self.detector.detect(frame)
        tracks = self.tracker.update(detections)
        image_points = [track.center for track in tracks if track.missed == 0]
        world_points = self._project(image_points)
        route, route_length, algorithm = self.planner.plan(world_points)
        annotated = self._annotate(frame, tracks, route)
        latency_ms = (time.perf_counter() - started) * 1000
        return FrameResult(
            frame=annotated,
            mask=mask,
            detections=detections,
            tracks=tracks,
            route=route,
            route_length=route_length,
            latency_ms=latency_ms,
            metrics={"planner": algorithm, "active_tracks": len(image_points)},
        )

    def _project(self, points: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if self.homography is None or not points:
            return points
        projected = cv2.perspectiveTransform(np.asarray(points, dtype=np.float32)[None, :, :], self.homography)[0]
        return [(float(x), float(y)) for x, y in projected]

    @staticmethod
    def _annotate(frame: np.ndarray, tracks, route) -> np.ndarray:
        output = frame.copy()
        for track in tracks:
            if track.missed:
                continue
            center = tuple(int(value) for value in track.center)
            cv2.circle(output, center, max(3, int(track.radius)), (41, 211, 145), 2)
            cv2.putText(output, f"#{track.track_id} {track.confidence:.2f}", (center[0] + 8, center[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2)
        if route:
            display_route = [(int(x), int(y)) for x, y in route]
            for index, point in enumerate(display_route):
                if index:
                    cv2.arrowedLine(output, display_route[index - 1], point, (45, 170, 255), 2, tipLength=0.08)
                cv2.putText(output, str(index + 1), point, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (45, 170, 255), 2)
        return output

