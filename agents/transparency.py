# agents/transparency.py
#
# EU AI Act Article 50 — Transparency obligations
# NIST AI RMF: MEASURE 2.11 | AIGP BOK v2.1: Domain 4
#
# Purpose:
#   Appends a machine-readable + human-readable transparency disclosure
#   to every Decide-stage output. Required for Limited Risk classification
#   under EU AI Act Article 50.
#
# Called by: agents/decider.py — after parse_json_response()
# Owner: Saurabh Mahajan (saurabh@arcaence.com)
# Version: 1.0 | June 2026

import hashlib
from datetime import datetime, timezone


# ── Constants ──────────────────────────────────────────────────────────────

SYSTEM_NAME    = "AI Product Intelligence Loop"
SYSTEM_VERSION = "1.0"
EU_AI_ACT_TIER = "limited_risk"
EU_AI_ACT_ART  = "Article 50 — Transparency obligations"
CONFIDENCE_THRESHOLD = 0.75   # below this → human review REQUIRED


# ── Main function ──────────────────────────────────────────────────────────

def add_transparency_disclosure(report: dict, run_id: str = None) -> dict:
    """
    Appends EU AI Act Article 50 transparency disclosure to a
    Decide-stage agent output.

    Args:
        report:  The parsed JSON report from the Decider agent.
        run_id:  Pipeline run ID. Auto-generated if not provided.

    Returns:
        The same report dict with '_grc_disclosure' field appended.
        Original fields are never modified.

    Example:
        report = parse_json_response(response)
        report = add_transparency_disclosure(report, run_id)
    """

    # ── Extract decision fields ────────────────────────────────────────────
    confidence  = report.get("confidence_score", 0.0)
    decision    = report.get("decision", "UNKNOWN")
    escalate    = report.get("escalate_to_human", True)
    model_used  = report.get("model_used", "gpt-4o-mini")

    # ── Determine human review requirement ────────────────────────────────
    human_review_required = escalate or (confidence < CONFIDENCE_THRESHOLD)

    if confidence < CONFIDENCE_THRESHOLD:
        review_reason = (
            f"Confidence score {confidence:.0%} is below "
            f"the {CONFIDENCE_THRESHOLD:.0%} threshold"
        )
    elif decision == "GO":
        review_reason = (
            "All GO decisions require human review before feature ships"
        )
    elif escalate:
        review_reason = "Reflexion loop escalated — critique score below 0.70"
    else:
        review_reason = "Standard governance review"

    # ── Generate output hash for audit trail linkage ───────────────────────
    output_content = f"{decision}:{confidence}:{run_id}"
    output_hash = hashlib.sha256(
        output_content.encode()
    ).hexdigest()[:16]

    # ── Auto-generate run_id if not provided ──────────────────────────────
    if not run_id:
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # ── Build disclosure ───────────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc).isoformat()

    disclosure = {
        # Identity
        "generated_by":            SYSTEM_NAME,
        "system_version":          SYSTEM_VERSION,
        "pipeline_stage":          "Stage 03 — Decide",
        "agent":                   "Decider Agent",

        # Run linkage
        "run_id":                  run_id,
        "output_hash":             output_hash,
        "generated_at":            timestamp,

        # Decision summary
        "decision":                decision,
        "confidence_score":        confidence,

        # Regulatory
        "eu_ai_act_classification": EU_AI_ACT_TIER,
        "eu_ai_act_article":        EU_AI_ACT_ART,

        # Human oversight
        "human_review_required":   human_review_required,
        "human_review_reason":     review_reason,

        # Model
        "model_used":              model_used,

        # NIST linkage
        "nist_rmf_function":       "MEASURE",
        "nist_subcategory":        "MEASURE 2.11",

        # Human-readable disclosure text
        "disclosure_text": (
            f"[AI-generated product decision | "
            f"System: {SYSTEM_NAME} v{SYSTEM_VERSION} | "
            f"Decision: {decision} | "
            f"Confidence: {confidence:.0%} | "
            f"Human review: {'REQUIRED' if human_review_required else 'optional'} | "
            f"EU AI Act: {EU_AI_ACT_TIER} — {EU_AI_ACT_ART} | "
            f"Run: {run_id} | "
            f"Generated: {timestamp}]"
        ),
    }

    # ── Append to report — never modify original fields ────────────────────
    report["_grc_disclosure"] = disclosure

    # ── Console output ─────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"EU AI Act Article 50 — Transparency Disclosure Applied")
    print(f"  Decision:      {decision}")
    print(f"  Confidence:    {confidence:.0%}")
    print(f"  Human review:  {'REQUIRED ⚠' if human_review_required else 'optional ✓'}")
    print(f"  Reason:        {review_reason}")
    print(f"  Run ID:        {run_id}")
    print(f"  Output hash:   {output_hash}")
    print(f"{'─'*60}\n")

    return report


# ── Utility ────────────────────────────────────────────────────────────────

def get_disclosure_summary(report: dict) -> dict:
    """
    Returns just the disclosure fields from a report.
    Useful for audit log entries and dashboard display.
    """
    disclosure = report.get("_grc_disclosure", {})
    return {
        "eu_ai_act_tier":        disclosure.get("eu_ai_act_classification"),
        "human_review_required": disclosure.get("human_review_required"),
        "human_review_reason":   disclosure.get("human_review_reason"),
        "output_hash":           disclosure.get("output_hash"),
        "generated_at":          disclosure.get("generated_at"),
        "disclosure_text":       disclosure.get("disclosure_text"),
    }


# ── Self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with a GO decision above threshold
    test_go = {
        "decision": "GO",
        "confidence_score": 0.84,
        "escalate_to_human": False,
        "model_used": "gpt-4o-mini",
        "reasoning_chain": ["Signal A supports", "Signal B supports"],
    }

    print("TEST 1 — GO decision, confidence above threshold")
    result = add_transparency_disclosure(test_go, run_id="RUN_TEST_001")
    print(f"Disclosure applied: {result['_grc_disclosure']['disclosure_text']}\n")

    # Test with low confidence — should require human review
    test_low = {
        "decision": "CONDITIONAL_GO",
        "confidence_score": 0.62,
        "escalate_to_human": False,
        "model_used": "gpt-4o-mini",
        "reasoning_chain": ["Weak signal"],
    }

    print("TEST 2 — CONDITIONAL_GO, confidence below threshold")
    result2 = add_transparency_disclosure(test_low, run_id="RUN_TEST_002")
    print(f"Human review required: {result2['_grc_disclosure']['human_review_required']}")
    print(f"Reason: {result2['_grc_disclosure']['human_review_reason']}\n")

    # Test with escalation
    test_escalate = {
        "decision": "NO_GO",
        "confidence_score": 0.78,
        "escalate_to_human": True,
        "model_used": "gpt-4o",
        "reasoning_chain": ["Critique failed twice"],
    }

    print("TEST 3 — NO_GO, escalated by Reflexion loop")
    result3 = add_transparency_disclosure(test_escalate, run_id="RUN_TEST_003")
    print(f"Human review required: {result3['_grc_disclosure']['human_review_required']}")
    print(f"Reason: {result3['_grc_disclosure']['human_review_reason']}")