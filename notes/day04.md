# Day 04 — Persona Simulation + Hallucination Eval + Responsible AI Governance
**Date:** May 28, 2026
**Stage:** Stage 02 — Evaluate
**Status:** ✅ Complete

---

## 1. What We Built
- `agents/persona_agent.py` — simulates 6 distinct user personas, scores their reactions to the feature, surfaces objections and champion cases
- `agents/eval_agent.py` — evaluates AI feature output for hallucinations, distinguishes faithfulness from factuality failures, produces a full eval report card
- `agents/governance.py` — runs PII scrubbing before any text reaches the LLM, classifies the feature under EU AI Act risk tiers, detects bias, and produces a governance verdict

**Files created:**
```
AI-PRODUCT-LOOP/
├── agents/
│   ├── persona_agent.py
│   ├── eval_agent.py
│   └── governance.py
└── data/
    ├── hallucination_eval_report.json    ← eval agent output
    └── governance_report.json            ← governance module output
```

**Key outputs from today's runs:**

Persona simulation (feature: AI ticket summariser):
- Avg reaction score: 7.0 / 10
- Champions: Enterprise Buyer, SMB Owner, End User, Champion / Power User
- Blockers: IT / Security Lead, Legal / Compliance
- Root cause of both blockers: PII handling and data privacy risk

Hallucination eval (AI ticket summary vs source ticket):
- Faithfulness score: 0.0 — AI invented a server outage not in the source
- Factuality score: 0.0 — AI stated customer affected for 3 days and requesting refund — both false
- Overall hallucination rate: 1.0
- Eval verdict: FAIL

Governance check:
- EU AI Act risk tier: HIGH
- PII detected and redacted: email, phone
- Bias flag: historical ticket data may over-represent enterprise segments
- Governance verdict: FLAGGED
- Required actions: data protection assessment, GDPR compliance review, bias mitigation

---

## 2. Why We Built It
Stage 01 produces user signal. Stage 02 stress-tests it. Before any feature goes to the Orchestrator for a go/no-go decision, it needs to pass three independent checks: how different user types will actually react (Persona Agent), whether the AI is producing faithful and factual output (Hallucination Eval Agent), and whether the feature clears governance, legal, and compliance requirements (Governance Module). Building all three on the same day is intentional — they represent three dimensions of the same question: is this feature safe to ship? The answer today, across all three agents, is: not yet.

---

## 3. Code and Logic Explained

**Persona Agent — how it works step by step**

1. Defines 6 hardcoded personas, each with a role and a context string
2. Loops through each persona and constructs a prompt that asks the LLM to simulate that persona's reaction
3. The prompt instructs the LLM to return a strict JSON object with reaction score, objections, champion/blocker classification, and a key quote
4. Each response is parsed with `json.loads()` directly — if parsing fails, the raw response is stored with an error flag
5. After all 6 personas run, a summary is assembled with average score and lists of blockers and champions

```python
# Why personas are hardcoded not LLM-generated
PERSONAS = [
    {"role": "Enterprise Buyer", "context": "Fortune 500, procurement-driven, risk-averse"},
    {"role": "Legal / Compliance", "context": "EU AI Act aware, flags PII and liability risk"},
    ...
]
```
The persona definitions are hardcoded because consistency matters more than variety here. The same 6 personas run against every feature hypothesis — this makes scores comparable across different features and different days. If personas were generated dynamically, there would be no stable baseline for comparison.

**Hallucination Eval Agent — two types of hallucination**

Faithfulness hallucination: the AI says something that is not grounded in the source material — it invents claims. In today's test, the AI invented a server outage that was never mentioned in the ticket.

Factuality hallucination: the AI states something that is factually incorrect — it contradicts verifiable reality. In today's test, the AI said the customer was affected for 3 days and requesting a refund — both directly contradicted by the source ticket.

```python
# The test case design
ai_output = "Our systems have been down since yesterday..."   # invented outage
source_context = "No server outage has been reported internally."  # source truth
```
The test is deliberately adversarial — a worst-case summary of a real support ticket. This calibrates the eval agent against a known failure before it is used on real output.

**Governance Module — three layers running in sequence**

Layer 1 — PII scrubber (runs before anything reaches the LLM):
Uses regex patterns to detect and redact emails, phone numbers, credit card numbers, and SSNs. Returns both the scrubbed text and a list of PII types found. Operates entirely in Python — no LLM involved — so PII never touches the API.

```python
# Why PII scrubbing happens before the LLM call, not after
scrubbed_description, pii_found = scrub_pii(feature_description)
# Only the scrubbed version is sent to call_llm()
```

