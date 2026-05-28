# agents/decider.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import DECIDER_PROMPT


def run_decider(orchestrator_report: dict, feature_hypothesis: str) -> dict:
    """
    Receives the full Orchestrator context package.
    Produces a documented GO / NO_GO / CONDITIONAL_GO decision
    with confidence score and full reasoning chain.
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
    print(f"Decision:          {report.get('decision')}")
    print(f"Confidence score:  {report.get('confidence_score')}")
    print(f"Escalate to human: {report.get('escalate_to_human')}")
    print(f"Key risks:         {report.get('key_risks')}")
    print(f"\nReasoning chain:")
    for step in report.get("reasoning_chain", []):
        print(f"  {step}")

    print(f"\n✅ Decider report saved to {output_path}")
    return report


if __name__ == "__main__":
    # Load the orchestrator report
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