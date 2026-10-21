from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from .mcp_client import MCPClient
from .models import Plan, Task, TaskState
from .recovery import classify
from .tracing import TraceStore
from .validator import validate_result


class WorkflowEngine:
    def __init__(self, client: MCPClient | None = None, max_concurrency: int = 4,
                 retries: int = 1, trace_store: TraceStore | None = None):
        self.client = client or MCPClient()
        self.max_concurrency = max(1, max_concurrency)
        self.retries = max(0, retries)
        self.trace_store = trace_store or TraceStore()

    async def execute(self, plan: Plan) -> dict[str, Any]:
        trace_id = f"TRACE-{uuid.uuid4().hex[:10].upper()}"
        tasks = {task.task_id: task for task in plan.tasks}
        results: dict[str, Any] = {}
        started = time.perf_counter()
        while True:
            pending = [task for task in tasks.values() if task.state in {TaskState.PENDING, TaskState.READY}]
            if not pending:
                break
            ready = []
            for task in pending:
                dependencies = [tasks[dep] for dep in task.dependencies]
                if any(dep.state in {TaskState.FAILED, TaskState.BLOCKED, TaskState.TIMED_OUT} for dep in dependencies):
                    task.state = TaskState.BLOCKED
                    task.error = "Required dependency failed"
                elif all(dep.state == TaskState.SUCCEEDED for dep in dependencies):
                    task.state = TaskState.READY
                    ready.append(task)
            if not ready:
                break
            batch = ready[:self.max_concurrency]
            await asyncio.gather(*(self._run_task(task, tasks, results, trace_id) for task in batch))
        return {"trace_id": trace_id, "workflow_id": plan.workflow_id, "tasks": [task.to_dict() for task in tasks.values()],
                "results": results, "duration_seconds": time.perf_counter() - started,
                "dop": min(self.max_concurrency, len(plan.tasks)), "dos": sum(bool(t.dependencies) for t in plan.tasks)}

    async def _run_task(self, task: Task, tasks: dict[str, Task], results: dict[str, Any], trace_id: str) -> None:
        if task.tool_name == "generate_quality_report":
            task.arguments["results"] = results
        task.state = TaskState.RUNNING
        task.attempts += 1
        start = time.perf_counter()
        try:
            result = await asyncio.wait_for(self.client.call(task.tool_name, task.arguments), timeout=90)
            valid, validation_message = validate_result(task.tool_name, result)
            if not valid:
                raise ValueError(validation_message)
            task.result = result
            results[task.task_id] = result
            task.state = TaskState.SUCCEEDED
            error_category = None
        except Exception as exc:  # noqa: BLE001 - task failures are classified centrally
            decision = classify(exc, task.attempts, self.retries, task.tool_name)
            error_category = decision.category
            if decision.retry and task.attempts <= self.retries:
                task.state = TaskState.PENDING
                task.error = str(exc)
                return
            task.state = TaskState.TIMED_OUT if "timeout" in decision.category else TaskState.FAILED
            task.error = str(exc)
        self.trace_store.append(trace_id=trace_id, task_id=task.task_id, tool_name=task.tool_name,
                                arguments={"keys": sorted(task.arguments)}, status=task.state.value,
                                started_at=start, completed_at=time.perf_counter(),
                                duration_ms=round((time.perf_counter() - start) * 1000, 2),
                                retry_count=max(0, task.attempts - 1), error_category=error_category,
                                validation_status="valid" if task.state == TaskState.SUCCEEDED else "failed",
                                dependencies=task.dependencies, execution_mode="parallel")
