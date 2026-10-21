"""Workflow Studio page."""
import streamlit as st

st.set_page_config(page_title="Workflow Studio")
st.title("Workflow Studio")
st.info("Use the Workflow Studio controls in the main app to generate and execute a plan.")
if st.session_state.get("plan"):
    st.json(st.session_state.plan.to_dict())
else:
    st.warning("No plan has been generated yet.")
