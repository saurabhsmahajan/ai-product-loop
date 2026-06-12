# Responsible AI Use Policy — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Framework:** ISO/IEC 42001 Annex A.6.1 · AIGP BOK v2.1 Domain 1

---

## Purpose

This document defines the acceptable and prohibited uses of the
AI Product Intelligence Loop pipeline. It exists to make explicit
what this system is designed for — and what it must never be used for.

---

## Approved Use Cases

| Use case | Approved | Notes |
|---|---|---|
| Processing synthetic support ticket data for testing | Yes | Primary development use case |
| Processing anonymised support ticket data | Yes | PII must be scrubbed before pipeline entry |
| Evaluating feature hypotheses in product planning | Yes | Core intended use |
| Portfolio demonstration and research | Yes | Author's primary purpose |
| AI governance framework demonstration | Yes | GRC portfolio use case |
| Academic or educational reference | Yes | With attribution |

---

## Prohibited Uses

The following uses are explicitly prohibited without written approval
from the system owner:

| Prohibited use | Reason | Framework reference |
|---|---|---|
| Processing real PII without explicit consent | Privacy violation | EU AI Act Art. 10, GDPR |
| Autonomous final decisions without human review | Removes human oversight | EU AI Act Art. 14 |
| Employment screening or hiring decisions | High-risk AI use case | EU AI Act Annex III |
| Credit scoring or financial eligibility | High-risk AI use case | EU AI Act Annex III |
| Healthcare diagnosis or treatment recommendation | High-risk AI use case | EU AI Act Annex III |
| Law enforcement or legal judgment | Prohibited/high-risk | EU AI Act Art. 5 |
| Deployment on populations not in test data | Bias and fairness risk | NIST MEASURE 2.11 |
| Disabling the human-in-the-loop gate | Removes core control | NIST MANAGE 1 |
| Bypassing PII redaction | Privacy violation | EU AI Act Art. 10 |
| Sharing outputs externally without AI disclosure | Transparency violation | EU AI Act Art. 50 |

---

## Approval Process for New Use Cases

Any use case not listed above requires:

1. Risk assessment against EU AI Act Annex III criteria
2. Update to `IMPACT_ASSESSMENT.md`
3. Update to `EU_AI_ACT_CLASSIFICATION.md` if risk tier changes
4. Owner sign-off documented in `IMPROVEMENT_LOG.md`
5. Re-review of `RISK_REGISTER.md` for new risks introduced

---

## Enforcement

Violations of this policy must be documented in `INCIDENT_RESPONSE.md`
as a minimum SEV-2 incident regardless of whether harm occurred.

**Policy owner:** Saurabh Mahajan — saurabh@arcaence.com
**Review cadence:** Quarterly or after any new use case is approved