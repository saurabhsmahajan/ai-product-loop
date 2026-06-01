# Day 13 Notes — Prompt Version Control Hardening + System Hardening
**AI Product Intelligence Loop | VP / Director AI PM Career Project**
Date: June 5, 2026 | Status: Complete ✅

---

## What You Built Today

### Deliverable 1 — `agents/prompt_ab.py` (hardened)
Replaced the Day 5 hardcoded dict-based version registry with a file-based system that survives process restarts.

**5 changes from Day 5 version:**

| What changed | Day 5 | Day 13 |
|-------------|-------|--------|
| Prompt storage | Hardcoded Python dict | `.txt` files in `prompts/versions/` |
| Version registry | In-memory only | `prompts/versions/ticket_summariser_registry.json` |
| Active version | Hardcoded `active: True` flag | Persisted to registry file |
| Promotion | Updates dict in memory | `promote_version()` — logs reason + timestamp |
| Rollback | Not possible | `rollback()` — reverts to previous version in one call |

**New functions:**
- `save_version(prompt_name, version, text)` — saves prompt as `.txt` file
- `load_version(prompt_name, version)` — reads prompt from file
- `get_registry(prompt_name)` — loads version registry
- `promote_version(prompt_name, version, reason)` — sets active, logs event
- `rollback(prompt_name, reason)` — reverts to previous_version
- `get_active_prompt(prompt_name)` — returns (version_tag, prompt_text) for current active
- `seed_versions()` — one-time migration: creates v1, v2, v3 files from hardcoded prompts

**Version history logged to:** `data/prompt_version_history.json`

### Deliverable 2 — `prompts/versions/` folder
Three prompt versions saved as files:

| File | Description |
|------|-------------|
| `ticket_summariser_v1.txt` | Basic summariser — concise and accurate |
| `ticket_summariser_v2.txt` | Strict factual — only explicit facts, no inference |
| `ticket_summariser_v3.txt` | Structured 3-sentence with action item |
| `ticket_summariser_registry.json` | Active version + version list |

### Deliverable 3 — `limitations.md`
8 known limitations, each documented with:
- What the limitation is
- Impact on the system
- Current workaround
- Reversal condition (what it takes to fix properly)

Also includes:
- **Component cut first under scope pressure** — Competitive Intel Agent (reasoning explained)
- **How the system scales with a 5-person AI PM team** — what changes vs what stays the same

### Deliverable 4 — `frontend/src/App.jsx` (updated)
Two additions to the Learn tab:

**Third metric card added:**
- "Cost reduction ~90% vs always using gpt-4o"

**Collapsible Model Routing Policy panel:**
- Shows every agent, its assigned model, and the routing reason
- Agents eligible for upgrade (orchestrator, decider, critic) shown in orange
- Toggle button — hidden by default, expands on click
- Explains the routing rule: upgrade to gpt-4o only when confidence < 0.75

---

## Concepts You Learned

### Prompt engineering as an engineering discipline
Prompts are code. They need version control, testing, promotion logic, and rollback — the same as any production software. The Day 13 system treats prompts exactly like code: versioned files, a registry, automated eval before promotion, and a documented history of every change. This is what "prompt ops" looks like in practice.

### Why rollback matters in agentic systems
In a traditional app, a bad deploy can be rolled back in seconds. In an agentic system, a bad prompt can produce incorrect decisions that get stored in the audit trail, fed back into RAG memory, and influence future decisions before anyone notices. Rollback needs to be instant and require zero manual file editing — that's what `rollback()` provides.

### Limitations documentation as VP-level signal
Most candidates present their project as perfect. VP-level candidates document what doesn't work, why it doesn't work, and exactly what it would take to fix it. The `limitations.md` file demonstrates that you understand the system deeply enough to know where it breaks — and that you've already thought through the path to production.

### Model routing as an architectural decision on principle
The routing policy isn't "use the cheap model to save money." It's a deliberate architectural decision: use the minimum model capability required for the task, upgrade only when the stakes are high enough to justify it. The routing policy explainer panel makes this reasoning visible to anyone reading the dashboard.

