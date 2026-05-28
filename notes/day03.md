# Day 03 — Interview Agent + Synthesis Agent
**Date:** May 27, 2026
**Stage:** Stage 01 — Discover
**Status:** ✅ Complete

---

## 1. What We Built
- `agents/interview_agent.py` — conducts async text interviews, generates contextual follow-ups, saves transcripts as structured JSON
- `agents/synthesis_agent.py` — reads all saved transcripts, extracts top 5 pain themes scored by frequency and severity, outputs a structured opportunity map
- `data/` folder — stores all interview transcripts and the opportunity map as JSON files
- `test_day3.py` — end-to-end test running both agents in sequence

**Files created:**
```
AI-PRODUCT-LOOP/
├── data/
│   ├── INT_20260527_131950.json    ← real interview transcript
│   └── opportunity_map.json        ← synthesised opportunity map
├── agents/
│   ├── interview_agent.py
│   └── synthesis_agent.py
└── test_day3.py
```

**Opportunity map output from first real interview:**
- T1 — Overwhelming Volume of Support Tickets (Score: 11)
- T2 — Ineffective Manual Ticket Prioritization (Score: 10)
- T3 — Difficulty in Assessing Impact of Ticket Failures (Score: 9)
- T4 — Time Consumption in Ticket Management (Score: 8)
- T5 — Escalation Overload During Peak Times (Score: 8)
- Top opportunity identified: *Develop an AI-powered solution to automate ticket prioritization and summarization*

---

## 2. Why We Built It
Before any AI product decision can be made, you need to understand what users actually suffer from — not what they say they want. The Interview Agent operationalises the most important skill in product management: asking the right questions and digging deeper with follow-ups. The Synthesis Agent removes the most time-consuming part of user research — reading through transcripts and manually identifying themes. Together they turn raw user conversations into a scored, structured opportunity map that the Orchestrator Agent will use in Stage 03 to make go/no-go decisions. This is the first stage of the intelligence loop: real signal enters the system.

---

## 3. Code and Logic Explained

**Interview Agent — how it works step by step**

1. Takes a feature hypothesis as input
2. Calls `call_llm()` with the `INTERVIEW_AGENT_PROMPT` and the hypothesis — generates 5 opening questions
3. Parses the response with `parse_json_response()` into a Python dictionary
4. Loops through each question, prints it to the terminal, waits for real user input
5. For each answer, makes a second LLM call to generate a contextual follow-up question based on what the user actually said
6. Collects the follow-up answer
7. Assembles the full transcript as a dictionary with a unique ID and timestamp
8. Saves the transcript to `data/` as a JSON file

```python
# Why follow-ups are generated dynamically, not pre-written
follow_up_response = call_llm(
    system_prompt="...generate one sharp follow-up...",
    user_message=f"Question: {q['question']}\nAnswer: {user_answer}"
)
```
This is the key design choice — follow-ups are contextual to the actual answer, not generic. A user who answers "I have 500 tickets a day" gets a different follow-up than one who says "my team keeps missing SLAs."

**Synthesis Agent — how it works step by step**

1. Scans the `data/` folder and loads all `.json` transcript files
2. Converts all transcripts into a single formatted text block
3. Sends the entire text to `call_llm()` with the `SYNTHESIS_AGENT_PROMPT`
4. The LLM reasons over all transcripts and returns a structured opportunity map
5. Each theme has a frequency score (how often mentioned), severity score (how much it hurts), and an opportunity score (average of both)
6. Saves the opportunity map to `data/opportunity_map.json`
7. Prints a summary to the terminal

**How agents communicate through files**
The Interview Agent writes to `data/`. The Synthesis Agent reads from `data/`. They do not call each other directly — they communicate through persisted JSON files. This means each agent can be run independently, rerun without affecting the other, and the data survives a system restart. This is the file-based state management pattern that the vector memory system (Day 10–11) will eventually replace.

---

## 4. Issues We Faced

### Issue 1 — Follow-up question ignores the user's actual answer
**Problem:** The first version of the Interview Agent generated follow-ups from the original question alone, not from the user's answer. This produced generic follow-ups like "Can you elaborate?" regardless of what the user said — which defeats the entire purpose of a contextual interview.
**Solution:** The follow-up LLM call was restructured to pass both the original question AND the user's actual answer as context. The prompt explicitly instructs the LLM to generate a follow-up that responds to the specific content of the answer. Output quality improved significantly.

### Issue 2 — Synthesis Agent hallucinates themes not in the transcripts
**Problem:** With only one or two short interviews, the Synthesis Agent sometimes invents pain themes that were not mentioned — filling gaps with plausible-sounding but fabricated insights. This is a faithfulness hallucination and a critical failure mode for a discovery system.
**Solution:** The `SYNTHESIS_AGENT_PROMPT` was updated to require `supporting_quotes` — direct quotes from the transcript for every theme. If a theme cannot be supported by a quote, it should not be included. The Hallucination Eval Agent (Day 6) will catch this automatically once the pipeline is fully wired.

### Issue 3 — Transcript files accumulate without versioning
**Problem:** Every time `run_interview()` is called, a new JSON file is created in `data/`. After 20 interviews, the Synthesis Agent reads all of them — including outdated transcripts from early testing that pollute the theme extraction with irrelevant data.
**Solution:** Transcript files are named with a timestamp ID (`INT_20260527_131950.json`) so they can be sorted and filtered. A future improvement is to add a `session_id` field to group transcripts by product area, allowing the Synthesis Agent to be run on a filtered subset. This is documented as a known limitation in the strategy document (Day 14).

---

## 5. VP / Director Decisions Made

