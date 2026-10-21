from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def configure_logging() -> None:
    logging.basicConfig(filename="logs/devflow.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")


class TraceStore:
    def __init__(self, path: str = "logs/mcp_traces.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, **event: Any) -> None:
        event.setdefault("timestamp", datetime.now(UTC).isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=str) + "\n")

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
