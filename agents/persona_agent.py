import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm

PERSONAS = [
    {"role": "Enterprise Buyer", "context": "Fortune 500, procurement-driven, risk-averse"},
    {"role": "SMB Owner", "context": "10-person company, cost-sensitive, fast decisions"},
    {"role": "End User", "context": "Daily hands-on user, cares about speed and simplicity"},
    {"role": "IT / Security Lead", "context": "Controls access, worried about data leakage"},
    {"role": "Legal / Compliance", "context": "EU AI Act aware, flags PII and liability risk"},
    {"role": "Champion / Power User", "context": "Early adopter, high engagement, evangelises internally"},
]

def simulate_personas(feature_hypothesis: str) -> dict:
    results = []

    for persona in PERSONAS:
        prompt = f"""
You are simulating a {persona['role']}.
Context: {persona['context']}

A product team is proposing this feature:
\"\"\"{feature_hypothesis}\"\"\"

Respond ONLY in this exact JSON format — no extra text:
{{
  "persona": "{persona['role']}",
  "reaction_score": <integer 0-10>,
  "first_reaction": "<one sentence gut reaction>",
  "objections": ["<objection 1>", "<objection 2>"],
  "champion_or_blocker": "<champion | neutral | blocker>",
  "key_quote": "<one sentence this person would say in a meeting>"
}}
"""
        response = call_llm(
            system_prompt="You are a product research simulator. Output only valid JSON.",
            user_message=prompt
        )

        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            parsed = {"persona": persona["role"], "error": "Failed to parse", "raw": response}

        results.append(parsed)

    summary = {
        "feature_hypothesis": feature_hypothesis,
        "personas": results,
        "avg_reaction_score": round(
            sum(p.get("reaction_score", 0) for p in results if "reaction_score" in p) / len(results), 2
        ),
        "blockers": [p["persona"] for p in results if p.get("champion_or_blocker") == "blocker"],
        "champions": [p["persona"] for p in results if p.get("champion_or_blocker") == "champion"],
    }

    return summary


if __name__ == "__main__":
    hypothesis = "An AI assistant that automatically summarises customer support tickets and suggests responses to agents."
    result = simulate_personas(hypothesis)
    print(json.dumps(result, indent=2))