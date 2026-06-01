"""
agents/impact_translator.py
Business Impact Translator Agent — Day 10

What this does:
  1. Reads the audit trail (decisions + metric history)
  2. Finds metric drops correlated with revenue signals
  3. Calls GPT-4o-mini to generate a concise executive memo
  4. Posts the memo to Slack

Concepts you are learning here:
  - Tool use / function calling in a business context
  - Structured output from LLM (JSON schema)
  - Correlating multiple signals into a single narrative
  - Auto-routing LLM output to a downstream channel (Slack)

Run standalone:  python agents/impact_translator.py
Called by:       backend/routes.py (POST /impact-report)
                 n8n (daily cron after /run-pipeline completes)
"""
from dotenv import load_dotenv
load_dotenv()
import json
import os
from datetime import datetime
from openai import OpenAI
import requests

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─── Config ───────────────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")   # set in .env
MODEL = "gpt-4o-mini"

# ─── Revenue assumption table ─────────────────────────────────────────────────
# Maps each tracked metric to an estimated revenue-per-point value.
# You define these based on your product's business model.
# Example: a 1pp drop in trust score historically correlates with a 0.4%
# increase in churn, which at $50k ARR/customer means ~$200 revenue risk.
REVENUE_ASSUMPTIONS = {
    "hallucination_rate":   {"direction": "increase", "revenue_per_point": 180,  "unit": "pp"},
    "confidence_score":     {"direction": "decrease", "revenue_per_point": 220,  "unit": "pp"},
    "trust_score":          {"direction": "decrease", "revenue_per_point": 200,  "unit": "pp"},
    "cost_per_decision":    {"direction": "increase", "revenue_per_point": 50,   "unit": "cents"},
}

# ─── Step 1: Load audit trail ─────────────────────────────────────────────────
def load_audit_trail() -> list[dict]:
    """
    In production: reads from memory/audit_logger.py (ChromaDB or JSON store).
    For Day 10 demo: returns inline mock data that mirrors real audit structure.

    Each entry is one pipeline run. Keys:
      run_id, timestamp, decisions[], metrics{}, cost_usd, governance_flags[]
    """
    return [
        {
            "run_id": "run_012",
            "timestamp": "2026-06-01T08:14:00",
            "metrics": {
                "hallucination_rate": 3.9,
                "confidence_score": 85.0,
                "trust_score": 84.0,
                "cost_per_decision": 2.3,
            },
            "decisions": [{"id": "D-012", "feature": "AI report summariser", "verdict": "GO", "confidence": 87}],
            "governance_flags": [],
        },
        {
            "run_id": "run_011",
            "timestamp": "2026-05-30T08:11:00",
            "metrics": {
                "hallucination_rate": 5.1,
                "confidence_score": 82.0,
                "trust_score": 81.0,
                "cost_per_decision": 4.7,
            },
            "decisions": [{"id": "D-011", "feature": "Predictive churn model", "verdict": "NO-GO", "confidence": 71}],
            "governance_flags": ["escalated"],
        },
        {
            "run_id": "run_010",
            "timestamp": "2026-05-28T08:09:00",
            "metrics": {
                "hallucination_rate": 7.3,
                "confidence_score": 76.0,
                "trust_score": 74.0,
                "cost_per_decision": 2.8,
            },
            "decisions": [{"id": "D-010", "feature": "Auto email drafter", "verdict": "GO", "confidence": 81}],
            "governance_flags": [],
        },
    ]


