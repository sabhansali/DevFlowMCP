from typing import Any


def calculate_score(report: dict[str, Any]) -> dict[str, Any]:
    required = {"code_quality", "test_health", "security", "documentation"}
    available = set(report.get("available_categories", []))
    if not required.issubset(available):
        return {"score": None, "status": "incomplete", "missing_categories": sorted(required - available)}
    return {"score": report.get("score"), "status": report.get("audit_status", "incomplete"), "missing_categories": []}
