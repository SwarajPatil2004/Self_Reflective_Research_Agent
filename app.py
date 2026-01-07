import os
import streamlit as st
from dotenv import load_dotenv, find_dotenv

from src.agent.graph import build_graph
from src.agent.state import AgentState

load_dotenv(find_dotenv(usecwd=True), override=True)

st.set_page_config(page_title="Self-Reflective Research Agent", layout="wide")
st.title("Self-Reflective Research Agent (LangGraph + Ollama)")

# --- Sidebar controls (define ONCE) ---
with st.sidebar:
    st.header("Settings")

    research_enabled = st.toggle(
        "Enable web research",
        value=os.getenv("RESEARCH_ENABLED", "1") == "1",
        key="research_enabled",
    )

    max_iters = st.number_input(
        "Max Reflexion iterations",
        min_value=1, max_value=10,
        value=int(os.getenv("MAX_ITERS", "3")),
        key="max_iters",
    )

    max_search_calls = st.number_input(
        "Max search calls (Budget)",
        min_value=0, max_value=50,
        value=int(os.getenv("BUDGET_MAX_SEARCH_CALLS", "6")),
        key="max_search_calls",
    )

    max_pages_fetched = st.number_input(
        "Max pages fetched (Budget)",
        min_value=0, max_value=50,
        value=int(os.getenv("BUDGET_MAX_PAGES_FETCHED", "6")),
        key="max_pages_fetched",
    )

    recursion_limit = st.number_input(
        "LangGraph recursion_limit",
        min_value=10, max_value=500,
        value=int(os.getenv("LANGGRAPH_RECURSION_LIMIT", "50")),
        key="recursion_limit",
    )

    st.caption("Tip: If your network blocks DDGS, turn research off.")

# Cache graph in session
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_q = st.chat_input("Ask a question…")  # Streamlit chat input pattern [web:420]
if user_q:
    # Apply config for this run (env var approach)
    os.environ["RESEARCH_ENABLED"] = "1" if research_enabled else "0"
    os.environ["MAX_ITERS"] = str(max_iters)
    os.environ["BUDGET_MAX_SEARCH_CALLS"] = str(max_search_calls)
    os.environ["BUDGET_MAX_PAGES_FETCHED"] = str(max_pages_fetched)

    st.session_state.messages.append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.markdown(user_q)

    with st.chat_message("assistant"):
        with st.spinner("Thinking (Planner → Research → Draft → Critique → Revise)…"):
            state: AgentState = {
                "question": user_q,
                "plan": "",
                "research_enabled": bool(research_enabled),
                "sources": [],
                "notes": "",
                "draft": "",
                "critique": "",
                "revision": "",
                "decision": "continue",
                "iteration": 0,
                "quality_score": 0,
                "budget": {
                    "search_calls": 0,
                    "pages_fetched": 0,
                    "token_estimate": 0,
                    "stopped": False,
                    "reasons": [],
                },
            }

            out = st.session_state.graph.invoke(
                state,
                {"recursion_limit": int(recursion_limit)},
            )

            answer = out.get("draft") or out.get("revision") or "(No output)"
            st.markdown(answer)

            sources = out.get("sources", []) or []
            if sources:
                st.markdown("### References")
                for s in sources:
                    st.markdown(f"- **[{s['id']}]** [{s['title']}]({s['url']})")

            with st.expander("Budget / Debug"):
                st.write(out.get("budget", {}))

    st.session_state.messages.append({"role": "assistant", "content": answer})