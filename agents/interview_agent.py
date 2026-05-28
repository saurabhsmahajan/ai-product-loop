# agents/interview_agent.py

import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
from agents.utils import call_llm, parse_json_response
from agents.prompts import INTERVIEW_AGENT_PROMPT

def run_interview(feature_hypothesis: str) -> dict:
    """
    Conducts an async interview for a given feature hypothesis.
    - Generates 5 opening questions
    - Asks each question to the user in the terminal
    - Generates a contextual follow-up per answer
    - Saves the full transcript as JSON
    """

    print("\n" + "="*60)
    print("INTERVIEW AGENT — Stage 01: Discover")
    print("="*60)
    print(f"Feature hypothesis: {feature_hypothesis}")
    print("Generating interview questions...\n")

    # Step 1 — Generate 5 opening questions
    response = call_llm(
        system_prompt=INTERVIEW_AGENT_PROMPT,
        user_message=f"Feature hypothesis: {feature_hypothesis}. Generate 5 interview questions only. Leave user_answer blank."
    )

    transcript = parse_json_response(response)

    if not transcript:
        print("Error: Could not generate questions.")
        return {}

    # Step 2 — Ask each question, collect real answers, generate follow-ups
    completed_questions = []

    for q in transcript.get("questions", []):
        print(f"\nQuestion {q['question_id']}: {q['question']}")
        user_answer = input("Your answer: ").strip()

        # Generate contextual follow-up based on actual answer
        follow_up_response = call_llm(
            system_prompt="You are an expert user researcher. Given a question and a user's answer, generate exactly one sharp follow-up question that digs deeper into the pain. Return only the follow-up question as plain text.",
            user_message=f"Question: {q['question']}\nAnswer: {user_answer}"
        )

        follow_up = follow_up_response.strip()
        print(f"Follow-up: {follow_up}")
        follow_up_answer = input("Your answer: ").strip()

        completed_questions.append({
            "question_id": q["question_id"],
            "question": q["question"],
            "user_answer": user_answer,
            "follow_up": follow_up,
            "follow_up_answer": follow_up_answer
        })

    # Step 3 — Assemble final transcript
    final_transcript = {
        "interview_id": f"INT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "feature_hypothesis": feature_hypothesis,
        "conducted_at": datetime.now().isoformat(),
        "questions": completed_questions
    }

    # Step 4 — Save to data folder
    os.makedirs("data", exist_ok=True)
    filename = f"data/{final_transcript['interview_id']}.json"

    with open(filename, "w") as f:
        json.dump(final_transcript, f, indent=2)

    print(f"\n✅ Interview complete. Transcript saved to {filename}")
    return final_transcript


if __name__ == "__main__":
    hypothesis = input("Enter your feature hypothesis: ").strip()
    run_interview(hypothesis)