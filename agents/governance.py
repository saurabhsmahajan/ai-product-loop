# agents/governance.py

import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import GOVERNANCE_PROMPT

# Simple PII patterns to detect before sending to LLM
import re

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{10}\b|\+\d{1,3}\s?\d{10}",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}

def scrub_pii(text: str) -> tuple[str, list]:
    """
    Detects and redacts PII from text before it reaches the LLM.
    Returns scrubbed text and list of PII types found.
    """
    found_pii = []
    scrubbed = text

    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, scrubbed)
        if matches:
            found_pii.append(pii_type)
            scrubbed = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", scrubbed)

    return scrubbed, found_pii


def run_governance_check(feature_description: str, decision: str) -> dict:
    """
    Runs the full governance check on a feature before it ships:
    - PII scrubbing
    - EU AI Act risk classification
    - Bias detection
    - Governance verdict
    """

    print("\n" + "="*60)
    print("RESPONSIBLE AI GOVERNANCE MODULE — Stage 02: Evaluate")
    print("="*60)

    # Step 1 — PII scrub before anything touches the LLM
    print("Running PII scrubber...")
    scrubbed_description, pii_found = scrub_pii(feature_description)

    if pii_found:
        print(f"⚠️  PII detected and redacted: {pii_found}")
    else:
        print("✅ No PII detected in feature description.")

    # Step 2 — Send to Governance Agent
    print("Running EU AI Act classification and bias check...\n")

    response = call_llm(
        system_prompt=GOVERNANCE_PROMPT,
        user_message=f"""
Feature description (PII scrubbed):
\"\"\"{scrubbed_description}\"\"\"

Current go/no-go decision:
\"\"\"{decision}\"\"\"
"""
    )

    report = parse_json_response(response)

    if not report:
        print("Error: Could not generate governance report.")
        return {}

    # Step 3 — Add PII scrubber results to report
    report["pii_detected"] = len(pii_found) > 0
    report["pii_details"] = f"PII types found and redacted: {pii_found}" if pii_found else "No PII detected."

    # Step 4 — Save report
    os.makedirs("data", exist_ok=True)
    output_path = "data/governance_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    # Step 5 — Print summary
    print(f"EU AI Act risk tier:   {report.get('eu_ai_act_risk_tier')}")
    print(f"PII detected:          {report.get('pii_detected')}")
    print(f"Bias flags:            {report.get('bias_flags')}")
    print(f"Governance verdict:    {report.get('governance_verdict')}")
    print(f"Required actions:      {report.get('required_actions')}")
    print(f"\n✅ Governance report saved to {output_path}")

    return report


if __name__ == "__main__":
    feature = """
    An AI assistant that automatically summarises customer support tickets 
    and suggests responses to agents. The system processes all incoming 
    tickets including customer emails, phone numbers, and account details.
    Contact us at support@company.com or call +91 9876543210.
    """

    decision = "CONDITIONAL_GO — pending security review"

    result = run_governance_check(feature, decision)
    print("\nFull governance report:")
    print(json.dumps(result, indent=2))