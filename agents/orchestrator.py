# agents/orchestrator.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
from agents.utils import call_llm, parse_json_response
from agents.prompts import ORCHESTRATOR_PROMPT


def load_signal(filepath: str, label: str) -> dict:
    """Loads a JSON signal file. Returns empty dict with warning if missing."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        print(f"⚠️  Warning: {label} not found at {filepath} — skipping.")
        return {}


def aggregate_confidence(signals: dict) -> float:
    """
    Aggregates confidence scores from all pipeline signals into one number.
    Weights:
    - Hallucination eval: 30% (most critical for AI quality)
    - Confidence calibration trust score: 30%
    - Persona avg reaction score: 20%
    - Governance verdict: 20%
    """
    scores = []

    # Hallucination eval — faithfulness score (0-1), weight 0.30
    hall = signals.get("hallucination_eval", {})
    faithfulness = hall.get("faithfulness_score", 0)
    scores.append(("hallucination_eval", faithfulness, 0.30))

    # Confidence calibration — trust score (0-10), normalise to 0-1, weight 0.30
    conf = signals.get("confidence_report", {})
    trust_raw = conf.get("trust_score", 0)
    trust_normalised = trust_raw / 10
    scores.append(("confidence_calibration", trust_normalised, 0.30))

    # Persona simulation — avg reaction score (0-10), normalise to 0-1, weight 0.20
    persona = signals.get("persona_simulation", {})
    reaction_raw = persona.get("avg_reaction_score", 0)
    reaction_normalised = reaction_raw / 10
    scores.append(("persona_simulation", reaction_normalised, 0.20))

    # Governance verdict — CLEAR=1.0, FLAGGED=0.5, BLOCKED=0.0, weight 0.20
    gov = signals.get("governance_report", {})
    verdict = gov.get("governance_verdict", "BLOCKED")
    gov_score = {"CLEAR": 1.0, "FLAGGED": 0.5, "BLOCKED": 0.0}.get(verdict, 0.0)
    scores.append(("governance", gov_score, 0.20))

    # Weighted sum
    aggregated = sum(score * weight for _, score, weight in scores)
    return round(aggregated, 3)


def run_orchestrator(feature_hypothesis: str) -> dict:
    """
    Reads all pipeline signals, aggregates confidence, and routes to next step.
    """

    print("\n" + "=" * 60)
    print("ORCHESTRATOR AGENT — Stage 03: Decide")
    print("=" * 60)
    print(f"Feature: {feature_hypothesis}")
    print("Loading all pipeline signals...\n")

    # Step 1 — Load all signals
    signals = {
        "opportunity_map":    load_signal("data/opportunity_map.json",             "Opportunity map"),
        "hallucination_eval": load_signal("data/hallucination_eval_report.json",   "Hallucination eval"),
        "governance_report":  load_signal("data/governance_report.json",           "Governance report"),
        "confidence_report":  load_signal("data/confidence_report.json",           "Confidence report"),
    }

    # Step 2 — Load persona simulation result if saved
    persona_path = "data/persona_simulation.json"
    if not os.path.exists(persona_path):
        # Run persona agent to generate it
        print("Persona simulation file not found — generating now...")
        from agents.persona_agent import simulate_personas
        persona_result = simulate_personas(feature_hypothesis)
        os.makedirs("data", exist_ok=True)
        with open(persona_path, "w") as f:
            json.dump(persona_result, f, indent=2)
        signals["persona_simulation"] = persona_result
    else:
        signals["persona_simulation"] = load_signal(persona_path, "Persona simulation")

    # Step 3 — Aggregate confidence score
    agg_confidence = aggregate_confidence(signals)
    print(f"Aggregated pipeline confidence score: {agg_confidence}")

    # Step 4 — Determine routing
    route = "HUMAN_ESCALATION" if agg_confidence < 0.6 else "DECIDER"
    routing_reason = (
        f"Aggregated confidence {agg_confidence} is below 0.6 threshold — escalating to human."
        if route == "HUMAN_ESCALATION"
        else f"Aggregated confidence {agg_confidence} meets threshold — routing to Decider Agent."
    )
    print(f"Routing decision: {route}")
    print(f"Reason: {routing_reason}\n")

    # Step 5 — Ask LLM to reason over all signals and produce pipeline summary
    signals_summary = {
        "opportunity_map_top": signals["opportunity_map"].get("top_opportunity", "N/A"),
        "hallucination_verdict": signals["hallucination_eval"].get("eval_verdict", "N/A"),
        "hallucination_rate": signals["hallucination_eval"].get("overall_hallucination_rate", "N/A"),
        "governance_verdict": signals["governance_report"].get("governance_verdict", "N/A"),
        "eu_ai_act_tier": signals["governance_report"].get("eu_ai_act_risk_tier", "N/A"),
        "trust_score": signals["confidence_report"].get("trust_score", "N/A"),
        "calibration_verdict": signals["confidence_report"].get("calibration_verdict", "N/A"),
        "persona_avg_score": signals["persona_simulation"].get("avg_reaction_score", "N/A"),
        "persona_blockers": signals["persona_simulation"].get("blockers", []),
    }

    response = call_llm(
        system_prompt=ORCHESTRATOR_PROMPT,
        user_message=f"""
Feature hypothesis: {feature_hypothesis}

Pipeline signals summary:
{json.dumps(signals_summary, indent=2)}

Aggregated confidence score: {agg_confidence}
Routing decision: {route}
Routing reason: {routing_reason}

Produce the full orchestrator pipeline state report.
"""
    )

    report = parse_json_response(response)

    if not report:
        print("Error: Could not generate orchestrator report.")
        return {}

    # Step 6 — Inject calculated values
    report["pipeline_run_id"] = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report["aggregated_confidence_score"] = agg_confidence
    report["route_to"] = route
    report["routing_reason"] = routing_reason

    # Step 7 — Save report
    os.makedirs("data", exist_ok=True)
    output_path = "data/orchestrator_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Orchestrator report saved to {output_path}")
    return report


if __name__ == "__main__":
    hypothesis = "An AI assistant that automatically summarises customer support tickets and suggests responses to agents."
    result = run_orchestrator(hypothesis)
    print("\nFull orchestrator report:")
    print(json.dumps(result, indent=2))