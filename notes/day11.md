# Day 11 Notes — n8n Automation + Slack + Jira + Competitive Intel Agent
**AI Product Intelligence Loop | VP / Director AI PM Career Project**
Date: June 1, 2026 | Status: Complete ✅

---

## What You Built Today

### Deliverable 1 — `agents/competitive_intel.py`
A nightly competitive intelligence agent that scans for competitor updates and injects signals into the Orchestrator before each pipeline run.

**How it works:**
1. Takes a product domain and list of known competitors
2. Calls GPT-4o-mini to scan for feature launches, pricing changes, partnerships, executive moves, negative press
3. Scores each signal by urgency (high / medium / low)
4. Generates a 2-sentence `orchestrator_injection` brief
5. Stores the brief in ChromaDB via `store_decision()` — Orchestrator picks it up automatically via RAG

### Deliverable 2 — `agents/slack_notifier.py`
A reusable Slack alert function used by 3 agents.

| Agent | Alert type | When it fires |
|-------|-----------|---------------|
| Orchestrator | `info` or `escalation` | After every pipeline run |
| Decider | `go`, `no-go`, or `escalation` | After every decision |
| Critic (Reflexion Loop) | `escalation` | When critique score stays below 0.7 after 2 passes |

### Deliverable 3 — `agents/jira_notifier.py`
Auto-creates Jira feature tickets from Synthesis Agent output. Top 3 pain themes by opportunity score become Jira Stories automatically. Runs in dry-run mode if env vars not configured.

### Deliverable 4 — n8n Daily Cron Workflow
A 5-node automation workflow published at `localhost:5678`.

```
Schedule Trigger (6am daily)
    ↓
HTTP Request → POST localhost:8000/run-pipeline
    ↓
If → decision == "GO"
    ↓ true              ↓ false
Slack (GO ✅)      Slack (NO-GO 🚫)
```

### Deliverable 5 — Updated existing agents
| File | What changed |
|------|-------------|
| `agents/utils.py` | `call_llm()` now returns real token counts via `return_usage=True` |
| `agents/model_router.py` | Uses real API token counts instead of character estimation |
| `agents/synthesis_agent.py` | Stores pain themes in RAG + auto-creates Jira tickets |
| `agents/interview_agent.py` | Stores transcript chunks in RAG after save |
| `agents/decider.py` | Fires Slack alert after every go/no-go decision |
| `agents/critic.py` | Fires Slack escalation alert after Reflexion Loop fails |
| `agents/orchestrator.py` | Retrieves RAG context + competitive intel before LLM call |
| `memory/rag_retriever.py` | Added `source` parameter (backward compatible with `mode`) |

---

## Concepts You Learned

### Tool use in a business context
The Competitive Intel Agent doesn't just call an LLM — it uses the LLM's knowledge to reason about competitor landscapes and extract structured signals. The output is typed JSON that feeds directly into the Orchestrator prompt. This is tool use at the product layer.

### RAG as a data flywheel
Every interview transcript, pain theme, and competitive signal is now stored in ChromaDB. Every future agent run retrieves the top-3 relevant chunks before acting. The system gets smarter with every pipeline run — this is the data flywheel the LinkedIn post on Day 16 is about.

### Real token counting vs estimation
The original `model_router.py` estimated tokens using `len(text) // 4` — a rough guess that can be 30-40% off. The fix: pass `return_usage=True` to `call_llm()` and read `completion.usage.prompt_tokens` and `completion.usage.completion_tokens` directly from the API response. Cost dashboard now shows accurate numbers.

### n8n workflow automation
n8n runs workflows on a schedule without keeping a Python process alive. The 5-node workflow replaces a cron job + bash script with a visual, auditable automation. Published = active and running daily.

---

## Commands You Ran Today

```powershell
# Install n8n globally
npm install -g n8n

# Start n8n
n8n start

# Test Slack alert
python -c "from agents.slack_notifier import send_slack_alert; send_slack_alert('Test alert from Day 11', 'info')"

# Test competitive intel agent
python agents/competitive_intel.py

# Test full pipeline end to end
Invoke-RestMethod -Method POST -Uri http://localhost:8000/run-pipeline `
  -ContentType "application/json" `
  -Body '{"feature_hypothesis": "An AI assistant that automatically summarises customer support tickets and suggests responses to agents."}'

# Push to GitHub
git add .
git commit -m "Day 11 complete — Slack, Jira, competitive intel, RAG, real token tracking"
git push origin master
```

