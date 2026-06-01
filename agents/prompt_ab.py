# agents/prompt_ab.py
# Prompt Version Control — Day 13 hardened version
#
# Changes from Day 5:
#   1. Prompts versioned as files in prompts/versions/ (not hardcoded in dict)
#   2. Rollback logic — revert to any previous version with one call
#   3. Version history persisted to data/prompt_version_history.json
#   4. Active version loaded from file — survives process restarts
#   5. Promotion and rollback both logged with reason

import json
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import HALLUCINATION_EVAL_PROMPT

VERSIONS_DIR     = "prompts/versions"
VERSION_LOG_PATH = "data/prompt_version_history.json"


# ── Version file helpers ──────────────────────────────────────────────────

def _version_path(prompt_name: str, version: str) -> str:
    return os.path.join(VERSIONS_DIR, f"{prompt_name}_{version}.txt")


def _registry_path(prompt_name: str) -> str:
    return os.path.join(VERSIONS_DIR, f"{prompt_name}_registry.json")


def save_version(prompt_name: str, version: str, prompt_text: str) -> str:
    """Saves a prompt version as a .txt file. Returns the file path."""
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    path = _version_path(prompt_name, version)
    with open(path, "w") as f:
        f.write(prompt_text)
    print(f"[PromptVC] Saved {prompt_name} {version} → {path}")
    return path


def load_version(prompt_name: str, version: str) -> str:
    """Loads a prompt version from file."""
    path = _version_path(prompt_name, version)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt version not found: {path}")
    with open(path) as f:
        return f.read()


def get_registry(prompt_name: str) -> dict:
    """Loads the version registry for a prompt. Creates if missing."""
    path = _registry_path(prompt_name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"prompt_name": prompt_name, "active_version": None, "versions": []}


def save_registry(prompt_name: str, registry: dict) -> None:
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    with open(_registry_path(prompt_name), "w") as f:
        json.dump(registry, f, indent=2)


def register_version(prompt_name: str, version: str, description: str = "") -> None:
    """Adds a version to the registry without activating it."""
    registry = get_registry(prompt_name)
    versions = [v["version"] for v in registry["versions"]]
    if version not in versions:
        registry["versions"].append({
            "version":     version,
            "description": description,
            "created_at":  datetime.now().isoformat(),
        })
        save_registry(prompt_name, registry)


def get_active_prompt(prompt_name: str) -> tuple[str, str]:
    """Returns (version_tag, prompt_text) for the currently active version."""
    registry = get_registry(prompt_name)
    active = registry.get("active_version")
    if not active:
        raise ValueError(f"No active version set for '{prompt_name}'")
    return active, load_version(prompt_name, active)


# ── Promotion and rollback ────────────────────────────────────────────────

