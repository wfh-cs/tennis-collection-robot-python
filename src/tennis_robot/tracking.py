from __future__ import annotations

import math

from .config import TrackerConfig
from .models import Detection, Track


class CentroidTracker:
    """Dependency-light online tracker with velocity prediction and EMA smoothing."""

    def __init__(self, config: TrackerConfig):
        self.config = config
        self.tracks: dict[int, Track] = {}
        self.next_id = 1

    def update(self, detections: list[Detection]) -> list[Track]:
        candidates: list[tuple[float, int, int]] = []
        for track_id, track in self.tracks.items():
            predicted = (track.center[0] + track.velocity[0], track.center[1] + track.velocity[1])
            for detection_index, detection in enumerate(detections):
                distance = math.dist(predicted, detection.center)
                if distance <= self.config.max_distance:
                    candidates.append((distance, track_id, detection_index))

        matched_tracks: set[int] = set()
        matched_detections: set[int] = set()
        for _, track_id, detection_index in sorted(candidates):
            if track_id in matched_tracks or detection_index in matched_detections:
                continue
            track = self.tracks[track_id]
            detection = detections[detection_index]
            old_center = track.center
            alpha = self.config.smoothing
            track.center = (
                alpha * detection.center[0] + (1 - alpha) * old_center[0],
                alpha * detection.center[1] + (1 - alpha) * old_center[1],
            )
            track.velocity = (track.center[0] - old_center[0], track.center[1] - old_center[1])
            track.radius = detection.radius
            track.confidence = detection.confidence
            track.age += 1
            track.missed = 0
            matched_tracks.add(track_id)
            matched_detections.add(detection_index)

        for track_id, track in list(self.tracks.items()):
            if track_id not in matched_tracks:
                track.missed += 1
                if track.missed > self.config.max_missed:
                    del self.tracks[track_id]

        for index, detection in enumerate(detections):
            if index in matched_detections:
                continue
            self.tracks[self.next_id] = Track(
                self.next_id, detection.center, detection.radius, detection.confidence
            )
            self.next_id += 1
        return sorted(self.tracks.values(), key=lambda item: item.track_id)

