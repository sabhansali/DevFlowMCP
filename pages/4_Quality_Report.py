"""Quality Report page."""
import streamlit as st

from core.reporting import csv_report, json_report, markdown_report

st.set_page_config(page_title="Quality Report")
st.title("Quality Report")
result = st.session_state.get("result")
report = None
if result:
    report = next((value for value in result["results"].values()
                   if isinstance(value, dict) and "audit_status" in value), None)
if not report:
    st.warning("No quality report is available yet.")
else:
    st.metric("Release score", report.get("score", "Inconclusive"))
    st.write(report.get("audit_status"))
    st.dataframe(report.get("findings", []), use_container_width=True)
    st.download_button("Download JSON", json_report(report), "devflow-report.json", "application/json")
    st.download_button("Download Markdown", markdown_report(report), "devflow-report.md", "text/markdown")
    st.download_button("Download CSV", csv_report(report), "devflow-findings.csv", "text/csv")