# ─── Step 2: Detect significant metric movements ──────────────────────────────
def detect_metric_movements(audit_trail: list[dict]) -> list[dict]:
    """
    Compares the two most recent runs.
    Returns a list of metric changes with direction and magnitude.

    In production: extend to compare against rolling 7-day baseline,
    not just the previous single run.
    """
    if len(audit_trail) < 2:
        return []

    # Most recent run vs the one before
    current = audit_trail[0]["metrics"]
    previous = audit_trail[1]["metrics"]

    movements = []
    for metric, config in REVENUE_ASSUMPTIONS.items():
        if metric not in current or metric not in previous:
            continue

        delta = round(current[metric] - previous[metric], 2)
        if delta == 0:
            continue

        # Is this movement in the bad direction?
        bad = (config["direction"] == "increase" and delta > 0) or \
              (config["direction"] == "decrease" and delta < 0)

        revenue_at_risk = abs(delta) * config["revenue_per_point"] if bad else 0

        movements.append({
            "metric": metric,
            "previous": previous[metric],
            "current": current[metric],
            "delta": delta,
            "delta_unit": config["unit"],
            "bad_direction": bad,
            "revenue_at_risk_usd": round(revenue_at_risk),
        })

    # Sort: bad movements first, then by revenue at risk descending
    movements.sort(key=lambda x: (-x["bad_direction"], -x["revenue_at_risk_usd"]))
    return movements


# ─── Step 3: Build revenue impact summary ─────────────────────────────────────
def build_impact_summary(movements: list[dict], audit_trail: list[dict]) -> dict:
    """
    Aggregates movements into a single impact summary object.
    This is what gets passed to the LLM for memo generation.
    """
    total_risk = sum(m["revenue_at_risk_usd"] for m in movements if m["bad_direction"])
    total_gains = sum(
        abs(m["delta"]) * REVENUE_ASSUMPTIONS[m["metric"]]["revenue_per_point"]
        for m in movements if not m["bad_direction"]
    )

    latest = audit_trail[0]
    previous = audit_trail[1]

    return {
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "run_id_current": latest["run_id"],
        "run_id_previous": previous["run_id"],
        "total_revenue_at_risk_usd": round(total_risk),
        "total_potential_gains_usd": round(total_gains),
        "net_revenue_impact_usd": round(total_gains - total_risk),
        "governance_flags": latest["governance_flags"],
        "decisions_this_run": latest["decisions"],
        "metric_movements": movements,
    }


# ─── Step 4: Generate executive memo via LLM ──────────────────────────────────
MEMO_SYSTEM_PROMPT = """You are a Senior AI Product Manager writing a daily briefing memo for an executive audience.

Your memo must be:
- Concise: 4–6 sentences maximum
- Business-focused: translate technical metric names into plain language
- Action-oriented: end with one clear recommended action
- Honest: if numbers are estimates, say so

Output ONLY valid JSON with this exact schema, no preamble, no markdown:
{
  "subject": "<email subject line, max 10 words>",
  "headline": "<one sentence: most important thing happening right now>",
  "body": "<3–4 sentences: what moved, why it matters in revenue terms, what caused it>",
  "recommendation": "<one sentence starting with an action verb>",
  "urgency": "low" | "medium" | "high",
  "estimated_confidence": "<your confidence that estimates are directionally correct, e.g. 70%>"
}"""


