# agents/model_router.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm
from agents.cost_tracker import log_call

# ── Routing policy ─────────────────────────────────────────────────────────
DEFAULT_MODEL        = "gpt-4o-mini"
CAPABLE_MODEL        = "gpt-4o"
CONFIDENCE_THRESHOLD = 0.75

UPGRADE_ELIGIBLE_AGENTS = {
    "orchestrator",
    "decider",
    "critic"
}


def select_model(agent_name: str, confidence_score: float = 1.0) -> str:
    if agent_name in UPGRADE_ELIGIBLE_AGENTS and confidence_score < CONFIDENCE_THRESHOLD:
        return CAPABLE_MODEL
    return DEFAULT_MODEL


def routed_call(
    agent_name: str,
    system_prompt: str,
    user_message: str,
    confidence_score: float = 1.0,
    run_id: str = "UNKNOWN"
) -> str:
    """
    Wrapper around call_llm() that:
    1. Selects the right model based on agent and confidence
    2. Makes the LLM call — uses return_usage=True to get REAL token counts
    3. Logs real tokens and cost to the cost tracker
    Returns the LLM response as a string.
    """
    model = select_model(agent_name, confidence_score)

    if model == CAPABLE_MODEL:
        print(f"  🔼 Model upgrade: {agent_name} → {CAPABLE_MODEL} "
              f"(confidence {confidence_score} < {CONFIDENCE_THRESHOLD})")
    else:
        print(f"  ✓  Model: {agent_name} → {DEFAULT_MODEL}")

    # Real token counts from API — no more character estimation
    response, input_tokens, output_tokens = call_llm(
        system_prompt=system_prompt,
        user_message=user_message,
        model=model,
        return_usage=True
    )

    log_call(
        agent_name=agent_name,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        run_id=run_id
    )

    return response


if __name__ == "__main__":
    from agents.cost_tracker import print_cost_report

    print("\n" + "=" * 60)
    print("MODEL ROUTER — LLMOps Cost Intelligence")
    print("=" * 60)

    print("\nTest: routing logic only (no API calls)")
    low_confidence  = 0.327
    high_confidence = 0.85

    agents_to_test = [
        ("interview_agent", 1.0),
        ("synthesis_agent", 1.0),
        ("orchestrator",    low_confidence),
        ("decider",         low_confidence),
        ("critic",          low_confidence),
    ]

    print(f"\nLow confidence ({low_confidence}):")
    for agent, conf in agents_to_test:
        print(f"  {agent} → {select_model(agent, conf)}")

    print(f"\nHigh confidence ({high_confidence}):")
    for agent, conf in agents_to_test:
        print(f"  {agent} → {select_model(agent, high_confidence)}")

    print("\n" + "=" * 60)
    print(f"Default model:     {DEFAULT_MODEL}")
    print(f"Capable model:     {CAPABLE_MODEL}")
    print(f"Upgrade threshold: confidence < {CONFIDENCE_THRESHOLD}")
    print(f"Upgrade eligible:  {UPGRADE_ELIGIBLE_AGENTS}")
