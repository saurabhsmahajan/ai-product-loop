# Day 05 — Confidence Scoring + Prompt A/B Eval
**Date:** May 29, 2026
**Stage:** Stage 02 — Evaluate (continued)
**Status:** ✅ Complete

---

## 1. What We Built
- `agents/confidence.py` — calculates Brier score, measures calibration gap between stated confidence and actual accuracy, produces a full trust score and calibration verdict
- `agents/prompt_ab.py` — versions prompts, runs v_old vs v_new against the same test set, scores each version on hallucination rate and faithfulness, automatically promotes the winner

**Files created:**
```
AI-PRODUCT-LOOP/
├── agents/
│   ├── confidence.py
│   └── prompt_ab.py
└── data/
    ├── confidence_report.json       ← calibration agent output
    └── prompt_ab_report.json        ← A/B eval report
```

**Key outputs from today's runs:**

Confidence calibration (AI ticket summariser — 5 statements):
- Stated confidence: 0.85 — the AI claimed to be 85% confident
- Actual accuracy: 0.40 — it was correct only 40% of the time
- Calibration gap: 0.45 — overconfident by 45 percentage points
- Brier score: 0.3875 — worse than random guessing (0.25 baseline)
- Trust score: 3 / 10
- Calibration verdict: OVERCONFIDENT

Prompt A/B eval (ticket_summariser — v1 vs v2, 3 test cases):
- v1 scores: faithfulness 1.0 | factuality 1.0 | hallucination rate 0.0 | pass 3/3
- v2 scores: faithfulness 1.0 | factuality 1.0 | hallucination rate 0.0 | pass 3/3
- Winner: v1 (tiebreaker — appears first when scores are equal)
- Reason both tied: clean, unambiguous test cases. Adversarial test cases added on Day 13 hardening will expose the real difference between prompt versions.

---

## 2. Why We Built It
Stage 02: Evaluate is not complete until we know two things: whether the AI is hallucinating (Days 4 eval agent), and whether it knows when it is hallucinating (Day 5 confidence calibration). A model that is wrong but uncertain is manageable — a human escalation threshold catches it. A model that is wrong but highly confident is dangerous — it looks trustworthy while producing harmful output. The confidence calibration agent quantifies this risk into a single trust score the Orchestrator can act on. The Prompt A/B Eval system adds the engineering discipline that ensures every prompt improvement is measurable, comparable, and documented — not just a gut-feel tweak.

---

## 3. Code and Logic Explained

**Confidence Calibration Agent — how it works step by step**

1. Receives a list of AI statements, each with a stated confidence (0–1) and an actual outcome (1 = correct, 0 = wrong)
2. Calculates the Brier score using the formula: average of (stated_confidence − actual_outcome)²
3. Calculates average stated confidence and average actual accuracy across all statements
4. Derives the calibration gap: absolute difference between stated and actual
5. Sends all metrics to the LLM with the `CONFIDENCE_SCORING_PROMPT` to produce a reasoned calibration report
6. Overwrites the LLM's calculated values with the Python-calculated values to guarantee accuracy
7. Saves the full report to `data/confidence_report.json`

```python
# Why we overwrite LLM-calculated metrics with Python-calculated ones
report["brier_score"] = brier
report["stated_confidence"] = avg_stated
report["estimated_actual_accuracy"] = avg_actual
report["calibration_gap"] = calibration_gap
```
The LLM is used for reasoning and verdict — not arithmetic. Mathematical values are always calculated in Python and injected into the report after the LLM responds. This prevents the LLM from introducing rounding errors or miscalculations into a metric that the Orchestrator will use for routing decisions.

**Brier score explained**

Brier score = average of (stated_confidence − actual_outcome)²

- Perfect calibration = 0.0 (every confidence matches reality exactly)
- Random guessing = 0.25
- Today's score = 0.3875 — worse than random, because the AI was highly confident on wrong answers

```python
def calculate_brier_score(predictions: list) -> float:
    total = sum(
        (p["stated_confidence"] - p["actual_outcome"]) ** 2
        for p in predictions
    )
    return round(total / len(predictions), 4)
```

The three hallucinated statements (server outage, 3-day duration, refund request) each had high stated confidence (0.85, 0.80, 0.75) and actual outcome of 0. Squaring the gap amplifies the penalty for confident wrong answers — exactly the behaviour you want in a trust metric.

**Prompt A/B Eval System — how it works step by step**

1. Maintains a prompt versions registry — a dictionary mapping prompt names to a list of versioned prompt strings, each tagged active or inactive
2. Defines a fixed test set — the same 3 test cases run against every prompt version so results are comparable
3. For each version, loops through the test set and calls `run_single_eval()` — fills the prompt template with the test ticket, gets an AI summary, then runs the hallucination eval agent on that summary against the ground truth
4. Aggregates faithfulness, factuality, and hallucination scores across all test cases for each version
5. Picks the winner by lowest hallucination rate, with faithfulness as a tiebreaker
6. Updates the active flag in the registry and saves the full report

