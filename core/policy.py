from dataclasses import dataclass
from typing import Any


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    risk: str = "LOW"


def check_tool(tool_name: str, arguments: dict[str, Any], allow_tests: bool = True) -> PolicyDecision:
    allowed_tools = {"list_project_files", "read_project_file", "search_code", "analyze_python_project",
                     "inspect_test_inventory", "run_project_tests", "check_quality_rules", "generate_quality_report"}
    if tool_name not in allowed_tools:
        return PolicyDecision(False, "Tool is not registered in the policy", "HIGH")
    if tool_name == "run_project_tests" and (not allow_tests or not arguments.get("approved")):
        return PolicyDecision(False, "Explicit test approval is required", "MEDIUM")
    if any(key in arguments for key in ("command", "shell_command")):
        return PolicyDecision(False, "Arbitrary shell commands are not permitted", "HIGH")
    return PolicyDecision(True, "Allowed by configured policy", "MEDIUM" if tool_name == "run_project_tests" else "LOW")
