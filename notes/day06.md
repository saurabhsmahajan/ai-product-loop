# Day 06 — Orchestrator Agent + Go/No-Go + Reflexion Loop
**Date:** May 30, 2026
**Stage:** Stage 03 — Decide
**Status:** ✅ Complete

---

## 1. What We Built
- `agents/orchestrator.py` — reads all Stage 01 and Stage 02 signals, aggregates them into a single weighted confidence score, maintains pipeline state, and routes to Decider or Human Escalation
- `agents/decider.py` — receives the Orchestrator's full context package and produces a documented GO / NO_GO / CONDITIONAL_GO with confidence score and full reasoning chain
- `agents/critic.py` — Reflexion Loop: reviews the Decider's reasoning, scores it, sends back for revision if critique score < 0.7, escalates to human after 2 passes if score stays below threshold

**Files created:**
```
AI-PRODUCT-LOOP/
├── agents/
│   ├── orchestrator.py
│   ├── decider.py
│   └── critic.py
└── data/
    ├── orchestrator_report.json     ← pipeline state and routing decision
    ├── decider_report.json          ← go/no-go with reasoning chain
    └── reflexion_report.json        ← full reflexion loop audit trail
```

**Key outputs from today's runs:**

Orchestrator (aggregated across all 4 signals):
- Hallucination eval weight 30%: faithfulness score 0.0
- Confidence calibration weight 30%: trust score 3/10 = 0.3 normalised
- Persona simulation weight 20%: avg score 6.83/10 = 0.683 normalised
- Governance verdict weight 20%: FLAGGED = 0.5
- Aggregated confidence score: 0.327
- Routing decision: HUMAN_ESCALATION

Decider (Pass 1 — before Reflexion):
- Decision: NO_GO
- Confidence score: 0.327
- Escalate to human: true

Reflexion Loop — Pass 1:
- Critic score: 0.5 — REVISE
- Weakness: no mitigation strategies, confidence score not contextualised
- Missing: alternative solutions, business implications of NO_GO

Reflexion Loop — Pass 2:
- Revised decision: CONDITIONAL_GO, confidence 0.475
- Critic score: 0.5 — REVISE again
- Missing: market impact assessment, stakeholder feedback
- Max passes reached — escalated to human

Final decision: CONDITIONAL_GO with 4 specific conditions:
- Hallucination rate reduced below 0.3 through testing
- EU AI Act governance framework established before development
- Trust score of at least 7/10 achieved in beta evaluations
- Continuous feedback loops and recalibration implemented

---

## 2. Why We Built It
Stage 01 produces signal. Stage 02 stress-tests it. Stage 03 makes a decision. But a single-pass decision from a single agent is not trustworthy — it reflects one reasoning path, one set of assumptions, one blind spot. The Orchestrator aggregates all signals into a weighted confidence score so the decision is grounded in data, not LLM intuition. The Decider documents every step of its reasoning so the decision is auditable. The Reflexion Loop adds a structured adversarial critic so the reasoning is challenged before it is committed. Together, these three agents produce the kind of documented, defensible, human-escalated product decision that a VP can take to a board — or a regulator.

---

## 3. Code and Logic Explained

**Orchestrator Agent — weighted confidence aggregation**

The Orchestrator reads four signal files from `data/` and aggregates them into one confidence score using a weighted formula:

```python
# Weighting logic — why these weights
# Hallucination eval:        30% — most critical AI quality signal
# Confidence calibration:    30% — trust is as important as accuracy
# Persona simulation:        20% — user reaction is real but noisier
# Governance verdict:        20% — binary compliance signal
```

Scores from different scales are normalised before weighting:
- Trust score (0–10) is divided by 10 to produce 0–1
- Persona avg reaction (0–10) is divided by 10 to produce 0–1
- Governance verdict is mapped: CLEAR=1.0, FLAGGED=0.5, BLOCKED=0.0

```python
aggregated = sum(score * weight for _, score, weight in scores)
```

