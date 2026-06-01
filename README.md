# AI Product Intelligence Loop

> A living, self-improving multi-agent AI system that manages the full intelligence cycle of an AI product — from user pain discovery through post-launch model monitoring.

Every architectural decision is documented. Every threshold is justified. The system closes the feedback loop that most AI product teams leave open.

---

## What this system does

Most AI product teams operate in a straight line:

```
User research → Build feature → Ship → Hope it works
```

This system closes the loop:

```
Discover user pain → Evaluate AI quality → Make documented decision → Learn from outcomes → repeat
```

The result: every future decision is informed by every past decision. The system gets smarter over time.

---

## The 4-stage pipeline

### Stage 01 — Discover
An AI agent conducts async user interviews and generates contextual follow-up questions. A Synthesis Agent reads all transcripts, extracts the top pain themes, scores them by frequency and severity, and outputs a structured opportunity map. Pain themes are stored in ChromaDB so every future agent can retrieve them.

### Stage 02 — Evaluate
Three parallel evaluation tracks run before any feature decision is made:
- **Hallucination Eval Agent** — scores faithfulness and factuality separately. These are two different failure modes with different fixes.
- **Confidence Calibration Agent** — measures the gap between how confident the AI says it is and how accurate it actually is. Uses Brier score.
- **Responsible AI Governance Module** — classifies features under EU AI Act risk tiers, scrubs PII, detects bias in synthesis output.

### Stage 03 — Decide
- **Orchestrator Agent** — aggregates all signals into one confidence score, retrieves relevant past decisions from RAG memory, injects competitive intelligence, and routes to the Decider or escalates to a human.
- **Decider Agent** — produces a documented GO / NO_GO / CONDITIONAL_GO with a full reasoning chain.
- **Reflexion Loop (Critic Agent)** — reviews the Decider's reasoning. If critique score < 0.7, sends back for revision. After 2 failed passes, escalates to human and fires a Slack alert.
- **Agent Security Layer** — blocks prompt injection attempts, redacts PII from inputs, validates output schema before any action is committed.

### Stage 04 — Learn
- **ChromaDB** — stores every interview transcript and past decision as vector embeddings. Every agent retrieves relevant context before acting.
- **Audit Trail** — logs every decision with input signals, reasoning chain, confidence score, escalation flag, model used, and tokens consumed.
- **Calibration Analysis Agent** — reviews the audit trail, calculates Brier score, recommends threshold adjustments.
- **Business Impact Translator** — maps metric movements to revenue estimates and auto-posts executive memos to Slack.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI PRODUCT INTELLIGENCE LOOP                      │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│  01 DISCOVER │ 02 EVALUATE  │  03 DECIDE   │      04 LEARN         │
│              │              │              │                        │
│  Interview   │ Hallucination│ Orchestrator │  ChromaDB             │
│  Agent       │ Eval Agent   │ Agent        │  RAG Memory           │
│              │              │              │                        │
│  Synthesis   │ Confidence   │ Decider      │  Audit Trail          │
│  Agent       │ Calibration  │ Agent        │                        │
│              │              │              │  Calibration          │
│              │ Governance   │ Reflexion    │  Agent                │
│              │ Module       │ Loop         │                        │
│              │              │              │  Business Impact      │
│              │ Prompt A/B   │ Security     │  Translator           │
│              │ Eval         │ Layer        │                        │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
         │                                               │
         └──────────── feedback loop ────────────────────┘

Automation: n8n daily cron → FastAPI → all 4 stages → Slack alerts
```

---

## Tech stack

| Tool | Purpose |
|------|---------|
| Python | All agents, pipeline logic, backend |
| OpenAI API (gpt-4o-mini / gpt-4o) | Powers all 9 agents |
| ChromaDB | Local vector database — RAG memory |
| FastAPI | Backend API server |
| React + Recharts | Dashboard frontend |
| n8n (self-hosted) | Daily cron automation |
| Slack | Alerts and human escalation |

**Model routing:** gpt-4o-mini for all agents by default. Orchestrator, Decider, and Critic upgrade to gpt-4o only when aggregated confidence drops below 0.75. This cuts inference costs by ~90% while preserving quality on high-stakes decisions.

**Total cost to run:** ~$0.003 per full pipeline run.

---

## Project structure

```
ai-product-loop/
├── agents/
│   ├── interview_agent.py       # Async user interviews
│   ├── synthesis_agent.py       # Pain theme extraction
│   ├── eval_agent.py            # Hallucination evaluation
│   ├── confidence.py            # Brier score calibration
│   ├── governance.py            # EU AI Act + PII + bias
│   ├── persona_agent.py         # Synthetic user simulation
│   ├── orchestrator.py          # Signal aggregation + routing
│   ├── decider.py               # GO/NO_GO recommendation
│   ├── critic.py                # Reflexion loop
│   ├── security_layer.py        # Prompt injection + output validation
│   ├── calibration_agent.py     # Threshold recalibration
│   ├── competitive_intel.py     # Nightly competitor scan
│   ├── impact_translator.py     # Revenue impact + exec memo
│   ├── prompt_ab.py             # Prompt version control
│   ├── model_router.py          # Cost-aware model routing
│   ├── cost_tracker.py          # Token + cost logging
│   ├── slack_notifier.py        # Slack alerts
│   ├── jira_notifier.py         # Auto ticket creation
│   └── prompts.py               # All system prompts
├── memory/
│   ├── chroma_store.py          # ChromaDB write layer
│   ├── rag_retriever.py         # Semantic retrieval
│   └── audit_logger.py          # Decision audit trail
├── backend/
│   ├── main.py                  # FastAPI app
│   └── routes.py                # All API endpoints
├── frontend/
│   └── src/
│       └── App.jsx              # React dashboard
├── prompts/
│   └── versions/                # Versioned prompt files
├── notes/                       # Day-by-day build notes
├── limitations.md               # Known limitations + reversal conditions
├── test_report.md               # Integration test results
└── .env.example                 # Environment variables template
```

---

## Getting started

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key
- Slack webhook URL (optional — alerts run in dry-run mode without it)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/saurabhsmahajan/ai-product-loop.git
cd ai-product-loop

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Install Python dependencies
pip install openai python-dotenv fastapi uvicorn chromadb requests

# 4. Copy environment variables
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 5. Start the FastAPI backend
uvicorn backend.main:app --reload

# 6. Run the full pipeline
curl -X POST http://localhost:8000/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"feature_hypothesis": "Your feature idea here"}'
```