---

## Errors You Hit and How You Fixed Them

| Error | Cause | Fix |
|-------|-------|-----|
| `curl -X POST` not working | PowerShell's `curl` is an alias for `Invoke-WebRequest`, not Linux curl | Used `Invoke-RestMethod` instead |
| `retrieve_context() got unexpected keyword argument 'source'` | `rag_retriever.py` used `mode` parameter, Day 11 code used `source` | Added `source` parameter to function signature, kept `mode` for backward compatibility |
| `2>/dev/null` not working | Linux syntax, not valid in PowerShell | Used `2>$null` instead |
| `.env` visible on GitHub | Was committed before `.gitignore` was set up | `git rm --cached .env`, rotated OpenAI API key immediately |

---

## What the Output Looked Like

### Full pipeline run
```
status     : success
run_id     : RUN_20260601_123704
decision   : NO_GO
confidence : 0.42
escalated  : True
cost       : 0.002878
```

### Slack alerts received (3 alerts per pipeline run)
**Alert 1 — Orchestrator:**
> Orchestrator complete — Feature: An AI assistant...
> Confidence: `0.327` | Route: `HUMAN_ESCALATION`

**Alert 2 — Decider:**
> Decision: ESCALATED TO HUMAN
> Confidence: `0.327` — below threshold after reasoning.

**Alert 3 — Reflexion Loop:**
> Reflexion Loop escalated to human 🔴
> Critique score after 2 passes: `0.55`

### Competitive Intel Agent output
```json
{
  "scan_date": "2026-06-01",
  "domain": "AI-powered product management tools",
  "signals": [...],
  "orchestrator_injection": "Two competitors launched AI-native roadmap features this week..."
}
```

---

## Tech Stack Used Today

| Tool | Purpose |
|------|---------|
| n8n (self-hosted) | Daily cron schedule, workflow automation |
| Slack Incoming Webhooks | 3 alert types: go, no-go, escalation |
| ChromaDB | RAG storage for competitive intel + interview chunks |
| OpenAI API | Competitive intel signal extraction |
| FastAPI | `/run-pipeline` endpoint triggered by n8n |

---

## Files Created Today

```
ai-product-loop/
├── agents/
│   ├── competitive_intel.py     ← NEW — nightly competitor scan
│   ├── slack_notifier.py        ← NEW — reusable Slack alerts
│   ├── jira_notifier.py         ← NEW — auto ticket creation
│   ├── utils.py                 ← UPDATED — real token counts
│   ├── model_router.py          ← UPDATED — real token counts
│   ├── synthesis_agent.py       ← UPDATED — RAG store + Jira
│   ├── interview_agent.py       ← UPDATED — RAG store
│   ├── decider.py               ← UPDATED — Slack alert
│   ├── critic.py                ← UPDATED — Slack escalation
│   └── orchestrator.py          ← UPDATED — RAG + competitive intel
├── memory/
│   └── rag_retriever.py         ← UPDATED — source parameter added
└── notes/
    └── day11.md                 ← This file
```

---

## .env Variables Used Today

```
OPENAI_API_KEY=your_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/url/here
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=your_token_here
JIRA_PROJECT_KEY=AIPM
```

---

## VP Problems Addressed Today

| Problem | Component |
|---------|-----------|
| 1 — AI pilots to real business impact | Business Impact Translator posts revenue memos to Slack |
| 4 — Data quality and feedback loops | RAG memory now stores every interview chunk and decision |
| 9 — Cost explosion | Real token counts in cost tracker — dashboard shows accurate numbers |
| 11 — Build vs buy vs partner | Competitive Intel Agent shows build decision in live action |

---

## What's Next — Day 12

**Agent Security Layer + Calibration Analysis Agent + Integration Test**

- `agents/security_layer.py` — prompt injection detection, PII filter on inputs, output validation before actions are committed, security event logger
- `agents/calibration_agent.py` — reviews accumulated audit trail, recalibrates confidence thresholds
- `test_report.md` — full end-to-end integration test across all 4 stages

This closes VP Problems 7 (Shadow AI) and 8 (Prompt injection, agentic security) — the most distinctive day in the project.
