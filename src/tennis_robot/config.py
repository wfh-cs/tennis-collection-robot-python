from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(slots=True)
class DetectorConfig:
    backend: str = "hsv"
    model_path: str = ""
    confidence: float = 0.45
    hsv_lower: tuple[int, int, int] = (20, 65, 55)
    hsv_upper: tuple[int, int, int] = (90, 255, 255)
    min_area: float = 80.0
    max_area: float = 80000.0
    min_circularity: float = 0.35
    morph_kernel: int = 7


@dataclass(slots=True)
class TrackerConfig:
    max_distance: float = 80.0
    max_missed: int = 8
    smoothing: float = 0.65


@dataclass(slots=True)
class PlannerConfig:
    start: tuple[float, float] = (0.0, 0.0)
    exact_limit: int = 12
    merge_distance: float = 45.0
    return_to_start: bool = False


@dataclass(slots=True)
class AppConfig:
    source: str = "data/ball_7.jpg"
    camera_index: int = 0
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    planner: PlannerConfig = field(default_factory=PlannerConfig)
    homography: list[list[float]] | None = None


def load_config(path: str | Path | None = None) -> AppConfig:
    if path is None:
        return AppConfig()
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AppConfig(
        source=str(raw.get("source", "data/ball_7.jpg")),
        camera_index=int(raw.get("camera_index", 0)),
        detector=DetectorConfig(**raw.get("detector", {})),
        tracker=TrackerConfig(**raw.get("tracker", {})),
        planner=PlannerConfig(**raw.get("planner", {})),
        homography=raw.get("homography"),
    )

