from tennis_robot.config import PlannerConfig
from tennis_robot.planner import RoutePlanner, merge_nearby


def test_merge_nearby_reduces_collection_groups():
    assert len(merge_nearby([(0, 0), (3, 4), (100, 0)], 10)) == 2


def test_exact_route_uses_all_points():
    planner = RoutePlanner(PlannerConfig(start=(0, 0), exact_limit=12, merge_distance=1))
    route, length, algorithm = planner.plan([(10, 0), (10, 10), (0, 10)])
    assert len(route) == 3
    assert length > 0
    assert algorithm == "held-karp"
