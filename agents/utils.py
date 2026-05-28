# agents/utils.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(system_prompt: str, user_message: str, model: str = "gpt-4o-mini") -> str:
    """
    Sends a system prompt + user message to the LLM.
    Returns the response as a plain string.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content


def parse_json_response(text: str) -> dict:
    """
    Safely parses a JSON string returned by the LLM.
    Strips markdown code fences if present (LLMs often wrap JSON in ```json ... ```).
    Returns a Python dictionary.
    """
    # Strip markdown fences if LLM wrapped the JSON
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw text was: {text}")
        return {}