# test_utils.py

from agents.utils import call_llm, parse_json_response
from agents.prompts import INTERVIEW_AGENT_PROMPT, DECIDER_PROMPT

# Test 1 — basic call
response = call_llm(
    system_prompt="You are a helpful assistant. Always reply in one sentence.",
    user_message="What is a product manager?"
)
print("Test 1 response:", response)

# Test 2 — JSON parsing
response2 = call_llm(
    system_prompt="You are a helpful assistant. Always reply with valid JSON only. No explanation.",
    user_message='Return this as JSON: name is "Alice", role is "PM", experience is 5'
)
print("Test 2 raw:", response2)
parsed = parse_json_response(response2)
print("Test 2 parsed:", parsed)
print("Name field:", parsed.get("name"))

# Test 3 — Interview Agent prompt
response3 = call_llm(
    system_prompt=INTERVIEW_AGENT_PROMPT,
    user_message="Feature hypothesis: An AI assistant that auto-summarises customer support tickets."
)
print("\nTest 3 - Interview Agent response:")
print(response3)