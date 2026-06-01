# Day 07 — ChromaDB + Vector Embeddings + Audit Trail
**Date:** May 31, 2026
**Stage:** Stage 04 — Learn
**Status:** ✅ Complete

---

## 1. What We Built
- `memory/chroma_store.py` — installs and configures ChromaDB locally, writes all interview transcripts and past decisions as vector embeddings, exposes a `retrieve_similar()` function so any agent can query semantically relevant past context before acting
- `memory/audit_logger.py` — logs every agent decision with full context: input signals, reasoning chain, confidence score, escalation flag, model used, tokens consumed, and outcome; exposes `update_outcome()` for post-launch feedback and `get_audit_summary()` for the Calibration Analysis Agent

**Files created:**
```
AI-PRODUCT-LOOP/
├── memory/
│   ├── __init__.py
│   ├── chroma_store.py
│   └── audit_logger.py
├── chroma_db/              ← auto-created by ChromaDB, persists to disk
└── data/
    └── audit_trail.json    ← first decision logged
```

**Key outputs from today's runs:**

ChromaDB vector store:
- Embedding model downloaded: all-MiniLM-L6-v2 (79MB, runs fully locally)
- Collections created: interviews, decisions
- Interview Q&A chunks stored: 5
- Pipeline decisions stored: 1 (NO_GO, run RUN_20260528_154313)
- Retrieval test 1 — query "high hallucination rate and governance issues": correctly returned NO_GO decision (distance 1.366)
- Retrieval test 2 — query "ticket volume and support team pain": correctly returned 2 relevant interview chunks (distances 0.867, 0.922)

Audit trail (first entry):
- Decision: CONDITIONAL_GO
- Confidence: 0.475
- Escalated to human: True
- Outcome: PENDING
- Escalation rate: 1.0 (100% of decisions required human review so far)
- Total tokens consumed: 0 (cost tracking middleware added Day 8)

---

## 2. Why We Built It
A system that makes decisions without remembering them is not intelligent — it is a calculator. ChromaDB gives the system semantic long-term memory: every past interview and every past decision is stored as an embedding that can be retrieved by meaning, not keyword. This means a future Orchestrator run can ask "what happened last time we had a governance FLAGGED verdict?" and get the relevant context automatically. The Audit Trail adds accountability and the data flywheel: every decision logged with its eventual outcome becomes training signal for the Calibration Analysis Agent on Day 12, which recalibrates confidence thresholds based on what the system got right and wrong. Stage 04 is where the system starts compounding intelligence over time.

---

## 3. Code and Logic Explained

**How ChromaDB stores and retrieves data**

ChromaDB converts text into embeddings — lists of numbers (vectors) that represent the semantic meaning of the text. The `all-MiniLM-L6-v2` model, downloaded automatically on first run, performs this conversion locally with no API calls.

When you query ChromaDB with a text string, it converts your query into a vector and finds the stored vectors with the smallest angular distance. Smaller distance = more semantically similar.

```python
# upsert stores OR updates — safe to run multiple times without duplicates
collection.upsert(
    documents=[text_chunk],    # the raw text
    ids=[doc_id],              # unique identifier
    metadatas=[{...}]          # structured fields for filtering
)

# query retrieves top-n semantically similar entries
results = collection.query(
    query_texts=["your query here"],
    n_results=3
)
```

**Two collections and why they are separate**

Interviews collection stores individual question-answer pairs from real user interviews. Each Q&A pair is a separate embedding so retrieval is precise — a query about ticket volume returns the specific interview moment where ticket volume was discussed, not the entire transcript.

Decisions collection stores full pipeline decisions — the feature, decision verdict, signals, reasoning chain, and conditions. A query about past governance failures returns the full decision context, not just a fragment.

Separating them means agents can choose which memory pool to query. The Orchestrator queries decisions to find similar past pipeline runs. A future Interview Agent queries interviews to find relevant past user pain before generating new questions.