def _log_version_event(prompt_name: str, event: str, version: str, reason: str) -> None:
    os.makedirs("data", exist_ok=True)
    log = []
    if os.path.exists(VERSION_LOG_PATH):
        with open(VERSION_LOG_PATH) as f:
            log = json.load(f)
    log.append({
        "timestamp":   datetime.now().isoformat(),
        "prompt_name": prompt_name,
        "event":       event,
        "version":     version,
        "reason":      reason,
    })
    with open(VERSION_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def promote_version(prompt_name: str, version: str, reason: str = "") -> None:
    """Sets a version as active. Logs the promotion."""
    registry = get_registry(prompt_name)
    previous = registry.get("active_version", "none")
    registry["active_version"] = version
    registry["previous_version"] = previous
    save_registry(prompt_name, registry)
    _log_version_event(prompt_name, "PROMOTED", version, reason or f"Promoted over {previous}")
    print(f"[PromptVC] ✅ Promoted {prompt_name} → {version} (was: {previous})")


def rollback(prompt_name: str, reason: str = "") -> str:
    """
    Rolls back to the previous version.
    Returns the version rolled back to.
    """
    registry = get_registry(prompt_name)
    previous = registry.get("previous_version")

    if not previous:
        print(f"[PromptVC] ⚠️  No previous version to roll back to for '{prompt_name}'")
        return registry.get("active_version", "unknown")

    current = registry.get("active_version")
    registry["active_version"]  = previous
    registry["previous_version"] = current
    save_registry(prompt_name, registry)
    _log_version_event(prompt_name, "ROLLBACK", previous, reason or f"Rolled back from {current}")
    print(f"[PromptVC] 🔄 Rolled back {prompt_name}: {current} → {previous}")
    return previous


# ── Test set ──────────────────────────────────────────────────────────────

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


# ── Eval ──────────────────────────────────────────────────────────────────

def run_single_eval(prompt_template: str, test_case: dict) -> dict:
    filled_prompt = prompt_template.replace("{ticket}", test_case["ticket"])
    ai_summary = call_llm(system_prompt=filled_prompt, user_message=test_case["ticket"])
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
    eval_result["test_case"]  = test_case["ticket"][:80] + "..."
    return eval_result


def run_ab_eval(prompt_name: str = "ticket_summariser") -> dict:
    """
    Runs all registered versions against the test set.
    Promotes the winner. Logs the result.
    If winner is same as current active — no change needed.
    If loser was active — rollback is available via rollback().
    """
    print("\n" + "=" * 60)
    print("PROMPT A/B EVAL SYSTEM — Stage 02: Evaluate (Hardened)")
    print("=" * 60)
    print(f"Running A/B eval for: '{prompt_name}'\n")

    registry = get_registry(prompt_name)
    versions = registry.get("versions", [])

    if len(versions) < 2:
        print("Need at least 2 registered versions to run A/B eval.")
        return {}

    results = {}

    for v_entry in versions:
        version_tag = v_entry["version"]
        try:
            prompt_template = load_version(prompt_name, version_tag)
        except FileNotFoundError:
            print(f"  ⚠️  Version file missing for {version_tag} — skipping.")
            continue

        print(f"Testing {version_tag}...")
        version_scores = []

        for test_case in TEST_SET:
            score = run_single_eval(prompt_template, test_case)
            version_scores.append(score)

        avg_faithfulness  = round(sum(s.get("faithfulness_score", 0)       for s in version_scores) / len(version_scores), 3)
        avg_factuality    = round(sum(s.get("factuality_score", 0)          for s in version_scores) / len(version_scores), 3)
        avg_hallucination = round(sum(s.get("overall_hallucination_rate", 1) for s in version_scores) / len(version_scores), 3)
        pass_count        = sum(1 for s in version_scores if s.get("eval_verdict") == "PASS")

        results[version_tag] = {
            "version":               version_tag,
            "avg_faithfulness_score": avg_faithfulness,
            "avg_factuality_score":   avg_factuality,
            "avg_hallucination_rate": avg_hallucination,
            "pass_rate":              f"{pass_count}/{len(TEST_SET)}",
            "individual_runs":        version_scores,
        }

        print(f"  Faithfulness: {avg_faithfulness} | Factuality: {avg_factuality} | "
              f"Hallucination: {avg_hallucination} | Pass: {pass_count}/{len(TEST_SET)}")

    if not results:
        print("No versions could be evaluated.")
        return {}

    # Winner = lowest hallucination rate, tiebreak = highest faithfulness
    winner_tag = min(
        results,
        key=lambda v: (results[v]["avg_hallucination_rate"], -results[v]["avg_faithfulness_score"])
    )
    losers = [v for v in results if v != winner_tag]
    loser_tag = losers[0] if losers else None

    print(f"\n🏆 Winner: {winner_tag}")

    # Promote winner
    reason = (
        f"{winner_tag} had lower hallucination rate "
        f"({results[winner_tag]['avg_hallucination_rate']} vs "
        f"{results[loser_tag]['avg_hallucination_rate'] if loser_tag else 'N/A'})"
    )
    promote_version(prompt_name, winner_tag, reason)

    report = {
        "prompt_name":     prompt_name,
        "versions_tested": list(results.keys()),
        "winner":          winner_tag,
        "loser":           loser_tag,
        "promotion_reason": reason,
        "scores": {v: {
            "avg_faithfulness_score":  results[v]["avg_faithfulness_score"],
            "avg_factuality_score":    results[v]["avg_factuality_score"],
            "avg_hallucination_rate":  results[v]["avg_hallucination_rate"],
            "pass_rate":               results[v]["pass_rate"],
        } for v in results}
    }

    os.makedirs("data", exist_ok=True)
    with open("data/prompt_ab_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ A/B eval report saved to data/prompt_ab_report.json")
    return report


# ── Seed helper (run once to migrate from hardcoded to file-based) ─────────

def seed_versions():
    """
    Creates v1, v2, v3 prompt files for ticket_summariser.
    Run once to initialise the version system.
    """
    v1 = """You are an AI support assistant. Summarise the customer support ticket below.
Be concise and accurate.
Ticket: {ticket}"""

    v2 = """You are an AI support assistant. Summarise ONLY what is explicitly stated in the ticket below.
Do not infer, assume, or add any information not present in the ticket.
If something is unclear, say so — do not guess.
Ticket: {ticket}"""

    v3 = """You are an AI support assistant. Your task is to produce a one-paragraph summary of the support ticket below.

Rules:
1. Include ONLY facts explicitly stated in the ticket
2. Do not infer intent, emotion, or context not written in the ticket
3. If the customer has NOT requested a refund, do not mention refunds
4. End with one sentence stating the next action required
5. Maximum 3 sentences total

Ticket: {ticket}"""

    for version, text in [("v1", v1), ("v2", v2), ("v3", v3)]:
        save_version("ticket_summariser", version, text)
        register_version("ticket_summariser", version,
                         description={"v1": "Basic summariser", "v2": "Strict factual summariser", "v3": "Structured 3-sentence summariser with action item"}[version])

    # Set v2 as active by default (current winner from Day 5)
    promote_version("ticket_summariser", "v2", "Initial promotion — v2 was Day 5 winner")
    print("\n✅ Versions seeded: v1, v2, v3 — v2 set as active.")


if __name__ == "__main__":
    import sys

    if "--seed" in sys.argv:
        seed_versions()
    elif "--rollback" in sys.argv:
        rolled_back_to = rollback("ticket_summariser", reason="Manual rollback test")
        print(f"Rolled back to: {rolled_back_to}")
    elif "--active" in sys.argv:
        version, text = get_active_prompt("ticket_summariser")
        print(f"Active version: {version}")
        print(f"Prompt:\n{text}")
    else:
        # Seed first if versions don't exist
        if not os.path.exists(_registry_path("ticket_summariser")):
            print("No versions found — seeding first...")
            seed_versions()
        result = run_ab_eval("ticket_summariser")
        print("\nFull A/B eval report:")
        print(json.dumps(result, indent=2))
