# AI Product Intelligence Loop — Known Limitations
**Day 13 | System Hardening Document**

---

## How to use this document

This document is part of the Written Strategy Document (Day 14). In interviews, referencing known limitations proactively signals VP-level thinking — you understand the system deeply enough to know where it breaks.

---

## Limitation 1 — Calibration requires resolved outcomes

**What:** The Calibration Analysis Agent calculates Brier scores and recommends threshold adjustments. This requires decisions with known outcomes (CORRECT / INCORRECT). New deployments only have PENDING outcomes.

**Impact:** Calibration verdict stays INSUFFICIENT_DATA until 5+ decisions are resolved. Threshold recommendations are not meaningful until then.

**Workaround:** Manually update outcomes via `POST /update-outcome` as real-world results come in. After 2 weeks of production use, calibration becomes meaningful.

**Reversal condition:** Wire post-launch feature metrics (user retention, support ticket volume) as automatic outcome signals. When a GO feature's metrics exceed baseline by >10%, auto-mark as CORRECT.

---

## Limitation 2 — Competitive intel uses LLM knowledge, not live web search

**What:** The Competitive Intelligence Agent calls GPT-4o-mini and relies on its training data for competitor signals. It does not browse the web in real time.

**Impact:** Signals may be weeks or months stale. A competitor launch from yesterday will not appear.

**Workaround:** For demo purposes this is sufficient. The agent structure, RAG injection, and Orchestrator wiring are all production-ready.

**Reversal condition:** Replace `call_llm()` in `competitive_intel.py` with a Perplexity API call or SerpAPI web search. The rest of the pipeline requires zero changes.

---

## Limitation 3 — Interview agent is terminal-only

**What:** The Interview Agent collects answers via `input()` — terminal prompts. It cannot receive async responses from real users over email, Slack, or a web form.

**Impact:** Cannot run real user interviews at scale without manual terminal sessions.

**Workaround:** Use the Synthesis Agent directly on existing interview transcripts. The pipeline from Stage 02 onward is fully automated.

**Reversal condition:** Replace the `input()` loop with a FastAPI webhook endpoint that receives interview responses asynchronously. Each response triggers a follow-up question via email or Slack DM.

---

## Limitation 4 — Token cost logging is incomplete in pipeline runs

**What:** The `log_decision()` call in `routes.py` hardcodes `tokens_consumed=0`. Real token counts are tracked per-agent in `cost_log.json` via the cost tracker but not aggregated into the audit trail entry.

**Impact:** Audit trail shows 0 tokens per decision. Cost-per-decision in the audit trail is not accurate (though the `/cost-report` endpoint is accurate).

**Workaround:** The `/cost-report` endpoint gives the correct numbers. Use that for the demo.

**Reversal condition:** After each pipeline run, read the total tokens from `get_cost_report()` and pass the value to `log_decision()`.

---

## Limitation 5 — Prompt version registry is in-process only during A/B eval

**What:** `PROMPT_VERSIONS` in the old `prompt_ab.py` was a Python dict — reset every process restart. The Day 13 hardened version persists to `prompts/versions/` files and `data/prompt_version_history.json`.

**Impact (resolved):** Day 13 hardening fixes this. Version state now survives restarts.

**Remaining gap:** If `prompts/versions/` is deleted, version history is lost. Backup to S3 or git for production.

---

## Limitation 6 — Security layer uses regex, not an LLM classifier

**What:** Prompt injection detection uses 15 regex patterns. A sophisticated attacker can craft injections that bypass pattern matching (e.g. using Unicode lookalikes or encoding tricks).

**Impact:** Security layer catches common injection patterns but is not adversarially robust.

**Workaround:** For the current use case (internal PM tool, not public-facing), regex is sufficient.

**Reversal condition:** Add a secondary LLM-based injection classifier that scores input on a 0-1 risk scale. Block inputs above 0.7. This adds ~$0.001 per call but closes the adversarial gap.

---

## Limitation 7 — React dashboard uses mock data

**What:** `App.jsx` uses hardcoded `PAIN_THEMES`, `EVAL_HISTORY`, `DECISIONS`, and `COST_DATA` constants. It does not call the FastAPI backend in real time.

**Impact:** Dashboard shows demo data, not live pipeline output.

**Workaround:** For the interview demo this is fine — the data is realistic and the architecture is explained. The FastAPI endpoints exist and return real data.

**Reversal condition:** Replace mock constants with `useEffect` + `fetch()` calls to `/discover`, `/audit-trail`, and `/cost-report`. The component structure requires no changes.

---

## Limitation 8 — n8n workflow fails if FastAPI is not running

**What:** The n8n cron workflow POSTs to `localhost:8000/run-pipeline`. If uvicorn is not running, the HTTP Request node fails silently.

**Impact:** Daily automation stops without notification.

**Reversal condition:** Add an n8n error workflow that fires a Slack alert when any node fails. Takes 5 minutes to configure in the n8n UI under Settings → Error Workflow.

---

## Component cut first under scope pressure

If the project had to ship with one component removed, the **Competitive Intelligence Agent** is cut first.

**Reasoning:** It provides the least unique signal — a PM can do a manual competitor check in 10 minutes. Every other component (security layer, RAG memory, calibration, reflexion loop, governance module) provides automation that genuinely cannot be replicated manually at scale. Competitive intel can be added back in 2 hours once the core system is stable.

---

## How this scales with a 5-person AI PM team

| What changes | What stays the same |
|-------------|-------------------|
| Interview Agent replaced by async webhook — multiple PMs run interviews in parallel | Orchestrator, Decider, Reflexion Loop architecture unchanged |
| Synthesis Agent processes 10x more transcripts | RAG retrieval gets better — more signal, not more noise |
| Calibration Agent has enough resolved outcomes to make meaningful recommendations | Threshold logic unchanged |
| Multiple features in the pipeline simultaneously — need run_id namespacing | Cost tracker already uses run_id |
| Security layer needs team-level audit log (not just per-run) | Event structure already supports this |

**One role needed:** A dedicated AI PM Ops person who owns threshold calibration, monitors the security log weekly, and manages prompt version promotions. Without this role, the system runs on autopilot but drift goes unreviewed.
