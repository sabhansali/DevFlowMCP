"""Live MCP Tool Explorer page."""
import asyncio

import streamlit as st

from core.mcp_client import MCPClient

st.set_page_config(page_title="MCP Tool Explorer")
st.title("MCP Tool Explorer")
if st.button("Discover live MCP tools"):
    names, _ = asyncio.run(MCPClient().discover_and_call([]))
    st.session_state.discovered_tools = names
tools = st.session_state.get("discovered_tools", [])
st.metric("Discovered tools", len(tools))
st.write(tools)