### Dashboard setup

```bash
cd frontend
npm install
npm run dev
# Open localhost:5173
```

### n8n automation (optional)

```bash
npm install -g n8n
n8n start
# Open localhost:5678 and import the workflow
```

---

## API endpoints

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/run-pipeline` | POST | Triggers all 4 stages end-to-end |
| `/discover` | POST | Runs synthesis on existing transcripts |
| `/evaluate` | POST | Runs persona simulation + governance |
| `/decide` | POST | Runs orchestrator + decider + reflexion |
| `/learn` | POST | Stores decision in ChromaDB + audit trail |
| `/cost-report` | GET | Full cost breakdown by agent and model |
| `/audit-trail` | GET | Full decision history with outcomes |
| `/security-report` | GET | Security events log |
| `/calibrate` | POST | Runs calibration analysis on audit trail |
| `/update-outcome` | POST | Marks a decision as correct or incorrect |

---

## Environment variables

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/url/here
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=your_token_here
JIRA_PROJECT_KEY=AIPM
```

Only `OPENAI_API_KEY` is required. Everything else has a dry-run fallback.

---

## Key design decisions

**Why hallucination eval is weighted at 30%**
Hallucination is the one failure mode that is invisible until it reaches the user. A governance flag is recoverable. A hallucinated fact that ships is not. It gets more weight than other signals because the cost of getting it wrong is asymmetric.

**Why the Reflexion Loop has exactly 2 passes**
One pass is not enough to catch genuine reasoning gaps. Three passes adds latency and cost with diminishing returns. Two passes catches the majority of weak reasoning while keeping the pipeline fast enough to run daily.

**Why gpt-4o-mini is the default with selective upgrade**
The cheap model handles 90%+ of pipeline runs correctly. Upgrading to gpt-4o on every call would cost 15x more with marginal quality improvement on routine decisions. The upgrade triggers only when the system's own confidence signals that more capability is needed.

**Why competitive intel is cut first under scope pressure**
A PM can do a manual competitor check in 10 minutes. Every other component provides automation that genuinely cannot be replicated manually at scale. Competitive intel is the one component where human effort is a viable substitute.

**Why ChromaDB over a managed vector DB**
Local ChromaDB is free, runs without network calls, and is fast enough for the volume of decisions a PM team generates. The switch to a managed service (Pinecone, Weaviate) is a one-file change when the team scales.

---

## Known limitations

See [`limitations.md`](./limitations.md) for the full list with reversal conditions.

The short version:
- Calibration agent needs 5+ resolved outcomes to make meaningful recommendations
- Competitive intel uses LLM knowledge, not live web search
- React dashboard uses mock data — FastAPI wiring is production-ready but not connected
- Security layer uses regex patterns, not an LLM classifier

---

## VP problems this system addresses

| Problem | Component |
|---------|-----------|
| AI pilots → real business impact | Business Impact Translator auto-generates revenue memos |
| Proving ROI beyond vanity metrics | Cost-per-decision dashboard + audit trail |
| Choosing the right AI use cases | Orchestrator go/no-go with documented reasoning |
| Data quality and feedback loops | RAG memory compounds with every decision |
| Measuring AI quality reliably | Hallucination eval + confidence calibration + prompt A/B |
| AI governance and risk | EU AI Act classifier + PII scrubber + bias detector |
| Shadow AI and uncontrolled usage | Security layer is the governed alternative |
| Prompt injection and agentic security | Input sanitisation + output validation + security log |
| Cost explosion and unit economics | Model routing + cost tracker — ~$0.003 per run |
| Human trust and adoption | Confidence calibration + human escalation threshold |

---

## A note on how this was built

The Python code in this project was written with Claude (Anthropic). Every architectural decision — agent design, confidence thresholds, routing policy, memory strategy, security patterns — was made by the author.

This distinction matters. In 2026, writing code is table stakes. The scarce skill is knowing what to build, why to build it that way, and what to do when it breaks. This project documents that thinking in the decision records, the limitations file, and the 18-post blog series on [arcaence.com](https://arcaence.com).

---

## Blog series

18 posts documenting every decision made while building this system — technical depth + management thinking for each component.

Follow the series on [arcaence.com](https://arcaence.com) and [LinkedIn](https://linkedin.com/in/saurabhsmahajan).

---

## License

MIT — use it, fork it, build on it.

If you use this in your work, a mention or star on GitHub is appreciated but not required.
