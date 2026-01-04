## Overview
This is a copy-paste notebook plan for Windows 11 that stays free: local Ollama + free DDGS search + local evaluation.

> Use Jupyter Notebook or VS Code Notebook.

***

## Cell 1 — Create/activate venv
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Cell 2 — Configure environment
```powershell
copy .env.example .env
```

Open `.env` and set:
- `OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M`
- `RESEARCH_ENABLED=1`
- Budget limits (pages, chars, token estimate)

## Cell 3 — Start Ollama and pull model
```powershell
ollama serve
```

In a new terminal:
```powershell
ollama pull llama3.1:8b-instruct-q4_K_M
```

Ollama provides local inference on Windows.[2]

## Cell 4 — Quick Ollama API test (PowerShell)
```powershell
$body = @{
  model  = "llama3.1:8b-instruct-q4_K_M"
  prompt = "Say hi"
  stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:11434/api/generate" -ContentType "application/json" -Body $body
```

## Cell 5 — Run the agent (one-shot)
```powershell
python -m src.cli "Explain Reflexion in LangGraph with citations."
```

## Cell 6 — Switch variants (single place)
Edit `.env`:
- Small/dry run:
  - `RESEARCH_ENABLED=0`
  - `MAX_ITERS=1`
- Full run:
  - `RESEARCH_ENABLED=1`
  - `MAX_ITERS=3`

## Cell 7 — Data loading + validation (Sample_Dataset.jsonl)
```python
import json

path = "Sample_Dataset.jsonl"
rows = []
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

assert len(rows) >= 10
for r in rows:
    assert "id" in r and "question" in r and "research_enabled" in r
print("Loaded", len(rows), "rows")
```

## Cell 8 — Inference demo over dataset
```python
import subprocess, json, shlex

def run_query(q: str):
    cmd = f'python -m src.cli "{q}"'
    return subprocess.check_output(cmd, shell=True, text=True, encoding="utf-8", errors="ignore")

# Demo first 3
for r in rows[:3]:
    print("====", r["id"], "====")
    print(run_query(r["question"])[:1200])
```

## Cell 9 — Offline evaluation script (simple rubric)
```python
import re

def has_valid_cites(text: str) -> bool:
    return bool(re.search(r"\[S\d+\]", text or ""))

def has_how_to_verify(text: str) -> bool:
    return "How to verify" in (text or "")

# Simple checks (expand as needed)
results = []
for r in rows:
    out = run_query(r["question"])
    results.append({
        "id": r["id"],
        "research_enabled": r["research_enabled"],
        "has_cites": has_valid_cites(out),
        "has_verify": has_how_to_verify(out),
    })

bad = [x for x in results if x["research_enabled"] and not x["has_cites"]]
print("Missing cites (research_enabled=1):", len(bad))
```

## Cell 10 — Troubleshooting table
| Problem | Cause | Fix |
|---|---|---|
| OOM / slow | Model too big | Use smaller model or lower max iterations |
| DDGS errors / WinError 10013 | Network/firewall blocks search backend | Set `RESEARCH_ENABLED=0` or try different network |
| Duplicate References | Model printed references + code appended | Strip model references in `cli.py` and keep only appended block |
| Fake citations [S7] | Model hallucinated IDs | Add “only cite provided sources” rule + Quality Gate |

DDGS is free and requires no API key, but it can fail depending on network policies.[5][4]

***
