import os
import sys
import html
from datetime import datetime, timezone
import requests

COMPOSIO_API_KEY = os.environ["COMPOSIO_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
COMPOSIO_CONNECTED_ACCOUNT = os.environ.get("COMPOSIO_CONNECTED_ACCOUNT", "ca_SaF5isUHhqP7")
COMPOSIO_ENTITY_ID = os.environ.get("COMPOSIO_ENTITY_ID", "amitkumar.devnode@gmail.com")

COMPOSIO_BASE = "https://backend.composio.dev/api/v3"
GMAIL_BASE = "https://mail.google.com/mail/u/0/#inbox"

JOB_SOURCES = {
    "indeed": "Indeed",
    "freelancer": "Freelancer",
    "linkedin": "LinkedIn",
    "naukri": "Naukri",
    "glassdoor": "Glassdoor",
    "monster": "Monster",
}

def esc(text):
    return html.escape(str(text or ""))

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })
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
            "query": "from:(indeed OR freelancer OR linkedin OR naukri OR glassdoor OR monster) after:2025/01/01",
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

def detect_source(sender, subject):
    s = (sender + " " + subject).lower()
    for key, name in JOB_SOURCES.items():
        if key in s:
            return name
    return "Job Portal"

def format_summary(messages):
    today = datetime.now(timezone.utc).strftime("%b %d, %Y")
    lines = [
        f"<b>📋 Daily Job Reminder</b>",
        f"<code>{today}</code>",
        "",
    ]

    if not messages:
        lines.append("<i>No recent job-related emails found.</i>")
        return "\n".join(lines)

    job_count = {"Indeed": 0, "Freelancer": 0, "LinkedIn": 0, "Naukri": 0, "Glassdoor": 0, "Monster": 0, "Other": 0}

    for i, m in enumerate(messages, 1):
        subj = (m.get("subject") or "No subject")[:80]
        sender = (m.get("sender") or m.get("from") or "Unknown")[:50]
        msg_id = m.get("messageId", "")
        gmail_url = f"{GMAIL_BASE}/{msg_id}" if msg_id else ""
        source = detect_source(sender, subj)

        if source in job_count:
            job_count[source] += 1
        else:
            job_count["Other"] += 1

        source_emoji = {
            "Indeed": "💼",
            "Freelancer": "💻",
            "LinkedIn": "🔗",
            "Naukri": "📄",
            "Glassdoor": "🏢",
            "Monster": "👾",
        }.get(source, "📧")

        subj_clean = esc(subj)
        sender_clean = esc(sender)

        lines.append(f"<b>{i}.</b> {source_emoji} <b>{subj_clean}</b>")
        lines.append(f"   👤 {sender_clean}")
        if gmail_url:
            lines.append(f"   🔗 <a href='{gmail_url}'>Open in Gmail</a>")
        lines.append("")

    summary_lines = ["", "━━━━━━━━━━━━━━━", f"<b>📊 Summary</b>"]
    has_items = False
    for name, count in job_count.items():
        if count > 0:
            emoji = {"Indeed": "💼", "Freelancer": "💻", "LinkedIn": "🔗", "Naukri": "📄", "Glassdoor": "🏢", "Monster": "👾"}.get(name, "📧")
            summary_lines.append(f"{emoji} {name}: <b>{count}</b>")
            has_items = True
    if has_items:
        summary_lines.append("")
    summary_lines.append(f"📬 Total: <b>{len(messages)}</b> job emails")

    lines.extend(summary_lines)
    return "\n".join(lines)

def main():
    print(f"Job reminder running at {datetime.now(timezone.utc).isoformat()}")

    messages = fetch_job_emails()
    summary = format_summary(messages)
    send_telegram(summary)

    print(f"Sent {len(messages)} job emails to Telegram")

if __name__ == "__main__":
    main()