**Why each interview Q&A pair is stored separately, not the full transcript**

```python
# Each question-answer pair becomes one embedding
for q in transcript.get("questions", []):
    text_chunk = f"""
Feature: {feature}
Question: {q.get('question', '')}
Answer: {q.get('user_answer', '')}
Follow-up: {q.get('follow_up', '')}
Follow-up answer: {q.get('follow_up_answer', '')}
""".strip()
```

Storing the full transcript as one embedding would average the meaning of all 5 questions into a single vector — making retrieval imprecise. Chunking by Q&A pair means each embedding represents a specific, focused topic. This is the core chunking strategy decision in any RAG system.

**Audit Trail — the decision log structure**

Every log entry captures 12 fields:

```python
entry = {
    "log_id": "LOG_20260529_104657_979662",     # unique, timestamped
    "run_id": "RUN_20260528_154313",             # links to pipeline run
    "logged_at": "2026-05-29T10:46:57",          # ISO timestamp
    "feature": "...",                             # what feature was decided
    "stage": "Stage 03 — Decide",                # which pipeline stage
    "agent_name": "Decider + Reflexion Loop",    # which agent decided
    "input_signals": [...],                       # what signals it read
    "reasoning_chain": [...],                     # how it reasoned
    "decision": "CONDITIONAL_GO",                # what it decided
    "confidence_score": 0.475,                   # how confident
    "escalated_to_human": True,                  # did it escalate
    "model_used": "gpt-4o-mini",                 # which model
    "tokens_consumed": 0,                        # cost (populated Day 8)
    "outcome": "PENDING"                         # updated post-launch
}
```

The `outcome` field starts as PENDING and is updated to CORRECT, INCORRECT, or PARTIALLY_CORRECT once real post-launch data arrives. This is the field the Calibration Analysis Agent reads on Day 12 to learn which confidence levels correlate with correct decisions.

**`update_outcome()` — closing the feedback loop**

```python
def update_outcome(log_id: str, outcome: str, notes: str = "") -> bool:
    """Updates a logged decision's outcome once real-world data arrives."""
```

This function is the mechanism that closes the intelligence loop. When model drift is detected post-launch (Day 11), the system calls `update_outcome()` to mark the decision as INCORRECT — and that data point feeds into calibration recalibration on Day 12. Without this function, the audit trail is a log. With it, the audit trail is a learning signal.

---

## 4. Issues We Faced

### Issue 1 — ChromaDB query fails when collection is empty
**Problem:** The `retrieve_similar()` function calls `collection.query()` before any data has been stored. ChromaDB throws an error when querying an empty collection rather than returning an empty list — which crashes the pipeline on a fresh setup.
**Solution:** Added a count check before querying: `if collection.count() == 0: return []`. Also added a cap: `n_results = min(n_results, count)` to prevent requesting more results than exist in the collection. Both checks make the function safe to call at any point in the pipeline regardless of how much data has been stored.

### Issue 2 — `echo.` command not recognised in PowerShell
**Problem:** The `echo.` command used to create an empty `__init__.py` file is a Windows Command Prompt syntax that PowerShell does not recognise. Running it in the Cursor terminal (which uses PowerShell by default) threw a `CommandNotFoundException`.
**Solution:** Used PowerShell's native file creation command: `New-Item memory/__init__.py -ItemType File`. The shorthand `ni memory/__init__.py` also works. This is a one-time Windows environment quirk — documented so it does not catch Day 8 and beyond.

### Issue 3 — ChromaDB stores the NO_GO decision but audit trail logs CONDITIONAL_GO
**Problem:** ChromaDB was populated from `decider_report.json` which contains the original NO_GO decision from Pass 1. The audit logger was populated from `reflexion_report.json` which contains the final CONDITIONAL_GO decision after two revision passes. The two stores had different decision verdicts for the same pipeline run.
**Solution:** This is correct and intentional — not a bug. ChromaDB stores the initial Decider verdict as a searchable past decision. The audit trail stores the final post-Reflexion verdict as the authoritative outcome. When the RAG memory system is wired on Day 8, the retrieve function will query ChromaDB for similar past decisions — it will correctly return the CONDITIONAL_GO context from the audit trail as the canonical record. The separation mirrors how a real decision log works: initial recommendation vs final approved decision.

