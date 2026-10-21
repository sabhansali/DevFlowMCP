from pathlib import Path

import pytest

from core.mcp_client import MCPClient


@pytest.mark.asyncio
async def test_failing_fixture_is_reported():
    project = str(Path(__file__).parents[1] / "fixtures" / "repositories" / "failing_tests_project")
    result = await MCPClient().call(
        "run_project_tests",
        {"project_path": project, "test_targets": ["tests"], "timeout_seconds": 5, "approved": True},
    )
    assert result["status"] == "failed", result
    assert result["exit_code"] != 0


@pytest.mark.asyncio
async def test_timeout_fixture_is_reported():
    project = str(Path(__file__).parents[1] / "fixtures" / "repositories" / "timeout_project")
    result = await MCPClient().call(
        "run_project_tests",
        {"project_path": project, "test_targets": ["tests"], "timeout_seconds": 1, "approved": True},
    )
    assert result["status"] == "timed_out"
    assert result["error_category"] == "timeout"
