# AI System Card — AI Product Intelligence Loop
**Version:** 1.0
**Owner:** Saurabh Mahajan (saurabh@arcaence.com)
**Last updated:** June 2026
**Framework:** EU AI Act Article 50 · NIST GOVERN 6 · AIGP Domain 1

---

## System Overview

| Field | Value |
|---|---|
| System name | AI Product Intelligence Loop |
| Version | 1.0 |
| Type | Multi-agent agentic pipeline |
| Total agents | 11 agents across 4 stages |
| Primary language | Python |
| Backend | FastAPI |
| Memory | ChromaDB (vector store) |
| Orchestration | n8n (daily cron) |
| Frontend | React + Recharts |
| LLM provider | OpenAI (gpt-4o-mini default, gpt-4o on upgrade trigger) |
| EU AI Act classification | Limited Risk |
| Repository | github.com/saurabhsmahajan/ai-product-loop |

---

## Intended Use

This system is designed to:
- Process customer support ticket data to extract product pain themes
- Evaluate feature hypotheses against multiple quality signals
- Generate documented GO / NO_GO / CONDITIONAL_GO product decisions
- Log every decision with full reasoning chain for audit and calibration
- Learn from past decisions to improve future recommendations

**Primary users:** Product managers, AI product teams, portfolio reviewers

---

## Out-of-Scope Uses

The following uses are explicitly outside the intended scope:

- Making autonomous final decisions without human review
- Processing real personally identifiable information without consent
- Employment, credit, legal, or healthcare decisions of any kind
- Deployment on populations not represented in test data
- Use as a sole basis for any consequential organisational decision

---

## Pipeline Stages and Agents

| Stage | Agent | Function |
|---|---|---|
| 01 Discover | Interview Agent | Async user interviews with contextual follow-up |
| 01 Discover | Synthesis Agent | Extracts pain themes, scores by frequency and severity |
| 02 Evaluate | Persona Agent | Simulates user reactions to feature hypothesis |
| 02 Evaluate | Hallucination Eval Agent | Scores faithfulness and factuality separately |
| 02 Evaluate | Confidence Calibration Agent | Measures Brier score — stated vs actual confidence |
| 02 Evaluate | Governance Module | EU AI Act classification, PII scrub, bias detection |
| 03 Decide | Orchestrator Agent | Aggregates all signals into weighted confidence score |
| 03 Decide | Decider Agent | Produces GO/NO_GO/CONDITIONAL_GO with reasoning chain |
| 03 Decide | Reflexion Agent | Critiques decision — escalates if critique score < 0.70 |
| 03 Decide | Security Layer | Blocks prompt injection, validates output schema |
| 04 Learn | Calibration Agent | Reviews audit trail, recommends threshold adjustments |
| 04 Learn | Business Impact Translator | Maps decisions to revenue estimates, posts to Slack |

---

## Data Sources

| Source | Type | PII risk | Treatment |
|---|---|---|---|
| Customer support ticket transcripts | Text | High | PII scrubbed before any LLM call |
| Synthetic interview data | Text | None | Used for testing and development |
| ChromaDB vector store | Embeddings | Low | Stores embeddings only, not raw text |
| OpenAI API | External LLM | Medium | No PII sent after scrubbing |

---

## Known Limitations

| Limitation | Impact | Condition for reversal |
|---|---|---|
| Calibration agent needs 5+ resolved outcomes | Brier score is indicative only below this threshold | Accumulate 5+ post-launch outcome updates |
| Competitive intel uses LLM training knowledge | Not real-time market data | Integrate web search tool |
| React dashboard uses mock data in places | Some metrics are illustrative | Complete FastAPI wiring |
| Security layer uses regex, not LLM classifier | Higher false positive rate on technical language | Replace with fine-tuned classifier |
| Persona simulation is synthetic | May not represent minority user segments | Validate against real user research |

---

## Performance Metrics

*Update this section after each set of 10 pipeline runs.*

| Metric | Value | Last updated |
|---|---|---|
| Average confidence score | Update after runs | — |
| Escalation rate | Update after runs | — |
| Average cost per run | ~$0.003 | June 2026 |
| Bias flag rate | Update after runs | — |
| PII detection rate | Update after runs | — |

---

## Bias Considerations

- Synthesis agent may over-index on themes from verbose respondents
- Persona simulation uses synthetic personas that may not represent all user segments
- Hallucination eval uses same model family as generation — self-referential evaluation risk
- Orchestrator confidence weighting (hallucination 30%, calibration 30%, persona 20%, governance 20%) encodes value judgements — review quarterly

---

## Contact

**System owner:** Saurabh Mahajan
**Email:** saurabh@arcaence.com
**Website:** arcaence.com
**Review cadence:** Quarterly or after any significant architecture change