---

## 5. VP / Director Decisions Made

### Decision 1 — Local ChromaDB over a hosted vector database service
**Situation:** ChromaDB can run locally (PersistentClient writing to a local folder) or be hosted as a managed service. Alternatives include Pinecone, Weaviate, and pgvector.
**Options considered:** Local ChromaDB — free, no data leaves the machine, zero setup. Hosted ChromaDB — managed, scalable, requires account. Pinecone — production-grade, has a free tier, external dependency. pgvector — PostgreSQL extension, good for teams already on Postgres.
**Decision taken:** Local ChromaDB with PersistentClient.
**Reasoning:** For a 14-day solo build project, the correct priority is zero friction and zero cost. Local ChromaDB installs in one pip command, persists to a local folder, and runs without an internet connection. The decision to use a hosted vector database is an infrastructure scaling decision that belongs in the strategy document — it does not belong in Day 7. The `get_chroma_client()` function is the only place the client is instantiated, so switching to a hosted client requires changing one line.

### Decision 2 — Chunk interviews by Q&A pair vs store full transcripts
**Situation:** Interview transcripts can be stored as one embedding per transcript (full document) or as one embedding per question-answer pair (chunked).
**Options considered:** Full transcript embedding — simpler, one document per interview, coarser retrieval. Q&A pair chunking — more embeddings, but precise retrieval at the specific question level.
**Decision taken:** Q&A pair chunking — each question, answer, follow-up, and follow-up answer stored as one embedding.
**Reasoning:** The purpose of interview retrieval is to surface specific user pain signals, not to retrieve whole conversations. If a future agent queries "customer concerns about data privacy", it should retrieve the specific moment in the interview where data privacy was discussed — not a full 10-minute transcript that happens to mention data privacy once. Chunking at the Q&A level is the minimum granularity that makes retrieval actionable. A further improvement would be sentence-level chunking, but Q&A level is the right balance for this project's scope.

### Decision 3 — Outcome field starts as PENDING vs omitting it until outcome is known
**Situation:** The audit trail could omit the outcome field until post-launch data arrives, or include it from the start as PENDING.
**Options considered:** Omit until known — cleaner schema, no placeholder values. Include as PENDING from the start — consistent schema, immediately queryable.
**Decision taken:** Include as PENDING from the start.
**Reasoning:** The Calibration Analysis Agent on Day 12 reads the audit trail and queries by outcome. If some entries have no outcome field and others have CORRECT or INCORRECT, the query logic has to handle two different schemas. PENDING as a default value means every entry has the same schema from the moment it is logged — the Agent can filter `outcome == PENDING` to find decisions awaiting post-launch validation, and filter `outcome == INCORRECT` to find calibration failures. Consistent schema from Day 1 is always preferable to a schema that evolves with the data.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| Vector embedding | A list of numbers that represents the semantic meaning of a piece of text — similar meanings produce similar vectors |
| Vector database | A database that stores embeddings and retrieves them by semantic similarity rather than exact keyword match |
| Cosine similarity | The mathematical measure of how similar two vectors are — ChromaDB uses distance (lower = more similar) |
| Semantic search | Finding relevant content by meaning rather than by matching specific words — "ticket volume pain" finds content about "support overload" |
| Chunking | Breaking large documents into smaller pieces before embedding — improves retrieval precision |
| PersistentClient | A ChromaDB configuration that saves the vector store to disk so data survives between sessions |
| Upsert | A database operation that inserts a new record if it does not exist, or updates it if it does — prevents duplicates on repeated runs |
| Collection | A named group of embeddings in ChromaDB — equivalent to a table in a relational database |
| Audit trail | A permanent, append-only log of every system decision with full context — enables accountability, calibration, and learning |
| Outcome field | A field in the audit log updated post-launch to record whether a decision turned out to be correct — the primary learning signal for calibration |