---

## Commands You Ran Today

```powershell
# Seed prompt versions — creates prompts/versions/ folder and all files
python agents/prompt_ab.py --seed

# Check active version
python agents/prompt_ab.py --active

# Manually promote v3 to test rollback
python -c "from agents.prompt_ab import promote_version; promote_version('ticket_summariser', 'v3', 'Test promotion to enable rollback test')"

# Test rollback
python agents/prompt_ab.py --rollback

# Confirm rolled back to v2
python agents/prompt_ab.py --active

# Start React dashboard to check routing policy panel
cd frontend
npm run dev

# Push to GitHub
git add agents/prompt_ab.py limitations.md frontend/src/App.jsx prompts/versions/ data/prompt_version_history.json
git commit -m "Day 13 complete — prompt version control hardened, rollback tested, limitations doc, routing policy panel"
git push origin master
```

---

## Test Results

```
Seed:
  [PromptVC] Saved ticket_summariser v1 → prompts/versions\ticket_summariser_v1.txt
  [PromptVC] Saved ticket_summariser v2 → prompts/versions\ticket_summariser_v2.txt
  [PromptVC] Saved ticket_summariser v3 → prompts/versions\ticket_summariser_v3.txt
  [PromptVC] ✅ Promoted ticket_summariser → v2 (was: None)

Active check:
  Active version: v2

Promote v3:
  [PromptVC] ✅ Promoted ticket_summariser → v3 (was: v2)

Rollback:
  [PromptVC] 🔄 Rolled back ticket_summariser: v3 → v2

Active check after rollback:
  Active version: v2 ✅
```

---

## Files Created / Updated Today

```
ai-product-loop/
├── agents/
│   └── prompt_ab.py             ← UPDATED — file-based versioning + rollback
├── prompts/
│   └── versions/
│       ├── ticket_summariser_v1.txt         ← NEW
│       ├── ticket_summariser_v2.txt         ← NEW
│       ├── ticket_summariser_v3.txt         ← NEW
│       └── ticket_summariser_registry.json  ← NEW
├── frontend/
│   └── src/
│       └── App.jsx              ← UPDATED — routing policy panel added
├── data/
│   └── prompt_version_history.json  ← NEW (auto-generated)
├── limitations.md               ← NEW — 8 limitations with reversal conditions
└── notes/
    └── day13.md                 ← This file
```

---

## Known Limitations Documented Today

| # | Limitation | Severity |
|---|-----------|----------|
| 1 | Calibration needs resolved outcomes — stays INSUFFICIENT_DATA until 5+ decisions resolved | Medium |
| 2 | Competitive intel uses LLM knowledge, not live web search | Medium |
| 3 | Interview agent is terminal-only — no async user responses | Medium |
| 4 | Token cost logging is 0 in audit trail entries | Low |
| 5 | Prompt version registry — Day 13 fixes this | Resolved ✅ |
| 6 | Security layer uses regex, not LLM classifier | Low |
| 7 | React dashboard uses mock data, not live FastAPI calls | Low |
| 8 | n8n workflow fails silently if FastAPI not running | Low |

---

## VP Problems Status After Day 13

All 12 VP Problems now addressed:

| Problems | Coverage |
|----------|----------|
| 1, 2, 3 | Full — pipeline, ROI, use case selection |
| 4, 5, 6 | Full — RAG, eval suite, governance module |
| 7, 8 | Full — Agent Security Layer (Day 12) |
| 9, 10 | Full — model routing, confidence calibration |
| 11, 12 | Partial — strategy doc + competitive intel agent |

---

## What's Next — Day 14 (Final Day)

**Written Strategy Document + Demo Prep**

- `strategy_doc.md` — every architectural decision with trade-off and reversal condition
- `demo_script.md` — 10-minute interview walkthrough script
- Final resume bullet — polished for CV
- `day14.md` notes

**After Day 14 the project is complete and interview-ready.**
