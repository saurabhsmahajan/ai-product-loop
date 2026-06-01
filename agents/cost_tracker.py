# agents/cost_tracker.py

import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ── Pricing per 1M tokens (as of May 2026) ────────────────────────────────
MODEL_PRICING = {
    "gpt-4o-mini": {
        "input":  0.15,   # $ per 1M input tokens
        "output": 0.60,   # $ per 1M output tokens
    },
    "gpt-4o": {
        "input":  2.50,   # $ per 1M input tokens
        "output": 10.00,  # $ per 1M output tokens
    }
}

COST_LOG_PATH = "data/cost_log.json"


def load_cost_log() -> list:
    if os.path.exists(COST_LOG_PATH):
        with open(COST_LOG_PATH, "r") as f:
            return json.load(f)
    return []


def save_cost_log(log: list) -> None:
    os.makedirs("data", exist_ok=True)
    with open(COST_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """Calculates the cost of a single LLM call in USD."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
    input_cost  = (input_tokens  / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def log_call(
    agent_name: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    run_id: str = "UNKNOWN"
) -> dict:
    """Logs a single LLM call with token usage and cost."""
    cost = calculate_cost(model, input_tokens, output_tokens)

    entry = {
        "agent_name": agent_name,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": cost,
        "run_id": run_id
    }

    log = load_cost_log()
    log.append(entry)
    save_cost_log(log)

    return entry


def get_cost_report() -> dict:
    """Returns a full cost breakdown by agent and model."""
    log = load_cost_log()

    if not log:
        return {"total_calls": 0, "total_cost_usd": 0}

    total_cost = sum(e["cost_usd"] for e in log)
    total_tokens = sum(e["total_tokens"] for e in log)

    # Cost by agent
    by_agent = {}
    for e in log:
        agent = e["agent_name"]
        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "tokens": 0, "cost_usd": 0}
        by_agent[agent]["calls"]    += 1
        by_agent[agent]["tokens"]   += e["total_tokens"]
        by_agent[agent]["cost_usd"] += e["cost_usd"]

    # Round agent costs
    for agent in by_agent:
        by_agent[agent]["cost_usd"] = round(by_agent[agent]["cost_usd"], 6)

    # Cost by model
    by_model = {}
    for e in log:
        model = e["model"]
        if model not in by_model:
            by_model[model] = {"calls": 0, "tokens": 0, "cost_usd": 0}
        by_model[model]["calls"]    += 1
        by_model[model]["tokens"]   += e["total_tokens"]
        by_model[model]["cost_usd"] += e["cost_usd"]

    for model in by_model:
        by_model[model]["cost_usd"] = round(by_model[model]["cost_usd"], 6)

    return {
        "total_calls":     len(log),
        "total_tokens":    total_tokens,
        "total_cost_usd":  round(total_cost, 6),
        "cost_by_agent":   by_agent,
        "cost_by_model":   by_model,
    }


def print_cost_report() -> None:
    report = get_cost_report()

    print("\n" + "=" * 60)
    print("COST REPORT — LLMOps Intelligence")
    print("=" * 60)
    print(f"Total calls:     {report['total_calls']}")
    print(f"Total tokens:    {report.get('total_tokens', 0)}")
    print(f"Total cost:      ${report['total_cost_usd']}")

    print("\nCost by agent:")
    for agent, data in report.get("cost_by_agent", {}).items():
        print(f"  {agent}: {data['calls']} calls | "
              f"{data['tokens']} tokens | ${data['cost_usd']}")

    print("\nCost by model:")
    for model, data in report.get("cost_by_model", {}).items():
        print(f"  {model}: {data['calls']} calls | "
              f"{data['tokens']} tokens | ${data['cost_usd']}")


if __name__ == "__main__":
    # Simulate logging a few agent calls
    print("Logging test calls...\n")

    log_call("interview_agent",   "gpt-4o-mini", 450,  280, "RUN_TEST_001")
    log_call("synthesis_agent",   "gpt-4o-mini", 800,  420, "RUN_TEST_001")
    log_call("persona_agent",     "gpt-4o-mini", 600,  350, "RUN_TEST_001")
    log_call("eval_agent",        "gpt-4o-mini", 500,  300, "RUN_TEST_001")
    log_call("governance_agent",  "gpt-4o-mini", 480,  290, "RUN_TEST_001")
    log_call("orchestrator",      "gpt-4o-mini", 900,  500, "RUN_TEST_001")
    log_call("decider",           "gpt-4o-mini", 1200, 600, "RUN_TEST_001")
    log_call("critic",            "gpt-4o-mini", 1100, 550, "RUN_TEST_001")

    print_cost_report()
    print("\nFull report JSON:")
    print(json.dumps(get_cost_report(), indent=2))