from core.models import Plan, Task
from core.scoring import calculate_score
from core.supervisor import validate_plan


def test_unknown_tool_rejected():
    plan = Plan("WF-X", "x", [Task("T1", "unknown", {})])
    assert validate_plan(plan, {"known"})


def test_incomplete_score_is_not_fabricated():
    result = calculate_score({"available_categories": ["code_quality"]})
    assert result["score"] is None
