# Day 09 — FastAPI Backend
**Date:** June 2, 2026
**Stage:** Backend Infrastructure
**Status:** ✅ Complete

---

## 1. What We Built
- `backend/main.py` — FastAPI application setup with CORS middleware, app metadata, and router registration
- `backend/routes.py` — all 8 REST endpoints exposing every pipeline stage and utility function as an independently callable API

**Files created:**
```
AI-PRODUCT-LOOP/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── routes.py
```

**Endpoints live at http://127.0.0.1:8000:**

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | /discover | Runs Stage 01 — Synthesis Agent on existing transcripts |
| POST | /evaluate | Runs Stage 02 — Persona simulation, eval, governance |
| POST | /decide | Runs Stage 03 — Orchestrator, Decider, Reflexion Loop |
| POST | /learn | Runs Stage 04 — ChromaDB store + audit trail log |
| POST | /run-pipeline | Triggers all 4 stages end-to-end with one call |
| GET | /cost-report | Returns full cost breakdown by agent and model |
| GET | /audit-trail | Returns full audit log with summary |
| POST | /update-outcome | Updates outcome of a logged decision post-launch |

**Full pipeline run via API — key results:**
- Run ID: RUN_20260529_125552
- Stage 01: 5 pain themes, top opportunity — automate ticket prioritisation and summarisation
- Stage 02: 3 blockers (Enterprise Buyer, IT/Security, Legal), avg reaction 6.67, trust score 3/10, OVERCONFIDENT
- Stage 03: Aggregated confidence 0.323, HUMAN_ESCALATION, CONDITIONAL_GO after 2 Reflexion passes
- Stage 04: Decision logged — LOG_20260529_125656, outcome PENDING
- HTTP response: 200 — clean, no errors, all 4 stages in one call
- Total cost: $0.002878

---

## 2. Why We Built It
Before Day 9, the intelligence loop was a collection of Python scripts run manually in a terminal — one at a time, in the right order, by someone who knew the project. That is not a system. It is a prototype. FastAPI transforms it into a unified service: any tool, any interface, any automation can now trigger the full pipeline with a single HTTP POST. The React dashboard on Day 10 calls these endpoints. The n8n automation on Day 11 calls `/run-pipeline` on a daily cron schedule. The Slack bot receives the response and posts alerts. None of that is possible without a backend. Day 9 is the day the project becomes a real system.

---

## 3. Code and Logic Explained

**FastAPI — why it is the right choice for this project**

FastAPI is a Python web framework that turns Python functions into REST API endpoints with minimal boilerplate. It auto-generates an interactive Swagger UI at `/docs` — so every endpoint is immediately testable from a browser without writing any client code. It uses Pydantic for request validation — if a required field is missing from a request body, FastAPI returns a clear 422 error with the exact field that failed. It is async-native — endpoints can run without blocking, which matters when multi-agent pipeline runs take 30–60 seconds.

**CORS middleware — why it is needed**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

The React dashboard runs on a different port (3000) than the FastAPI server (8000). Without CORS middleware, the browser blocks requests from one port to another as a security measure. `allow_origins=["*"]` permits all origins during development. In production, this would be restricted to the specific dashboard domain.

**Request model — Pydantic validation**

```python
class FeatureRequest(BaseModel):
    feature_hypothesis: str
    run_id: str = None
```

Every POST endpoint accepts a `FeatureRequest` body. Pydantic validates the request automatically — if `feature_hypothesis` is missing, FastAPI returns a 422 before the endpoint function even runs. The `run_id` field defaults to None and is generated inside `/run-pipeline` if not provided, ensuring every pipeline run has a unique traceable identifier.

**How `/run-pipeline` orchestrates all 4 stages**

```python
@router.post("/run-pipeline")
async def run_pipeline(request: FeatureRequest):
    run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Stage 01 — Discover
    discover_result = run_synthesis()

    # Stage 02 — Evaluate
    persona_result = simulate_personas(request.feature_hypothesis)
    confidence_result = run_confidence_calibration(ai_outputs, eval_report)

    # Stage 03 — Decide
    orch_result = run_orchestrator(request.feature_hypothesis)
    dec_result  = run_decider(orch_result, request.feature_hypothesis)
    ref_result  = run_reflexion_loop(dec_result, request.feature_hypothesis, orch_result)

    # Stage 04 — Learn
    store_decision(run_id, ...)
    log_entry = log_decision(run_id, ...)
```

Each stage runs sequentially — the output of Stage 01 informs Stage 02, Stage 02 informs Stage 03, Stage 03 is stored in Stage 04. The entire sequence runs inside one async function and returns a single JSON response containing every stage's output. One HTTP call, one response, complete audit trail.

**Why imports are inside endpoint functions, not at module level**

```python
@router.post("/discover")
async def discover(request: FeatureRequest):
    from agents.synthesis_agent import run_synthesis   # import inside function
    result = run_synthesis()
```

