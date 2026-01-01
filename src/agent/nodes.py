import os
from typing import List
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from duckduckgo_search import DDGS
from langchain_ollama import ChatOllama

from .state import AgentState, Source
from .prompts import PLANNER_PROMPT, RESEARCH_PROMPT, DRAFT_PROMPT, CRITIQUE_PROMPT, REVISE_PROMPT
from .guards import BudgetGuard, QualityGate
from .utils import env_int, env_float

def _llm() -> ChatOllama:
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=env_float("OLLAMA_TEMPERATURE", 0.2),
    )

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def fetch_page_text(url: str, timeout: int, max_chars: int) -> str:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text("\n", strip=True)
        return text[:max_chars]

def planner_node(state: AgentState) -> AgentState:
    llm = _llm()
    bg = BudgetGuard()
    q = state["question"]

    prompt = f"{PLANNER_PROMPT}\n\nUser question:\n{q}\n"
    bg.add_tokens(state, prompt, "planner prompt")
    if bg.is_stopped(state):
        state["plan"] = "Budget stopped before planning; proceed cautiously with verification steps."
        return state

    state["plan"] = llm.invoke(prompt).content
    bg.add_tokens(state, state["plan"], "planner output")
    return state

def research_node(state: AgentState) -> AgentState:
    bg = BudgetGuard()
    if not state["research_enabled"] or bg.is_stopped(state):
        return state

    # 1) Search (free, no key)
    bg.inc_search(state)
    if bg.is_stopped(state):
        return state

    max_results = env_int("DDG_MAX_RESULTS", 5)
    region = os.getenv("DDG_REGION", "wt-wt")
    safesearch = os.getenv("DDG_SAFESEARCH", "moderate")
    timelimit = os.getenv("DDG_TIME_LIMIT", "y")

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(state["question"], region=region, safesearch=safesearch, timelimit=timelimit, max_results=max_results):
            results.append(r)

    sources: List[Source] = []
    for i, r in enumerate(results, start=1):
        sources.append({
            "id": f"S{i}",
            "url": r.get("href", ""),
            "title": r.get("title", "") or f"Result {i}",
            "snippet": r.get("body", "") or "",
        })
    state["sources"] = sources

    # 2) Fetch a small number of pages
    timeout = env_int("HTTP_TIMEOUT_SECS", 15)
    max_chars = env_int("BUDGET_MAX_CHARS_PER_PAGE", 12000)

    fetched_blocks = []
    for s in state["sources"][: env_int("BUDGET_MAX_PAGES_FETCHED", 6)]:
        if bg.is_stopped(state):
            break
        if not s["url"]:
            continue

        bg.inc_fetch(state)
        if bg.is_stopped(state):
            break

        try:
            text = fetch_page_text(s["url"], timeout=timeout, max_chars=max_chars)
            fetched_blocks.append(f"[{s['id']}] {s['title']}\nURL: {s['url']}\nEXTRACT:\n{text}\n")
            bg.add_tokens(state, text, f"fetch {s['id']}")
        except Exception:
            fetched_blocks.append(f"[{s['id']}] {s['title']}\nURL: {s['url']}\nEXTRACT: (failed to fetch)\n")

    # 3) Synthesize notes
    llm = _llm()
    prompt = (
        f"{RESEARCH_PROMPT}\n\n"
        f"Question: {state['question']}\n\n"
        f"Plan:\n{state['plan']}\n\n"
        f"Sources (snippets):\n" +
        "\n".join(f"[{s['id']}] {s['title']} — {s['snippet']}" for s in state["sources"]) +
        "\n\nFetched text:\n" + "\n".join(fetched_blocks)
    )
    bg.add_tokens(state, prompt, "research prompt")
    if bg.is_stopped(state):
        state["notes"] = "Budget stopped during research; proceed with uncertainty and verification steps."
        return state

    state["notes"] = llm.invoke(prompt).content
    bg.add_tokens(state, state["notes"], "research notes output")
    return state

def draft_node(state: AgentState) -> AgentState:
    llm = _llm()
    bg = BudgetGuard()

    context = ""
    if state["research_enabled"] and state["sources"] and state["notes"] and not bg.is_stopped(state):
        context = f"Research notes:\n{state['notes']}\n\nSources:\n" + "\n".join(
            f"[{s['id']}] {s['title']} — {s['url']}" for s in state["sources"]
        )
    else:
        context = "Research unavailable/blocked. Be cautious and include verification steps."

    prompt = f"{DRAFT_PROMPT}\n\nQuestion:\n{state['question']}\n\n{context}\n"
    bg.add_tokens(state, prompt, "draft prompt")
    if bg.is_stopped(state):
        state["draft"] = "Budget stopped before drafting. Provide a cautious outline and verification steps."
        return state

    state["draft"] = llm.invoke(prompt).content
    bg.add_tokens(state, state["draft"], "draft output")
    return state

def critique_node(state: AgentState) -> AgentState:
    llm = _llm()
    bg = BudgetGuard()
    qg = QualityGate()

    # LLM critique (Reflexion)
    prompt = f"{CRITIQUE_PROMPT}\n\nQuestion:\n{state['question']}\n\nDraft:\n{state['draft']}\n"
    bg.add_tokens(state, prompt, "critique prompt")

    if bg.is_stopped(state):
        state["critique"] = "Budget stopped; skipping critique."
        state["quality_score"] = 0
        return state

    critique = llm.invoke(prompt).content
    bg.add_tokens(state, critique, "critique output")

    # Rule-based Quality Gate overlays the critique
    score, gate_feedback = qg.check(state, state["draft"])
    state["quality_score"] = score
    state["critique"] = f"{critique}\n\n[QualityGate]\nScore={score}\n{gate_feedback}"
    return state

def revise_node(state: AgentState) -> AgentState:
    llm = _llm()
    bg = BudgetGuard()

    prompt = f"{REVISE_PROMPT}\n\nDraft:\n{state['draft']}\n\nCritique:\n{state['critique']}\n"
    bg.add_tokens(state, prompt, "revise prompt")
    if bg.is_stopped(state):
        state["revision"] = state["draft"]
        return state

    state["revision"] = llm.invoke(prompt).content
    bg.add_tokens(state, state["revision"], "revise output")

    # After revision, treat revision as the new draft
    state["draft"] = state["revision"]
    return state

def decide_node(state: AgentState) -> AgentState:
    state["iteration"] += 1
    max_iters = env_int("MAX_ITERS", 3)
    min_score = env_int("EARLY_STOP_MIN_SCORE", 8)

    if state["budget"]["stopped"]:
        state["decision"] = "stop"
        return state

    if state["quality_score"] >= min_score:
        state["decision"] = "stop"
        return state

    if state["iteration"] >= max_iters:
        state["decision"] = "stop"
        return state

    state["decision"] = "continue"
    return state