# Self-Reflective Research Agent (LangGraph + Ollama)

A $0 “DeepResearch-like” self-reflective research agent that runs locally with **LangGraph** and a Reflexion loop:

Planner → Research → Draft → Critique → Revise → Decide (Stop/Continue)

Local LLM inference is done via **Ollama** (GPU if available, CPU fallback). External research uses free web search (DDG via `ddgs`) and free page fetching.

---

## Features

- Cyclic LangGraph workflow with Reflexion loop (self-critique + revision).  
- Budget Guard: hard limits for search calls / page fetches / rough token estimate.  
- Quality Gate: enforces citations when research is enabled; otherwise forces uncertainty + verification steps.  
- Works offline (set `RESEARCH_ENABLED=0`).  
- Windows 11 friendly (WSL2 optional).

---

## Repo structure

```text
Self_Reflective_Research_Agent/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ Makefile
├─ scripts/
│  ├─ smoke_test_windows.ps1
│  └─ smoke_test_wsl.sh
└─ src/
   ├─ __init__.py
   ├─ cli.py
   └─ agent/
      ├─ __init__.py
      ├─ graph.py
      ├─ guards.py
      ├─ nodes.py
      ├─ prompts.py
      ├─ state.py
      └─ utils.py
```

---

## Requirements

- Windows 11 (recommended)  
- Python 3.11+  
- Ollama installed and running  
- (Optional) NVIDIA GPU with CUDA drivers for faster inference

---

## 1) Setup (Windows PowerShell)

From the repo root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip

pip install -r requirements.txt

copy .env.example .env
```

---

## 2) Start Ollama + pull a model

### Start Ollama
- Start the **Ollama** desktop app from Start Menu, OR
- Run in terminal:

```powershell
ollama serve
```

### Pull the default model

```powershell
ollama pull llama3.1:8b-instruct-q4_K_M
```

### Verify Ollama API (PowerShell)

```powershell
$body = @{
  model  = "llama3.1:8b-instruct-q4_K_M"
  prompt = "Say hi"
  stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:11434/api/generate" -ContentType "application/json" -Body $body
```

---

## 3) Configure `.env`

Open `.env` and set:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
OLLAMA_TEMPERATURE=0.2

RESEARCH_ENABLED=1
MAX_ITERS=3
EARLY_STOP_MIN_SCORE=8

BUDGET_MAX_SEARCH_CALLS=6
BUDGET_MAX_PAGES_FETCHED=8
BUDGET_MAX_CHARS_PER_PAGE=12000
BUDGET_MAX_TOKEN_ESTIMATE=80000
```

Notes:
- If your network blocks free web search (DDG / mojeek routing), set `RESEARCH_ENABLED=0`.
- If you want faster and more stable runs, reduce `BUDGET_MAX_PAGES_FETCHED` and `BUDGET_MAX_CHARS_PER_PAGE`.

---

## 4) Run the agent

### One-shot
```powershell
python -m src.cli "Write a short brief on LangGraph Reflexion and add citations."
```

### Interactive
```powershell
python -m src.cli
```

You’ll see:
- `--- FINAL ANSWER ---`
- `--- SOURCES ---` (and the code appends a single clean `## References` block)

---

## 5) Use the Makefile (Windows)

Windows doesn’t ship with GNU `make`. Install one of these:

### Option A: Scoop (no admin)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
scoop install make
make --version
```

Then run targets (repo root, venv activated):

```powershell
.\.venv\Scripts\activate
make run
make run-i
make test-smoke
```

### Option B: WSL2
Inside WSL2:

```bash
sudo apt update
sudo apt install -y make
make run
```

---

## How the Reflexion loop works

### Nodes
- **Planner**: Creates a compact research plan for the question.
- **Research**: Runs free web search + fetches a small number of pages + synthesizes notes.
- **Draft**: Writes an answer using the notes and sources.
- **Critique**: Scores quality and lists what to fix (missing citations, weak claims, structure).
- **Revise**: Applies critique to improve the draft.
- **Decide**: Stops early if quality is high, or loops back to Research until max iterations.

### Early stopping
The loop stops when:
- `quality_score >= EARLY_STOP_MIN_SCORE`, OR
- `iteration >= MAX_ITERS`, OR
- Budget Guard triggers a hard stop.

---

## Budget Guard (what it limits)

Tracked counters:
- `search_calls`
- `pages_fetched`
- `token_estimate` (rough heuristic)

Hard stops happen when a limit is exceeded (depending on your implementation). If you prefer “soft stop research but still draft”, keep drafting even when research caps are hit.

---

## Quality Gate rules

When `RESEARCH_ENABLED=1`:
- Every factual claim should have an inline citation like `[S1]` on the same sentence.
- The model must not invent citations outside the provided sources list.

When `RESEARCH_ENABLED=0` (or search is blocked):
- The agent must be cautious, clearly state uncertainty, and include verification steps.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'agent'`
Run using:
```powershell
python -m src.cli "..."
```
Also ensure `src/__init__.py` exists.

### `ddgs.exceptions.DDGSException` / WinError 10013
Your network/firewall may be blocking outbound calls used by the free search backend.
Fix:
- Set `RESEARCH_ENABLED=0`, or
- Try another network / allow Python through firewall.

### Duplicate references section
If the model prints its own “References” and your CLI appends another, strip the model’s references section in `cli.py` before appending your final `## References`.

---

## Suggested models (local)

Default:
- `llama3.1:8b-instruct-q4_K_M`

Fallbacks:
- Smaller CPU-friendly: `qwen2.5:3b-instruct`
- If Windows GPU routing is tricky: keep same model but accept CPU mode.

---

## License
Apache-2.0
