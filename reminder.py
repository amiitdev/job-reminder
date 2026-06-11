import os
import sys
from datetime import datetime, timezone
import requests

COMPOSIO_API_KEY = os.environ["COMPOSIO_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
COMPOSIO_CONNECTED_ACCOUNT = os.environ.get("COMPOSIO_CONNECTED_ACCOUNT", "ca_SaF5isUHhqP7")
COMPOSIO_ENTITY_ID = os.environ.get("COMPOSIO_ENTITY_ID", "amitkumar.devnode@gmail.com")

COMPOSIO_BASE = "https://backend.composio.dev/api/v3"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    if r.ok:
        print("Telegram message sent")
    else:
        print(f"Telegram send failed: {r.text}", file=sys.stderr)

def fetch_job_emails():
    payload = {
        "connected_account_id": COMPOSIO_CONNECTED_ACCOUNT,
        "entity_id": COMPOSIO_ENTITY_ID,
        "arguments": {
            "max_results": 15,
            "query": "from:(indeed OR freelancer OR linkedin OR naukri OR glassdoor) after:2025/01/01",
            "include_payload": True,
            "verbose": True,
        },
    }
    r = requests.post(
        f"{COMPOSIO_BASE}/tools/execute/GMAIL_FETCH_EMAILS",
        json=payload,
        headers={"x-api-key": COMPOSIO_API_KEY},
        timeout=30,
    )
    if not r.ok:
        print(f"API error: {r.text}", file=sys.stderr)
        return []
    return r.json().get("data", {}).get("messages", [])

def format_summary(messages):
    today = datetime.now(timezone.utc).strftime("%b %d, %Y")
    lines = [f"Daily Job Reminder - {today}", ""]

    if not messages:
        lines.append("No recent job-related emails found.")
        return "\n".join(lines)

    for i, m in enumerate(messages, 1):
        subj = (m.get("subject") or "No subject")[:60]
        sender = (m.get("sender") or m.get("from") or "Unknown")[:40]
        lines.append(f"{i}. {subj}")
        lines.append(f"   {sender}")
        lines.append("")

    lines.append("---")
    lines.append(f"Total: {len(messages)} job emails")
    return "\n".join(lines)

def main():
    print(f"Job reminder running at {datetime.now(timezone.utc).isoformat()}")

    messages = fetch_job_emails()
    summary = format_summary(messages)
    send_telegram(summary)

    print(f"Sent {len(messages)} job emails to Telegram")

if __name__ == "__main__":
    main()
