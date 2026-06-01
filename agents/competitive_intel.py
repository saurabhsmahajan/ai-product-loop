# agents/competitive_intel.py

import json
from datetime import datetime
from agents.utils import call_llm
from memory.rag_retriever import store_decision

SYSTEM_PROMPT = """You are a Competitive Intelligence Agent for an AI product team.

Your job: given a product domain, search for competitor updates from the last 24 hours and extract structured signals.

You must output ONLY valid JSON in this exact schema:
{
  "scan_date": "YYYY-MM-DD",
  "domain": "string",
  "signals": [
    {
      "competitor": "string",
      "signal_type": "feature_launch | pricing_change | partnership | executive_move | negative_press",
      "summary": "string (1-2 sentences)",
      "urgency": "high | medium | low",
      "recommended_action": "string"
    }
  ],
  "orchestrator_injection": "string — a 2-sentence brief the Orchestrator should read before today's pipeline run"
}

Chain-of-thought: First list what you know about the competitive landscape. Then identify the 3 most significant recent signals. Then assess urgency for each. Then write the orchestrator_injection last."""

def run_competitive_intel(domain: str, known_competitors: list[str]) -> dict:
    """
    Runs a competitive intelligence scan for a given product domain.
    Stores the output in RAG memory so it's available to the Orchestrator.
    """
    print(f"\n[Competitive Intel] Scanning domain: {domain}")
    
    user_prompt = f"""Product domain: {domain}
Known competitors to monitor: {', '.join(known_competitors)}

Scan for competitor updates, feature launches, pricing changes, and strategic moves 
from the last 24–48 hours. Extract the signals most relevant to our product decisions today."""

    response = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_prompt,
        model="gpt-4o-mini"  # cost-efficient for nightly runs
    )

    try:
        # Strip markdown fences if present
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        result = {
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "domain": domain,
            "signals": [],
            "orchestrator_injection": f"Competitive intel scan failed to parse on {datetime.now().strftime('%Y-%m-%d')}. Proceed with prior context.",
            "parse_error": response[:300]
        }

    # Store in RAG so Orchestrator retrieves it automatically
    store_decision(
        decision_id=f"competitive_intel_{datetime.now().strftime('%Y%m%d')}",
        text=result.get("orchestrator_injection", "") + " " + json.dumps(result.get("signals", [])),
        metadata={
            "type": "competitive_intel",
            "domain": domain,
            "date": result.get("scan_date", ""),
            "signal_count": str(len(result.get("signals", [])))
        }
    )

    print(f"[Competitive Intel] Found {len(result.get('signals', []))} signals. Stored in RAG.")
    return result


if __name__ == "__main__":
    result = run_competitive_intel(
        domain="AI-powered product management tools",
        known_competitors=["Productboard AI", "Pendo AI", "Amplitude AI", "Notion AI"]
    )
    print(json.dumps(result, indent=2))