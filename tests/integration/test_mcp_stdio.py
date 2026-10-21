import pytest
from mcp.shared.exceptions import McpError

from core.mcp_client import MCPClient


@pytest.mark.asyncio
async def test_real_stdio_discovery_and_tools(sample_project):
    client = MCPClient()
    names, results = await client.discover_and_call([
        ("list_project_files", {"project_path": sample_project}),
        ("analyze_python_project", {"project_path": sample_project}),
    ])
    assert set(names) == {
        "list_project_files", "read_project_file", "search_code", "analyze_python_project",
        "inspect_test_inventory", "run_project_tests", "check_quality_rules", "generate_quality_report",
    }
    assert results[0]["status"] == "success"
    assert results[1]["function_count"] >= 2


@pytest.mark.asyncio
async def test_real_stdio_rejects_traversal(sample_project):
    with pytest.raises((RuntimeError, McpError, BaseExceptionGroup)):
        await MCPClient().call("read_project_file", {"project_path": sample_project, "file_path": "../../outside.txt"})
