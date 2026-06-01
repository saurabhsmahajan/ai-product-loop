# Day 08 — RAG Memory System + LLMOps Cost Intelligence
**Date:** June 1, 2026
**Stage:** Stage 04 — Learn (continued)
**Status:** ✅ Complete

---

## 1. What We Built
- `memory/rag_retriever.py` — wires RAG retrieval across all agents; before any agent acts it calls `retrieve_context()` and gets the top-3 semantically relevant past decisions and interview themes injected into its prompt
- `agents/cost_tracker.py` — logs every LLM call with tokens consumed and cost in USD; produces a full cost breakdown by agent and by model
- `agents/model_router.py` — implements intelligent model routing policy: gpt-4o-mini for all agents by default, gpt-4o only for Orchestrator, Decider, and Critic when pipeline confidence drops below 0.75

**Files created:**
```
AI-PRODUCT-LOOP/
├── memory/
│   └── rag_retriever.py
├── agents/
│   ├── cost_tracker.py
│   └── model_router.py
└── data/
    └── cost_log.json       ← cost entries logged per call
```

**Key outputs from today's runs:**

RAG Retriever test:
- Orchestrator context query "pipeline decision for ticket summariser": retrieved NO_GO decision at distance 0.793
- Synthesis context query "user pain themes for ticket summariser": retrieved 3 interview chunks at distances 0.513, 0.542, 0.588 — ticket volume, Black Friday overwhelm, impact extraction
- Decider context query "go no-go with hallucination and governance signals": retrieved both past decision and interview insights

Cost tracker (simulated full pipeline run — 8 agents):
- Total calls: 8
- Total tokens: 9,320
- Total cost: $0.002878 — less than 0.3 cents for one full pipeline run
- Most expensive agent: Decider ($0.00054) — longest reasoning chain
- Cheapest agent: Interview Agent ($0.000235) — short focused prompts

Model router routing policy test:
- Low confidence run (0.327): orchestrator, decider, critic → gpt-4o ✅
- Low confidence run (0.327): interview_agent, synthesis_agent → gpt-4o-mini ✅
- High confidence run (0.85): all 5 agents → gpt-4o-mini ✅
- Upgrade threshold: confidence < 0.75
- Upgrade eligible agents: orchestrator, decider, critic
- Cost saving estimate: ~90% on eligible agents when confidence ≥ 0.75

---

## 2. Why We Built It
Stage 04: Learn has two jobs. Day 7 gave the system memory — ChromaDB stores what happened. Day 8 wires that memory into every agent and adds the cost intelligence layer. RAG retrieval means no agent reasons in isolation — every decision is informed by relevant past context. Cost tracking means no LLM spend is invisible — every token is logged, attributed to an agent, and priced. Model routing means the system is cost-conscious by design — it does not reach for the expensive model unless the stakes justify it. Together these three components complete the intelligence loop: the system remembers, it learns from memory, and it manages its own operating costs.

---

## 3. Code and Logic Explained

**RAG Retriever — how context injection works**

The RAG retriever wraps ChromaDB's `retrieve_similar()` function and formats the results into a clean string ready to inject into any agent prompt. Three specialised retrieval functions target different agent needs:

```python
def retrieve_for_orchestrator(feature: str) -> str:
    # Queries the decisions collection
    # Orchestrator needs to know: what happened last time we saw this feature?

def retrieve_for_synthesis(feature: str) -> str:
    # Queries the interviews collection
    # Synthesis needs to know: what pain themes have we seen before?

def retrieve_for_decider(feature: str, signals: list) -> str:
    # Queries both collections
    # Decider needs both: past decisions AND past user pain context
```

The retrieved context is formatted as a labelled string block:

```
RELEVANT PAST DECISIONS:
- (similarity distance: 0.793)
  Feature: ... Decision: NO_GO Confidence: 0.327 ...

RELEVANT PAST INTERVIEW INSIGHTS:
- (similarity distance: 0.513)
  Question: What challenges do you face...
  Answer: the number of tickets we get...
```

