from core.policy import check_tool
from mcp_server.security import SecurityError, safe_file


def test_policy_blocks_unapproved_tests():
    assert not check_tool("run_project_tests", {"approved": False}).allowed


def test_unknown_tool_blocked():
    assert not check_tool("shell", {}).allowed


def test_traversal_rejected(sample_project):
    try:
        safe_file(sample_project, "../../outside.txt")
    except (SecurityError, FileNotFoundError):
        return
    raise AssertionError("Traversal was accepted")