Today's aggregated score of 0.327 breaks down as:
- Hallucination: 0.0 × 0.30 = 0.000
- Confidence: 0.3 × 0.30 = 0.090
- Persona: 0.683 × 0.20 = 0.137
- Governance: 0.5 × 0.20 = 0.100
- Total: 0.327

**Routing threshold logic**

```python
route = "HUMAN_ESCALATION" if agg_confidence < 0.6 else "DECIDER"
```

0.6 is the routing threshold. Features above 0.6 go to the Decider for an autonomous decision. Features below 0.6 are escalated to a human before the Decider even runs. Today's score of 0.327 is well below — the system correctly refused to let the Decider operate without human oversight.

**Decider Agent — reasoning chain design**

The Decider receives the full Orchestrator report and is instructed to produce a reasoning chain — not just a verdict. The chain forces the LLM to reason step by step before committing to a decision, which produces more reliable outputs than asking for a verdict directly.

Three possible decisions:
- GO — feature is ready to ship
- NO_GO — feature should not proceed in current form
- CONDITIONAL_GO — feature can proceed if specific conditions are met

CONDITIONAL_GO always requires a populated `conditions_if_conditional` list. An empty conditions list on a CONDITIONAL_GO is a reasoning failure — the Critic flags this.

**Reflexion Loop — how the self-critique cycle works**

```
Decider → decision + reasoning chain
    ↓
Critic → critique score + weaknesses + missing signals
    ↓
If score >= 0.7 → APPROVE — done
If score < 0.7 and passes remain → revision instructions sent back to Decider
    ↓
Decider → revised decision incorporating critique
    ↓
Critic → re-scores revised reasoning
    ↓
If max passes reached and score still < 0.7 → HUMAN_ESCALATION
```

The Critic is deliberately adversarial — its prompt instructs it to find holes, not validate reasoning. A critique score of 0.5 on both passes means the Critic found legitimate gaps both times. The system correctly refused to approve a decision with unresolved reasoning weaknesses.

**Why the Decider revised from NO_GO to CONDITIONAL_GO**

On Pass 1, the Critic's revision instructions asked the Decider to add mitigation strategies and contextualise the confidence score. A Decider that adds specific conditions for how risks can be resolved will naturally shift from NO_GO to CONDITIONAL_GO — because CONDITIONAL_GO is the correct decision when risks are real but addressable. This is the Reflexion Loop working as designed: critique pressure produces more nuanced reasoning.

---

## 4. Issues We Faced

### Issue 1 — Orchestrator prompt returning signals as key-value objects instead of plain strings
**Problem:** The first run of the Orchestrator produced invalid JSON because the LLM formatted the `signals` array as `["FAIL": "Hallucination verdict is FAIL", ...]` — a key-value structure inside an array, which is not valid JSON. The `parse_json_response()` function could not parse it.
**Solution:** Updated `ORCHESTRATOR_PROMPT` to add an explicit rule: the signals field must be a plain JSON array of strings with no keys, colons, or nested objects. Added a concrete example in the prompt: `["Hallucination verdict is FAIL", "EU AI Act tier is HIGH"]`. The second run parsed correctly.

### Issue 2 — Persona simulation file not found on first Orchestrator run
**Problem:** The Orchestrator expects `data/persona_simulation.json` but the Persona Agent from Day 4 saves its output as an in-memory dictionary, not to a file. The file did not exist on disk.
**Solution:** Added a fallback in the Orchestrator: if `persona_simulation.json` is not found, it imports and runs `simulate_personas()` from `persona_agent.py` automatically, saves the result to `data/persona_simulation.json`, and continues. Future runs find the file and skip the regeneration step.

### Issue 3 — Reflexion Loop critique score stayed at 0.5 across both passes
**Problem:** The Critic scored both the original and revised decision at 0.5. This raised the question: is the Critic too strict, or are there genuine unresolved gaps in the reasoning?
**Solution:** No code change was needed — this is correct behaviour. The Critic identified two legitimate missing signals on both passes: market impact assessment and stakeholder feedback. Neither was addressed in the revision because the Decider only had access to the pipeline data, not external market research or stakeholder input. The system correctly escalated to human rather than approving a decision with known gaps. The Calibration Analysis Agent on Day 12 will review whether the 0.7 critique threshold needs recalibration based on accumulated audit data.

