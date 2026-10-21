from __future__ import annotations

import uuid

from .models import Plan, Task


def build_plan(request: str, project_path: str, run_tests: bool = False) -> Plan:
    text = request.lower().strip()
    supported_terms = ("audit", "inspect", "quality", "test", "repository", "code", "release")
    if not request or not any(term in text for term in supported_terms):
        return Plan(str(uuid.uuid4()), request, [], False,
                    "Supported requests mention repository, code, quality, tests, audit, or release.")
    prefix = str(uuid.uuid4())[:8].upper()
    tasks = [
        Task(f"{prefix}-001", "list_project_files", {"project_path": project_path},
             expected_output="file inventory"),
        Task(f"{prefix}-002", "analyze_python_project", {"project_path": project_path},
             expected_output="AST metrics and findings"),
        Task(f"{prefix}-003", "inspect_test_inventory", {"project_path": project_path},
             expected_output="test inventory and potential gaps"),
        Task(f"{prefix}-004", "check_quality_rules", {"project_path": project_path},
             expected_output="quality checks and findings"),
    ]
    if run_tests or "test" in text or "release" in text or "audit" in text:
        tasks.append(Task(f"{prefix}-005", "run_project_tests",
                          {"project_path": project_path, "test_targets": ["tests"], "timeout_seconds": 60, "approved": True},
                          dependencies=[tasks[2].task_id], expected_output="pytest result", risk="MEDIUM"))
    tasks.append(Task(f"{prefix}-006", "generate_quality_report",
                      {"project_path": project_path, "results": {}},
                      dependencies=[task.task_id for task in tasks],
                      expected_output="validated report"))
    return Plan(f"WF-{prefix}", request, tasks)
