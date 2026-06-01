# agents/slack_notifier.py

import requests
import json
import os

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  # add to your .env

def send_slack_alert(message: str, alert_type: str = "info"):
    """Send a formatted alert to Slack."""
    
    emoji_map = {
        "go": "✅",
        "no-go": "🚫",
        "drift": "⚠️",
        "escalation": "🔴",
        "intel": "🔍",
        "info": "ℹ️"
    }
    
    emoji = emoji_map.get(alert_type, "ℹ️")
    
    payload = {
        "text": f"{emoji} *AI Product Loop Alert*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *AI Product Intelligence Loop*\n{message}"
                }
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Alert type: `{alert_type}`"}]
            }
        ]
    }
    
    if not SLACK_WEBHOOK_URL:
        print(f"[Slack - DRY RUN] Would send: {message[:100]}")
        return {"status": "dry_run"}

    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    return {"status": response.status_code}


# Call this from your Orchestrator/Decider after a go/no-go decision:
# send_slack_alert(f"Go/No-Go: GO — Feature: Async Interviews — Confidence: 0.84", alert_type="go")

# Call this from your monitoring/drift detection:
# send_slack_alert(f"Model drift detected — hallucination rate up 12% in last 6 hours", alert_type="drift")