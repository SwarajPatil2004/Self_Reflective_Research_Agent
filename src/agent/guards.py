import os
from .utils import env_int, rough_token_estimation, has_citation_markers, find_numeric_claim_lines_without_cites

class BudgetGuard:

    def __init__(self):
        self.max_search_calls = env_int("BUDGET_MAX_SEARCH_CALLS", 6)
        self.max_pages_fetched = env_int("BUDGET_MAX_PAGES_FETCHED", 6)
        self.max_token_estimate = env_int("BUDGET_MAX_TOKEN_ESTIMATE", 24000)

    def add_tokens(self, state, text: str, reason: str):
        inc = rough_token_estimation(text)
        state["budget"]["token_estimate"] += inc
        if state["budget"]["token_estimate"] > self.max_token_estimate:
            self.stop(state, f"Token estimate exceeded after {reason} (+{inc}).")

    def inc_search(self, state):
        state["budget"]["search_calls"] += 1
        if state["budget"]["search_calls"] > self.max_search_calls:
            self.stop(state, "Maximum search calls limit exceeded.")

    def fetch(self, state):
        state["budget"]["pages_fetched"] += 1
        if state["budget"]["pages_fetched"] > self.max_pages_fetched:
            self.stop(state, "Maximum pages fetch limit exceeded.")

    def stop(self, state, why: str):
        state["budget"]["stopped"] = True
        state["budget"]["reasons"].append(why)

    def is_stopped(self, state) -> bool:
        return bool(state["budget"]["stopped"])
    
class QualityGate:

    def __init__(self):
        self.require_citations = os.getenv("REQUIRE_CITATIONS_WHEN_RESEARCH_ENABLED", "1") == "1"
        
    def check(self, state, text: str) -> tuple[int, str]:
        '''
        Returns: (score 0-10, critique_text)
        '''
        if not state["research_enabled"] or self.require_citations is False:
            if "verify" in (text or "") or "Verify" in (text or ""):
                return (8, "Good: Includes verification guidance while research is disabled.")
            
            return (5, "Research is disabled / blocked. Add uncertainity and clear verification guidance using the term- verify")
        
        if not has_citation_markers(text):
            return (3, "Missing citation marks. Add inline markers like [S#] representing a source while claiming a fact.")
        
        bad_lines = find_numeric_claim_lines_without_cites(text)
        if bad_lines:
            sample= "\n".join(f"- {l}" for l in bad_lines[:6])
            return (6, f"Some numeric/dated claims lack citations. Add [S#] on the same line:\n{sample}")
        
        return (9, "No major issues: citations present and numeric claims appear supported.")