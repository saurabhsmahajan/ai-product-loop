# OWASP Top 10 for Agentic Applications 2026 — Pipeline Assessment
**Framework:** OWASP ASI Top 10 for Agentic Applications 2026 (December 2025)
**Source:** genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026
**Version:** 1.0
**Owner:** Saurabh Mahajan (saurabh@arcaence.com)
**Last updated:** June 2026
**Repository:** github.com/saurabhsmahajan/ai-product-loop

---

## Purpose

This document maps the AI Product Intelligence Loop — a 4-stage, 11-agent
agentic pipeline — against the OWASP Top 10 for Agentic Applications 2026.
For each risk, it documents the current implementation status, specific
controls in place, honest gaps, and planned remediation.

The OWASP Agentic Top 10 complements the existing GRC framework:

| Framework | What it covers |
|---|---|
| NIST AI RMF | Organisational AI risk management — GOVERN/MAP/MEASURE/MANAGE |
| EU AI Act | Regulatory compliance — transparency, human oversight, data governance |
| ISO/IEC 42001 | AI management system — policy, lifecycle, continual improvement |
| AIGP BOK v2.1 | AI governance practitioner — responsible deployment and monitoring |
| **OWASP ASI Top 10** | **Agentic-specific security — attacks, exploits, emergent failure** |

The OWASP framework adds what the others cover incompletely: tool use risks,
multi-step reasoning exploits, inter-agent trust vulnerabilities, and
emergent rogue behaviour that exists only in agentic architectures.

---

## System Context

The AI Product Intelligence Loop is a multi-agent system that processes
feature hypotheses through four stages:

```
Feature hypothesis input
        │
        ▼
┌─────────────────┐
│  01 DISCOVER    │  synthesis_agent — extracts pain themes from ChromaDB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  02 EVALUATE    │  persona_agent, hallucination_eval_agent,
│                 │  confidence_calibration_agent, governance_agent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  03 DECIDE      │  orchestrator_agent → decider_agent → reflexion_agent
│                 │  security_agent (wraps all inputs/outputs)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  04 LEARN       │  calibration_agent, business_impact_agent
│                 │  ChromaDB storage, audit trail logging
└─────────────────┘
```

**What makes this pipeline agentic (and therefore in scope for OWASP ASI):**
- Agents execute multi-step reasoning without constant human oversight
- Agents read from and write to a persistent vector store (ChromaDB)
- Agents call external services (OpenAI API, Slack, Jira)
- Agents communicate through structured JSON outputs consumed by downstream agents
- The Reflexion loop allows agents to critique and revise prior agent outputs

---

## Status Definitions

| Status | Meaning |
|---|---|
| **Implemented** | Active technical control in place — risk materially reduced |
| **Partial** | Control exists but does not fully address the risk |
| **Documented** | Risk acknowledged, managed via policy rather than code |
| **Gap** | No current control — remediation required |

---

## ASI01:2026 — Agent Goal Hijack

**Risk:** Attackers manipulate agent goals, plans, or decision paths through
direct or indirect instruction injection, causing agents to pursue unintended
or malicious objectives.

**Subtypes:**
- Direct goal manipulation — explicit override via prompt injection
- Indirect instruction injection — hidden instructions in documents or RAG content
- Recursive hijacking — modifications that propagate through reasoning chains
- Cross-context injection — instructions in one context affecting another

### Pipeline exposure

Your pipeline is exposed to this risk at two surfaces:
1. **Feature hypothesis input** — the primary user input that enters the
   Discover stage and flows through all 11 agents
2. **ChromaDB retrieval** — retrieved chunks may contain previously stored
   content that influences synthesis and evaluation agent reasoning

### Current controls

| Control | File | Coverage |
|---|---|---|
| Injection pattern scanner | `agents/security_layer.py` | Blocks known injection patterns at pipeline entry |
| Input sanitisation | `agents/security_layer.py` | Strips unsafe strings before any LLM call |
| Agent scope boundaries | `config/agent_manifest.yaml` | Declared permitted inputs per agent |
| PII scrubbing | `agents/governance.py` | Removes PII before LLM exposure |

**Status: Partial**

### Honest gap

