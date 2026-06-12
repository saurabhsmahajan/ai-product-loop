# EU AI Act Risk Classification — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Classification basis:** EU AI Act Article 6 + Annex III
**Framework:** AIGP BOK v2.1 Domain 2

---

## System-Level Classification: LIMITED RISK

**Rationale:**
The pipeline processes support ticket data and generates product
intelligence recommendations. It does not make consequential autonomous
decisions about individuals. All Decide-stage outputs require human
review before any action is taken.

This places the system outside Annex III High-Risk categories.

**Applicable obligations:**
- Article 50 (transparency) — implemented via `agents/transparency.py`
- Article 12 (logging) — implemented via `memory/audit_logger.py`
- Article 14 (human oversight) — implemented via confidence gate at Decide stage

---

## Per-Agent Classification

| Agent | Function | EU AI Act Tier | Obligation | Implementation |
|---|---|---|---|---|
| synthesis_agent | Pain theme extraction | Minimal risk | None | N/A |
| persona_agent | Simulates user reactions | Limited risk | Transparency | agents/transparency.py |
| hallucination_eval_agent | Quality assessment | Limited risk | Transparency | agents/transparency.py |
| confidence_calibration_agent | Brier score calibration | Limited risk | Transparency | agents/transparency.py |
| governance_agent | EU AI Act + bias check | Limited risk | Transparency | agents/governance.py |
| orchestrator_agent | Signal aggregation | Limited risk | Transparency + HITL | Confidence gate |
| decider_agent | GO/NO_GO recommendation | Limited risk | Transparency + HITL | HITL gate + transparency.py |
| reflexion_agent | Decision critique | Limited risk | Transparency + HITL | Escalation to Slack |
| security_agent | Injection + schema validation | Minimal risk | None | agents/security_layer.py |
| calibration_agent | Audit trail review | Minimal risk | None | agents/calibration_agent.py |
| business_impact_agent | Revenue estimation | Limited risk | Transparency | Human review before sharing |

---

## Annex III Assessment

| Category | Applies? | Reasoning |
|---|---|---|
| 1. Biometric identification | No | No biometric data processed |
| 2. Critical infrastructure | No | Product planning tool only |
| 3. Education and training | No | Not used for educational assessment |
| 4. Employment and workers | No | No employment decisions made |
| 5. Essential private services | No | Not used for credit or insurance |
| 6. Law enforcement | No | No law enforcement application |
| 7. Migration and border | No | No migration application |
| 8. Administration of justice | No | No legal or judicial application |

**Conclusion:** No Annex III category applies. System remains Limited Risk.

---

## Article 50 Transparency Implementation

Every Decide-stage output includes a machine-readable disclosure appended
by `agents/transparency.py`:

```json
{
  "_grc_disclosure": {
    "generated_by": "AI Product Intelligence Loop v1.0",
    "eu_ai_act_classification": "limited_risk",
    "eu_ai_act_article": "Article 50 — Transparency obligations",
    "human_review_required": true,
    "disclosure_text": "[AI-generated product decision. Human review required.]"
  }
}
```

---

## Review Trigger

This classification must be reviewed if:
- The pipeline is used to make decisions affecting real individuals
- Use cases expand to any Annex III domain
- A new EU AI Act guidance update changes Limited Risk obligations
- The pipeline is deployed in a production environment serving real users

**Next scheduled review:** September 2026