---

## 5. VP / Director Decisions Made

### Decision 1 — Weighted confidence aggregation over simple average
**Situation:** The Orchestrator needs to combine four signals with different scales and different importance levels into one number. A simple average treats all signals as equally important. A weighted average reflects the relative importance of each signal.
**Options considered:** Simple average — transparent, no assumptions. Weighted average — reflects domain knowledge about signal importance. ML-based scoring — learns weights from historical outcomes, requires data.
**Decision taken:** Weighted average with explicit weights: hallucination 30%, confidence 30%, persona 20%, governance 20%.
**Reasoning:** Hallucination and confidence calibration are weighted higher because they measure AI quality directly — a feature that hallucinates at high confidence is dangerous regardless of how much users want it. Persona and governance are weighted lower because they can be addressed through product design and compliance work. The weights are documented and reversible — the Calibration Analysis Agent on Day 12 will review whether the weighting needs adjustment based on audit trail data.

### Decision 2 — Route to human escalation at 0.6 threshold vs letting Decider decide at any confidence
**Situation:** The Orchestrator could route every feature to the Decider and let the Decider decide whether to escalate. Or it could apply a routing threshold — features below a confidence score go straight to human escalation before the Decider runs.
**Options considered:** Always route to Decider — simpler, Decider handles escalation. Threshold routing at 0.6 — Orchestrator pre-filters, reduces load on Decider for clear cases. Dynamic threshold — adjusts based on feature risk tier.
**Decision taken:** Fixed threshold of 0.6 with explicit human escalation routing.
**Reasoning:** Letting a Decider with confidence 0.327 make an autonomous product decision — even a NO_GO — without surfacing to a human is the wrong design for a system making VP-level product calls. The 0.6 threshold acts as a circuit breaker: below it, the Orchestrator forces human involvement before any agent commits to a decision. Above it, the Decider runs with a mandate to decide. The threshold is a configuration value, not hardcoded logic — it can be adjusted per product domain or risk appetite.

### Decision 3 — Cap Reflexion Loop at 2 passes vs unlimited revision cycles
**Situation:** The Reflexion Loop could run until the Critic approves, potentially looping indefinitely. It needs a cap.
**Options considered:** No cap — loops until approved, risks infinite loop. Cap at 1 pass — not enough for meaningful revision. Cap at 2 passes — one revision cycle before escalation. Cap at 3 passes — more thorough, higher API cost.
**Decision taken:** Cap at 2 passes (`MAX_REVISION_PASSES = 2`).
**Reasoning:** A single revision pass gives the Decider one opportunity to address the Critic's feedback. If the revised reasoning still scores below 0.7 after one revision, the gap is likely caused by missing external information — market data, stakeholder input, business context — that no amount of LLM reasoning can fill. Further passes would produce diminishing returns at increasing API cost. Two passes is the right balance: thorough enough to catch improvable reasoning, disciplined enough to escalate rather than loop on unresolvable gaps.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| Orchestrator Agent | The pipeline brain — reads all signals, aggregates them, and decides what happens next without making the actual product decision |
| Weighted confidence score | A single number combining multiple signals with different importance weights — more meaningful than a simple average |
| Signal normalisation | Converting scores on different scales (0–10, 0–1, categorical) to a common 0–1 scale before combining them |
| Routing threshold | A confidence score below which the system escalates to human rather than proceeding autonomously |
| Decider Agent | The agent that produces the actual GO / NO_GO / CONDITIONAL_GO recommendation with a documented reasoning chain |
| Reasoning chain | A step-by-step log of every argument the Decider considered before reaching its verdict — makes the decision auditable and reversible |
| CONDITIONAL_GO | A decision that says the feature can proceed only if specific, named conditions are met — more useful than a binary GO / NO_GO |
| Reflexion Loop | A self-critique cycle where a Critic Agent reviews the Decider's reasoning and sends it back for revision if quality is below threshold |
| Critique score | A 0–1 rating of how well-reasoned a decision is — below 0.7 triggers revision, above 0.7 triggers approval |
| Human escalation | The system's mechanism for surfacing uncertainty to a human when it cannot resolve a decision with sufficient confidence |

