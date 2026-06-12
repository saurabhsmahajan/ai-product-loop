# ISO/IEC 42001 Gap Analysis — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan
**Last updated:** June 2026
**Standard:** ISO/IEC 42001:2023 — Artificial Intelligence Management System

---

## Purpose

A clause-by-clause assessment of where this implementation stands
against ISO/IEC 42001. Standard practice for any organisation
implementing an AI management system. Documents both what is complete
and what remains as known gaps.

---

## Gap Analysis

| Clause | Requirement | Status | Evidence | Gap / Notes |
|---|---|---|---|---|
| 4.1 | Understand organisational context | Complete | AI_GOVERNANCE_POLICY.md §1–2 | Single-system scope, not enterprise |
| 4.2 | Understand interested parties | Partial | AI_SYSTEM_CARD.md stakeholders | Limited to pipeline owner and reviewers |
| 4.3 | Determine scope of AIMS | Complete | AI_GOVERNANCE_POLICY.md §2 | Scope explicitly defined |
| 5.1 | Leadership commitment | Complete | AI_GOVERNANCE_POLICY.md | Owner documented and contactable |
| 5.2 | AI policy | Complete | AI_GOVERNANCE_POLICY.md | Published in repository |
| 5.3 | Roles and responsibilities | Complete | config/agent_manifest.yaml | Per-agent ownership declared |
| 6.1.1 | Risk and opportunity assessment | Complete | RISK_REGISTER.md | 10 risks identified and treated |
| 6.1.2 | Risk assessment process | Complete | RISK_REGISTER.md methodology | Likelihood × impact scoring |
| 6.1.3 | Risk treatment | Complete | RISK_REGISTER.md treatment plan | All risks have treatment decision |
| 6.1.4 | AI system impact assessment | Complete | IMPACT_ASSESSMENT.md | 5 harm scenarios assessed |
| 6.2 | Objectives and planning | Partial | README.md | No formal OKRs for governance targets |
| 7.1 | Resources | Complete | Tech stack documented in README.md | All resources identified |
| 7.2 | Competence | Partial | Publications on Built In and Mind the Product | No formal competence record |
| 7.3 | Awareness | Partial | RESPONSIBLE_AI_USE.md | No formal awareness programme |
| 7.4 | Communication | Partial | Slack alerts implemented | No stakeholder comms plan |
| 8.1 | Operational planning and control | Partial | n8n cron orchestration | No formal change control process |
| 8.2 | AI risk assessment (operational) | Complete | Governance module runs per pipeline execution | Per-run assessment active |
| 8.3 | AI risk treatment (operational) | Complete | Security layer + PII scrub run per execution | Per-run treatment active |
| 8.4 | AI system lifecycle | Partial | model_registry.json | No formal deprecation process |
| 9.1 | Monitoring and measurement | Complete | Governance dashboard + performance_baselines.yaml | Live monitoring active |
| 9.2 | Internal audit | Partial | IMPROVEMENT_LOG.md | No formal audit cycle scheduled |
| 9.3 | Management review | Partial | Quarterly review cadence stated | No formal review record yet |
| 10.1 | Nonconformity and corrective action | Complete | INCIDENT_RESPONSE.md | SEV-1/2/3 process defined |
| 10.2 | Continual improvement | Complete | IMPROVEMENT_LOG.md | Running log initiated |

---

## Summary

| Status | Count | Clauses |
|---|---|---|
| Complete | 15 | 4.1, 4.3, 5.1, 5.2, 5.3, 6.1.1, 6.1.2, 6.1.3, 6.1.4, 7.1, 8.2, 8.3, 9.1, 10.1, 10.2 |
| Partial | 9 | 4.2, 6.2, 7.2, 7.3, 7.4, 8.1, 8.4, 9.2, 9.3 |
| Gap | 0 | — |

**Overall maturity:** Foundation level — all critical clauses complete,
operational clauses partially addressed. Appropriate for a portfolio
demonstration system.

---

## Remediation Roadmap

| Clause | Gap | Planned action | Priority |
|---|---|---|---|
| 6.2 | No formal governance OKRs | Add governance metrics to dashboard | Low |
| 8.1 | No change control process | Document change control in IMPROVEMENT_LOG | Medium |
| 8.4 | No model deprecation process | Extend model_registry.json with deprecation fields | Low |
| 9.2 | No formal audit cycle | Schedule quarterly review in IMPROVEMENT_LOG | Low |