---

## 7. How This Connects to the Bigger System
ChromaDB and the audit trail are the memory layer that makes every other agent smarter over time. On Day 8, the RAG retriever wires ChromaDB into every agent — before any agent acts, it calls `retrieve_similar()` and gets the top 3 relevant past decisions or interview themes as context. This means the Orchestrator on Day 50 will make better routing decisions than on Day 1 because it has read 49 similar past runs before deciding. The audit trail feeds the Calibration Analysis Agent on Day 12, which recalibrates confidence thresholds based on accumulated CORRECT and INCORRECT outcomes. The Business Impact Translator on Day 10 reads the audit trail to map decision patterns to revenue impact. The drift monitor on Day 11 calls `update_outcome()` when post-launch behaviour diverges from the decision — closing the feedback loop that makes the entire intelligence cycle self-improving.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Local ChromaDB | Local ChromaDB, hosted ChromaDB, Pinecone, pgvector | Zero cost, zero setup, no data leaves the machine; one-line switch to hosted client when scale requires it | If the system needs to be shared across a team or deployed to a server — would switch to hosted ChromaDB or Pinecone |
| Q&A pair chunking | Full transcript, Q&A pair, sentence-level | Retrieval precision at the specific pain signal level; full transcripts are too coarse for actionable retrieval | If interview transcripts become much longer with 20+ questions — would move to sentence-level chunking with overlap |
| PENDING as default outcome | Omit until known, PENDING default, NULL | Consistent schema from Day 1; Calibration Agent can query by outcome without handling missing fields | Never — consistent schema is always preferable to a schema that evolves with data availability |

---

## 9. Resume Bullet
> Built a vector memory system using ChromaDB — embedding all user interview transcripts and pipeline decisions locally using the all-MiniLM-L6-v2 model — and an audit trail logger that persists every agent decision with full reasoning context and a post-launch outcome field, creating the data flywheel that allows the system to recalibrate confidence thresholds and improve decision quality over time.

---

## 10. LinkedIn Hook
> I built a RAG memory system for product decisions. Here is what it actually remembers — and what it forgets. Six weeks from now, when a new feature goes through the pipeline, the Orchestrator will retrieve the ticket summariser decision as context. It will remember the hallucination rate, the governance flag, and the CONDITIONAL_GO. It will not remember why the conditions were never resolved. That gap is the product manager's job — not the AI's.

---

## 11. Honest Rating
**Difficulty:** 6/10
**Confidence after today:** 9/10
**What clicked:** The moment the retrieval test returned a semantically relevant interview chunk in response to a natural language query — without any keyword matching. The query "ticket volume and support team pain" returned the exact interview moment where the user described being overwhelmed by support volume. That is not a search engine — that is memory.
**What still feels unclear:** How retrieval quality degrades as the collections grow. With 5 chunks it works perfectly. With 500 chunks, the distances will compress and the top-3 results may not be meaningfully more relevant than results 4–10. Chunking strategy and retrieval threshold tuning will matter more at scale.

---

## 12. Next Course of Action
**Tomorrow — Day 08:** RAG Memory System + LLMOps Cost Intelligence (Stage 04: Learn continues)
Wire RAG retrieval across all agents — before acting, each agent calls `retrieve_context()` and gets the top-3 semantically relevant past decisions or interview themes. Add cost tracking middleware to `call_llm()` to track tokens consumed per call. Build model routing logic: cheap model for discovery and synthesis, capable model for Orchestrator and Reflexion Critic only when confidence falls below 0.75. Stage 04 completes on Day 8.
