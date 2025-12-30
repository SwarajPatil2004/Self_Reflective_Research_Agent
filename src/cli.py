import os
import sys

from dotenv import load_dotenv
from agent.graph import build_graph
from agent.state import AgentState

def main():

    load_dotenv()
    graph = build_graph()

    if len(sys.argv) > 1:
        question = "".join(sys.argv[1:])                #For question(s) mentioned in command-line
    
    else:
        question = input("Question: ").strip()          #For interactive behaviour

    state : AgentState = {
        "question" : question,
        "plan" : "",
        "research_enabled" : os.getenv("RESEARCH_ENABLED", "1") == "1",
        "sources" : [],
        "notes" : "",
        "draft" : "",
        "critique" : "",
        "revision" : "",
        "decision" : "continue",
        "iteration" : 0,
        "quality_score" : 0,
        'budget' : {
            "search_calls" : 0,
            "pages_fetched" : 0,
            "token_estimate" : 0,
            "stopped" : False,
            "reasons" : []
        }
    }

    out = graph.invoke(state)

    print("----- Result -----")
    print(out.get("draft") or out.get("revision") or "")

    print("----- Sources -----")
    for s in out.get("sources",[]):
        print(f"[{s['id']}] {s['title']} {s['url']}")


if __name__ == "__main__":
    main()