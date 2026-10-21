import pytest

from core.mcp_client import MCPClient
from core.planner import build_plan
from core.supervisor import validate_plan
from core.workflow_engine import WorkflowEngine


@pytest.mark.asyncio
async def test_workflow_produces_report(sample_project, tmp_path):
    plan = build_plan("audit repository release quality", sample_project, run_tests=False)
    names, _ = await MCPClient().discover_and_call([])
    assert validate_plan(plan, set(names)) == []
    result = await WorkflowEngine(trace_store=__import__("core.tracing", fromlist=["TraceStore"]).TraceStore(str(tmp_path / "trace.jsonl"))).execute(plan)
    assert result["trace_id"].startswith("TRACE-")
    report = next(value for value in result["results"].values()
                  if isinstance(value, dict) and "audit_status" in value)
    assert report["audit_status"] == "complete"
    assert report["score"] is not None
