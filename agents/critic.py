# agents/critic.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import CRITIC_PROMPT, DECIDER_PROMPT

try:
    from agents.slack_notifier import send_slack_alert
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

MAX_REVISION_PASSES = 2


def run_critic(decider_report: dict) -> dict:
    """Reviews the Decider's reasoning and scores it."""

    print("\n" + "=" * 60)
    print("CRITIC AGENT — Reflexion Loop")
    print("=" * 60)

    response = call_llm(
        system_prompt=CRITIC_PROMPT,
        user_message=f"""
Review this go/no-go decision and reasoning chain:

{json.dumps(decider_report, indent=2)}

Score the quality of the reasoning and produce your critique.
"""
    )

    report = parse_json_response(response)

    if not report:
        print("Error: Could not generate critique.")
        return {}

    print(f"Critique score:  {report.get('critique_score')}")
    print(f"Verdict:         {report.get('verdict')}")
    print(f"Strengths:       {report.get('strengths')}")
    print(f"Weaknesses:      {report.get('weaknesses')}")
    print(f"Missing signals: {report.get('missing_signals')}")

    return report


def run_reflexion_loop(
    decider_report: dict,
    feature_hypothesis: str,
    orchestrator_report: dict
) -> dict:
    """
    Full Reflexion Loop:
    1. Critic reviews Decider's reasoning
    2. If critique score >= 0.7 — APPROVE, done
    3. If critique score < 0.7 — send back to Decider with revision instructions
    4. After MAX_REVISION_PASSES — escalate to human, fire Slack alert (Day 11)
    """

    print("\n" + "=" * 60)
    print("REFLEXION LOOP — Stage 03: Decide")
    print("=" * 60)

    current_decision = decider_report.copy()
    revision_history = []

    for pass_num in range(1, MAX_REVISION_PASSES + 1):
        print(f"\n--- Reflexion Pass {pass_num} of {MAX_REVISION_PASSES} ---")

        critique = run_critic(current_decision)
        if not critique:
            break

        critique_score = critique.get("critique_score", 0)
        verdict = critique.get("verdict", "REVISE")

        revision_history.append({
            "pass": pass_num,
            "critique_score": critique_score,
            "verdict": verdict,
            "weaknesses": critique.get("weaknesses", []),
            "missing_signals": critique.get("missing_signals", [])
        })

        if verdict == "APPROVE":
            print(f"\n✅ Reflexion Loop APPROVED on pass {pass_num}.")
            print(f"   Critique score: {critique_score} — above 0.7 threshold.")
            break

        if pass_num < MAX_REVISION_PASSES:
            print(f"\n🔄 Critique score {critique_score} below 0.7 — sending back for revision.")
            print(f"   Revision instructions: {critique.get('revision_instructions')}")

            revised_response = call_llm(
                system_prompt=DECIDER_PROMPT,
                user_message=f"""
Your previous decision was critiqued. Revise it based on the feedback below.

Feature hypothesis:
\"\"\"{feature_hypothesis}\"\"\"

Your previous decision:
{json.dumps(current_decision, indent=2)}

Critic's feedback:
{json.dumps(critique, indent=2)}

Full pipeline context:
{json.dumps(orchestrator_report, indent=2)}

Produce a revised GO / NO_GO / CONDITIONAL_GO decision addressing all critique points.
"""
            )

            revised_decision = parse_json_response(revised_response)
            if revised_decision:
                current_decision = revised_decision
                print(f"   Revised decision: {current_decision.get('decision')}")
                print(f"   Revised confidence: {current_decision.get('confidence_score')}")
            else:
                print("   Revision failed to parse — keeping previous decision.")

        else:
            # Max passes reached — escalate and alert
            print(f"\n⚠️  Max revision passes ({MAX_REVISION_PASSES}) reached.")
            print(f"   Critique score still {critique_score} — escalating to human.")
            current_decision["escalate_to_human"] = True
            current_decision["escalation_reason"] = (
                f"Critique score {critique_score} remained below 0.7 after "
                f"{MAX_REVISION_PASSES} revision passes. Human review required."
            )

            # Slack alert on Reflexion escalation (Day 11)
            if SLACK_AVAILABLE:
                send_slack_alert(
                    message=(
                        f"*Reflexion Loop escalated to human* 🔴\n"
                        f"Feature: _{feature_hypothesis[:60]}_\n"
                        f"Critique score after {MAX_REVISION_PASSES} passes: `{critique_score}`\n"
                        f"Weaknesses: {', '.join(critique.get('weaknesses', [])[:2])}"
                    ),
                    alert_type="escalation"
                )
                print("📨 Escalation alert sent to Slack.")

    # Build final report
    final_report = {
        "final_decision": current_decision,
        "revision_passes": len(revision_history),
        "revision_history": revision_history,
        "escalate_to_human": current_decision.get("escalate_to_human", False),
        "escalation_reason": current_decision.get("escalation_reason", "")
    }

    os.makedirs("data", exist_ok=True)
    output_path = "data/reflexion_report.json"
    with open(output_path, "w") as f:
        json.dump(final_report, f, indent=2)

    print(f"\n✅ Reflexion report saved to {output_path}")
    print(f"\nFinal decision: {current_decision.get('decision')}")
    print(f"Escalate to human: {current_decision.get('escalate_to_human')}")

    return final_report


if __name__ == "__main__":
    decider_path = "data/decider_report.json"
    orch_path    = "data/orchestrator_report.json"

    if not os.path.exists(decider_path):
        print("Decider report not found — run decider.py first.")
        exit(1)
    if not os.path.exists(orch_path):
        print("Orchestrator report not found — run orchestrator.py first.")
        exit(1)

    with open(decider_path, "r") as f:
        decider_report = json.load(f)
    with open(orch_path, "r") as f:
        orchestrator_report = json.load(f)

    hypothesis = "An AI assistant that automatically summarises customer support tickets and suggests responses to agents."
    result = run_reflexion_loop(decider_report, hypothesis, orchestrator_report)
    print("\nFull reflexion report:")
    print(json.dumps(result, indent=2))