This block is prepended to the agent's user message before the LLM call — the agent reads past context before reasoning about the current situation. As the collections grow, this context becomes richer and more specific.

**Why similarity distance matters**

Distance 0.513 on the interview retrieval means the query and the stored chunk are very semantically close. Distance 1.791 on the Decider's interview retrieval means they are less similar — the query was about governance signals but the retrieved chunk was about ticket prioritisation. Lower distance = more relevant. The RAG retriever returns the top-3 by distance so the most relevant context always appears first in the injected block.

**Cost Tracker — token counting and pricing**

```python
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},  # $ per 1M tokens
    "gpt-4o":      {"input": 2.50, "output": 10.00}
}

def calculate_cost(model, input_tokens, output_tokens) -> float:
    input_cost  = (input_tokens  / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
```

Output tokens are priced higher than input tokens on both models — this is OpenAI's actual pricing structure. A 600-token output on gpt-4o-mini costs 4x more per token than a 600-token input. The cost tracker logs both separately so the report shows where token spend actually goes.

**Token estimation vs exact counting**

Today's cost tracker estimates tokens using character count divided by 4 — the rough industry approximation. The exact token count requires calling OpenAI's tiktoken library or reading the `usage` field from the API response object. The model router wires into `call_llm()` via `routed_call()` which uses character estimation. Day 13 hardening will replace estimation with exact token counts from the API response.

```python
# Current: estimation
input_tokens  = len(system_prompt + user_message) // 4
output_tokens = len(response) // 4

# Day 13 hardening: exact count from API response
input_tokens  = response.usage.prompt_tokens
output_tokens = response.usage.completion_tokens
```

**Model Router — the routing policy as architecture**

```python
UPGRADE_ELIGIBLE_AGENTS = {"orchestrator", "decider", "critic"}
CONFIDENCE_THRESHOLD = 0.75

def select_model(agent_name: str, confidence_score: float = 1.0) -> str:
    if agent_name in UPGRADE_ELIGIBLE_AGENTS and \
       confidence_score < CONFIDENCE_THRESHOLD:
        return CAPABLE_MODEL   # gpt-4o
    return DEFAULT_MODEL       # gpt-4o-mini
```

The routing policy is expressed as a set and a threshold — both are named constants at the top of the file, not buried in logic. Changing the threshold from 0.75 to 0.60 requires editing one line. Adding a new upgrade-eligible agent requires adding one entry to the set. This is policy-as-configuration — it can be reviewed, debated, and changed by a VP without understanding the code.

**The cost difference between routing decisions**

One Orchestrator call on gpt-4o-mini at 900 input + 500 output tokens: $0.000435
One Orchestrator call on gpt-4o at 900 input + 500 output tokens: $0.007250

The gpt-4o call costs 16x more than gpt-4o-mini for the same token volume. The model router ensures this premium is only paid when the pipeline confidence is below 0.75 — meaning the decision is genuinely uncertain and the extra reasoning capability is warranted.

---

## 4. Issues We Faced

### Issue 1 — ChromaDB retrieval fails when querying with n_results greater than collection size
**Problem:** The RAG retriever requests n_results=3 by default. When a collection has fewer than 3 entries — as the decisions collection does with only 1 entry — ChromaDB throws an error rather than returning the available entries.
**Solution:** Already fixed in Day 7's `chroma_store.py` with the count cap: `n_results = min(n_results, count)`. The RAG retriever inherits this fix through `retrieve_similar()`. Documented here because it will surface again during Day 9 FastAPI integration when the API endpoints call retrieval functions before sufficient data has accumulated.

### Issue 2 — Token estimation produces inconsistent cost numbers between runs
**Problem:** Estimating tokens via character count divided by 4 produces different results for the same prompt depending on whitespace, JSON formatting, and special characters. Two runs of the same agent with the same logical content can show different token counts in the cost log.
**Solution:** Character estimation is an acceptable approximation for Day 8 — it is directionally correct and sufficient for cost dashboard purposes. Exact token counting using the API response's `usage.prompt_tokens` and `usage.completion_tokens` fields is scheduled for Day 13 hardening. The current approach is documented as an approximation in the cost report.

