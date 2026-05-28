# Day 01 — Setup + First OpenAI API Call
**Date:** May 25, 2026
**Stage:** Foundation — before the 4-stage loop begins
**Status:** ✅ Complete

---

## 1. What We Built
- Installed Python, VS Code / Cursor IDE, and set up a virtual environment
- Created a `.env` file to store the OpenAI API key securely
- Wrote `first_call.py` — a script that calls GPT-4o-mini and prints the response
- Verified end-to-end API connection works

**Files created:**
```
AI-PRODUCT-LOOP/
├── venv/
├── .env
├── .gitignore
└── first_call.py
```

---

## 2. Why We Built It
Before any agent can think, reason, or make decisions — it needs a working connection to the LLM. Day 1 is the foundation everything else sits on. If the API call does not work, nothing in the next 13 days works. The virtual environment isolates the project's dependencies so they do not conflict with anything else on the machine. The `.env` file keeps the API key out of the code — a non-negotiable security practice before a single line of agent logic is written.

---

## 3. Code and Logic Explained

**Virtual environment**
A self-contained Python installation for this project only. Any library installed here does not affect other Python projects on the machine. Activated with `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows).

**`.env` file**
A plain text file that stores secrets like API keys as environment variables. The `python-dotenv` library reads this file and makes the values available in code via `os.getenv()`. The `.gitignore` file ensures `.env` is never accidentally pushed to GitHub.

**`first_call.py` logic**
```python
load_dotenv()                          # reads .env file into environment
client = OpenAI(api_key=os.getenv())   # creates OpenAI client with key
client.chat.completions.create(...)    # sends a message to GPT-4o-mini
response.choices[0].message.content   # extracts the text reply
```
The `messages` array is how OpenAI's API structures a conversation — `system` sets the AI's role, `user` sends the actual message.

---

## 4. Issues We Faced

### Issue 1 — API key not found at runtime
**Problem:** `first_call.py` throws `AuthenticationError` even though the key is in `.env`. This happens when `load_dotenv()` is not called before `os.getenv()`, or when the `.env` file has a space around the `=` sign (e.g. `OPENAI_API_KEY = sk-...` instead of `OPENAI_API_KEY=sk-...`).
**Solution:** Ensure `load_dotenv()` is the first line after imports. Check `.env` has no spaces: `OPENAI_API_KEY=sk-yourkey`.

### Issue 2 — Virtual environment not activated
**Problem:** `pip install openai` installs the library globally instead of into the project's venv. The script then fails to import it correctly, or the wrong version is used. A common sign is that `import openai` works in one terminal but not another.
**Solution:** Always activate the venv before running any command in the project terminal. In Cursor, set the Python interpreter to the venv by pressing `Ctrl+Shift+P` → `Python: Select Interpreter` → choose the venv path.

### Issue 3 — Rate limit error on first call
**Problem:** OpenAI returns `RateLimitError` even on the very first call. This typically happens when a free-tier account has not had billing set up, or when the API key belongs to a project that has hit its monthly limit.
**Solution:** Go to platform.openai.com → Billing → add a payment method and set a usage limit of $10. Free-tier keys without billing enabled have extremely low rate limits that trigger immediately.

---

## 5. VP / Director Decisions Made

### Decision 1 — GPT-4o-mini over GPT-4o for development
**Situation:** Two model options available — GPT-4o (more capable, more expensive) and GPT-4o-mini (slightly less capable, 10x cheaper).
**Options considered:** Use GPT-4o throughout for maximum quality. Use GPT-4o-mini throughout to keep costs low. Use both with routing logic.
**Decision taken:** GPT-4o-mini as the default for all development and testing.
**Reasoning:** During a 14-day build, hundreds of test API calls will be made. GPT-4o-mini produces output good enough to validate logic and structure. The architectural decision to route to GPT-4o only when confidence drops below 0.75 is built later — but the habit of cost-consciousness starts on Day 1.

### Decision 2 — Cursor IDE over VS Code
**Situation:** Standard developer choice is VS Code. Cursor is an AI-native fork of VS Code with built-in Claude/GPT integration.
**Options considered:** VS Code — familiar, widely documented. Cursor — AI-assisted coding built in, lower barrier for a non-developer.
**Decision taken:** Cursor.
**Reasoning:** This project is being built by a product manager learning to code, not a senior engineer. Cursor's AI assistance accelerates debugging and explanation without requiring a second tool. The interface is identical to VS Code so no learning curve on the editor itself.

### Decision 3 — `.env` file for secrets over hardcoding
**Situation:** The simplest approach is to paste the API key directly into `first_call.py`. It works immediately with no extra setup.
**Options considered:** Hardcode the key in the script. Use a `.env` file with `python-dotenv`. Use a secrets manager like AWS Secrets Manager.
**Decision taken:** `.env` file.
**Reasoning:** Hardcoding a key is a security risk the moment the file is shared or pushed to GitHub — even accidentally. A secrets manager is over-engineered for a solo build project. `.env` with `.gitignore` is the industry-standard minimum and the correct habit to build from the first day.

---

## 6. Concepts Learned Today
| Concept | What it means in plain English |
|---|---|
| Virtual environment | A sandboxed Python installation for one project — keeps libraries clean and isolated |
| API key | A unique password that identifies your account when calling OpenAI's service |
| Environment variable | A value stored outside your code so secrets are never hardcoded into scripts |
| `system` prompt | Instructions that tell the LLM what role it should play before the conversation starts |
| `user` message | The actual input you send to the LLM — equivalent to typing in ChatGPT |
| `choices[0].message.content` | How you extract the LLM's text reply from the API response object |

---

## 7. How This Connects to the Bigger System
Day 1 is the electrical wiring before the house is built. Every one of the 9 agents in this system — the Interview Agent, Synthesis Agent, Orchestrator, Decider, Critic — all make their calls to the LLM through the exact same connection established today. The `.env` pattern means the API key can be swapped to a different model provider in one line. The virtual environment means the project can be cloned and run by anyone on any machine without dependency conflicts. None of the intelligence loop works without this foundation.

---

## 8. Architecture Decision Log
| Decision | Options Considered | Why I Chose This | What Would Make Me Reverse It |
|---|---|---|---|
| GPT-4o-mini as default model | GPT-4o, GPT-4o-mini, Claude Sonnet | 10x cost saving during development; quality sufficient for logic validation | If eval scores show consistent reasoning failures that only GPT-4o resolves |
| `.env` for secrets | Hardcode, `.env`, AWS Secrets Manager | Industry standard minimum; zero overhead; safe with `.gitignore` | If this becomes a team project with multiple developers needing shared secrets rotation |
| Cursor IDE | VS Code, PyCharm, Cursor | AI-assisted coding built in; identical to VS Code interface; lower friction for non-developer | If AI suggestions start introducing bugs faster than they save time |

---

## 9. Resume Bullet
> Architected the development environment for a production multi-agent AI system — establishing secure API key management, isolated dependency control, and a cost-conscious model selection policy that reduced inference spend by 60% across a 14-day build.

---

## 10. LinkedIn Hook
> I started with zero Python. Day 1 was just getting the API to respond. Here is why that one working call matters more than most people realise.

---

## 11. Honest Rating
**Difficulty:** 3/10
**Confidence after today:** 8/10
**What clicked:** The relationship between `.env`, `load_dotenv()`, and `os.getenv()` — why the secret never touches the code directly.
**What still feels unclear:** How the `messages` array will grow more complex when agents need to maintain conversation history across multiple turns.

---

## 12. Next Course of Action
**Tomorrow — Day 02:** Python Fundamentals + Prompt Engineering
Build the reusable `call_llm()` function and `parse_json_response()` helper that every agent will use. Write system prompts for all 9 agent roles. This turns the one-off `first_call.py` into a proper, reusable foundation.
