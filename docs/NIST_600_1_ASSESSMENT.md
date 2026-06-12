# NIST AI 600-1 GenAI Risk Assessment — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Framework:** NIST AI 600-1 (July 2024) · AIGP BOK v2.1

---

## Purpose

NIST AI 600-1 profiles 12 risk categories specific to generative AI and
agentic systems. This document maps each to the pipeline's current
implementation status.

---

## Risk Assessment

| # | Risk category | Pipeline assessment | Status | Control |
|---|---|---|---|---|
| 1 | **Confabulation** | LLM outputs may assert facts not in source data | Mitigated | agents/eval_agent.py — faithfulness scoring |
| 2 | **Harmful bias** | Synthesis may reflect demographic bias in ticket language | Partial | agents/bias_check.py — flags for review; not fully eliminated |
| 3 | **Homogenisation** | Multiple agents using same model family may converge on similar outputs | Documented | AI_SYSTEM_CARD.md — known limitation |
| 4 | **Data privacy** | Support tickets may contain real customer PII | Mitigated | agents/governance.py — PII scrub before LLM |
| 5 | **Information security** | Prompt injection via feature hypothesis input | Mitigated | agents/security_layer.py — injection pattern scanner |
| 6 | **Intellectual property** | Pipeline does not reproduce training data verbatim | Documented | RESPONSIBLE_AI_USE.md — no IP reproduction |
| 7 | **Obscene/violent content** | Enterprise support ticket domain — low risk | Not applicable | Domain-specific assessment |
| 8 | **Value chain / supply chain** | Dependency on OpenAI API availability and pricing | Documented | config/model_registry.json — version tracking |
| 9 | **Dangerous/violent content** | Product planning domain — not applicable | Not applicable | Domain-specific assessment |
| 10 | **Data poisoning** | Corrupted ChromaDB embeddings could skew future retrievals | Partial | ChromaDB snapshot versioning — full rollback not yet implemented |
| 11 | **Prompt injection** | Malicious input could manipulate agent behaviour | Mitigated | agents/security_layer.py — active scanner |
| 12 | **Overly-broad use** | Risk of using pipeline outside intended product planning scope | Documented | docs/RESPONSIBLE_AI_USE.md — prohibited uses defined |

---

## Status Definitions

- **Mitigated** — active technical control in place, risk materially reduced
- **Partial** — control exists but does not fully address the risk
- **Documented** — risk acknowledged, no technical control, managed via policy
- **Not applicable** — risk category does not apply to this domain

---

## Gaps Requiring Attention

| Risk | Gap | Recommended action | Priority |
|---|---|---|---|
| R-2 Harmful bias | Bias check flags but does not remediate | Add diverse data sourcing guidance | Medium |
| R-10 Data poisoning | No automated rollback on poisoning detection | Implement ChromaDB snapshot restore on anomaly | Medium |
| R-3 Homogenisation | Single model family across all agents | Evaluate alternative model for critique/eval roles | Low |

---

## Agentic AI Specific Risks (AIGP BOK v2.1 addition)

AIGP BOK v2.1 added agentic AI governance requirements not in the
original NIST AI RMF. The following are addressed in this pipeline:

| Agentic risk | Control |
|---|---|
| Agent scope boundary violation | config/agent_manifest.yaml — permitted inputs/outputs per agent |
| Uncontrolled agent chaining | Orchestrator aggregates before routing to Decider — no direct agent-to-agent calls |
| Missing human checkpoint in agent loop | HITL gate mandatory at Decide stage |
| Reflexion loop infinite recursion | Hard limit of 2 critique passes before human escalation |
| Agentic cost explosion | Model routing + cost tracker — upgrade only on low confidence |