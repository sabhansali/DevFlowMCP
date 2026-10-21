from __future__ import annotations

import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Any

from .mcp_client import MCPClient

CALLS = ("list_project_files", "analyze_python_project", "inspect_test_inventory", "check_quality_rules")


async def benchmark(project_path: str, repetitions: int = 5, client: MCPClient | None = None) -> dict[str, Any]:
    client = client or MCPClient()
    samples: dict[str, list[float]] = {"sequential": [], "parallel": []}
    for _ in range(max(1, repetitions)):
        started = time.perf_counter()
        for name in CALLS:
            await client.call(name, {"project_path": project_path})
        samples["sequential"].append(time.perf_counter() - started)
        started = time.perf_counter()
        await asyncio.gather(*(client.call(name, {"project_path": project_path}) for name in CALLS))
        samples["parallel"].append(time.perf_counter() - started)
    stats = {}
    for mode, values in samples.items():
        stats[mode] = {"samples": values, "mean": statistics.mean(values), "median": statistics.median(values),
                       "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                       "minimum": min(values), "maximum": max(values)}
    sequential, parallel = stats["sequential"]["mean"], stats["parallel"]["mean"]
    result = {"calls": list(CALLS), "repetitions": repetitions, "sequential": stats["sequential"],
              "parallel": stats["parallel"], "speedup": sequential / parallel if parallel else None,
              "time_reduction_percent": ((sequential - parallel) / sequential * 100) if sequential else None}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/benchmark.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