---

## 7. How This Connects to the Bigger System
Stage 03: Decide is the centrepiece of the intelligence loop. Every signal built in Days 3–5 flows into the Orchestrator today. The aggregated confidence score, routing decision, Decider verdict, and Reflexion audit trail are all saved to `data/` — these files become the primary input for the ChromaDB vector store on Day 7. Every decision made by the system is embedded into vector memory so that future Orchestrator runs can retrieve semantically similar past decisions and learn from them. The Calibration Analysis Agent on Day 12 reads the accumulated audit trail and recalibrates the confidence thresholds based on which past decisions turned out to be correct. The Business Impact Translator on Day 10 reads the Decider's CONDITIONAL_GO conditions and maps them to revenue impact estimates for the executive memo. Stage 03 is the node everything else connects to.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Weighted confidence aggregation | Simple average, weighted average, ML-based scoring | Domain knowledge about signal importance produces more reliable routing than equal weighting; weights are explicit and reviewable | If audit trail data from Day 12 shows consistent miscalibration — would shift weights or move to ML-based scoring |
| 0.6 routing threshold | 0.5, 0.6, 0.7, dynamic by risk tier | 0.6 reflects meaningful uncertainty — below it the system does not have enough signal to decide safely; above it the Decider has a real mandate | If false escalation rate is too high in production — would lower to 0.5; if unsafe decisions slip through — would raise to 0.7 |
| 2 Reflexion passes | 1 pass, 2 passes, 3 passes, unlimited | One revision is sufficient for improvable reasoning; persistent gaps after revision signal missing external data, not reasoning failure | If audit data shows 3-pass loops consistently produce better decisions without significant cost increase — would raise to 3 |

---

## 9. Resume Bullet
> Built a three-agent decision layer — Orchestrator aggregating pipeline signals into a weighted confidence score, Decider producing documented GO / NO_GO / CONDITIONAL_GO recommendations with full reasoning chains, and a Reflexion Loop where a Critic Agent challenges reasoning quality and triggers revision cycles before any decision is committed — producing a CONDITIONAL_GO with 4 specific ship conditions and a full audit trail of every argument considered and rejected.

---

## 10. LinkedIn Hook
> I built a self-critiquing AI agent that argues with itself before making product decisions. Pass 1: NO_GO. Critic found the reasoning had holes. Pass 2: CONDITIONAL_GO with 4 specific conditions. Critic still found gaps. System escalated to human. Here is exactly how the Reflexion Loop works — and why it matters more than the decision itself.

---

## 11. Honest Rating
**Difficulty:** 7/10
**Confidence after today:** 9/10
**What clicked:** The moment the Reflexion Loop revised the decision from NO_GO to CONDITIONAL_GO under critic pressure — the system produced a more nuanced and actionable outcome than either the original decision or a simple human override would have. The loop is not just defensive; it actively improves reasoning quality.
**What still feels unclear:** How the system will handle a feature that the Critic consistently approves at 0.7 but which later turns out to be wrong post-launch. That is what the drift monitoring and audit trail on Days 7–8 are designed to catch — the loop closes there.

---

## 12. Next Course of Action
**Tomorrow — Day 07:** ChromaDB + Vector Embeddings + Audit Trail (Stage 04: Learn begins)
Install and configure ChromaDB locally. Write all interview transcripts and past decisions into the vector store as embeddings. Build the Audit Trail logger: every agent decision persisted with input signals, reasoning chain, confidence score, escalation flag, model used, tokens consumed, and eventual outcome. Stage 04 is where the system starts remembering — and getting smarter over time.