Importing agents at the top of `routes.py` would load all 9 agent modules when the server starts — including ChromaDB, which downloads its embedding model on first import. This would make server startup slow and error-prone. Importing inside each endpoint function means the import only happens when that endpoint is called — lazy loading that keeps startup fast and isolates import errors to the specific endpoint that triggered them.

**The `/run-pipeline` response structure**

The response returns a nested JSON object with five top-level fields:

```json
{
  "status": "success",
  "run_id": "RUN_20260529_125552",
  "decision": "CONDITIONAL_GO",
  "confidence": 0.6,
  "escalated": true,
  "cost": 0.002878,
  "stages": {
    "discover": {...},
    "evaluate": {...},
    "decide": {...},
    "learn": {...}
  }
}
```

The top-level fields give an immediate summary — decision, confidence, escalation flag, cost — without requiring the client to parse nested data. The `stages` object contains the full output of every agent for complete auditability. The React dashboard on Day 10 reads the top-level fields for the summary panels and drills into `stages` for the detail views.

---

## 4. Issues We Faced

### Issue 1 — `backend` folder not recognised as a Python module
**Problem:** Running `uvicorn backend.main:app` throws a `ModuleNotFoundError` because Python does not treat the `backend/` folder as a package without an `__init__.py` file.
**Solution:** Created `backend/__init__.py` using `ni backend/__init__.py` in PowerShell. The `ni` command is the PowerShell equivalent of `touch` — it creates an empty file. All three project subfolders (`agents/`, `memory/`, `backend/`) now have `__init__.py` files and are recognised as Python packages.

### Issue 2 — PowerShell does not support the `echo.` command for creating empty files
**Problem:** The standard Unix command `echo. > filename` to create an empty file is not recognised in PowerShell, throwing a `CommandNotFoundException`.
**Solution:** Use `ni filename` (short for `New-Item`) in PowerShell for all empty file creation going forward. This issue has appeared on Days 7, 9 — documented once here as the definitive fix for the project.

### Issue 3 — `/run-pipeline` confidence in response (0.6) differs from Orchestrator aggregated confidence (0.323)
**Problem:** The top-level `confidence` field in the `/run-pipeline` response shows 0.6, but the Orchestrator's `aggregated_confidence_score` shows 0.323. A reader of the response might assume these are the same metric.
**Solution:** These are two different confidence scores measuring different things — not a bug. The Orchestrator's 0.323 is the weighted aggregation of all Stage 02 signals (hallucination, trust, persona, governance). The final 0.6 is the Decider's confidence score after the Reflexion Loop revised the reasoning — the Decider judged that a CONDITIONAL_GO with specific conditions was 60% confident despite the pipeline signals being weak. Both are correct and both are returned in the full response. The React dashboard Day 10 will label these separately: "Pipeline signal confidence" and "Decision confidence."

---

## 5. VP / Director Decisions Made

### Decision 1 — One `/run-pipeline` endpoint running all stages vs separate endpoints only
**Situation:** The API could expose only individual stage endpoints and require the caller to chain them, or include a convenience `/run-pipeline` endpoint that runs all 4 stages end-to-end.
**Options considered:** Individual stages only — maximum flexibility, caller controls the sequence. Combined `/run-pipeline` — convenience, less flexible, hides stage boundaries.
**Decision taken:** Both — individual stage endpoints AND `/run-pipeline`.
**Reasoning:** Individual endpoints are needed for the React dashboard which will display each stage's output as it becomes available. The `/run-pipeline` endpoint is needed for n8n automation which needs to trigger the full loop on a cron schedule without managing stage sequencing. Having both means the system supports both use cases without compromising either. The individual endpoints also make testing and debugging easier — a failing Stage 03 can be retried independently without rerunning Stages 01 and 02.

### Decision 2 — Lazy imports inside endpoint functions vs module-level imports
**Situation:** Agent imports can be placed at the top of `routes.py` (module-level, loaded once at server start) or inside each endpoint function (lazy, loaded on first call).
**Options considered:** Module-level — faster per-call execution, slower startup, all errors surface at startup. Lazy imports — slower per-call on first execution, fast startup, errors isolated per endpoint.
**Decision taken:** Lazy imports inside endpoint functions.
**Reasoning:** ChromaDB loads a 79MB embedding model on first import. Loading this at server startup would add 10–15 seconds to the startup time and would fail the server if ChromaDB is not initialised yet. Lazy imports mean the server starts in under 1 second and each agent is loaded only when its endpoint is first called. The performance difference on subsequent calls is negligible — Python caches imported modules after the first load.

