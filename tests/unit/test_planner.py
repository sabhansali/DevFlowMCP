from core.planner import build_plan


def test_full_plan_has_dependencies():
    plan = build_plan("audit repository quality and tests", "sample_quality_project")
    assert plan.supported
    assert len(plan.tasks) == 6
    assert plan.tasks[-1].dependencies


def test_unsupported_request_is_explicit():
    plan = build_plan("make me a sandwich", "sample_quality_project")
    assert not plan.supported
    assert "Supported" in plan.message
