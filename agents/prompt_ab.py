# agents/prompt_ab.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import HALLUCINATION_EVAL_PROMPT


# ── Prompt versions registry ───────────────────────────────────────────────
# Each version is stored here with a version tag and the prompt text.
# When a new version wins, it gets marked as active = True.

PROMPT_VERSIONS = {
    "ticket_summariser": [
        {
            "version": "v1",
            "active": False,
            "prompt": """
You are an AI support assistant. Summarise the customer support ticket below.
Be concise and accurate.
Ticket: {ticket}
""".strip()
        },
        {
            "version": "v2",
            "active": True,
            "prompt": """
You are an AI support assistant. Summarise ONLY what is explicitly stated in the ticket below.
Do not infer, assume, or add any information not present in the ticket.
If something is unclear, say so — do not guess.
Ticket: {ticket}
""".strip()
        }
    ]
}


# ── Test set ───────────────────────────────────────────────────────────────
# Same test cases run against both prompt versions.
# ground_truth is what a correct summary must reflect.

TEST_SET = [
    {
        "ticket": "Customer says they cannot log in since this morning. They have tried resetting their password twice. No refund has been mentioned.",
        "ground_truth": "Customer cannot log in since this morning. Password reset attempted twice. No refund requested."
    },
    {
        "ticket": "User reports the dashboard is loading slowly. They are on a Windows 11 machine using Chrome. No error message shown.",
        "ground_truth": "Dashboard loading slowly on Windows 11 with Chrome. No error message reported."
    },
    {
        "ticket": "Customer wants to upgrade their subscription from Basic to Pro. They asked about pricing for annual billing.",
        "ground_truth": "Customer wants to upgrade from Basic to Pro. Asked about annual billing pricing."
    }
]


def run_single_eval(prompt_template: str, test_case: dict) -> dict:
    """
    Runs one prompt version against one test case.
    Returns hallucination eval scores for that run.
    """
    filled_prompt = prompt_template.replace("{ticket}", test_case["ticket"])

    # Get AI summary using this prompt version
    ai_summary = call_llm(
        system_prompt=filled_prompt,
        user_message=test_case["ticket"]
    )

    # Evaluate the summary against ground truth
    eval_response = call_llm(
        system_prompt=HALLUCINATION_EVAL_PROMPT,
        user_message=f"""
AI Output to evaluate:
\"\"\"{ai_summary}\"\"\"

Source context the AI output should be grounded in:
\"\"\"{test_case['ground_truth']}\"\"\"
"""
    )

    eval_result = parse_json_response(eval_response)
    eval_result["ai_summary"] = ai_summary
    eval_result["test_case"] = test_case["ticket"][:80] + "..."

    return eval_result


def run_ab_eval(prompt_name: str = "ticket_summariser") -> dict:
    """
    Runs all versions of a named prompt against the full test set.
    Scores each version and promotes the winner.
    """

    print("\n" + "=" * 60)
    print("PROMPT A/B EVAL SYSTEM — Stage 02: Evaluate")
    print("=" * 60)
    print(f"Running A/B eval for prompt: '{prompt_name}'\n")

    versions = PROMPT_VERSIONS.get(prompt_name)
    if not versions or len(versions) < 2:
        print("Need at least 2 prompt versions to run A/B eval.")
        return {}

    results = {}

    for version_entry in versions:
        version_tag = version_entry["version"]
        prompt_template = version_entry["prompt"]

        print(f"Testing {version_tag}...")
        version_scores = []

        for test_case in TEST_SET:
            score = run_single_eval(prompt_template, test_case)
            version_scores.append(score)

        # Aggregate scores across test cases
        avg_faithfulness = round(
            sum(s.get("faithfulness_score", 0) for s in version_scores) / len(version_scores), 3
        )
        avg_factuality = round(
            sum(s.get("factuality_score", 0) for s in version_scores) / len(version_scores), 3
        )
        avg_hallucination = round(
            sum(s.get("overall_hallucination_rate", 1) for s in version_scores) / len(version_scores), 3
        )
        pass_count = sum(1 for s in version_scores if s.get("eval_verdict") == "PASS")

        results[version_tag] = {
            "version": version_tag,
            "avg_faithfulness_score": avg_faithfulness,
            "avg_factuality_score": avg_factuality,
            "avg_hallucination_rate": avg_hallucination,
            "pass_rate": f"{pass_count}/{len(TEST_SET)}",
            "individual_runs": version_scores
        }

        print(f"  Faithfulness: {avg_faithfulness} | Factuality: {avg_factuality} | "
              f"Hallucination rate: {avg_hallucination} | Pass: {pass_count}/{len(TEST_SET)}")

    # ── Determine winner ───────────────────────────────────────────────────
    # Primary metric: lowest hallucination rate
    # Tiebreaker: highest faithfulness score
    winner_tag = min(
        results,
        key=lambda v: (
            results[v]["avg_hallucination_rate"],
            -results[v]["avg_faithfulness_score"]
        )
    )

    loser_tag = [v for v in results if v != winner_tag][0]

    print(f"\n🏆 Winner: {winner_tag} (lower hallucination rate)")
    print(f"   Promoting {winner_tag} as active prompt.")

    # Update active flags in registry
    for entry in PROMPT_VERSIONS[prompt_name]:
        entry["active"] = (entry["version"] == winner_tag)

    # ── Build final report ─────────────────────────────────────────────────
    report = {
        "prompt_name": prompt_name,
        "versions_tested": list(results.keys()),
        "winner": winner_tag,
        "loser": loser_tag,
        "promotion_reason": f"{winner_tag} had lower hallucination rate "
                            f"({results[winner_tag]['avg_hallucination_rate']} vs "
                            f"{results[loser_tag]['avg_hallucination_rate']})",
        "scores": {v: {
            "avg_faithfulness_score": results[v]["avg_faithfulness_score"],
            "avg_factuality_score": results[v]["avg_factuality_score"],
            "avg_hallucination_rate": results[v]["avg_hallucination_rate"],
            "pass_rate": results[v]["pass_rate"]
        } for v in results}
    }

    # Save report
    os.makedirs("data", exist_ok=True)
    output_path = "data/prompt_ab_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ A/B eval report saved to {output_path}")
    return report


if __name__ == "__main__":
    result = run_ab_eval("ticket_summariser")
    print("\nFull A/B eval report:")
    print(json.dumps(result, indent=2))