### Decision 3 — `allow_origins=["*"]` CORS vs restricted origins
**Situation:** CORS configuration can allow all origins (wildcard) or restrict to specific allowed domains.
**Options considered:** Wildcard `*` — maximum flexibility during development, security risk in production. Specific origins — secure, requires knowing the frontend URL in advance.
**Decision taken:** Wildcard during development, with a documented production requirement to restrict.
**Reasoning:** During a 14-day build, the React dashboard port may change and other tools (Postman, n8n, browser) need unrestricted access for testing. Restricting origins during development adds friction with no security benefit since the server is running locally. The strategy document on Day 14 will document the production requirement: restrict `allow_origins` to the specific dashboard domain before any deployment outside localhost.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| REST API | A web interface that exposes functionality via HTTP endpoints — clients send requests, the server processes them and returns JSON responses |
| FastAPI | A Python framework that turns annotated Python functions into REST endpoints with automatic validation and documentation |
| Endpoint | A specific URL path that triggers a specific function — `/run-pipeline` triggers the full 4-stage pipeline |
| POST vs GET | POST sends data to the server to trigger an action; GET retrieves data without changing state |
| Pydantic | A Python library that validates request data against a schema — missing or wrong-type fields return a clear error before the function runs |
| CORS | Cross-Origin Resource Sharing — a browser security policy that blocks requests between different ports or domains unless explicitly allowed |
| Swagger UI | Auto-generated interactive documentation at `/docs` — every endpoint is testable from a browser without writing any client code |
| HTTP 200 | The response code for a successful request — the server processed the request and returned a valid response |
| HTTP 422 | The response code for a validation error — the request body was missing a required field or contained a wrong data type |
| Lazy import | Importing a module inside a function rather than at the top of the file — the import only happens when the function is called, keeping startup fast |
| Async endpoint | A FastAPI endpoint defined with `async def` — it can handle multiple concurrent requests without blocking the server while waiting for long operations |

---

## 7. How This Connects to the Bigger System
The FastAPI backend is the integration layer that makes every component built in Days 1–8 accessible to the outside world. The React dashboard on Day 10 calls `/run-pipeline` and displays the response in real time — the dashboard has no direct access to Python code, only to these endpoints. The n8n automation on Day 11 sends a POST to `/run-pipeline` on a daily cron schedule, completely automating the intelligence loop without any manual intervention. The Slack bot receives the response and posts the decision and cost to a channel. The `/update-outcome` endpoint closes the feedback loop post-launch — when the drift monitor detects model degradation, it calls this endpoint to mark the original decision as INCORRECT, feeding the Calibration Analysis Agent on Day 12. Everything from Day 10 onwards builds on top of the API established today.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| Individual stages + `/run-pipeline` | Individual only, combined only, both | Dashboard needs individual stages; automation needs combined endpoint; both serve different valid use cases | If the system is simplified to automation-only — would remove individual stage endpoints to reduce API surface area |
| Lazy imports inside endpoints | Module-level, lazy, hybrid | Fast server startup; ChromaDB embedding model load is deferred until first call; import errors isolated per endpoint | If per-call latency on first execution becomes unacceptable in production — would pre-warm endpoints on startup |
| Wildcard CORS in development | Wildcard, restricted, disabled | Zero friction during 14-day build; multiple tools need unrestricted access; no security risk on localhost | Must be restricted to specific origins before any production deployment — non-negotiable |

---

## 9. Resume Bullet
> Built a FastAPI backend exposing the full multi-agent AI pipeline as 8 REST endpoints — individual stage endpoints for granular control and a `/run-pipeline` endpoint that triggers all 4 stages end-to-end in a single HTTP call, returning a structured JSON response with decision verdict, confidence score, escalation flag, and cost — enabling the React dashboard, n8n automation, and Slack alerting to operate as independent clients on top of a unified API.

---

## 10. LinkedIn Hook
> I went from 9 Python scripts to a production REST API in one day. One HTTP call now triggers the full AI product intelligence loop — user discovery, hallucination eval, go/no-go decision, vector memory update — and returns a structured JSON response with the decision, confidence score, and cost. Here is exactly how the backend is wired.

---

## 11. Honest Rating
**Difficulty:** 5/10
**Confidence after today:** 9/10
**What clicked:** Seeing the Swagger UI load at `/docs` with all 8 endpoints listed — and then hitting Execute on `/run-pipeline` and watching the full pipeline run through the API in real time. The system stopped feeling like a coding exercise the moment it became an API. That is the moment it became something a team could build on.
**What still feels unclear:** How the async processing will hold up when the React dashboard makes multiple concurrent requests — for example, if the user triggers `/run-pipeline` while `/audit-trail` is still loading. FastAPI handles concurrency natively but the agent functions are all synchronous Python — a long-running pipeline run will block its worker thread. Proper async agent execution is a Day 13 hardening task.

---

## 12. Next Course of Action
**Tomorrow — Day 10:** React Dashboard + Business Impact Translator
Build the React dashboard with panels for user pain themes, eval report card, go/no-go decision history, cost-per-decision chart, calibration trend, and live drift alerts — all calling the FastAPI endpoints built today. Build the Business Impact Translator Agent that maps metric drops to revenue-impact estimates and auto-generates an executive memo posted to Slack.
