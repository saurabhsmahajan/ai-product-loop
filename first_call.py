from dotenv import load_dotenv
import os
from openai import OpenAI

# Load API key from .env file
load_dotenv()

# Create the client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Make your first API call
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful AI product assistant."},
        {"role": "user", "content": "Give me one creative name for an AI product assistant"}
    ],
    temperature=0
)

# Print the response
print(response.choices[0].message.content)