Layer 2 — EU AI Act classifier (LLM-powered):
The LLM receives the scrubbed feature description and classifies it into one of four risk tiers: UNACCEPTABLE, HIGH, LIMITED, MINIMAL. HIGH risk means mandatory human review. UNACCEPTABLE means BLOCKED regardless of any other signal.

Layer 3 — Bias detector (LLM-powered):
The LLM reviews the feature for potential bias sources — skewed training data, differential performance across user segments, proxy discrimination. Today's flag: enterprise ticket data likely dominates training sets, producing better summaries for enterprise customers than SMB customers.

---

## 4. Issues We Faced

### Issue 1 — `ModuleNotFoundError: No module named 'agents'` on all agent files
**Problem:** Running any agent file directly with `python agents/persona_agent.py` from the project root throws a `ModuleNotFoundError`. Python cannot resolve `from agents.utils import call_llm` even though `__init__.py` exists in the `agents/` folder. This is a Windows + venv path resolution quirk.
**Solution:** Added the sys.path fix to the top of every agent file before any import from the agents module:
```python
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```
This tells Python to look one level up from the current file's directory when resolving imports. It is a one-time fix per file. When FastAPI is wired on Day 9, this issue disappears because FastAPI runs from the project root and handles module resolution automatically.

### Issue 2 — `interview_agent.py` and `synthesis_agent.py` missing the sys.path fix
**Problem:** The fix was added to `persona_agent.py` during debugging but the same import pattern in `interview_agent.py` and `synthesis_agent.py` was not updated, leaving them broken for direct execution.
**Solution:** Added the same two-line sys.path fix to both files before the `from agents.utils` and `from agents.prompts` imports. All agent files now follow the same import pattern.

### Issue 3 — Persona Agent `json.loads()` fails when LLM wraps output in markdown fences
**Problem:** The persona prompt instructs the LLM to return only valid JSON, but GPT-4o-mini occasionally wraps the response in ` ```json ... ``` ` fences. `json.loads()` called directly on the fenced string throws a `JSONDecodeError`.
**Solution:** The persona agent catches `JSONDecodeError` and stores the raw response with an error flag rather than crashing. A future improvement is to run the response through `parse_json_response()` from `utils.py` which already handles fence stripping — this will be standardised across all agents during Day 13 hardening.

---

## 5. VP / Director Decisions Made

### Decision 1 — Hardcode 6 fixed personas vs generate them dynamically per feature
**Situation:** The Persona Agent could generate a different set of personas for each feature (dynamic) or always run the same 6 personas against every feature (fixed).
**Options considered:** Dynamic personas — more tailored per feature, less comparable across features. Fixed personas — less tailored, fully comparable across features, stable baseline.
**Decision taken:** Fixed 6 personas.
**Reasoning:** The value of persona simulation at portfolio level is comparability. If the Enterprise Buyer scores 7 on feature A and 4 on feature B, that comparison is only meaningful if the same persona definition was used in both runs. Dynamic personas would produce scores that cannot be compared across features — making it impossible to build the kind of historical signal that the RAG memory system (Day 11) is designed to retrieve. Tailoring can be added later as an optional override.

### Decision 2 — Run PII scrubbing in Python before the LLM call vs instruct the LLM to redact PII
**Situation:** PII detection could be done by the LLM (instructed to identify and redact sensitive data in its output) or by a regex-based Python function before any text reaches the API.
**Options considered:** LLM-based redaction — flexible, handles edge cases, but PII still travels to the API. Python regex — limited to known patterns, but PII never leaves the local machine.
**Decision taken:** Python regex scrubber running before the LLM call.
**Reasoning:** Instructing an LLM to redact PII still sends the PII to the API endpoint, which means it travels over the network and potentially logs to OpenAI's servers. For a feature processing customer support tickets containing real customer data, this is not acceptable under GDPR. The regex scrubber is not perfect — it will miss novel PII formats — but it provides a deterministic, auditable first line of defence that operates entirely locally. The governance module documents its known limitations explicitly.

