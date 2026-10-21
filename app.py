from __future__ import annotations

import asyncio
import os
from pathlib import Path

import streamlit as st

from core.mcp_client import MCPClient
from core.performance import benchmark
from core.planner import build_plan
from core.reporting import csv_report, json_report, markdown_report
from core.supervisor import validate_plan
from core.workflow_engine import WorkflowEngine

ROOT = Path(__file__).parent
DEFAULT_PROJECT = str(ROOT / "sample_quality_project")


def run(coro):
    return asyncio.run(coro)


st.set_page_config(page_title="DevFlow MCP", page_icon="🔧", layout="wide")
if "light_mode" not in st.session_state:
    st.session_state.light_mode = False
st.session_state.light_mode = st.sidebar.toggle("Light mode", value=st.session_state.light_mode)
if st.session_state.light_mode:
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stSidebar"] { background-color: #ffffff; color: #17202a; }
        [data-testid="stMetricValue"], .stMarkdown, label { color: #17202a !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
st.title("DevFlow MCP")
st.caption("MCP-based intelligent developer workflow orchestrator")
project = st.sidebar.text_input("Approved project path", DEFAULT_PROJECT)
allowed_root = os.environ.get("DEVFLOW_ALLOWED_WORKSPACE_ROOT", str(ROOT))
st.sidebar.caption(f"Allowed workspace root: `{allowed_root}`")
st.sidebar.caption("Use a project folder inside this root. Set DEVFLOW_ALLOWED_WORKSPACE_ROOT to audit another trusted parent folder.")
page = st.sidebar.radio("Workspace", ["Workflow Studio", "Tool Explorer", "Performance Lab"])

if page == "Workflow Studio":
    request = st.text_area("Audit request", "Audit this repository for code quality, test inventory, configuration risks, and release readiness.")
    run_tests = st.checkbox("Include approved pytest execution", value=True)
    if "plan" not in st.session_state:
        st.session_state.plan = None
    if st.button("Generate / Validate Plan"):
        plan = build_plan(request, project, run_tests)
        if plan.supported:
            names, _ = run(MCPClient().discover_and_call([]))
            errors = validate_plan(plan, set(names))
            st.session_state.plan = plan
            st.session_state.plan_errors = errors
        else:
            st.error(plan.message)
    plan = st.session_state.plan
    if plan:
        st.subheader("Validated task plan")
        st.json(plan.to_dict())
        if st.session_state.get("plan_errors"):
            st.error("\n".join(st.session_state.plan_errors))
        elif st.button("Approve and Execute"):
            result = run(WorkflowEngine().execute(plan))
            st.session_state.result = result
            st.success(f"Workflow completed with trace {result['trace_id']}")
    if st.session_state.get("result"):
        result = st.session_state.result
        report = result["results"].get(next((k for k, v in result["results"].items() if "audit_status" in v), ""), {})
        if report:
            st.metric("Release score", report.get("score", "Inconclusive"))
            st.write(report.get("audit_status"))
            st.download_button("Download JSON", json_report(report), "devflow-report.json", "application/json")
            st.download_button("Download Markdown", markdown_report(report), "devflow-report.md", "text/markdown")
            st.download_button("Download CSV", csv_report(report), "devflow-findings.csv", "text/csv")
elif page == "Tool Explorer":
    if st.button("Discover live MCP tools"):
        names, _ = run(MCPClient().discover_and_call([]))
        st.success(f"{len(names)} tools discovered from the live server")
        st.write(names)
elif page == "Performance Lab":
    repetitions = st.number_input("Repetitions", min_value=1, max_value=20, value=5)
    if st.button("Run benchmark"):
        result = run(benchmark(project, int(repetitions)))
        st.json(result)
