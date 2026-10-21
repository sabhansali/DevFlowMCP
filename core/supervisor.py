from __future__ import annotations

from .models import Plan
from .policy import check_tool


def validate_plan(plan: Plan, discovered_tools: set[str], allow_tests: bool = True) -> list[str]:
    errors = []
    ids = {task.task_id for task in plan.tasks}
    for task in plan.tasks:
        if task.tool_name not in discovered_tools:
            errors.append(f"{task.task_id}: tool {task.tool_name} was not discovered")
        missing = set(task.dependencies) - ids
        if missing:
            errors.append(f"{task.task_id}: missing dependencies {sorted(missing)}")
        decision = check_tool(task.tool_name, task.arguments, allow_tests)
        if not decision.allowed:
            errors.append(f"{task.task_id}: {decision.reason}")
    if _has_cycle(plan):
        errors.append("Task graph contains a cycle")
    return errors


def _has_cycle(plan: Plan) -> bool:
    graph = {task.task_id: task.dependencies for task in plan.tasks}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(dep) for dep in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)