def generate_memo(impact_summary: dict) -> dict:
    """
    Calls GPT-4o-mini with the impact summary.
    Returns parsed JSON memo.
    """
    user_message = f"""Generate an executive memo based on this AI system pipeline report:

{json.dumps(impact_summary, indent=2)}

Revenue assumptions: each 1pp increase in hallucination rate = ~$180 revenue risk.
Each 1pp drop in confidence = ~$220 revenue risk.
Each 1pp drop in trust = ~$200 revenue risk.
These are estimates based on historical churn correlation — flag this in your confidence score."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": MEMO_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.3,    # Low temperature: business writing should be stable
        max_tokens=600,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        memo = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: return raw text wrapped in expected structure
        memo = {
            "subject": "AI Pipeline Daily Report",
            "headline": raw[:120],
            "body": raw,
            "recommendation": "Review metrics manually.",
            "urgency": "medium",
            "estimated_confidence": "unknown",
        }

    return memo


# ─── Step 5: Format Slack message ─────────────────────────────────────────────
def format_slack_message(memo: dict, impact_summary: dict) -> dict:
    """
    Formats the memo as a Slack Block Kit message.
    Block Kit gives you clean formatting in Slack — headers, dividers, fields.

    Docs: https://api.slack.com/block-kit
    """
    urgency_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(memo["urgency"], "⚪")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{urgency_emoji} AI Pipeline Report — {impact_summary['report_date']}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{memo['headline']}*"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": memo["body"]},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Revenue at risk:*\n${impact_summary['total_revenue_at_risk_usd']:,}"},
                {"type": "mrkdwn", "text": f"*Net impact:*\n${impact_summary['net_revenue_impact_usd']:+,}"},
                {"type": "mrkdwn", "text": f"*Governance flags:*\n{', '.join(impact_summary['governance_flags']) or 'none'}"},
                {"type": "mrkdwn", "text": f"*Estimate confidence:*\n{memo['estimated_confidence']}"},
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Recommendation:* {memo['recommendation']}"},
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Runs compared: {impact_summary['run_id_previous']} → {impact_summary['run_id_current']} · Subject: {memo['subject']}"},
            ],
        },
    ]

    return {"blocks": blocks}


# ─── Step 6: Post to Slack ────────────────────────────────────────────────────
def post_to_slack(slack_payload: dict) -> bool:
    """
    Posts to the Slack incoming webhook URL from your .env.
    Returns True on success.

    To set up a Slack webhook:
    1. Go to https://api.slack.com/apps
    2. Create app → Incoming Webhooks → Activate
    3. Add webhook to workspace, copy URL into .env as SLACK_WEBHOOK_URL
    """
    if not SLACK_WEBHOOK_URL:
        print("⚠  SLACK_WEBHOOK_URL not set in .env — skipping Slack post.")
        print("   Set it up via https://api.slack.com/apps (Incoming Webhooks)")
        return False

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=slack_payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            print("✅  Memo posted to Slack.")
            return True
        else:
            print(f"❌  Slack returned {response.status_code}: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌  Slack request failed: {e}")
        return False


# ─── Main orchestration function ──────────────────────────────────────────────
def run_impact_translator(post_slack: bool = True) -> dict:
    """
    Full pipeline:
      load audit → detect movements → build summary → generate memo → post Slack

    Returns the full output dict for use by FastAPI /impact-report endpoint.
    """
    print("📊  Business Impact Translator — starting...")

    # 1. Load audit trail
    audit_trail = load_audit_trail()
    print(f"   Loaded {len(audit_trail)} audit entries.")

    # 2. Detect metric movements
    movements = detect_metric_movements(audit_trail)
    print(f"   Detected {len(movements)} metric movements.")
    for m in movements:
        direction = "▲" if m["delta"] > 0 else "▼"
        risk_label = f"  ← ${m['revenue_at_risk_usd']} risk" if m["bad_direction"] else ""
        print(f"   {direction} {m['metric']}: {m['previous']} → {m['current']} ({m['delta']:+.2f}{m['delta_unit']}){risk_label}")

    # 3. Build impact summary
    impact_summary = build_impact_summary(movements, audit_trail)
    print(f"   Revenue at risk: ${impact_summary['total_revenue_at_risk_usd']}")
    print(f"   Net revenue impact: ${impact_summary['net_revenue_impact_usd']:+}")

    # 4. Generate memo
    print("   Generating executive memo via LLM...")
    memo = generate_memo(impact_summary)
    print(f"   Memo subject: {memo['subject']}")
    print(f"   Urgency: {memo['urgency']}")
    print(f"\n--- MEMO ---")
    print(f"Headline: {memo['headline']}")
    print(f"\n{memo['body']}")
    print(f"\nRecommendation: {memo['recommendation']}")
    print(f"Confidence: {memo['estimated_confidence']}")
    print(f"---\n")

    # 5. Post to Slack
    if post_slack:
        slack_payload = format_slack_message(memo, impact_summary)
        post_to_slack(slack_payload)

    return {
        "memo": memo,
        "impact_summary": impact_summary,
        "metric_movements": movements,
    }


# ─── FastAPI integration stub ─────────────────────────────────────────────────
# In backend/routes.py, add:
#
#   from agents.impact_translator import run_impact_translator
#
#   @app.post("/impact-report")
#   async def impact_report():
#       result = run_impact_translator(post_slack=True)
#       return result
#
# The n8n workflow on Day 11 will call this endpoint nightly after /run-pipeline.


# ─── Run standalone ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_impact_translator(post_slack=True)
    print("Done. Full output:")
    print(json.dumps(result, indent=2))
