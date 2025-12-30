from typing import TypedDict, List, Literal, Dict, Any

Decision = Literal["stop", "continue"]

class Source(TypedDict):
    id : str
    url : str
    title : str
    snippet : str

class BudgetState(TypedDict):
    search_calls : int
    pages_fetched : int
    token_estimate : int
    stopped : bool
    reason : List[str]

class AgentState(TypedDict):
    # Main state objects passed around the graph
    question : str
    plan : str

    # Research-related fields
    research_enabled : bool
    sources : List[Source]
    notes : str

    # Writing and Reflexion loops
    draft : str
    critique : str
    revision : str

    # Loop control fields
    decision : Decision
    iteration : int
    quality_score : int
    budget : BudgetState