import json

from core.reporting import csv_report, json_report, markdown_report
from core.tracing import TraceStore


def test_report_exports():
    report = {"audit_status": "complete", "score": 88, "findings": []}
    assert '"score": 88' in json_report(report)
    assert "DevFlow" in markdown_report(report)
    assert "severity" in csv_report(report)


def test_jsonl_trace(tmp_path):
    store = TraceStore(str(tmp_path / "trace.jsonl"))
    store.append(trace_id="T", task_id="1", status="success")
    assert json.loads((tmp_path / "trace.jsonl").read_text())["trace_id"] == "T"