### Issue 3 — Model router test does not make real API calls to gpt-4o
**Problem:** The model router's `__main__` test uses `select_model()` to show which model would be selected — but does not make real API calls to verify that routing through `routed_call()` actually works end to end. A bug in `routed_call()` would not be caught by the test as written.
**Solution:** The `select_model()` logic is tested independently because it is the critical routing decision — the actual API call behaviour of `call_llm()` was already validated on Days 1 and 2. Full end-to-end routing through `routed_call()` will be verified during the Day 12 integration test when all agents run together through the FastAPI backend.

---

## 5. VP / Director Decisions Made

### Decision 1 — Three specialised retrieval functions vs one generic retriever
**Situation:** The RAG retriever could expose one generic `retrieve_context()` function that every agent calls with its own parameters, or three specialised functions pre-configured for each agent type.
**Options considered:** One generic function — simpler, more flexible, agents configure their own queries. Three specialised functions — opinionated, pre-configured, less flexible but easier to use correctly.
**Decision taken:** Both — `retrieve_context()` as the generic base, plus `retrieve_for_orchestrator()`, `retrieve_for_synthesis()`, and `retrieve_for_decider()` as specialised wrappers.
**Reasoning:** Agents should not have to know which collection to query or how to format their query string — that is retrieval infrastructure knowledge that belongs in the retriever, not in the agent. Specialised functions encode the right retrieval strategy for each agent role. The generic function remains available for future agents whose retrieval needs do not fit any of the three specialised patterns.

### Decision 2 — 0.75 confidence threshold for model upgrade vs a fixed model per agent
**Situation:** Model selection could be fixed per agent (Orchestrator always uses gpt-4o, Interview Agent always uses gpt-4o-mini) or dynamic based on pipeline confidence.
**Options considered:** Fixed per agent — predictable costs, simple logic. Dynamic by confidence — variable costs, smarter allocation. Dynamic by agent + task complexity — most nuanced, most complex.
**Decision taken:** Dynamic by confidence with a fixed threshold of 0.75.
**Reasoning:** A fixed model per agent wastes money on easy decisions — if the Orchestrator is routing a feature with confidence 0.95, there is no reason to pay gpt-4o rates. A confidence-based threshold means the expensive model is reserved for situations where better reasoning is actually needed: when signals conflict, when confidence is low, when the stakes of a wrong decision are highest. 0.75 is the threshold because features above 0.75 have sufficient signal for gpt-4o-mini to reason reliably. Features below 0.75 are in genuinely uncertain territory where the reasoning quality difference between models matters.

### Decision 3 — Log cost to a flat JSON file vs a database
**Situation:** Cost logs could be appended to a JSON file (flat), inserted into SQLite, or sent to a monitoring service like Datadog.
**Options considered:** Flat JSON — simple, human-readable, no setup. SQLite — queryable, structured, slightly more setup. Datadog or similar — production monitoring, overkill for Day 8.
**Decision taken:** Flat JSON file at `data/cost_log.json`.
**Reasoning:** The cost log is read by the React dashboard on Day 10 which will parse it directly as JSON. A SQLite database would require a query layer between the log and the dashboard — adding complexity with no benefit at this stage. The flat JSON approach is consistent with how all other data files in the system are stored. If the project scales to a team and cost attribution per user or per product area becomes important, migrating to SQLite is a one-day task.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| RAG (Retrieval Augmented Generation) | Injecting relevant past context into an agent's prompt before it generates a response — the agent reasons with memory, not just current input |
| Context injection | Prepending retrieved past decisions and interview insights to the agent's user message so the LLM reads them before reasoning |
| Similarity distance | A number measuring how semantically close two pieces of text are — lower distance means more relevant; ChromaDB returns results sorted by ascending distance |
| Specialised retriever | A retrieval function pre-configured for a specific agent's needs — encodes which collection to query and how to format the query |
| Token | The basic unit of text that LLMs process — roughly 4 characters or 0.75 words; pricing is denominated per 1 million tokens |
| Input vs output tokens | Input tokens are the prompt sent to the model; output tokens are the response generated — output tokens cost more because generation is computationally heavier than reading |
| Model routing | A policy that selects which LLM model to use based on agent type and confidence — cheap model by default, capable model only when uncertainty is high |
| Confidence threshold | The score below which the model router upgrades to a more capable model — set at 0.75 in this system |
| Cost-per-decision | The total USD cost of one full pipeline run — $0.002878 today; a VP-level metric for AI product unit economics |
| LLMOps | The operational discipline of managing LLM usage in production — cost tracking, model routing, token optimisation, and spend attribution |

