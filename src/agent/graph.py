from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    planner_node,
    research_node,
    draft_node,
    critique_node,
    revise_node,
    decide_node,
)

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("planner", planner_node)
    g.add_node("research", research_node)
    g.add_node("draft", draft_node)
    g.add_node("critique", critique_node)
    g.add_node("revise", revise_node)
    g.add_node("decide", decide_node)

    g.add_edge(START, "planner")
    g.add_edge("planner", "research")
    g.add_edge("research", "draft")
    g.add_edge("draft", "critique")
    g.add_edge("critique", "revise")
    g.add_edge("revise", "decide")

    def route(state: AgentState):
        return END if state["decision"] == "stop" else "research"

    g.add_conditional_edges("decide", route, {END: END, "research": "research"})
    return g.compile()