### Decision 3 — FLAGGED verdict on HIGH risk tier vs automatic BLOCKED
**Situation:** The EU AI Act classifier returned HIGH risk tier for the ticket summariser feature. The governance module could automatically block HIGH risk features or flag them for human review.
**Options considered:** Auto-BLOCK on HIGH risk — maximum caution, may block legitimate features. FLAGGED with required actions — escalates to human review, feature can still proceed with conditions.
**Decision taken:** FLAGGED with required actions list — human review required before GO.
**Reasoning:** UNACCEPTABLE risk tier is the only category that warrants an automatic block — those features are prohibited under the EU AI Act regardless of mitigation. HIGH risk features can ship if proper controls are in place: human oversight, data protection assessments, transparency requirements. Auto-blocking HIGH risk would make the system too conservative for a product team to trust. The FLAGGED verdict with a specific required actions list gives the PM team a clear path to resolution rather than a wall.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| Persona simulation | Running a feature hypothesis through the lens of different user types to surface reactions and objections before real users see it |
| Faithfulness hallucination | The AI generates a claim that has no grounding in the source material — it invents something |
| Factuality hallucination | The AI states something that directly contradicts verifiable facts in the source |
| Hallucination rate | A score from 0 to 1 measuring how much of the AI output cannot be trusted — 0 is clean, 1 is entirely fabricated |
| EU AI Act risk tiers | Four categories (UNACCEPTABLE, HIGH, LIMITED, MINIMAL) that classify how much risk an AI feature poses to individuals and society |
| PII (Personally Identifiable Information) | Any data that can identify a specific person — emails, phone numbers, ID numbers — regulated under GDPR |
| Regex | Pattern-matching rules written in code to find specific text structures — used here to detect PII before it reaches the API |
| Bias in AI systems | Systematic skew in AI output caused by imbalances in training data — here, enterprise tickets likely outnumber SMB tickets, producing better results for enterprise users |
| Governance verdict | A classification of CLEAR, FLAGGED, or BLOCKED that summarises whether a feature is safe to proceed to the next pipeline stage |

---

## 7. How This Connects to the Bigger System
Stage 02 produces three independent evaluation signals that the Orchestrator Agent will aggregate in Stage 03. The persona simulation provides a stakeholder reaction score and a list of blockers. The hallucination eval provides a faithfulness and factuality score. The governance module provides a risk tier and a verdict. When the Orchestrator reads all three on Day 6, it has a multi-dimensional picture of feature readiness — not just whether users want it, but whether it is safe, accurate, and legally compliant. Today's outputs also feed into the audit trail system built on Day 7: every eval report and governance verdict is logged with input signals and reasoning so the system learns over time which feature characteristics correlate with which evaluation outcomes.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Fixed 6 personas | Dynamic per feature, fixed 6, user-configurable set | Comparability across features is more valuable than tailoring; enables historical scoring in RAG memory | If product scope expands to multiple verticals with fundamentally different buyer types — would add persona sets per vertical |
| Python regex PII scrubber before API call | LLM-based redaction, regex pre-scrub, third-party PII API | PII must never reach the API endpoint; deterministic and auditable; no external dependency | If PII patterns become too complex for regex — would add a local ML-based NER model like spaCy |
| FLAGGED on HIGH risk vs auto-BLOCK | Auto-BLOCK HIGH risk, FLAGGED with required actions, warning only | HIGH risk features can ship with controls; auto-blocking would make governance too conservative to be trusted by the team | If regulatory environment tightens and HIGH risk features require pre-approval from a regulatory body — would move to auto-BLOCK with appeal process |

---

## 9. Resume Bullet
> Built a three-agent evaluation layer for an AI product pipeline — persona simulation across 6 user archetypes, hallucination detection distinguishing faithfulness from factuality failures, and a responsible AI governance module with regex-based PII scrubbing, EU AI Act risk classification, and automated bias flagging — catching two blocker personas, a 100% hallucination rate on a test case, and a HIGH risk EU AI Act classification before a single line of feature code shipped.

---

## 10. LinkedIn Hook
> I let an AI agent simulate 6 user personas before shipping a feature. What it caught that real interviews missed: a Legal stakeholder who flagged GDPR liability and a Security lead who blocked on data leakage — neither objection came up in the real interview. Here is exactly how the agent works.

---

## 11. Honest Rating
**Difficulty:** 6/10
**Confidence after today:** 8/10
**What clicked:** The moment the Governance Module flagged HIGH risk on the same feature that the Legal/Compliance persona had already blocked — two independent agents, built separately, reaching the same conclusion. That convergence made the system feel real.
**What still feels unclear:** How the Orchestrator will weight three signals that disagree — if persona scores are high but hallucination rate is also high, what does the go/no-go actually come out as. That question gets answered on Day 6.

---

## 12. Next Course of Action
**Tomorrow — Day 05:** Confidence Scoring + Prompt A/B Eval (Stage 02: Evaluate continues)
Two more evaluation tools: the Confidence Calibration Agent measures the gap between how confident the LLM says it is and how accurate it actually is — using the Brier score as the measurement tool. The Prompt A/B Eval system versions every prompt, runs old vs new against the same test set, and automatically promotes the winner. Stage 02 will be complete after Day 05 — all evaluation signals will be ready for the Orchestrator.