```python
# Winner selection logic — primary metric then tiebreaker
winner_tag = min(
    results,
    key=lambda v: (
        results[v]["avg_hallucination_rate"],
        -results[v]["avg_faithfulness_score"]
    )
)
```
Hallucination rate is the primary metric because it is the most critical failure mode in a support ticket summariser. Faithfulness is the tiebreaker because a summary that sticks to the source is more trustworthy than one that is technically factual but introduces unsupported framing.

**Why both versions scored identically today**

The test set uses clean, unambiguous tickets with explicit ground truth. Neither v1 ("be concise and accurate") nor v2 ("do not infer, assume, or add anything not in the ticket") is challenged by a clear ticket. The real performance gap between these prompts only surfaces on adversarial cases — tickets with missing information, conflicting signals, or ambiguous phrasing — which are added during Day 13 hardening. Today's run validates that the infrastructure works correctly. That is exactly what Day 5 needs.

---

## 4. Issues We Faced

### Issue 1 — LLM calculates metrics incorrectly when given raw numbers
**Problem:** When the LLM was asked to calculate the Brier score and calibration gap from raw prediction data, it introduced rounding errors and occasionally produced mathematically incorrect values. Trusting the LLM for arithmetic in a metric that drives routing decisions is unacceptable.
**Solution:** All numerical metrics (Brier score, calibration gap, average stated confidence, average actual accuracy) are calculated in Python before the LLM call. The LLM receives the pre-calculated numbers and is only asked to reason over them and produce a verdict. After the LLM responds, Python-calculated values are injected directly into the report, overwriting anything the LLM may have computed differently.

### Issue 2 — Prompt A/B eval winner declared on tied scores
**Problem:** Both v1 and v2 scored 0.0 hallucination rate on clean test cases, producing a tie. The system needed a deterministic tiebreaker that did not require human input.
**Solution:** When hallucination rates are equal, the winner is determined by highest faithfulness score. When faithfulness scores are also equal, the earlier version (v1) wins — preserving the existing active prompt unless there is a clear measurable improvement. This is the correct default: do not promote a new prompt unless it demonstrably outperforms the current one.

### Issue 3 — Prompt template filling with multi-line ticket text
**Problem:** The prompt template uses `{ticket}` as a placeholder. When the ticket text contains curly braces or special characters (common in JSON payloads pasted into support tickets), Python's `.replace()` method breaks the substitution.
**Solution:** Used `.replace("{ticket}", test_case["ticket"])` instead of Python's `.format()` method. `.format()` interprets all curly braces in the string as template slots — so a ticket containing `{"order_id": 123}` would crash the formatter. `.replace()` treats the string as plain text and substitutes only the exact `{ticket}` literal.

---

## 5. VP / Director Decisions Made

### Decision 1 — Python calculates metrics, LLM reasons over them — not the reverse
**Situation:** The calibration report needs both numerical metrics (Brier score, calibration gap) and a reasoned verdict (OVERCONFIDENT, WELL_CALIBRATED, UNDERCONFIDENT). Two options: ask the LLM to do everything including the maths, or calculate numbers in Python and ask the LLM only to reason.
**Options considered:** LLM computes everything — simpler code, single call, but arithmetic errors possible. Python computes numbers, LLM reasons — more code, but numerically reliable.
**Decision taken:** Python computes all numerical metrics. LLM produces only the reasoning and verdict.
**Reasoning:** The Orchestrator Agent uses the calibration gap and Brier score to make routing decisions — if these numbers are wrong, the routing is wrong. LLMs are unreliable at precise floating-point arithmetic. Separating calculation (Python) from reasoning (LLM) is the correct division of labour and a principle that applies across every agent in the system.

### Decision 2 — Hallucination rate as primary A/B eval metric over faithfulness or factuality
**Situation:** Three metrics are available to determine the winning prompt: faithfulness score, factuality score, and overall hallucination rate. The winner needs to be determined by one primary metric.
**Options considered:** Faithfulness — measures grounding in source. Factuality — measures real-world accuracy. Hallucination rate — combined measure of both failure modes.
**Decision taken:** Hallucination rate as primary metric, faithfulness as tiebreaker.
**Reasoning:** In a support ticket summariser, the most dangerous failure is the AI adding information that is not in the ticket — regardless of whether that addition is a faithfulness error or a factuality error. The overall hallucination rate captures both failure modes in a single number that is directly interpretable by a non-technical stakeholder. Faithfulness is the tiebreaker because grounding in the source is the more controllable failure mode — prompt engineering can address faithfulness more reliably than factuality.

