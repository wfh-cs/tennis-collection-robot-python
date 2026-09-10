from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from .config import load_config
from .pipeline import TennisRobotPipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Tennis collection robot vision and route planning")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--source", help="image/video path or camera index")
    parser.add_argument("--output", default="outputs/annotated.jpg")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config if Path(args.config).exists() else None)
    if args.source:
        config.source = args.source
    pipeline = TennisRobotPipeline(config)
    source: str | int = int(config.source) if config.source.isdigit() else config.source
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise SystemExit(f"Unable to open source: {source}")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    frames = 0
    last_result = None
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        last_result = pipeline.process(frame)
        frames += 1
        if not args.headless:
            cv2.imshow("Tennis Robot Console", last_result.frame)
            if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                break
        if not capture.isOpened() or (Path(config.source).suffix.lower() in {".jpg", ".jpeg", ".png"}):
            break
    capture.release()
    cv2.destroyAllWindows()
    if last_result is None:
        raise SystemExit("No frames received")
    cv2.imwrite(args.output, last_result.frame)
    print(json.dumps({"frames": frames, "detections": len(last_result.detections), "route": last_result.route, "route_length": last_result.route_length, "latency_ms": last_result.latency_ms}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

