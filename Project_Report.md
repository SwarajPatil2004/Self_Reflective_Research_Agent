#Self_Reflective_Research_Agent

## Executive summary
This project is a zero-cost, local “DeepResearch-like” research assistant that can search the web (free), read a few pages, write an answer, critique itself, and revise until it meets a quality bar or hits a budget limit.[1]
It is designed for a beginner-friendly workflow on a personal laptop, using Ollama for local inference so there are no paid APIs and no tokens to buy.[2]
The key idea is a Reflexion-style loop: draft → critique → revise, implemented as a cyclic LangGraph graph so the agent can improve its own answers instead of responding only once.[3][1]

## Real-world use case (why it matters)
People often need quick, cited explanations: “What is X?”, “Compare A vs B”, “Summarize this topic with sources”, and “List risks and best practices”.[3]
A self-reflective loop helps reduce common problems like missing citations, overconfident claims, and messy structure by forcing a second pass that checks and repairs the answer.[3]

## Personas (who uses it)
- Student (10th–college): needs summaries and citations for a topic report.  
- Developer: needs a quick research assistant for unfamiliar tools, with links to sources for verification.  
- Analyst/Writer: needs drafts that are improved by critique and revision, not just a single-shot answer.  

## Scope (what it does / does not)
### It does
- Creates a plan, performs free web search, fetches limited pages, synthesizes notes, drafts an answer, critiques it, and revises it in a loop.[1][3]
- Adds a final “References” list from the collected source URLs (no hallucinated bibliography).  

### It does not
- It does **not** use any paid search APIs or paid LLM APIs.  
- It does **not** guarantee that every claim is correct; it tries to be cautious and asks for verification when research is blocked.[3]
- It does **not** store personal data; the data plan below recommends avoiding any sensitive information.

## System design overview
### High-level architecture
```text
User Question
   |
   v
+-------------------+
| LangGraph Graph   |
| (cyclic workflow) |
+-------------------+
   |    |     |
   |    |     +----------------------+
   |    |                            |
   v    v                            v
Planner -> Research -> Draft -> Critique -> Revise -> Decide
                |                     ^               |
                |                     |               |
                +---- sources/notes ---+---- loop -----+
   |
   v
Final Answer + References (URLs)
```
LangGraph supports cyclic flows, which is why it fits the Reflexion loop pattern.[1][3]

### Components
- Local LLM: Ollama model served on localhost (no paid APIs).[2]
- Search tool: `ddgs`-based free search (no key).[4]
- Fetch tool: HTTP fetch + HTML-to-text extraction.  
- Guardrails: Budget Guard + Quality Gate.

## Data plan
### What data is used
- User’s question text.  
- Search results: title, URL, short snippet.[5]
- Fetched page text (limited by character caps and page caps).  

### How it’s collected
- Web search via DDGS `.text()` results.[5][4]
- Page fetch via HTTP GET and HTML text extraction.

### How it’s formatted
- `sources`: list of `{id: "S1", url, title, snippet}`.  
- `notes`: short synthesized notes referencing sources via `[S#]`.  
- `draft`: final answer with inline citations `[S#]`.

### What not to include (safety)
- Don’t paste passwords, phone numbers, Aadhaar/SSN, private documents, or confidential company info into prompts or datasets.  
- Don’t fetch or store pages that contain personal data unless you have permission.

## Method (simple explanation)
### Reflexion loop (simple analogy)
Think of it like writing an essay: first you write a rough draft, then you become your own teacher and mark mistakes, then you rewrite it.[3]
LangGraph lets you build this as a loop: the output of Critique goes back into Revise, and Decide controls whether to stop or continue.[1]

### Budget Guard (why it exists)
The agent has to avoid endless web requests and huge context windows, so it tracks how many searches and pages it used and stops when limits are hit.

### Quality Gate (why it exists)
If research is enabled, the answer should include citations for factual claims; if research is blocked, the system should be honest and provide verification steps instead of pretending certainty.[3]

## Step-by-step build plan (phases)
1) Phase A: Local LLM working  
- Install Ollama, pull a model, confirm `localhost:11434` works.[2]

2) Phase B: Graph skeleton  
- Build LangGraph nodes and edges; run a single iteration.[1]

3) Phase C: Free research tool  
- Add DDGS search + basic fetching and limit it with Budget Guard.[4][5]

4) Phase D: Reflexion loop + early stopping  
- Add Critique/Revise, stop on max iterations or good score.[1][3]

5) Phase E: Quality Gate + stable formatting  
- Block invented citations, append final references from collected sources.

## Evaluation plan
### Test set (offline)
Create a small set of 20 questions in a JSONL file (see Sample_Dataset.jsonl) covering:
- factual summaries  
- comparisons  
- “how-to” steps  
- “what are the risks?” prompts  
Run them with research on/off.

### Rubric (0–2 each)
- Correctness/caution: avoids over-claiming when uncertain  
- Citations: only cites valid `[S#]` entries when research enabled  
- Structure: clear headings/bullets  
- Completeness: addresses the question  
- Safety: no personal data, no sensitive instructions

### Acceptance criteria
- 18/20 queries finish without crashing.  
- With research enabled: 90% of outputs contain at least 2 valid sources and no fake citation IDs.  
- With research disabled: 100% outputs include a “How to verify” section.

## Glossary (beginner-friendly)
- **LLM**: Large Language Model; predicts text responses.  
- **Ollama**: A tool to run LLMs locally on your computer.[2]
- **LangGraph**: A library for building agent workflows as graphs (with loops).[1]
- **Ron**: A link (source) that supports a claim.  
- **eflexion**: A technique where an agent critiques its own output and retries/revises.[1][3]
- **CitatiBudget Guard**: rules that limit web calls/pages/tokens so the agent stays stable.  
- **Quality Gate**: rules that block overconfident or uncited claims.

***
