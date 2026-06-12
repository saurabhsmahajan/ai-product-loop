# Incident Response Playbook — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Framework:** NIST MANAGE 1.3 · ISO/IEC 42001 Clause 10 · EU AI Act Art. 20

---

## Purpose

Defines what constitutes an AI incident in this pipeline, who is
notified, what the response actions are, and how root cause analysis
is documented.

---

## Incident Severity Definitions

### SEV-1 — Critical (immediate response required)

Trigger conditions:
- PII detected in Learn-stage storage after redaction step
- Decide-stage output produced with no confidence score
- Hallucination rate exceeds 15% in rolling 5-run window
- Prompt injection attempt successfully bypasses security layer
- Pipeline produces output that contradicts its governance policy

**Response actions:**
1. Halt pipeline immediately — no further runs
2. Quarantine affected outputs — flag in audit trail
3. Notify system owner within 1 hour
4. Preserve all logs — do not modify audit trail
5. Complete root cause analysis within 24 hours
6. Document findings in IMPROVEMENT_LOG.md
7. Owner sign-off required before pipeline resumes

---

### SEV-2 — Significant (response within 24 hours)

Trigger conditions:
- Drift alert fires — metric crosses warning threshold in performance_baselines.yaml
- Model version mismatch between model_registry.json and runtime
- Bias flags raised on more than 30% of outputs in a single run
- Slack escalation alert fails to deliver
- Calibration agent recommends threshold adjustment

**Response actions:**
1. Flag affected run in audit trail
2. Human review of all affected outputs before any action is taken
3. Update RISK_REGISTER.md if new risk identified
4. Document in IMPROVEMENT_LOG.md within 48 hours
5. Review and update performance thresholds if warranted

---

### SEV-3 — Minor (log and review at next cycle)

Trigger conditions:
- Single output fails hallucination grounding check
- Confidence score between 0.60–0.75 (human review gate triggered normally)
- Single bias flag raised on one run
- Cost per run exceeds warning threshold once

**Response actions:**
1. Automatic logging to audit trail
2. Include in weekly governance review
3. No immediate action required unless pattern emerges across 3+ runs

---

## Root Cause Analysis Template

For every SEV-1 and SEV-2 incident, document in IMPROVEMENT_LOG.md: