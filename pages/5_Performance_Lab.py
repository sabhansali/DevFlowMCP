"""Performance Lab page."""
import asyncio

import streamlit as st

from core.performance import benchmark

st.set_page_config(page_title="Performance Lab")
st.title("Performance Lab")
project = st.text_input("Approved project path", st.session_state.get("project", "sample_quality_project"))
repetitions = st.number_input("Repetitions", min_value=1, max_value=20, value=5)
if st.button("Run benchmark"):
    st.session_state.benchmark = asyncio.run(benchmark(project, int(repetitions)))
if st.session_state.get("benchmark"):
    st.json(st.session_state.benchmark)
