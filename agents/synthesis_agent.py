# agents/synthesis_agent.py

import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.utils import call_llm, parse_json_response
from agents.prompts import SYNTHESIS_AGENT_PROMPT

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
        if filename.endswith(".json"):
            with open(os.path.join(data_folder, filename), "r") as f:
                transcripts.append(json.load(f))

    print(f"Loaded {len(transcripts)} transcript(s) from {data_folder}/")
    return transcripts


def run_synthesis(data_folder: str = "data") -> dict:
    """
    Reads all interview transcripts and extracts top pain themes.
    Outputs a structured opportunity map.
    """

    print("\n" + "="*60)
    print("SYNTHESIS AGENT — Stage 01: Discover")
    print("="*60)

    # Step 1 — Load all transcripts
    transcripts = load_transcripts(data_folder)

    if not transcripts:
        print("No transcripts to synthesise.")
        return {}

    # Step 2 — Format transcripts as text for the LLM
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

    # Step 5 — Print summary
    print(f"✅ Synthesis complete. Opportunity map saved to {output_path}\n")
    print(f"Total interviews analysed: {opportunity_map.get('total_interviews_analysed')}")
    print(f"Top opportunity: {opportunity_map.get('top_opportunity')}")
    print("\nPain Themes:")
    for theme in opportunity_map.get("pain_themes", []):
        print(f"  {theme['theme_id']} — {theme['theme_name']} (Opportunity score: {theme['opportunity_score']})")

    return opportunity_map


if __name__ == "__main__":
    run_synthesis()