### Decision 3 — Fixed test set across all prompt versions vs dynamic test set per run
**Situation:** The A/B eval test set could be fixed (same 3 cases every time) or dynamically generated from real interview transcripts and past tickets on each run.
**Options considered:** Fixed test set — fully comparable results, easy to reason about. Dynamic test set — more representative of real data, harder to compare across runs.
**Decision taken:** Fixed test set for now, with adversarial cases added on Day 13.
**Reasoning:** Comparability is the entire point of an A/B eval system. If the test set changes between runs, a score improvement could be caused by the new prompt being better or the new test set being easier — and there is no way to tell which. A fixed test set ensures that any score difference between versions is attributable only to the prompt change. Dynamic test sets are the right evolution once the system has enough real interview data to draw from — this is documented as a future state in the strategy document on Day 14.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| Confidence calibration | How well an AI's stated confidence matches its actual accuracy — a well-calibrated model that says 80% should be right 80% of the time |
| Brier score | A number from 0 to 1 measuring calibration quality — 0 is perfect, 0.25 is random guessing, higher is worse |
| Calibration gap | The absolute difference between stated confidence and actual accuracy — today's gap was 0.45, meaning the AI was 45 percentage points overconfident |
| Overconfident | A model that states high confidence on answers that turn out to be wrong — more dangerous than an underconfident model because it suppresses human review |
| Trust score | A 0–10 rating summarising how much a downstream agent or human should rely on this AI's outputs — today's score was 3/10 |
| Prompt versioning | Treating every prompt as a versioned artefact (v1, v2, v3) so changes can be tracked, compared, and rolled back |
| A/B eval | Running two versions of a prompt against the same test set and comparing scores to determine which one performs better |
| Test set | A fixed collection of inputs with known correct outputs used to score and compare AI behaviour consistently |
| Tiebreaker metric | A secondary metric used to decide between two options when the primary metric produces equal scores |

---

## 7. How This Connects to the Bigger System
The confidence calibration report and the prompt A/B eval report are the final two evaluation signals that Stage 02 produces. When the Orchestrator Agent is built on Day 6, it will read five signals from Stage 02: persona reaction scores, hallucination eval verdict, governance verdict, confidence trust score, and prompt A/B winner. The trust score of 3/10 from today will directly trigger the Orchestrator's human escalation routing — a score below the threshold means the system cannot auto-commit to a GO decision and must surface the uncertainty to a human. The Prompt A/B Eval system feeds into the Calibration Analysis Agent on Day 12, which reviews the accumulated A/B history and recalibrates thresholds based on which prompt characteristics consistently correlate with better hallucination scores.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Python calculates metrics, LLM reasons | LLM computes everything, Python computes everything, split responsibility | LLM arithmetic is unreliable for routing-critical numbers; reasoning is where LLMs add value | If a future LLM with verified arithmetic capabilities is integrated — would simplify to single call |
| Hallucination rate as primary A/B metric | Faithfulness, factuality, hallucination rate, composite score | Single interpretable number covering both failure modes; most relevant for the support ticket use case | If the feature domain shifts to one where factuality matters more than faithfulness — would weight factuality higher |
| Fixed test set | Fixed cases, dynamic from transcripts, rotating set | Comparability across runs is the precondition for meaningful A/B conclusions | Once 50+ real interview transcripts are in ChromaDB — would sample from them to create a representative rotating test set |

---

## 9. Resume Bullet
> Built a confidence calibration system measuring the gap between LLM stated confidence and actual accuracy using Brier scoring — surfacing a 0.45 calibration gap and 3/10 trust score that directly triggers human escalation in the Orchestrator — and a prompt A/B eval system that versions, tests, and automatically promotes prompt improvements against a fixed test set, turning prompt engineering from intuition into a measurable engineering discipline.

---

## 10. LinkedIn Hook
> I stopped trusting LLM confidence scores after I measured one. The AI said it was 85% confident. It was right 40% of the time. Here is the exact metric I built to catch this — and why it matters before you ship any AI feature.

---

## 11. Honest Rating
**Difficulty:** 6/10
**Confidence after today:** 9/10
**What clicked:** The Brier score formula — once it was clear that squaring the gap between confidence and outcome amplifies the penalty for confidently wrong answers, the whole point of calibration measurement clicked. A model that says 50% and is wrong loses 0.25 points. A model that says 90% and is wrong loses 0.81 points. Overconfidence is penalised exponentially.
**What still feels unclear:** How the Orchestrator will combine five evaluation signals that all point in different directions — what happens when persona scores are high but trust score is 3/10. Day 6 answers this.

---

## 12. Next Course of Action
**Tomorrow — Day 06:** Orchestrator Agent + Go/No-Go + Reflexion Loop (Stage 03: Decide)
Three components: the Orchestrator Agent reads all Stage 01 and Stage 02 signals and maintains pipeline state; the Decider Agent produces a documented go/no-go with confidence score and full reasoning chain; the Reflexion Loop adds a Critic Agent that reviews the Decider's reasoning — if the critique score falls below 0.7, the decision is sent back for revision. Stage 03 is where the system makes its first real product decision.