### Decision 1 — Async text interviews over live conversation simulation
**Situation:** The Interview Agent could simulate a full back-and-forth conversation in one LLM call (synthetic interviews) or conduct real terminal-based interviews with a human answering.
**Options considered:** Fully synthetic — fast, no human needed, scalable. Real terminal interviews — slower, requires human, produces genuine signal.
**Decision taken:** Real terminal interviews with a human answering.
**Reasoning:** The purpose of Stage 01 is to get real user signal into the system, not to simulate signal. Synthetic interviews can be added later via the Persona Agent (Day 4) as a red-teaming layer. Using real answers from Day 3 ensures the synthesis output reflects genuine pain — which makes the go/no-go decision in Stage 03 defensible to stakeholders.

### Decision 2 — Save transcripts to flat files vs a database
**Situation:** Transcripts can be saved as JSON files in a folder or inserted into a SQLite or PostgreSQL database.
**Options considered:** Flat JSON files — simple, no setup, human-readable. SQLite — queryable, structured. PostgreSQL — production-grade, overkill for Day 3.
**Decision taken:** Flat JSON files in `data/`.
**Reasoning:** On Day 7, ChromaDB is introduced to store transcripts as vector embeddings for semantic retrieval. At that point the flat files become the source data that gets embedded — so they need to exist as readable files. Adding a database layer now would create a migration step that adds no value at this stage. The flat file pattern is the right architecture for this point in the build.

### Decision 3 — Opportunity score as average of frequency and severity vs weighted formula
**Situation:** The opportunity score for each pain theme could be a simple average (frequency + severity / 2) or a weighted formula that prioritises severity over frequency.
**Options considered:** Simple average — transparent, easy to explain. Weighted formula (e.g. severity × 1.5) — more nuanced but introduces a weighting assumption. RICE or other PM frameworks — more complex, harder to automate.
**Decision taken:** Simple average for now, with severity and frequency scores kept separate.
**Reasoning:** The Orchestrator Agent reads both individual scores, not just the combined opportunity score. This means the decision layer can apply its own weighting when reasoning about go/no-go. A VP reading the output can also form their own view. Burying the weighting logic inside a formula at this stage would make the reasoning less transparent and harder to challenge in a product review.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| Agent | An LLM given a specific role, instructions, and the ability to take actions — here, asking questions and saving files |
| Async interview | An interview conducted over time via text, not in real time — allows users to answer on their own schedule |
| Transcript | A structured record of the full interview — questions, answers, follow-ups — saved as JSON |
| Opportunity map | A ranked list of user pain themes scored by how often they appear and how severely they affect users |
| File-based state | Agents communicate by writing and reading files rather than calling each other directly — simpler and more resilient |
| Frequency score | How many times a pain theme was mentioned across all interviews |
| Severity score | How much a pain theme impacts the user — rated by the LLM based on the language and context of the answers |
| `os.makedirs()` | Python function that creates a folder if it does not already exist — prevents file save errors |
| `datetime.now()` | Python function that returns the current date and time — used here to create unique transcript filenames |

---

## 7. How This Connects to the Bigger System
Stage 01: Discover is the entry point for real-world signal into the intelligence loop. The interview transcripts saved today in `data/` are the raw material for three downstream systems: the Synthesis Agent (reads them now), the ChromaDB vector store (embeds them on Day 7 for semantic retrieval), and the RAG memory system (retrieves them on Day 8 so future agents can reference past interviews when making new decisions). The opportunity map produced today is one of the key inputs the Orchestrator Agent will read in Stage 03 when deciding go/no-go. Without Stage 01 producing clean, structured signal, the entire decision layer is operating blind.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Real human answers in terminal | Fully synthetic, real terminal, API-connected survey tool | Genuine signal needed for a credible go/no-go; synthetic personas added separately as red-teaming | If scale requires 100+ interviews — would move to async web form or survey API integration |
| Flat JSON files for transcript storage | JSON files, SQLite, PostgreSQL | Files are the direct input format for ChromaDB embeddings on Day 7; no migration needed | If interview volume exceeds 500 and query performance becomes an issue — would add SQLite layer |
| Simple average opportunity score | Simple average, weighted formula, RICE framework | Keeps individual scores visible to the Orchestrator; avoids baking in weighting assumptions at the data layer | If stakeholder feedback shows consistent disagreement with the ranking — would introduce configurable weighting |

---

## 9. Resume Bullet
> Built a two-agent async discovery system that conducts contextual user interviews with dynamic follow-up generation and synthesises transcripts into a scored opportunity map — replacing manual research synthesis with an automated, auditable pipeline that feeds directly into the go/no-go decision layer.

---

## 10. LinkedIn Hook
> I let an AI agent interview me about my own product idea. The follow-up questions it asked were sharper than the ones I would have written myself. Here is exactly how it works — and what it found.

---

## 11. Honest Rating
**Difficulty:** 5/10
**Confidence after today:** 8/10
**What clicked:** The moment the Synthesis Agent returned a scored opportunity map from a real interview — it stopped feeling like a coding exercise and started feeling like a product system. The output was genuinely useful.
**What still feels unclear:** How the system will handle contradictory signals across multiple interviews — if 3 users say ticket volume is the biggest pain and 2 say prioritisation is worse, how does the scoring hold up at scale.

---

## 12. Next Course of Action
**Tomorrow — Day 04:** Persona Simulation + Hallucination Eval + Responsible AI Governance (Stage 02: Evaluate begins)
Three new agents: the Persona Agent simulates how 6 different user types react to the feature before it ships; the Hallucination Eval Agent checks whether the AI is making things up; the Governance Module classifies the feature under EU AI Act risk tiers and runs PII and bias checks. Stage 01 produces signal. Stage 02 stress-tests it.
