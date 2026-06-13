# agents/bias_check.py
#
# Bias Indicator Check — Evaluate Stage
# NIST AI RMF: MEASURE 2.11 | NIST AI 600-1: Risk 2 (Harmful bias)
# AIGP BOK v2.1: Domain 3
#
# Purpose:
#   Scans feature descriptions and synthesis outputs for language
#   patterns that may indicate biased framing. Raises flags for
#   human review — does NOT make a bias judgement.
#
# Called by: agents/governance.py — inside run_governance_check()
# Owner: Saurabh Mahajan (saurabh@arcaence.com)
# Version: 1.0 | June 2026

import re
from datetime import datetime


# ── Pattern definitions ────────────────────────────────────────────────────
# Three categories of bias indicators.
# Each pattern flags language worth human review — not definitive proof.

DEMOGRAPHIC_PATTERNS = [
    r"\b(gender|race|ethnicity|religion|nationality|age|disability)\b",
    r"\b(male|female|men|women|young|old|elderly|senior)\b",
    r"\b(urban|rural|western|developing|third.world)\b",
    r"\b(minority|majority|privileged|marginalised|underserved)\b",
]

GENERALISATION_PATTERNS = [
    r"\b(always|never|all users?|everyone|nobody|no one)\b",
    r"\b(typical|normally|usually|generally)\s+(they|these people|users)\b",
    r"\busers?\s+(always|never|typically|generally)\b",
    r"\beveryone\s+(knows|wants|needs|expects)\b",
]

LOADED_LANGUAGE_PATTERNS = [
    r"\b(obvious|clearly|simply|just|easy|trivial|straightforward)\b",
    r"\b(obviously|naturally|of course|everyone knows|goes without saying)\b",
    r"\b(should|must|need to)\s+(obviously|clearly|simply)\b",
]

# Map category names to their pattern lists
PATTERN_CATEGORIES = {
    "demographic_language": DEMOGRAPHIC_PATTERNS,
    "generalisation":       GENERALISATION_PATTERNS,
    "loaded_language":      LOADED_LANGUAGE_PATTERNS,
}

# Risk level mapping — demographic language is highest risk
RISK_LEVEL_MAP = {
    "demographic_language": "high",
    "generalisation":       "medium",
    "loaded_language":      "low",
}


# ── Main function ──────────────────────────────────────────────────────────

def run_bias_check(text: str, context: str = "feature_description") -> dict:
    """
    Scans text for bias indicators across three categories.

    Args:
        text:     The text to scan — feature description or synthesis output.
        context:  Label for what is being scanned. Used in the report.

    Returns:
        A structured report dict with:
        - bias_flags_raised (bool)
        - flag_count (int)
        - risk_level (str): none / low / medium / high
        - categories_flagged (list)
        - flags (list of dicts with detail per match)
        - human_review_recommended (bool)

    Does NOT make a bias judgement — raises flags for human review only.

    Example:
        from agents.bias_check import run_bias_check
        result = run_bias_check(feature_description, context="feature_description")
        report["bias_assessment"] = result
        report["bias_flags_raised"] = result["bias_flags_raised"]
    """

    flags = []
    categories_flagged = []

    # ── Scan each category ─────────────────────────────────────────────────
    for category, patterns in PATTERN_CATEGORIES.items():
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Deduplicate matches
                unique_matches = list(set(
                    m if isinstance(m, str) else " ".join(m)
                    for m in matches
                ))
                flags.append({
                    "category":    category,
                    "pattern":     pattern,
                    "matches":     unique_matches,
                    "match_count": len(unique_matches),
                    "risk_level":  RISK_LEVEL_MAP[category],
                    "review_note": _get_review_note(category),
                })
                if category not in categories_flagged:
                    categories_flagged.append(category)

    # ── Compute overall risk level ─────────────────────────────────────────
    if "demographic_language" in categories_flagged:
        overall_risk = "high"
    elif "generalisation" in categories_flagged and "loaded_language" in categories_flagged:
        overall_risk = "medium"
    elif categories_flagged:
        overall_risk = "low"
    else:
        overall_risk = "none"

    bias_flags_raised = len(flags) > 0

    # ── Build report ───────────────────────────────────────────────────────
    report = {
        "bias_check_timestamp":    datetime.now().isoformat(),
        "context":                 context,
        "text_length_chars":       len(text),
        "bias_flags_raised":       bias_flags_raised,
        "flag_count":              len(flags),
        "risk_level":              overall_risk,
        "categories_flagged":      categories_flagged,
        "human_review_recommended": bias_flags_raised,
        "flags":                   flags,
        "nist_control":            "NIST MEASURE 2.11 — Bias and fairness",
        "nist_ai_600_1_risk":      "Risk 2 — Harmful bias",
        "aigp_domain":             "Domain 3 — Governing AI Development",
        "interpretation": (
            "No bias indicators detected — proceed normally."
            if not bias_flags_raised else
            f"{len(flags)} bias indicator(s) flagged across "
            f"{len(categories_flagged)} category/categories. "
            f"Risk level: {overall_risk.upper()}. "
            f"Human review recommended before GO decision."
        ),
    }

    # ── Console output ─────────────────────────────────────────────────────
    _print_summary(report)

    return report


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_review_note(category: str) -> str:
    notes = {
        "demographic_language": (
            "Language referencing demographic groups detected. "
            "Verify the feature design does not disadvantage specific "
            "user segments or make assumptions about demographic groups."
        ),
        "generalisation": (
            "Broad generalisation about user behaviour detected. "
            "Verify this claim is supported by actual user research data "
            "rather than assumption."
        ),
        "loaded_language": (
            "Assumption-laden or dismissive language detected. "
            "Verify all claims are evidence-based and appropriately "
            "qualified."
        ),
    }
    return notes.get(category, "Review flagged language before proceeding.")


