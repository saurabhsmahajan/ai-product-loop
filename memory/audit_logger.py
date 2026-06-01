# memory/audit_logger.py

import json
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


AUDIT_LOG_PATH = "data/audit_trail.json"


def load_audit_trail() -> list:
    """Loads the existing audit trail or returns empty list."""
    if os.path.exists(AUDIT_LOG_PATH):
        with open(AUDIT_LOG_PATH, "r") as f:
            return json.load(f)
    return []


def save_audit_trail(trail: list) -> None:
    """Saves the full audit trail to disk."""
    os.makedirs("data", exist_ok=True)
    with open(AUDIT_LOG_PATH, "w") as f:
        json.dump(trail, f, indent=2)


def log_decision(
    run_id: str,
    feature: str,
    stage: str,
    agent_name: str,
    input_signals: dict,
    reasoning_chain: list,
    decision: str,
    confidence_score: float,
    escalated_to_human: bool,
    model_used: str = "gpt-4o-mini",
    tokens_consumed: int = 0,
    outcome: str = "PENDING"
) -> dict:
    """
    Logs a single agent decision to the audit trail.

    outcome: PENDING until post-launch data arrives.
             Update to CORRECT or INCORRECT once real outcome is known.
    """

    entry = {
        "log_id": f"LOG_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "run_id": run_id,
        "logged_at": datetime.now().isoformat(),
        "feature": feature,
        "stage": stage,
        "agent_name": agent_name,
        "input_signals": input_signals,
        "reasoning_chain": reasoning_chain,
        "decision": decision,
        "confidence_score": confidence_score,
        "escalated_to_human": escalated_to_human,
        "model_used": model_used,
        "tokens_consumed": tokens_consumed,
        "outcome": outcome,
        "outcome_notes": ""
    }

    trail = load_audit_trail()
    trail.append(entry)
    save_audit_trail(trail)

    return entry


def update_outcome(log_id: str, outcome: str, notes: str = "") -> bool:
    """
    Updates the outcome of a logged decision once real-world data arrives.
    outcome: CORRECT | INCORRECT | PARTIALLY_CORRECT
    """
    trail = load_audit_trail()

    for entry in trail:
        if entry["log_id"] == log_id:
            entry["outcome"] = outcome
            entry["outcome_notes"] = notes
            save_audit_trail(trail)
            print(f"✅ Updated outcome for {log_id}: {outcome}")
            return True

    print(f"⚠️  Log entry {log_id} not found.")
    return False


def get_audit_summary() -> dict:
    """
    Returns a summary of all logged decisions.
    Used by the Calibration Analysis Agent on Day 12.
    """
    trail = load_audit_trail()

    if not trail:
        return {"total_decisions": 0}

    decisions = [e["decision"] for e in trail]
    outcomes = [e["outcome"] for e in trail]
    confidences = [e["confidence_score"] for e in trail]
    escalations = [e for e in trail if e["escalated_to_human"]]

    return {
        "total_decisions": len(trail),
        "decision_breakdown": {
            "GO": decisions.count("GO"),
            "NO_GO": decisions.count("NO_GO"),
            "CONDITIONAL_GO": decisions.count("CONDITIONAL_GO"),
        },
        "outcome_breakdown": {
            "PENDING": outcomes.count("PENDING"),
            "CORRECT": outcomes.count("CORRECT"),
            "INCORRECT": outcomes.count("INCORRECT"),
            "PARTIALLY_CORRECT": outcomes.count("PARTIALLY_CORRECT"),
        },
        "avg_confidence_score": round(sum(confidences) / len(confidences), 3),
        "escalation_rate": round(len(escalations) / len(trail), 3),
        "total_tokens_consumed": sum(e["tokens_consumed"] for e in trail),
    }


def print_audit_trail() -> None:
    """Prints a readable summary of the full audit trail."""
    trail = load_audit_trail()

    print("\n" + "=" * 60)
    print("AUDIT TRAIL SUMMARY")
    print("=" * 60)

    if not trail:
        print("No decisions logged yet.")
        return

    for entry in trail:
        print(f"\n[{entry['logged_at']}]")
        print(f"  Feature:    {entry['feature'][:70]}...")
        print(f"  Agent:      {entry['agent_name']} ({entry['stage']})")
        print(f"  Decision:   {entry['decision']}")
        print(f"  Confidence: {entry['confidence_score']}")
        print(f"  Escalated:  {entry['escalated_to_human']}")
        print(f"  Outcome:    {entry['outcome']}")
        print(f"  Model:      {entry['model_used']}")

    summary = get_audit_summary()
    print(f"\n{'='*60}")
    print(f"TOTALS: {summary['total_decisions']} decisions | "
          f"Avg confidence: {summary['avg_confidence_score']} | "
          f"Escalation rate: {summary['escalation_rate']}")


if __name__ == "__main__":
    # Log today's pipeline decision to the audit trail
    feature = "An AI assistant that automatically summarises customer support tickets and suggests responses to agents."

    # Load reports
    with open("data/orchestrator_report.json") as f:
        orch = json.load(f)
    with open("data/reflexion_report.json") as f:
        ref = json.load(f)

    final_decision = ref.get("final_decision", {})

    entry = log_decision(
        run_id=orch.get("pipeline_run_id", "RUN_UNKNOWN"),
        feature=feature,
        stage="Stage 03 — Decide",
        agent_name="Decider + Reflexion Loop",
        input_signals=orch.get("signals", []),
        reasoning_chain=final_decision.get("reasoning_chain", []),
        decision=final_decision.get("decision", "UNKNOWN"),
        confidence_score=final_decision.get("confidence_score", 0),
        escalated_to_human=final_decision.get("escalate_to_human", False),
        model_used="gpt-4o-mini",
        tokens_consumed=0,
        outcome="PENDING"
    )

    print(f"\n✅ Decision logged: {entry['log_id']}")
    print_audit_trail()
    summary = get_audit_summary()
    print("\nAudit summary:")
    print(json.dumps(summary, indent=2))