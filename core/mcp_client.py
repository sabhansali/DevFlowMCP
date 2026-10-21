from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(self, server_script: str | None = None):
        self.server_module = "mcp_server.server"
        self.server_script = server_script or str(Path(__file__).parents[1] / "mcp_server" / "server.py")

    async def discover_and_call(self, calls: list[tuple[str, dict[str, Any]]]) -> tuple[list[str], list[dict[str, Any]]]:
        args = ["-m", self.server_module] if self.server_script.endswith("server.py") else [self.server_script]
        params = StdioServerParameters(command=sys.executable, args=args, env=None)
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = [tool.name for tool in tools.tools]
                results = []
                for name, arguments in calls:
                    response = await session.call_tool(name, arguments)
                    results.append(_decode(response))
                return names, results

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        _, results = await self.discover_and_call([(name, arguments)])
        return results[0]


def _decode(response: Any) -> dict[str, Any]:
    if getattr(response, "isError", False):
        message = "MCP tool returned an error"
        for content in getattr(response, "content", []):
            message = getattr(content, "text", message) or message
        raise RuntimeError(message)
    if getattr(response, "structuredContent", None):
        return response.structuredContent
    for content in getattr(response, "content", []):
        text = getattr(content, "text", "")
        try:
            value = json.loads(text)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    return {"status": "error", "error": "MCP response did not contain structured JSON"}