The security layer uses regex-based pattern matching. It catches known
injection strings ("ignore previous instructions", "forget your system
prompt") but cannot detect semantic goal drift — where a carefully crafted
input gradually steers agent reasoning without triggering any pattern.
Indirect injection via ChromaDB retrieved content is not currently scanned.

### Remediation roadmap

```
Priority 1 (Medium): Add semantic intent classifier to security_layer.py
  — compare input intent against declared agent purpose in agent_manifest.yaml
  — flag divergence above threshold for human review

Priority 2 (Low): Scan ChromaDB retrieved chunks for injection patterns
  — apply security_layer.sanitise_input() to retrieved content before
    passing to synthesis_agent
```

---

## ASI02:2026 — Tool Misuse & Exploitation

**Risk:** Agents misuse or abuse tools through unsafe composition, recursion,
or excessive execution, causing harmful side effects despite having valid
permissions.

**Subtypes:**
- Recursive tool calls — loops causing resource exhaustion
- Unsafe tool composition — chaining tools in dangerous sequences
- Tool budget exhaustion — overwhelming systems with excessive invocations
- Cross-tool state leakage — information flowing unsafely between tool contexts

### Pipeline exposure

Your agents use three external tool categories:
1. **OpenAI API** — all LLM calls (gpt-4o-mini, gpt-4o)
2. **ChromaDB** — read (retrieval) and write (storage) operations
3. **Slack / Jira** — output dispatch agents

### Current controls

| Control | File | Coverage |
|---|---|---|
| Model routing with upgrade threshold | `agents/model_router.py` | Prevents inadvertent gpt-4o upgrade loops |
| Cost tracker | `agents/cost_tracker.py` | Monitors token spend per run |
| Agent scope boundaries | `config/agent_manifest.yaml` | Permitted outputs declared per agent |
| Performance baselines | `config/performance_baselines.yaml` | Cost per run warning threshold: $0.010 |

**Status: Partial**

### Honest gap

There is no hard limit on the number of LLM API calls per pipeline run.
The Reflexion loop has a 2-pass hard limit (good) but other agents have no
call budget. A runaway Orchestrator could make repeated gpt-4o calls
without triggering a halt. ChromaDB write operations have no rate limit or
validation that the content being stored is within scope.

### Remediation roadmap

```
Priority 1 (Medium): Add per-run API call budget in agents/cost_tracker.py
  — hard limit: max 20 LLM calls per pipeline run
  — halt pipeline and alert if limit reached before completion

Priority 2 (Low): Add ChromaDB write validation in memory/chroma_store.py
  — validate content type and size before storage
  — reject writes that exceed defined schema
```

---

## ASI03:2026 — Agent Identity & Privilege Abuse

**Risk:** Delegated authority, ambiguous agent identity, or trust assumptions
lead to unauthorised actions.

**Subtypes:**
- Agent impersonation — one agent masquerading as another with higher privileges
- Cross-agent trust abuse — exploiting implicit trust relationships
- Identity inheritance — unauthorised assumption of privileges through agent chains
- Role bypass — circumventing role-based access controls

### Pipeline exposure

Your pipeline passes JSON reports between agents as files on disk
(`data/orchestrator_report.json`, `data/decider_report.json`, etc.).
Any agent can read any report file — there is no authentication between agents.
The Orchestrator trusts the Governance report without verifying it was
produced by the Governance agent in the current run.

### Current controls

| Control | File | Coverage |
|---|---|---|
| Agent role boundaries | `config/agent_manifest.yaml` | Declared scope per agent — not runtime enforced |
| Run ID tracking | `memory/audit_logger.py` | Each run has a unique run_id |
| Output schema validation | `agents/security_layer.py` | Validates output structure before downstream use |
| Immutable audit log | `memory/audit_logger.py` | Records which agent produced which output |

**Status: Partial**

### Honest gap

Agent identity is declared in `agent_manifest.yaml` but not cryptographically
verified at runtime. There is no mechanism to confirm that the
`data/governance_report.json` consumed by `routes.py` was produced by
`agents/governance.py` in the current run rather than a stale file from a
previous run or an injected replacement. This is the most significant
identity risk in the current architecture.

### Remediation roadmap

```
Priority 1 (High): Add run_id validation to inter-agent file handoffs
  — each agent output file must contain the current run_id
  — consuming agent validates run_id matches before processing
  — implementation: add _verify_report_run_id() helper to routes.py

Priority 2 (Low): Add HMAC signature to agent outputs
  — each agent signs its output with a shared secret
  — downstream agents verify signature before consuming
```

---

## ASI04:2026 — Agentic Supply Chain Compromise

**Risk:** Compromise of external agents, tools, schemas, or prompts that
agents dynamically trust or import.

**Subtypes:**
- Schema manipulation — corrupting tool or API schemas agents rely on
- Description deception — misleading tool descriptions that trick agents
- Permission misrepresentation — false capability or permission declarations
- Registry poisoning — compromised agent or tool registries

### Pipeline exposure

Your pipeline has two supply chain dependencies:
1. **OpenAI API** — if OpenAI's API response format changes or is compromised,
   all agents calling `parse_json_response()` are affected
2. **ChromaDB embeddings** — embedding model changes affect retrieval quality
   across all agents using RAG context

### Current controls

| Control | File | Coverage |
|---|---|---|
| Model version registry | `config/model_registry.json` | Tracks model ID, version, deployment date |
| `parse_json_response()` | `agents/utils.py` | Validates JSON structure before agent use |
| Performance baselines | `config/performance_baselines.yaml` | Drift detection catches quality degradation |
| Output schema validation | `agents/security_layer.py` | Validates output structure |

**Status: Partial**

### Honest gap

`model_registry.json` records which model is used but does not verify it.
If OpenAI silently changes model behaviour (which has happened historically
with model updates under the same model ID), the pipeline would not detect it
until drift metrics triggered. There is no cryptographic verification of
model identity or response provenance.

### Remediation roadmap

```
Priority 1 (Medium): Add system prompt hash verification per run
  — current: system_prompt_hash stored in audit log
  — add: verify hash matches model_registry.json entry at run start
  — alert if mismatch detected

Priority 2 (Low): Add embedding model version to ChromaDB metadata
  — tag each stored chunk with embedding model version
  — alert if retrieval uses chunks from a different model version
```

---

## ASI05:2026 — Unexpected Code Execution

**Risk:** Agent-generated or agent-triggered code executes without sufficient
validation or isolation.

**Subtypes:**
- Unauthorised code execution — agents generating and running arbitrary code
- Shell command execution — direct system command invocation
- Eval usage — unsafe evaluation of dynamic expressions
- Command injection — malicious commands embedded in agent outputs

### Pipeline exposure

Your agents generate text outputs (JSON recommendations, executive memos,
Slack messages) — not executable code. This significantly reduces ASI05
exposure compared to code-generation agents.

The primary risk is Slack and Jira notification content: if an agent output
contains malicious content, it is dispatched to external systems without
content validation beyond schema checking.

### Current controls

| Control | File | Coverage |
|---|---|---|
| Output schema validation | `agents/security_layer.py` | Validates JSON structure and field types |
| No `eval()` usage | Codebase-wide | Confirmed — no dynamic code evaluation |
| No shell command calls | Codebase-wide | Confirmed — no `subprocess` or `os.system` in agent files |
| PII scrubbing before dispatch | `agents/governance.py` | Redacts PII before Slack/Jira dispatch |

**Status: Implemented** (for this pipeline's scope)

### Honest gap

Content dispatched to Slack via `agents/slack_notifier.py` and Jira via
`agents/jira_notifier.py` is not validated for malicious content beyond
schema structure. An injected payload that passes schema validation could
reach external systems. This is low risk for the current scope but would
matter in production with real external integrations.

### Remediation roadmap

```
Priority 1 (Low): Add content safety check before external dispatch
  — scan executive memo and Slack post content for injection patterns
  — apply security_layer.sanitise_input() before dispatch calls
```

---

## ASI06:2026 — Memory & Context Poisoning

**Risk:** Injection or leakage of agent memory or contextual state that
influences future reasoning or actions.

**Subtypes:**
- Long-term memory poisoning — corrupting persistent agent memory stores
- Context injection — malicious information inserted into agent context
- State manipulation — altering agent reasoning state across sessions
- Memory leakage — unintended exposure of sensitive memory content

### Pipeline exposure

ChromaDB is your persistent memory layer. Every decision stored in the
Learn stage influences future Discover and Decide stage context via RAG
retrieval. A poisoned ChromaDB embedding could influence all future pipeline
runs — this is the most persistent risk in your architecture.

### Current controls

| Control | File | Coverage |
|---|---|---|
| ChromaDB snapshot versioning | `memory/chroma_store.py` | Enables rollback to last clean snapshot |
| Drift detection | `config/performance_baselines.yaml` | Detects quality degradation across runs |
| Human approval gate | `agents/orchestrator.py` | No output stored without human-approved decision |
| PII redaction before storage | `agents/governance.py` | Prevents PII from entering ChromaDB |
| Immutable audit log | `memory/audit_logger.py` | Tracks what was stored, when, and from which run |

**Status: Partial**

### Honest gap

ChromaDB snapshot rollback exists but is manual — there is no automated
trigger that detects memory poisoning and initiates rollback. Drift detection
catches output quality degradation (a symptom) but not memory integrity
violations (the cause). There are no integrity checks on ChromaDB chunk
content at retrieval time — retrieved chunks are trusted implicitly.

### Remediation roadmap

```
Priority 1 (High): Add retrieval-time content validation
  — when synthesis_agent retrieves chunks, apply security_layer scan
  — flag chunks containing injection patterns before passing to LLM

Priority 2 (Medium): Add automated rollback trigger
  — if grounding_fail_rate exceeds critical threshold across 3 runs
  — automatically restore ChromaDB from last clean snapshot
  — log rollback event as SEV-1 in INCIDENT_RESPONSE.md process

Priority 3 (Low): Add ChromaDB chunk integrity hashing
  — store SHA-256 hash of each chunk at write time
  — verify hash at retrieval time — mismatch triggers alert
```

---

## ASI07:2026 — Insecure Inter-Agent Communication

**Risk:** Manipulation of messages exchanged between agents, planners, and
executors.

**Subtypes:**
- Agent-in-the-middle — interception and modification of agent messages
- Message injection — insertion of malicious instructions into agent communication
- Message spoofing — forging messages that appear to come from trusted agents

### Pipeline exposure

Your agents communicate through JSON files on disk
(`data/orchestrator_report.json`, `data/decider_report.json`, etc.).
These files are written by one agent and read by the next. They are stored
in the `data/` directory which is in `.gitignore` but is not access-controlled
at the OS level.

### Current controls

| Control | File | Coverage |
|---|---|---|
| Output schema validation | `agents/security_layer.py` | Validates JSON structure of each agent output |
| Run ID in audit log | `memory/audit_logger.py` | Provides a reference chain of what was produced |
| `parse_json_response()` | `agents/utils.py` | Validates JSON before consumption |
| `.gitignore` on `data/` | `.gitignore` | Prevents accidental commit of agent outputs |

**Status: Partial**

### Honest gap

Inter-agent communication via disk files has no authentication or encryption.
Any process with file system access can modify `data/orchestrator_report.json`
between the Orchestrator writing it and the Decider reading it. In a local
development environment this is low risk. In any multi-user or cloud
deployment it becomes a significant attack surface.

This is acceptable for a portfolio pipeline but must be addressed before
any production deployment.

### Remediation roadmap

```
Priority 1 (Medium): Add run_id and content hash validation to each
  agent file handoff (see ASI03 Priority 1 — same fix addresses both)

Priority 2 (Low — production only): Replace file-based inter-agent
  communication with an authenticated message queue (Redis, RabbitMQ)
  when deploying beyond local development
```

---

## ASI08:2026 — Cascading Agent Failures

**Risk:** Small agent failures propagate through connected systems, causing
large-scale impact.

**Subtypes:**
- Tool chain failures — errors propagating through tool execution sequences
- Agent dependency failures — one agent's failure affecting dependent agents
- Resource exhaustion cascades — resource depletion spreading across systems
- Trust chain breakdowns — security failures propagating through trust

### Pipeline exposure

Your pipeline is sequential — each stage depends on the previous stage's
output. A failure in the Evaluate stage (e.g., hallucination_eval_agent
returning malformed JSON) could cascade to the Orchestrator (which aggregates
Evaluate signals), which cascades to the Decider, which cascades to the Learn
stage audit log entry.

### Current controls

| Control | File | Coverage |
|---|---|---|
| Reflexion hard limit (2 passes) | `agents/critic.py` | Prevents infinite critique loop |
| Human escalation on critique failure | `agents/critic.py` | Escalates to human after 2 failed passes |
| `try/except` in routes.py | `backend/routes.py` | Each stage wrapped — failure returns error, doesn't crash |
| Confidence threshold gate | `agents/orchestrator.py` | Low confidence halts at Decide, doesn't cascade |
| `parse_json_response()` fallback | `agents/utils.py` | Returns `{}` rather than crashing on bad JSON |

**Status: Implemented**

### Why this is your strongest OWASP risk area

The Reflexion loop's 2-pass hard limit is a textbook cascade prevention
control. The confidence gate at Orchestrator means a weak Evaluate signal
triggers human review rather than a bad GO decision cascading to Learn.
The `try/except` wrapping in `routes.py` means a single agent failure
returns an error response rather than crashing the whole pipeline.

These were architectural decisions made before the OWASP framework existed —
but they map precisely to ASI08 mitigations.

### Honest gap

There is no circuit breaker pattern across runs — if the same failure occurs
across 5 consecutive runs, the pipeline does not auto-pause. This is handled
by drift detection (which triggers alerts) but not by a hard stop at the
pipeline orchestration level.

---

## ASI09:2026 — Human-Agent Trust Exploitation

**Risk:** Exploiting human over-reliance on agents through misleading
explanations or authority framing.

**Subtypes:**
- Authority misrepresentation — agents presenting false credentials
- Misleading explanations — plausible but incorrect reasoning
- Over-confidence projection — agents expressing unwarranted certainty
- Responsibility diffusion — agents deflecting accountability for errors

### Pipeline exposure

The Business Impact Translator generates revenue estimates and executive memos
that are dispatched to Slack. If these outputs overstate confidence or present
AI-generated financial estimates as authoritative, human reviewers may act
on them without appropriate scrutiny.

The Decider's reasoning chain is LLM-generated — it can produce plausible-sounding
but incorrect justifications for a GO decision.

### Current controls

| Control | File | Coverage |
|---|---|---|
| EU AI Act Art. 50 transparency disclosure | `agents/transparency.py` | Every output labelled as AI-generated with confidence % |
| Confidence score on all Decide outputs | `agents/decider.py` | Human sees confidence before acting |
| Human-in-the-loop mandatory gate | `agents/orchestrator.py` | No GO decision ships without human review |
| Brier score calibration | `agents/confidence.py` | Measures stated vs actual confidence — detects over-confidence |
| Agent scope policy | `config/agent_manifest.yaml` | Revenue estimates labelled as illustrative, not financial projections |
| Responsible AI Use policy | `docs/RESPONSIBLE_AI_USE.md` | Explicitly prohibits using outputs as sole decision basis |

**Status: Implemented** — strongest coverage in the pipeline

### Why this is well-addressed

The combination of EU AI Act Article 50 disclosure (every output labelled),
Brier score calibration (catches over-confident agents), and the mandatory
HITL gate (human must review before action) directly addresses all four
ASI09 subtypes. The `agent_manifest.yaml` entry for `business_impact_agent`
explicitly states "revenue estimates are illustrative — not financial
projections" — this is documented responsibility assignment, not diffusion.

### Honest gap

The Decider's reasoning chain is not separately validated for logical
coherence — only for grounding (faithfulness to source material). A reasoning
chain that is factually grounded but logically unsound could pass the
hallucination eval and reach a human reviewer who may not scrutinise it
sufficiently.

---

## ASI10:2026 — Rogue Agent Behaviour

**Risk:** Agents acting beyond intended objectives due to goal drift,
collusion, or emergent behaviour.

**Subtypes:**
- Goal drift — gradual deviation from original objectives over time
- Agent collusion — multiple agents coordinating on unintended objectives
- Emergent behaviour — complex interactions producing unexpected outcomes
- Reward hacking — agents exploiting flawed metrics to optimise the wrong thing

### Pipeline exposure

The Calibration agent learns from the audit trail and recommends threshold
adjustments. If the audit trail is poisoned (ASI06) or the calibration
agent's LLM reasoning drifts, it could recommend threshold changes that
degrade the pipeline's governance controls over time — a rogue agent scenario
that is invisible until significant damage is done.

The Business Impact Translator maps decisions to revenue — if its prompts
are manipulated to consistently overstate revenue impact, it could bias
future GO decisions through the Learn stage.

### Current controls

| Control | File | Coverage |
|---|---|---|
| Drift detection | `config/performance_baselines.yaml` | Detects metric degradation across rolling 5-run window |
| Performance baselines | `config/performance_baselines.yaml` | Hard thresholds trigger alerts before significant drift |
| Calibration agent minimum data requirement | `config/agent_manifest.yaml` | Requires 5+ resolved outcomes before recommendations |
| Human review of calibration recommendations | `agents/calibration_agent.py` | Recommendations flagged for human review, not auto-applied |
| Immutable audit log | `memory/audit_logger.py` | Provides historical record for anomaly detection |
| Improvement log | `docs/IMPROVEMENT_LOG.md` | Documents all threshold changes with rationale |

**Status: Partial**

### Honest gap

Drift detection catches metric degradation but does not detect behavioural
drift — subtle changes in the reasoning patterns or recommendation styles of
agents that don't immediately show up in confidence scores or escalation rates.
There is no watchdog agent monitoring peer agent behaviour for anomalies.
The Calibration agent's own outputs are not audited against a baseline of
what "good calibration recommendations" look like.

### Remediation roadmap

```
Priority 1 (Medium): Add behavioural baseline to calibration agent
  — record first 10 calibration recommendations as baseline
  — flag future recommendations that deviate significantly from baseline
  — requires human review before any threshold change is applied

Priority 2 (Low): Add agent output distribution monitoring
  — track GO/NO_GO/CONDITIONAL_GO ratio per rolling 10-run window
  — alert if ratio drifts more than 20% from established baseline
  — catches reward hacking where Decider optimises toward GO regardless of evidence
```

---

## Summary Assessment

### Status by risk

| ASI Code | Risk | Status | Confidence |
|---|---|---|---|
| ASI01 | Agent Goal Hijack | Partial | Medium — regex blocks patterns, not semantics |
| ASI02 | Tool Misuse & Exploitation | Partial | Medium — cost monitoring exists, no call budget |
| ASI03 | Agent Identity & Privilege Abuse | Partial | Low — declared not enforced |
| ASI04 | Agentic Supply Chain Compromise | Partial | Medium — versioned not verified |
| ASI05 | Unexpected Code Execution | Implemented | High — no code generation in scope |
| ASI06 | Memory & Context Poisoning | Partial | Medium — rollback exists, integrity checking absent |
| ASI07 | Insecure Inter-Agent Communication | Partial | Low — file-based, no auth |
| ASI08 | Cascading Agent Failures | Implemented | High — Reflexion limit + HITL gate |
| ASI09 | Human-Agent Trust Exploitation | Implemented | High — EU AI Act + Brier + HITL |
| ASI10 | Rogue Agent Behaviour | Partial | Medium — drift detection, no behavioural monitoring |

### Coverage counts

| Status | Count | Risks |
|---|---|---|
| Implemented | 3 | ASI05, ASI08, ASI09 |
| Partial | 7 | ASI01, ASI02, ASI03, ASI04, ASI06, ASI07, ASI10 |
| Gap | 0 | — |

No OWASP Agentic risk is completely unaddressed. Every risk has at least
one active control. The three fully implemented risks (code execution safety,
cascade prevention, human trust) are the most critical for a product decision
pipeline that operates in a product planning context.

---

## Cross-Framework Mapping

The OWASP Agentic Top 10 extends rather than duplicates the existing GRC
framework. This table shows how the frameworks complement each other:

| OWASP Risk | Maps to NIST | Maps to EU AI Act | Maps to ISO 42001 |
|---|---|---|---|
| ASI01 Goal Hijack | MEASURE 2.6 (confabulation) | Art. 15 (robustness) | Clause 8.2 (risk treatment) |
| ASI02 Tool Misuse | GOVERN 4 (risk tolerance) | Art. 9 (risk management) | Clause 6.1.2 (risk assessment) |
| ASI03 Identity Abuse | GOVERN 2 (accountability) | Art. 14 (human oversight) | Clause 5.3 (roles) |
| ASI04 Supply Chain | MEASURE 2.2 (TEVV) | Art. 10 (data governance) | Clause 8.4 (lifecycle) |
| ASI05 Code Execution | MANAGE 1 (response) | Art. 15 (robustness) | Clause 8.3 (risk treatment) |
| ASI06 Memory Poisoning | MEASURE 2.13 (logging) | Art. 12 (record keeping) | Clause 8.1 (operational) |
| ASI07 Inter-Agent Comms | GOVERN 2 (accountability) | Art. 15 (robustness) | Clause 8.2 (risk treatment) |
| ASI08 Cascading Failures | MANAGE 1.3 (incident response) | Art. 9 (risk management) | Clause 10.1 (corrective action) |
| ASI09 Trust Exploitation | MEASURE 2.11 (bias/fairness) | Art. 50 (transparency) | Clause 9.1 (monitoring) |
| ASI10 Rogue Behaviour | MANAGE 4.1 (monitoring) | Art. 14 (human oversight) | Clause 9.1 (monitoring) |

**Key insight:** OWASP ASI addresses the three risk categories that the
other frameworks cover incompletely for agentic systems:
1. **Tool use** — agents taking actions in the world (ASI02, ASI05)
2. **Multi-step reasoning** — where a single injection compounds (ASI01, ASI08)
3. **Inter-agent communication** — agents talking to agents (ASI03, ASI07)

---

## Prioritised Remediation Roadmap

All items below are ranked by risk severity × implementation effort:

| Priority | Risk | Action | Effort | Addresses |
|---|---|---|---|---|
| P1 | ASI03, ASI07 | Add run_id validation to inter-agent file handoffs | 2h | Identity + comms integrity |
| P2 | ASI06 | Add retrieval-time content validation on ChromaDB chunks | 2h | Memory poisoning |
| P3 | ASI01 | Add semantic intent classifier to security layer | 4h | Goal hijacking |
| P4 | ASI02 | Add per-run API call budget (hard limit: 20 calls) | 1h | Tool misuse |
| P5 | ASI06 | Add automated ChromaDB rollback trigger | 3h | Memory poisoning |
| P6 | ASI10 | Add GO/NO_GO ratio distribution monitoring | 2h | Rogue behaviour |
| P7 | ASI04 | Add system prompt hash verification at run start | 1h | Supply chain |

Total estimated effort: ~15 hours

---

## What This Pipeline Does Well

Honest acknowledgement of genuine strengths before a regulator or auditor
asks:

**ASI08 — Cascade prevention is architectural, not bolted on.**
The Reflexion 2-pass hard limit, confidence gate at Orchestrator, and
`try/except` wrapping in routes.py were design decisions made before OWASP
published this framework. They independently arrived at the correct
architectural pattern for cascade prevention.

**ASI09 — Human trust exploitation is the most comprehensively addressed.**
The combination of EU AI Act Article 50 mandatory disclosure, Brier score
confidence calibration, mandatory HITL gate, and responsible use policy
provides defence-in-depth against every ASI09 subtype.

**ASI05 — Code execution risk is correctly scoped.**
By building a recommendation pipeline rather than a code generation agent,
the most dangerous OWASP agentic risk is eliminated by design. This is a
product management decision, not a security patch.

---

## References

- OWASP Top 10 for Agentic Applications 2026: genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026
- NIST AI RMF mapping: docs/NIST_RMF_MAPPING.md
- EU AI Act classification: docs/EU_AI_ACT_CLASSIFICATION.md
- NIST AI 600-1 assessment: docs/NIST_600_1_ASSESSMENT.md
- Risk register: docs/RISK_REGISTER.md
- Incident response: docs/INCIDENT_RESPONSE.md
- Agent manifest: config/agent_manifest.yaml

---

*Saurabh Mahajan · saurabh@arcaence.com · arcaence.com · June 2026*
