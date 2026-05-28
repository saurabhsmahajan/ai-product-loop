# test_day3.py

from agents.interview_agent import run_interview
from agents.synthesis_agent import run_synthesis

# Step 1 — Run one interview
print("Running Interview Agent...")
transcript = run_interview("An AI assistant that auto-summarises customer support tickets.")

# Step 2 — Run synthesis on saved transcripts
print("\nRunning Synthesis Agent...")
opportunity_map = run_synthesis()