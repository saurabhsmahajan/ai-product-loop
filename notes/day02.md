# Day 02 — Python Fundamentals + Prompt Engineering
**Date:** May 26, 2026
**Stage:** Foundation — reusable infrastructure for all 9 agents
**Status:** ✅ Complete

---

## 1. What We Built
- `agents/utils.py` — reusable `call_llm()` function and `parse_json_response()` helper
- `agents/prompts.py` — system prompts for all 9 agent roles with JSON output schemas
- `agents/__init__.py` — makes the agents folder a Python module
- `test_utils.py` — verified all functions work end to end

**Files created:**
```
AI-PRODUCT-LOOP/
├── agents/
│   ├── __init__.py
│   ├── utils.py
│   └── prompts.py
└── test_utils.py
```

---

## 2. Why We Built It
Without a shared utility layer, every agent file would duplicate the same API call logic. That means 9 copies of the same code — and if the model name changes or an error handling pattern needs updating, it has to be changed in 9 places. `utils.py` solves this by writing the LLM call once and importing it everywhere. `prompts.py` centralises all agent instructions in one place so they can be versioned, compared, and improved without hunting through multiple files. This is the engineering discipline that separates a production system from a prototype.

---

## 3. Code and Logic Explained

**`call_llm()` function**
Takes three inputs: a system prompt (the agent's role and instructions), a user message (the actual task), and an optional model name. Sends both to OpenAI and returns the response as plain text. Every agent in the system calls this one function — none of them talk to OpenAI directly.

**`parse_json_response()` function**
LLMs are instructed to return structured JSON but they often wrap it in markdown code fences (` ```json ... ``` `). This helper strips those fences, then uses Python's `json.loads()` to convert the text into a dictionary. If parsing fails, it prints the error and returns an empty dictionary rather than crashing the entire pipeline.

```python
# Why we strip fences before parsing
text = text.strip()
if text.startswith("```"):
    text = text.split("```")[1]      # removes opening fence
    if text.startswith("json"):
        text = text[4:]              # removes the word "json"
```

**System prompts structure in `prompts.py`**
Each prompt follows the same pattern:
1. Role definition — tells the LLM exactly what agent it is
2. Job description — what it must do with the input it receives
3. Output format — a JSON schema it must follow exactly
4. Rules — constraints on reasoning and output quality

This structure means every agent returns predictable, parseable output that the next agent in the pipeline can consume without ambiguity.

---

## 4. Issues We Faced

### Issue 1 — LLM returns JSON wrapped in markdown fences
**Problem:** The agent is instructed to return JSON only, but GPT-4o-mini frequently wraps the output in ` ```json ... ``` ` markdown fences. Calling `json.loads()` directly on this text throws a `JSONDecodeError` and crashes the pipeline.
**Solution:** The `parse_json_response()` helper detects and strips fences before parsing. This is a known LLM behaviour — any production system that parses LLM output must handle it.

### Issue 2 — Import errors when running from the wrong directory
**Problem:** Running `python agents/utils.py` directly throws `ModuleNotFoundError` because Python cannot resolve the relative imports. This confuses beginners who expect to run any file from anywhere.
**Solution:** Always run scripts from the project root (`AI-PRODUCT-LOOP/`) and use `python test_utils.py` not `python agents/test_utils.py`. The `__init__.py` file in the `agents/` folder is what makes `from agents.utils import call_llm` work correctly from the root.

### Issue 3 — System prompt length affecting response quality
**Problem:** When system prompts are too short (one line), the LLM produces vague, inconsistently structured output. When they are too long (500+ words), the LLM starts ignoring instructions at the end — a known issue called "lost in the middle."
**Solution:** Each system prompt is structured in four clear sections (role, job, output format, rules) and kept under 250 words. The JSON schema is explicit but not over-specified. Instructions are numbered so the LLM can follow them sequentially.

---

## 5. VP / Director Decisions Made

### Decision 1 — Centralise all prompts in one file vs inline per agent
**Situation:** Prompts can be written directly inside each agent file (inline) or stored centrally in `prompts.py` and imported.
**Options considered:** Inline prompts — simpler to read, everything in one file. Central `prompts.py` — more abstraction, requires imports.
**Decision taken:** Central `prompts.py`.
**Reasoning:** When the Prompt A/B Eval system is built on Day 5, it needs to compare prompt versions against each other. That comparison is only possible if prompts are versioned in one place. Inline prompts cannot be systematically tested. This is the same logic as separating configuration from logic in any production system.

### Decision 2 — Enforce JSON output schema in every prompt
**Situation:** Agents could return free-text responses that are parsed loosely, or strict JSON that is parsed precisely.
**Options considered:** Free text with loose parsing — more flexible, harder to chain. Strict JSON schema — less flexible, fully chainable.
**Decision taken:** Strict JSON schema in every prompt.
**Reasoning:** This system chains 9 agents — the output of one is the input of the next. If any agent returns unpredictable output, the chain breaks. The cost of strict schemas (slightly more complex prompts) is far lower than the cost of debugging unparseable outputs mid-pipeline at 2am before a board presentation.

### Decision 3 — Return empty dict on parse failure vs raise exception
**Situation:** When `parse_json_response()` fails, it can either crash the program with an exception or return an empty dictionary and let the caller handle it.
**Options considered:** Raise exception — fails loudly, easier to debug. Return empty dict — fails silently, pipeline continues.
**Decision taken:** Return empty dict with printed error.
**Reasoning:** In a multi-agent pipeline, a single agent failing should not bring down the entire run. The orchestrator layer (built Day 6) is designed to handle missing or empty signals gracefully. Crashing on every parse error would make the system unusable in production where LLM output is inherently variable.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| Python module | A folder with an `__init__.py` file that can be imported by other scripts |
| `import` statement | How one Python file uses functions defined in another file |
| System prompt | The persistent instruction that defines an agent's role and behaviour for the entire conversation |
| JSON schema | A defined structure that specifies exactly what fields and types an output must contain |
| Chain-of-thought | Instructing the LLM to reason step by step before giving a final answer — improves accuracy |
| Few-shot prompting | Giving the LLM 1–3 examples of the output you want before asking it to produce its own |
| Structured output | LLM response formatted as parseable data (JSON) rather than conversational prose |

---

## 7. How This Connects to the Bigger System
`utils.py` and `prompts.py` are the shared nervous system of the entire pipeline. Every agent built from Day 3 onwards imports `call_llm()` from `utils.py` and its system prompt from `prompts.py`. When the model router is built on Day 8, it extends `call_llm()` to route cheap tasks to GPT-4o-mini and complex reasoning to GPT-4o — that change happens in one place and propagates to all 9 agents automatically. When the Prompt A/B Eval system is built on Day 5, it reads from `prompts.py` directly to compare versions. Today's infrastructure decisions compound in value every day that follows.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Central `prompts.py` | Inline prompts per agent, central file, database-stored prompts | Enables systematic A/B testing and version control; single source of truth | If prompts need to be dynamically generated per user or per run — would move to a prompt registry |
| Strict JSON schema in every prompt | Free text, loose JSON, strict schema | Agents chain their outputs; strict schema is the only way to make chaining reliable | If a use case requires genuinely open-ended narrative output that cannot be structured |
| Empty dict on parse failure | Raise exception, return None, return empty dict | Pipeline resilience — one agent failing should not crash a multi-hour run | If silent failures prove harder to debug than loud ones in production monitoring |

---

## 9. Resume Bullet
> Designed a reusable multi-agent infrastructure layer — centralised LLM calling, JSON output parsing, and prompt management for 9 specialised agents — reducing per-agent code duplication by 100% and enabling systematic prompt A/B testing across the full pipeline.

---

## 10. LinkedIn Hook
> Most AI systems fail in production not because the model is wrong — but because no one designed what happens when the output cannot be parsed. Here is the two-line fix I built on Day 2 that keeps the entire pipeline alive.

---

## 11. Honest Rating
**Difficulty:** 4/10
**Confidence after today:** 8/10
**What clicked:** Why system prompts need a JSON schema — the moment it was clear that agents talk to each other through structured data, not prose, everything about the prompt design made sense.
**What still feels unclear:** How the system will handle a situation where an agent returns valid JSON but with semantically wrong values — a hallucination that passes the parser but fails the logic.

---

## 12. Next Course of Action
**Tomorrow — Day 03:** Interview Agent + Synthesis Agent (Stage 01: Discover)
The first two production agents. The Interview Agent conducts real async interviews and saves transcripts. The Synthesis Agent reads all transcripts and outputs a structured opportunity map. This is where the infrastructure built today gets used for the first time in a real product intelligence workflow.
