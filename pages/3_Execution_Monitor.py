"""Execution Monitor page."""
import streamlit as st

st.set_page_config(page_title="Execution Monitor")
st.title("Execution Monitor")
result = st.session_state.get("result")
if not result:
    st.warning("No workflow execution is available yet.")
else:
    st.success(f"Trace ID: {result['trace_id']}")
    st.metric("Duration", f"{result['duration_seconds']:.2f} seconds")
    st.dataframe(result["tasks"], use_container_width=True)
