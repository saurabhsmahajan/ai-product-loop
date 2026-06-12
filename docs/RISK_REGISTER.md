# AI Risk Register — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Framework:** ISO/IEC 42001 Clause 6.1.2 · NIST MAP 5

---

## Risk Assessment Methodology

**Likelihood scale:** Low (1) · Medium (2) · High (3)
**Impact scale:** Low (1) · Medium (2) · High (3)
**Risk score:** Likelihood × Impact (1–9)
**Treatment threshold:** Score ≥ 4 requires active mitigation

---

## Risk Register

| ID | Risk | Stage | Likelihood | Impact | Score | Mitigation | Control | Residual risk |
|---|---|---|---|---|---|---|---|---|
| R-01 | Hallucination in LLM output presented as fact | Evaluate | Medium (2) | High (3) | **6** | Hallucination faithfulness eval | agents/eval_agent.py | Low |
| R-02 | PII leak into Learn-stage storage or LLM call | Evaluate / Learn | Low (1) | High (3) | **3** | PII scrubbing before LLM + audit log | agents/governance.py | Very low |
| R-03 | Prompt injection via feature hypothesis input | Discover / Decide | Medium (2) | High (3) | **6** | Security layer injection scanner | agents/security_layer.py | Low |
| R-04 | Model drift degrading decision quality over runs | All stages | Medium (2) | Medium (2) | **4** | Drift detection + rollback + baselines | performance_baselines.yaml | Low |
| R-05 | Stale ChromaDB chunks producing outdated context | Discover | High (3) | Medium (2) | **6** | Source timestamps on all stored chunks | memory/chroma_store.py | Medium |
| R-06 | Bias in synthesis or feature description | Evaluate | Medium (2) | Medium (2) | **4** | Bias indicator check + human review | agents/bias_check.py | Low |
| R-07 | Self-referential hallucination eval (judge = defendant) | Evaluate | Medium (2) | Medium (2) | **4** | Flag scores > 0.95 for review | agents/eval_agent.py | Medium |
| R-08 | Confidence score miscalibration leading to wrong GO | Decide | Low (1) | High (3) | **3** | Brier score calibration + outcome tracking | agents/confidence.py | Low |
| R-09 | Slack alert failure masking required human escalation | Decide | Low (1) | High (3) | **3** | Audit log as primary record; Slack as secondary | memory/audit_logger.py | Low |
| R-10 | Cost explosion from inadvertent gpt-4o upgrade loops | All stages | Low (1) | Medium (2) | **2** | Model routing threshold + cost tracker | agents/cost_tracker.py | Very low |

---

## Risk Treatment Plan

| ID | Treatment decision | Owner | Target date | Review date |
|---|---|---|---|---|
| R-01 | Mitigate — hallucination eval active | Saurabh Mahajan | Done | Sep 2026 |
| R-02 | Mitigate — PII scrub active | Saurabh Mahajan | Done | Sep 2026 |
| R-03 | Mitigate — security layer active | Saurabh Mahajan | Done | Sep 2026 |
| R-04 | Mitigate — baselines defined | Saurabh Mahajan | Done | Sep 2026 |
| R-05 | Mitigate — add source timestamps | Saurabh Mahajan | July 2026 | Sep 2026 |
| R-06 | Mitigate — bias check active | Saurabh Mahajan | Done | Sep 2026 |
| R-07 | Accept — document limitation | Saurabh Mahajan | Done | Sep 2026 |
| R-08 | Mitigate — Brier score tracking | Saurabh Mahajan | Done | Sep 2026 |
| R-09 | Mitigate — dual logging | Saurabh Mahajan | Done | Sep 2026 |
| R-10 | Mitigate — cost tracker active | Saurabh Mahajan | Done | Sep 2026 |

---

## Review Log

| Date | Reviewer | Changes made |
|---|---|---|
| June 2026 | Saurabh Mahajan | Initial register created — 10 risks identified |

---

## Escalation Contacts

| Role | Contact | Method |
|---|---|---|
| System owner | Saurabh Mahajan | saurabh@arcaence.com |
| Slack alert | Pipeline Slack channel | Automated via agents/slack_notifier.py |

---

## Relationship to Other Documents

- Incidents that reveal new risks → update `RISK_REGISTER.md`
- Incidents that require policy change → update `AI_GOVERNANCE_POLICY.md`
- All incidents → append to `IMPROVEMENT_LOG.md`
- SEV-1 PII incidents → may require GDPR breach assessment