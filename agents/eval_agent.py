# agents/eval_agent.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import HALLUCINATION_EVAL_PROMPT

def run_hallucination_eval(ai_output: str, source_context: str) -> dict:
    """
    Evaluates an AI feature output for hallucinations.
    - Faithfulness: is the output grounded in the source?
    - Factuality: is the output factually correct?
    Returns a full eval report card.
    """

    print("\n" + "="*60)
    print("HALLUCINATION EVAL AGENT — Stage 02: Evaluate")
    print("="*60)
    print("Evaluating AI output for hallucinations...\n")

    response = call_llm(
        system_prompt=HALLUCINATION_EVAL_PROMPT,
        user_message=f"""
AI Output to evaluate:
\"\"\"{ai_output}\"\"\"

Source context the AI output should be grounded in:
\"\"\"{source_context}\"\"\"
"""
    )

    report = parse_json_response(response)

    if not report:
        print("Error: Could not generate eval report.")
        return {}

    # Save report
    os.makedirs("data", exist_ok=True)
    output_path = "data/hallucination_eval_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"Faithfulness score:       {report.get('faithfulness_score')}")
    print(f"Factuality score:         {report.get('factuality_score')}")
    print(f"Overall hallucination rate: {report.get('overall_hallucination_rate')}")
    print(f"Eval verdict:             {report.get('eval_verdict')}")
    print(f"Flagged claims:           {len(report.get('flagged_claims', []))}")
    print(f"\n✅ Eval report saved to {output_path}")

    return report


if __name__ == "__main__":
    # Test case — AI summarised a support ticket incorrectly
    ai_output = """
    The customer is experiencing login issues due to a server outage on our end.
    Our systems have been down since yesterday and we expect resolution by 5pm today.
    The customer has been affected for 3 days and is requesting a full refund.
    """

    source_context = """
    Support ticket #4821:
    Customer reports they cannot log in since this morning.
    They have tried resetting their password twice.
    No server outage has been reported internally.
    Customer has not mentioned a refund.
    """

    result = run_hallucination_eval(ai_output, source_context)
    print("\nFull report:")
    print(json.dumps(result, indent=2))