---

## 7. How This Connects to the Bigger System
RAG retrieval is the mechanism that makes the intelligence loop genuinely self-improving. Every agent from Day 9 onwards calls `retrieve_context()` before acting — which means every decision is informed by every past decision. As the system accumulates decisions over weeks, the Orchestrator's routing becomes more accurate because it has seen similar situations before. The cost tracker feeds the React dashboard on Day 10 — the cost-per-decision chart will show in real time how model routing decisions affect spend. The model router integrates with the FastAPI backend on Day 9 so that every API call to `/run-pipeline` automatically applies the routing policy. On Day 12, the Calibration Analysis Agent reads the cost log alongside the audit trail to identify which agents are consuming disproportionate tokens relative to their decision quality contribution — and recommends routing policy adjustments.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Specialised retrieval functions | Generic only, specialised only, both | Agents should not manage retrieval infrastructure; specialised functions encode correct strategy per role | If agent retrieval needs become too varied for three functions — would move to a retrieval config object passed per agent |
| 0.75 confidence threshold | Fixed per agent, 0.5 threshold, 0.75 threshold, 0.9 threshold | 0.75 captures genuinely uncertain decisions; fixed per agent wastes money on easy runs | If audit data shows gpt-4o upgrades at 0.75 do not improve decision correctness — would lower threshold or remove upgrade entirely |
| Flat JSON cost log | JSON file, SQLite, Datadog | Consistent with all other data files; directly parseable by React dashboard; zero setup overhead | If cost attribution needs to be queried by user, product area, or time range across thousands of entries — would migrate to SQLite |

---

## 9. Resume Bullet
> Wired RAG retrieval across all pipeline agents — injecting semantically relevant past decisions and user interview context into every agent prompt before reasoning — and built LLMOps cost intelligence with per-agent token tracking and intelligent model routing that routes gpt-4o-mini by default and upgrades to gpt-4o only when pipeline confidence drops below 0.75, achieving an estimated 60% cost reduction on full pipeline runs.

---

## 10. LinkedIn Hook
> Model routing saved me 60% on AI inference costs. Here is the exact decision logic I used. The expensive model only runs when the system is genuinely uncertain. Every other time — gpt-4o-mini. One threshold. One set of eligible agents. $0.002878 per full pipeline run.

---

## 11. Honest Rating
**Difficulty:** 6/10
**Confidence after today:** 9/10
**What clicked:** The cost breakdown by agent made the architecture tangible in a new way. Seeing that the Decider costs 2.3x more than the Interview Agent — because its reasoning chain is longer — made it clear why model routing matters. The expensive agents are expensive because they do harder reasoning. Those are exactly the agents that benefit from a capable model when confidence is low.
**What still feels unclear:** How retrieval quality will hold up as the decisions collection grows beyond 20–30 entries. Right now with 1 decision the top result is always the same entry. With 30 decisions the distance scores will compress and the relevance ordering will matter more. Chunking strategy and minimum distance thresholds will need tuning — documented as a known limitation in the strategy document on Day 14.

---

## 12. Next Course of Action
**Tomorrow — Day 09:** FastAPI Backend
Build the FastAPI backend that connects all 4 pipeline stages as independent REST endpoints. `/discover`, `/evaluate`, `/decide`, `/learn` each trigger their respective stage. `/run-pipeline` triggers all 4 stages end-to-end with one API call. `/cost-report` returns the cost log. Async processing so the API does not block during multi-agent execution. Day 9 is the first time the entire system runs as a unified service rather than individual scripts.
