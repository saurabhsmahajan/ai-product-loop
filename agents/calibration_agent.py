# agents/calibration_agent.py
# Calibration Analysis Agent — Day 12
#
# Reviews the accumulated audit trail and recalibrates confidence thresholds.
# Answers the question: "Is our system's confidence well-calibrated against
# real outcomes, and should we adjust the escalation threshold?"

import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import CALIBRATION_AGENT_PROMPT
from memory.audit_logger import load_audit_trail, get_audit_summary

# Current thresholds (from orchestrator + decider)
CURRENT_THRESHOLDS = {
    "orchestrator_escalation": 0.60,   # below this → HUMAN_ESCALATION
    "decider_escalation":      0.70,   # below this → escalate_to_human
    "reflexion_critique":      0.70,   # below this → REVISE
    "model_upgrade":           0.75,   # below this → use gpt-4o
}


def analyse_calibration() -> dict:
    """
    Reads the audit trail, calculates calibration metrics,
    asks the LLM to recommend threshold adjustments,
    and saves the calibration report.
    """

    print("\n" + "=" * 60)
    print("CALIBRATION ANALYSIS AGENT — Day 12")
    print("=" * 60)

    trail = load_audit_trail()
    summary = get_audit_summary()

    print(f"Audit trail entries: {len(trail)}")
    print(f"Avg confidence: {summary.get('avg_confidence_score', 'N/A')}")
    print(f"Escalation rate: {summary.get('escalation_rate', 'N/A')}")

    if len(trail) < 2:
        print("⚠️  Not enough audit data yet — need at least 2 decisions to calibrate.")
        print("   Run the pipeline a few more times, then re-run calibration.")
        report = {
            "status": "insufficient_data",
            "entries_available": len(trail),
            "entries_needed": 2,
            "message": "Run the pipeline more times to accumulate calibration data.",
            "current_thresholds": CURRENT_THRESHOLDS,
            "recommended_thresholds": CURRENT_THRESHOLDS,
            "threshold_changes": [],
        }
        _save_report(report)
        return report

    # Build calibration dataset from audit trail
    calibration_data = []
    for entry in trail:
        calibration_data.append({
            "decision":        entry.get("decision"),
            "confidence":      entry.get("confidence_score"),
            "escalated":       entry.get("escalated_to_human"),
            "outcome":         entry.get("outcome"),
            "agent":           entry.get("agent_name"),
        })

    # Calculate Brier score if outcomes are known
    resolved = [e for e in calibration_data if e["outcome"] in ("CORRECT", "INCORRECT")]
    brier_score = None
    if resolved:
        brier_score = round(
            sum(
                (e["confidence"] - (1 if e["outcome"] == "CORRECT" else 0)) ** 2
                for e in resolved
            ) / len(resolved), 4
        )

    # Escalation analysis
    escalated = [e for e in calibration_data if e["escalated"]]
    non_escalated = [e for e in calibration_data if not e["escalated"]]
    avg_conf_escalated = round(
        sum(e["confidence"] for e in escalated) / len(escalated), 3
    ) if escalated else None
    avg_conf_non_escalated = round(
        sum(e["confidence"] for e in non_escalated) / len(non_escalated), 3
    ) if non_escalated else None

    calibration_metrics = {
        "total_decisions":        len(calibration_data),
        "resolved_outcomes":      len(resolved),
        "brier_score":            brier_score,
        "avg_confidence_all":     summary.get("avg_confidence_score"),
        "escalation_rate":        summary.get("escalation_rate"),
        "avg_conf_escalated":     avg_conf_escalated,
        "avg_conf_non_escalated": avg_conf_non_escalated,
        "decision_breakdown":     summary.get("decision_breakdown"),
        "outcome_breakdown":      summary.get("outcome_breakdown"),
    }

    print(f"\nCalibration metrics:")
    print(f"  Brier score: {brier_score} (lower is better, 0 = perfect)")
    print(f"  Avg confidence (escalated): {avg_conf_escalated}")
    print(f"  Avg confidence (not escalated): {avg_conf_non_escalated}")

    # Ask LLM to analyse and recommend threshold adjustments
    print("\nAsking LLM to recommend threshold adjustments...")
    response = call_llm(
        system_prompt=CALIBRATION_AGENT_PROMPT,
        user_message=f"""
Current threshold settings:
{json.dumps(CURRENT_THRESHOLDS, indent=2)}

Calibration metrics from audit trail:
{json.dumps(calibration_metrics, indent=2)}

Full calibration dataset:
{json.dumps(calibration_data, indent=2)}

Analyse the calibration data and recommend threshold adjustments.
"""
    )

    llm_report = parse_json_response(response)
    if not llm_report:
        llm_report = {"error": "Could not parse LLM calibration report"}

    # Build final report
    report = {
        "status":                  "complete",
        "analysed_at":             __import__("datetime").datetime.now().isoformat(),
        "entries_analysed":        len(trail),
        "calibration_metrics":     calibration_metrics,
        "current_thresholds":      CURRENT_THRESHOLDS,
        "recommended_thresholds":  llm_report.get("recommended_thresholds", CURRENT_THRESHOLDS),
        "threshold_changes":       llm_report.get("threshold_changes", []),
        "calibration_verdict":     llm_report.get("calibration_verdict", "INSUFFICIENT_DATA"),
        "reasoning":               llm_report.get("reasoning", ""),
        "action_required":         llm_report.get("action_required", False),
    }

    _save_report(report)

    print(f"\nCalibration verdict: {report['calibration_verdict']}")
    print(f"Action required: {report['action_required']}")
    if report["threshold_changes"]:
        print("Threshold changes recommended:")
        for change in report["threshold_changes"]:
            print(f"  {change}")

    return report


def _save_report(report: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open("data/calibration_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Calibration report saved to data/calibration_report.json")


if __name__ == "__main__":
    result = analyse_calibration()
    print("\nFull calibration report:")
    print(json.dumps(result, indent=2))
