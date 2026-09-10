from __future__ import annotations

import math
from functools import lru_cache

from .config import PlannerConfig

Point = tuple[float, float]


def merge_nearby(points: list[Point], threshold: float) -> list[Point]:
    """Cluster balls that can be collected in one pass."""
    groups: list[list[Point]] = []
    for point in points:
        for group in groups:
            centroid = (
                sum(item[0] for item in group) / len(group),
                sum(item[1] for item in group) / len(group),
            )
            if math.dist(point, centroid) <= threshold:
                group.append(point)
                break
        else:
            groups.append([point])
    return [
        (sum(p[0] for p in group) / len(group), sum(p[1] for p in group) / len(group))
        for group in groups
    ]


class RoutePlanner:
    """Exact Held-Karp planning for small scenes, nearest-neighbor + 2-opt otherwise."""

    def __init__(self, config: PlannerConfig):
        self.config = config

    def plan(self, points: list[Point]) -> tuple[list[Point], float, str]:
        points = merge_nearby(points, self.config.merge_distance)
        if not points:
            return [], 0.0, "idle"
        if len(points) <= self.config.exact_limit:
            route = self._held_karp(points)
            algorithm = "held-karp"
        else:
            route = self._two_opt(self._nearest_neighbor(points))
            algorithm = "nearest-neighbor+2opt"
        return route, self.route_length(route), algorithm

    def route_length(self, route: list[Point]) -> float:
        sequence = [self.config.start, *route]
        length = sum(math.dist(a, b) for a, b in zip(sequence, sequence[1:]))
        if self.config.return_to_start and route:
            length += math.dist(route[-1], self.config.start)
        return length

    def _held_karp(self, points: list[Point]) -> list[Point]:
        @lru_cache(maxsize=None)
        def visit(mask: int, last: int) -> tuple[float, tuple[int, ...]]:
            if mask == 1 << last:
                return math.dist(self.config.start, points[last]), (last,)
            previous_mask = mask ^ (1 << last)
            options = []
            for previous in range(len(points)):
                if previous_mask & (1 << previous):
                    cost, path = visit(previous_mask, previous)
                    options.append((cost + math.dist(points[previous], points[last]), path + (last,)))
            return min(options, key=lambda item: item[0])

        full_mask = (1 << len(points)) - 1
        choices = [visit(full_mask, last) for last in range(len(points))]
        if self.config.return_to_start:
            choices = [
                (cost + math.dist(points[path[-1]], self.config.start), path)
                for cost, path in choices
            ]
        _, indices = min(choices, key=lambda item: item[0])
        return [points[index] for index in indices]

    def _nearest_neighbor(self, points: list[Point]) -> list[Point]:
        remaining = points.copy()
        route: list[Point] = []
        current = self.config.start
        while remaining:
            nearest = min(remaining, key=lambda point: math.dist(current, point))
            route.append(nearest)
            remaining.remove(nearest)
            current = nearest
        return route

    def _two_opt(self, route: list[Point]) -> list[Point]:
        improved = True
        while improved:
            improved = False
            baseline = self.route_length(route)
            for left in range(len(route) - 1):
                for right in range(left + 2, len(route) + 1):
                    candidate = route[:left] + list(reversed(route[left:right])) + route[right:]
                    candidate_length = self.route_length(candidate)
                    if candidate_length + 1e-9 < baseline:
                        route, baseline, improved = candidate, candidate_length, True
        return route

