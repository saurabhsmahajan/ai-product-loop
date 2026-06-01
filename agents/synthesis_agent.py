# agents/synthesis_agent.py

import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import SYNTHESIS_AGENT_PROMPT

# Day 11 additions — graceful fallback if not yet built
try:
    from memory.rag_retriever import store_interview_chunk
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from agents.jira_notifier import create_feature_ticket
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False


def load_transcripts(data_folder: str = "data") -> list:
    """
    Loads all interview transcripts from the data folder.
    Returns a list of transcript dictionaries.
    """
    transcripts = []

    if not os.path.exists(data_folder):
        print("No data folder found. Run the Interview Agent first.")
        return []

    for filename in os.listdir(data_folder):
        if filename.startswith("INT_") and filename.endswith(".json"):
            with open(os.path.join(data_folder, filename), "r") as f:
                transcripts.append(json.load(f))

    print(f"Loaded {len(transcripts)} interview transcript(s) from {data_folder}/")
    return transcripts


def run_synthesis(data_folder: str = "data") -> dict:
    """
    Reads all interview transcripts, extracts top pain themes,
    stores themes in RAG, and auto-creates Jira tickets for top themes.
    """

    print("\n" + "=" * 60)
    print("SYNTHESIS AGENT — Stage 01: Discover")
    print("=" * 60)

    # Step 1 — Load all transcripts
    transcripts = load_transcripts(data_folder)

    if not transcripts:
        print("No transcripts to synthesise.")
        return {}

    # Step 2 — Format for LLM
    transcripts_text = json.dumps(transcripts, indent=2)

    # Step 3 — Run synthesis
    print("Analysing transcripts and extracting pain themes...\n")

    response = call_llm(
        system_prompt=SYNTHESIS_AGENT_PROMPT,
        user_message=f"Here are the interview transcripts to analyse:\n\n{transcripts_text}"
    )

    opportunity_map = parse_json_response(response)

    if not opportunity_map:
        print("Error: Could not generate opportunity map.")
        return {}

    # Step 4 — Save opportunity map
    output_path = "data/opportunity_map.json"
    with open(output_path, "w") as f:
        json.dump(opportunity_map, f, indent=2)

    # Step 5 — Store each pain theme in RAG memory (Day 11)
    if RAG_AVAILABLE:
        print("\nStoring pain themes in RAG memory...")
        for theme in opportunity_map.get("pain_themes", []):
            chunk_text = (
                f"Pain theme: {theme.get('theme_name')}. "
                f"{theme.get('description')} "
                f"Opportunity score: {theme.get('opportunity_score')}. "
                f"Quotes: {' | '.join(theme.get('supporting_quotes', []))}"
            )
            store_interview_chunk(
                chunk_id=f"theme_{theme.get('theme_id', 'T0')}_{len(transcripts)}",
                text=chunk_text,
                metadata={
                    "type": "pain_theme",
                    "theme_name": theme.get("theme_name", ""),
                    "opportunity_score": str(theme.get("opportunity_score", 0)),
                    "frequency_score": str(theme.get("frequency_score", 0)),
                    "severity_score": str(theme.get("severity_score", 0)),
                }
            )
        print(f"✅ {len(opportunity_map.get('pain_themes', []))} themes stored in RAG.")
    else:
        print("⚠️  RAG not available — skipping memory store.")

    # Step 6 — Auto-create Jira tickets for top 3 themes (Day 11)
    if JIRA_AVAILABLE:
        print("\nCreating Jira tickets for top pain themes...")
        sorted_themes = sorted(
            opportunity_map.get("pain_themes", []),
            key=lambda t: t.get("opportunity_score", 0),
            reverse=True
        )
        for theme in sorted_themes[:3]:
            ticket = create_feature_ticket({
                "theme": theme.get("theme_name"),
                "severity": theme.get("severity_score", 0) / 10,
                "frequency": theme.get("frequency_score", 0),
                "opportunity": theme.get("description", "")
            })
            status = ticket.get("key", ticket.get("status", "unknown"))
            print(f"  Ticket: {theme.get('theme_name')} → {status}")
    else:
        print("⚠️  Jira not configured — skipping ticket creation.")

    # Step 7 — Print summary
    print(f"\n✅ Synthesis complete. Opportunity map saved to {output_path}")
    print(f"Total interviews analysed: {opportunity_map.get('total_interviews_analysed')}")
    print(f"Top opportunity: {opportunity_map.get('top_opportunity')}")
    print("\nPain Themes:")
    for theme in opportunity_map.get("pain_themes", []):
        print(f"  {theme['theme_id']} — {theme['theme_name']} "
              f"(Opportunity score: {theme['opportunity_score']})")

    return opportunity_map


if __name__ == "__main__":
    run_synthesis()
