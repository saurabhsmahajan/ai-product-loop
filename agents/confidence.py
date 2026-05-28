# agents/confidence.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import CONFIDENCE_SCORING_PROMPT


def calculate_brier_score(predictions: list) -> float:
    """
    Brier score = average of (stated_confidence - actual_outcome)^2
    actual_outcome is 1 if the answer was correct, 0 if wrong.
    Lower is better. Perfect = 0. Random = 0.25.
    """
    if not predictions:
        return 0.0
    total = sum(
        (p["stated_confidence"] - p["actual_outcome"]) ** 2
        for p in predictions
    )
    return round(total / len(predictions), 4)


def run_confidence_calibration(
    ai_outputs: list,
    eval_report: dict
) -> dict:
    """
    Measures how well-calibrated the LLM's confidence is.

    ai_outputs: list of dicts with keys:
        - statement: what the AI said
        - stated_confidence: float 0-1 (how confident the AI claimed to be)
        - actual_outcome: int 1 (correct) or 0 (wrong)

    eval_report: the hallucination eval report from eval_agent.py
    """

    print("\n" + "=" * 60)
    print("CONFIDENCE CALIBRATION AGENT — Stage 02: Evaluate")
    print("=" * 60)
    print("Calculating Brier score and calibration gap...\n")

    # Step 1 — Calculate Brier score from raw predictions
    brier = calculate_brier_score(ai_outputs)

    # Step 2 — Derive average stated confidence and estimated actual accuracy
    avg_stated = round(
        sum(p["stated_confidence"] for p in ai_outputs) / len(ai_outputs), 3
    ) if ai_outputs else 0.0

    avg_actual = round(
        sum(p["actual_outcome"] for p in ai_outputs) / len(ai_outputs), 3
    ) if ai_outputs else 0.0

    calibration_gap = round(abs(avg_stated - avg_actual), 3)

    # Step 3 — Ask LLM to reason over the calibration data and produce full report
    response = call_llm(
        system_prompt=CONFIDENCE_SCORING_PROMPT,
        user_message=f"""
Here is the calibration data for an AI feature:

Predictions made by the AI:
{json.dumps(ai_outputs, indent=2)}

Hallucination eval report from the eval agent:
{json.dumps(eval_report, indent=2)}

Calculated metrics:
- Average stated confidence: {avg_stated}
- Estimated actual accuracy: {avg_actual}
- Calibration gap: {calibration_gap}
- Brier score: {brier}

Produce a full confidence calibration report.
"""
    )

    report = parse_json_response(response)

    if not report:
        print("Error: Could not generate calibration report.")
        return {}

    # Step 4 — Inject our calculated values to ensure accuracy
    report["brier_score"] = brier
    report["stated_confidence"] = avg_stated
    report["estimated_actual_accuracy"] = avg_actual
    report["calibration_gap"] = calibration_gap

    # Step 5 — Save report
    os.makedirs("data", exist_ok=True)
    output_path = "data/confidence_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    # Step 6 — Print summary
    print(f"Stated confidence:        {report.get('stated_confidence')}")
    print(f"Actual accuracy:          {report.get('estimated_actual_accuracy')}")
    print(f"Calibration gap:          {report.get('calibration_gap')}")
    print(f"Brier score:              {report.get('brier_score')}")
    print(f"Trust score:              {report.get('trust_score')} / 10")
    print(f"Calibration verdict:      {report.get('calibration_verdict')}")
    print(f"\n✅ Confidence report saved to {output_path}")

    return report


if __name__ == "__main__":
    # Test case — AI ticket summariser made 5 statements with varying confidence
    # actual_outcome: 1 = correct, 0 = wrong
    ai_outputs = [
        {"statement": "Customer cannot log in since this morning",
         "stated_confidence": 0.95, "actual_outcome": 1},
        {"statement": "Customer has tried resetting password twice",
         "stated_confidence": 0.90, "actual_outcome": 1},
        {"statement": "Server outage reported internally since yesterday",
         "stated_confidence": 0.85, "actual_outcome": 0},   # hallucinated
        {"statement": "Customer affected for 3 days",
         "stated_confidence": 0.80, "actual_outcome": 0},   # hallucinated
        {"statement": "Customer requesting a full refund",
         "stated_confidence": 0.75, "actual_outcome": 0},   # hallucinated
    ]

    # Load the hallucination eval report saved by eval_agent.py
    eval_report_path = "data/hallucination_eval_report.json"
    if os.path.exists(eval_report_path):
        with open(eval_report_path, "r") as f:
            eval_report = json.load(f)
    else:
        eval_report = {"note": "No eval report found — run eval_agent.py first"}

    result = run_confidence_calibration(ai_outputs, eval_report)
    print("\nFull calibration report:")
    print(json.dumps(result, indent=2))