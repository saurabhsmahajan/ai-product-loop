# AI Governance Policy — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan (saurabh@arcaence.com)
**Repository:** github.com/saurabhsmahajan/ai-product-loop
**Review cadence:** Quarterly
**Last reviewed:** June 2026

---

## 1. Purpose

This policy establishes the governance framework for the AI Product
Intelligence Loop — a multi-agent agentic pipeline processing customer
support ticket data to generate product intelligence recommendations.

It exists to ensure the pipeline operates within defined risk tolerances,
with clear accountability, documented controls, and a functioning
escalation path when outputs fall outside acceptable bounds.

---

## 2. Scope

This policy applies to:
- All 11 agents across four pipeline stages: Discover, Evaluate, Decide, Learn
- All data inputs: customer support ticket data (synthetic and real)
- All outputs: product intelligence recommendations, evaluation scores, stored embeddings
- All infrastructure: FastAPI backend, ChromaDB vector store, n8n orchestration, React dashboard

---

## 3. Risk Appetite

| Classification | Definition | Example |
|---|---|---|
| **Unacceptable** | Must trigger immediate pipeline halt | PII detected in Learn-stage storage post-redaction |
| **Unacceptable** | Must trigger immediate pipeline halt | Decide-stage output with no confidence score |
| **Tolerable** | Triggers alert, human review required | Hallucination rate > 10% in rolling 5-run window |
| **Acceptable** | Logged, reviewed at next cycle | Single output below confidence threshold |

---

## 4. Accountability

| Role | Responsibility | Assigned to |
|---|---|---|
| System Owner | Overall governance, policy review | Saurabh Mahajan |
| Data Processor | Evaluate agent outputs, bias flags | Evaluate Agent (automated) |
| Decision Authority | Final approval of Decide-stage outputs | Human reviewer |
| Audit Log Custodian | Immutable log integrity | audit_logger.py (automated) |

---

## 5. Escalation Path

When an agent produces an unacceptable output:

1. **Automated detection** — drift monitor or confidence gate fires
2. **Pipeline halt** — Decide stage blocked, output quarantined
3. **Human notification** — alert logged to audit trail and Slack
4. **Root cause analysis** — completed within 24 hours for SEV-1
5. **Remediation** — documented in IMPROVEMENT_LOG.md
6. **Resumption** — pipeline resumes only after owner sign-off

---

## 6. Framework Alignment

| Framework | Clause / Article | This document satisfies |
|---|---|---|
| NIST AI RMF | GOVERN 1 | Policy establishment |
| ISO/IEC 42001 | Clause 5 | Leadership and commitment |
| AIGP BOK v2.1 | Domain 1 | AI governance foundations |

---

## 7. Related Documents

- `EU_AI_ACT_CLASSIFICATION.md` — regulatory risk tier per agent
- `RISK_REGISTER.md` — identified risks and mitigations
- `INCIDENT_RESPONSE.md` — SEV-1/2/3 response procedures
- `IMPROVEMENT_LOG.md` — governance findings and changes
- `config/agent_manifest.yaml` — per-agent accountability record