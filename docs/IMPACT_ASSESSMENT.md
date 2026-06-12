# AI System Impact Assessment — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Framework:** ISO/IEC 42001 Clause 6.1.4 · AIGP BOK v2.1 Domain 2

---

## Purpose

This assessment documents the potential consequences of the AI Product
Intelligence Loop on individuals, groups, and society — both from correct
operation and from system failures.

Required by ISO 42001 Clause 6.1.4. Outcomes feed into RISK_REGISTER.md.

---

## System Description for Assessment

The pipeline processes customer support ticket data to generate product
feature recommendations. It operates in a product planning context —
outputs inform human product decisions but do not autonomously trigger
any actions affecting end users.

---

## Stakeholder Analysis

| Stakeholder | Relationship to system | Potential impact |
|---|---|---|
| Product managers | Primary users of recommendations | Low — human reviews all outputs |
| Customers (data subjects) | Source of support ticket data | Medium — PII risk if scrubbing fails |
| Engineering teams | Receive GO decisions for implementation | Low — recommendations only |
| End users of features shipped | Indirect — affected by feature decisions | Low to medium — depends on decision quality |

---

## Harm Assessment

### Scenario 1 — Hallucination in GO recommendation
**Description:** The Decider agent recommends GO on a feature based on
hallucinated evidence not present in the source data.
**Likelihood:** Low (hallucination eval active)
**Harm if occurs:** A poorly validated feature ships, wasting engineering
resources and potentially degrading user experience.
**Severity:** Medium — recoverable with post-launch monitoring
**Mitigation:** Hallucination faithfulness eval + human review gate
**Residual risk:** Low

### Scenario 2 — PII leak from support tickets
**Description:** Real customer PII (email, phone) passes through to LLM
call or is stored in ChromaDB without redaction.
**Likelihood:** Low (PII scrubbing active at pipeline entry)
**Harm if occurs:** Privacy violation affecting real customers. Potential
GDPR breach notification obligation.
**Severity:** High — regulatory and reputational consequence
**Mitigation:** PII scrubbing in agents/governance.py before any LLM call
**Residual risk:** Very low

### Scenario 3 — Biased synthesis skews feature prioritisation
**Description:** Pain theme extraction over-weights themes from a
non-representative subset of customers.
**Likelihood:** Medium (synthetic data may not represent all segments)
**Harm if occurs:** Features built for majority users, underserved
segments receive lower priority.
**Severity:** Medium — bias in product strategy
**Mitigation:** Bias check + diverse data sourcing + human review
**Residual risk:** Medium — documented limitation

### Scenario 4 — Prompt injection manipulates decision
**Description:** A malicious input crafted to bypass system instructions
causes the Decider to produce an incorrect or harmful recommendation.
**Likelihood:** Low (security layer active)
**Harm if occurs:** Corrupted GO decision potentially shipping a harmful
or wasteful feature.
**Severity:** High
**Mitigation:** Security layer injection scanner at pipeline entry
**Residual risk:** Low

### Scenario 5 — Over-reliance on AI recommendations
**Description:** Product team treats GO recommendations as authoritative
without applying independent judgement.
**Likelihood:** Medium — human behaviour risk, not technical
**Harm if occurs:** Poor product decisions made without adequate scrutiny.
**Severity:** Medium
**Mitigation:** Mandatory human review gate + confidence disclosure on
all outputs + responsible use policy prohibition on autonomous decisions
**Residual risk:** Medium — requires ongoing user education

---

## Underrepresented Populations

The current test dataset uses synthetic support ticket data. The following
populations may be underrepresented:

- Non-English speaking customers
- Users with accessibility needs
- Users in low-bandwidth environments
- Users from markets outside the primary test geography

**Mitigation:** Flag this in AI_SYSTEM_CARD.md known limitations.
Do not deploy on real populations without representative data validation.

---

## Worst-Case Failure Scenario

A hallucinated GO recommendation on a high-cost feature, based on
corrupted ChromaDB context from a prompt injection attack, passes through
an inattentive human review and ships. Post-launch, the feature fails
adoption metrics and causes user trust degradation.

**Controls that prevent this chain:**
1. Injection scanner blocks malicious input (agents/security_layer.py)
2. Hallucination eval scores faithfulness (agents/eval_agent.py)
3. Orchestrator requires minimum confidence before GO routes to Decider
4. Reflexion loop critiques the reasoning chain
5. Human review gate is mandatory — no autonomous shipping
6. Audit trail enables full post-incident reconstruction

No single control failure produces the worst case — all five must fail
simultaneously. This is the defence-in-depth argument for the pipeline's
multi-agent architecture.

---

## Assessment Conclusion

The AI Product Intelligence Loop poses **low to medium risk** in its
current configuration. All identified high-severity harms have active
technical mitigations. The primary residual risks are human behaviour
risks (over-reliance, inattentive review) that are mitigated through
policy rather than code.

**Next review trigger:** Any change to data sources, agent architecture,
or deployment context.