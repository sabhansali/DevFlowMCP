from typing import Any

REQUIRED_BY_TOOL = {
    "list_project_files": ("status", "files"),
    "analyze_python_project": ("status", "findings", "function_count"),
    "inspect_test_inventory": ("status", "test_files"),
    "check_quality_rules": ("status", "findings"),
    "run_project_tests": ("status", "exit_code"),
    "generate_quality_report": ("status", "audit_status"),
}


def validate_result(tool_name: str, result: Any) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Tool result is not an object"
    missing = [field for field in REQUIRED_BY_TOOL.get(tool_name, ()) if field not in result]
    return (False, f"Missing required fields: {missing}") if missing else (True, "valid")