def _print_summary(report: dict) -> None:
    status = "⚠️  BIAS FLAGS RAISED" if report["bias_flags_raised"] else "✅ No bias flags"
    print(f"\n{'─'*60}")
    print(f"Bias Check — NIST MEASURE 2.11 | NIST AI 600-1 Risk 2")
    print(f"  Status:     {status}")
    print(f"  Risk level: {report['risk_level'].upper()}")
    print(f"  Flags:      {report['flag_count']}")
    if report["categories_flagged"]:
        print(f"  Categories: {', '.join(report['categories_flagged'])}")
    if report["bias_flags_raised"]:
        print(f"  Action:     Human review recommended before GO decision")
    print(f"{'─'*60}\n")


# ── Self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print("TEST 1 — Clean feature description (no flags expected)")
    clean = (
        "An AI assistant that summarises customer support tickets "
        "and suggests response templates to reduce resolution time."
    )
    result1 = run_bias_check(clean, context="feature_description")
    print(f"Flags raised: {result1['bias_flags_raised']}")
    print(f"Risk level:   {result1['risk_level']}\n")

    print("TEST 2 — Demographic language (high risk expected)")
    demographic = (
        "A feature for elderly users who always struggle with "
        "technology. Young users obviously don't need this help."
    )
    result2 = run_bias_check(demographic, context="feature_description")
    print(f"Flags raised: {result2['bias_flags_raised']}")
    print(f"Risk level:   {result2['risk_level']}")
    print(f"Categories:   {result2['categories_flagged']}\n")

    print("TEST 3 — Generalisation language (medium risk expected)")
    generalisation = (
        "Users always want faster response times. "
        "Everyone knows that speed is the top priority. "
        "Users typically expect instant results."
    )
    result3 = run_bias_check(generalisation, context="synthesis_output")
    print(f"Flags raised: {result3['bias_flags_raised']}")
    print(f"Risk level:   {result3['risk_level']}")
    print(f"Flag count:   {result3['flag_count']}\n")

    print("TEST 4 — Loaded language only (low risk expected)")
    loaded = (
        "This is obviously a simple fix. "
        "It is clearly straightforward to implement."
    )
    result4 = run_bias_check(loaded, context="feature_description")
    print(f"Flags raised: {result4['bias_flags_raised']}")
    print(f"Risk level:   {result4['risk_level']}")
    print(f"Interpretation: {result4['interpretation']}")