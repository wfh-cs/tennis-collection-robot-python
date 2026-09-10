from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class Detection:
    center: tuple[float, float]
    radius: float
    confidence: float
    bbox: tuple[int, int, int, int]


@dataclass(slots=True)
class Track:
    track_id: int
    center: tuple[float, float]
    radius: float
    confidence: float
    age: int = 1
    missed: int = 0
    velocity: tuple[float, float] = (0.0, 0.0)


@dataclass(slots=True)
class FrameResult:
    frame: np.ndarray
    mask: np.ndarray
    detections: list[Detection]
    tracks: list[Track]
    route: list[tuple[float, float]]
    route_length: float
    latency_ms: float
    metrics: dict[str, float | int | str] = field(default_factory=dict)

