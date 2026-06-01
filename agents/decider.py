# agents/decider.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import DECIDER_PROMPT

try:
    from agents.slack_notifier import send_slack_alert
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False


def run_decider(orchestrator_report: dict, feature_hypothesis: str) -> dict:
    """
    Receives the full Orchestrator context package.
    Produces a documented GO / NO_GO / CONDITIONAL_GO decision
    with confidence score and full reasoning chain.
    Fires a Slack alert after the decision is saved (Day 11).
    """

    print("\n" + "=" * 60)
    print("DECIDER AGENT — Stage 03: Decide")
    print("=" * 60)
    print("Reasoning over all pipeline signals...\n")

    response = call_llm(
        system_prompt=DECIDER_PROMPT,
        user_message=f"""
Feature hypothesis:
\"\"\"{feature_hypothesis}\"\"\"

Full orchestrator report:
{json.dumps(orchestrator_report, indent=2)}

Produce a documented GO / NO_GO / CONDITIONAL_GO decision.
"""
    )

    report = parse_json_response(response)

    if not report:
        print("Error: Could not generate decision report.")
        return {}

    # Save report
    os.makedirs("data", exist_ok=True)
    output_path = "data/decider_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    decision    = report.get("decision")
    confidence  = report.get("confidence_score")
    escalate    = report.get("escalate_to_human")

    print(f"Decision:          {decision}")
    print(f"Confidence score:  {confidence}")
    print(f"Escalate to human: {escalate}")
    print(f"Key risks:         {report.get('key_risks')}")
    print(f"\nReasoning chain:")
    for step in report.get("reasoning_chain", []):
        print(f"  {step}")
    print(f"\n✅ Decider report saved to {output_path}")

    # Slack alert (Day 11)
    if SLACK_AVAILABLE:
        if escalate:
            alert_type = "escalation"
            msg = (
                f"*Decision: ESCALATED TO HUMAN*\n"
                f"Feature: _{feature_hypothesis[:60]}_\n"
                f"Confidence: `{confidence}` — below threshold after reasoning.\n"
                f"Reason: {report.get('escalation_reason', 'N/A')}"
            )
        else:
            alert_type = "go" if decision == "GO" else "no-go"
            msg = (
                f"*Decision: {decision}*\n"
                f"Feature: _{feature_hypothesis[:60]}_\n"
                f"Confidence: `{confidence}`\n"
                f"Key risks: {', '.join(report.get('key_risks', [])[:2])}"
            )
        send_slack_alert(msg, alert_type=alert_type)
        print("📨 Slack alert sent.")

    return report


if __name__ == "__main__":
    orch_path = "data/orchestrator_report.json"
    if not os.path.exists(orch_path):
        print("Orchestrator report not found — run orchestrator.py first.")
        exit(1)

    with open(orch_path, "r") as f:
        orchestrator_report = json.load(f)

    hypothesis = "An AI assistant that automatically summarises customer support tickets and suggests responses to agents."
    result = run_decider(orchestrator_report, hypothesis)
    print("\nFull decider report:")
    print(json.dumps(result, indent=2))
