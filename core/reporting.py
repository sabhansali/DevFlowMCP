from __future__ import annotations

import csv
import io
import json
from typing import Any


def markdown_report(report: dict[str, Any]) -> str:
    lines = ["# DevFlow MCP Quality Report", "", f"Status: **{report.get('audit_status', 'unknown')}**",
             f"Score: **{report.get('score', 'inconclusive')}**", "", "## Findings"]
    for index, finding in enumerate(report.get("findings", []), 1):
        lines.append(f"{index}. **{finding.get('severity', 'INFO')}** {finding.get('description', 'Finding')} "
                     f"({finding.get('file', 'unknown')}:{finding.get('line', '-')})")
    return "\n".join(lines)


def csv_report(report: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["severity", "category", "file", "line", "description", "evidence", "recommendation"])
    writer.writeheader()
    for finding in report.get("findings", []):
        writer.writerow({key: finding.get(key, "") for key in writer.fieldnames})
    return output.getvalue()


def json_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, default=str)
