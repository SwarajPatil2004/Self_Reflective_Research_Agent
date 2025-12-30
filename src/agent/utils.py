import os
import re
import math

def env_int(name : str, default : int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default
    
def env_float(name : str, default : float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default
    
def rough_token_estimation(text: str) -> int:
    # 4 char per token -> roughly for this llm.
    if not text:
        return 0
    return max(1, math.ceil(len(text)/4))

def has_citation_markers(text: str) -> bool:
    return bool(re.search(r"\[S\d+\]", text or ""))

def find_numeric_claim_lines_without_cites(text: str) -> list[str]:
    '''
    Heuristic Quality Gate:
    - If a line contains digits (year, stats, quantity) and research is enabled, requires at least one [S#] marker on that line.
    '''

    bad = []
    for line in (text or "").splitlines():
        if any (ch.isdigit for ch in line) and ("[S" not in line):
            #ignore headings
            if line.strip().startswith("#"):
                continue
            bad.append(line.strip())
    return [b for b in bad if b]