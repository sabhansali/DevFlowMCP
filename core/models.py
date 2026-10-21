from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    RETRYING = "retrying"


@dataclass
class Task:
    task_id: str
    tool_name: str
    arguments: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    expected_output: str = ""
    risk: str = "LOW"
    required: bool = True
    state: TaskState = TaskState.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"state": self.state.value}


@dataclass
class Plan:
    workflow_id: str
    request: str
    tasks: list[Task]
    supported: bool = True
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"workflow_id": self.workflow_id, "request": self.request,
                "supported": self.supported, "message": self.message,
                "tasks": [task.to_dict() for task in self.tasks]}
