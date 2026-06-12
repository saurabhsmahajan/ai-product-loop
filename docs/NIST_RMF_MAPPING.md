# NIST AI RMF Controls Mapping — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Framework:** NIST AI Risk Management Framework 1.0 + AI 600-1 (July 2024)

---

## Purpose

This document maps every governance control in the pipeline to its
corresponding NIST AI RMF function and subcategory. It is the primary
evidence document showing the pipeline implements a structured,
framework-aligned approach to AI risk management.

---

## GOVERN Function

| NIST Subcategory | Control | File / Artifact | Status |
|---|---|---|---|
| GOVERN 1 — Policies | AI Governance Policy | docs/AI_GOVERNANCE_POLICY.md | Complete |
| GOVERN 2 — Accountability | Agent role boundaries and ownership | config/agent_manifest.yaml | Complete |
| GOVERN 4 — Risk tolerance | Risk appetite statement | docs/AI_GOVERNANCE_POLICY.md §3 | Complete |
| GOVERN 5 — Acceptable use | Responsible AI Use Policy | docs/RESPONSIBLE_AI_USE.md | Complete |
| GOVERN 6 — Transparency | AI System Card | docs/AI_SYSTEM_CARD.md | Complete |
| GOVERN 6 — Transparency | EU AI Act Article 50 disclosure | agents/transparency.py | Complete |

---

## MAP Function

| NIST Subcategory | Control | File / Artifact | Status |
|---|---|---|---|
| MAP 1 — Risk context | EU AI Act risk classification | docs/EU_AI_ACT_CLASSIFICATION.md | Complete |
| MAP 2 — Risk identification | Risk register | docs/RISK_REGISTER.md | Complete |
| MAP 4 — Risk prioritisation | Risk register (likelihood × impact) | docs/RISK_REGISTER.md | Complete |
| MAP 5 — Impact documentation | AI System Impact Assessment | docs/IMPACT_ASSESSMENT.md | Complete |
| MAP 5 — Impact documentation | AI System Card known limitations | docs/AI_SYSTEM_CARD.md | Complete |

---

## MEASURE Function

| NIST Subcategory | Control | File / Artifact | Status |
|---|---|---|---|
| MEASURE 2.2 — TEVV records | Model version registry | config/model_registry.json | Complete |
| MEASURE 2.5 — Data quality | PII scrubbing before LLM calls | agents/governance.py scrub_pii() | Existing |
| MEASURE 2.6 — Confabulation | Hallucination faithfulness eval | agents/eval_agent.py | Existing |
| MEASURE 2.7 — Drift monitoring | Performance baselines + drift detection | config/performance_baselines.yaml | Complete |
| MEASURE 2.9 — Explainability | Full reasoning chain in audit log | memory/audit_logger.py | Existing |
| MEASURE 2.11 — Bias/fairness | Bias indicator check | agents/bias_check.py | Complete |
| MEASURE 2.11 — Confidence | Brier score calibration | agents/confidence.py | Existing |
| MEASURE 2.13 — Audit logging | Extended audit trail with data lineage | memory/audit_logger.py | Extended |
| NIST AI 600-1 Risk 1 | Confabulation — hallucination grounding | agents/eval_agent.py | Existing |
| NIST AI 600-1 Risk 2 | Harmful bias — bias check | agents/bias_check.py | Complete |
| NIST AI 600-1 Risk 4 | Data privacy — PII redaction | agents/governance.py | Existing |
| NIST AI 600-1 Risk 11 | Prompt injection — security layer | agents/security_layer.py | Existing |

---

## MANAGE Function

| NIST Subcategory | Control | File / Artifact | Status |
|---|---|---|---|
| MANAGE 1 — Human oversight | HITL gate at Decide stage | agents/orchestrator.py | Existing |
| MANAGE 1 — Human oversight | Slack escalation on critique < 0.70 | agents/critic.py | Existing |
| MANAGE 1.3 — Incident response | Incident response playbook | docs/INCIDENT_RESPONSE.md | Complete |
| MANAGE 2 — Risk treatment | Risk register mitigations | docs/RISK_REGISTER.md | Complete |
| MANAGE 3 — Residual risk | Gap analysis | docs/GAP_ANALYSIS.md | Complete |
| MANAGE 4 — Post-deployment | Governance dashboard | frontend/src/GovernanceDashboard.jsx | Complete |
| MANAGE 4.1 — Monitoring | Performance baselines monitoring | config/performance_baselines.yaml | Complete |
| MANAGE 4.2 — Improvement | Continual improvement log | docs/IMPROVEMENT_LOG.md | Ongoing |

---

## Coverage Summary

| NIST Function | Controls implemented | Status |
|---|---|---|
| GOVERN | 6 | Complete |
| MAP | 5 | Complete |
| MEASURE | 12 | Complete |
| MANAGE | 8 | Complete |
| **Total** | **31** | **Complete** |