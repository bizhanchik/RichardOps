#!/usr/bin/env python3
"""
Simple test script to send an email via Brevo (Sendinblue) API.
Reads configuration from a .env file (or environment variables).
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load .env if present
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
TO_EMAIL = os.getenv("ALERT_EMAIL") or os.getenv("TEST_EMAIL")
SENDER_NAME = os.getenv("ALERT_SENDER_NAME", "Monitoring Bot")
SENDER_EMAIL = os.getenv("ALERT_SENDER_EMAIL", "noreply@yourdomain.com")
TIMEOUT = int(os.getenv("BREVO_TIMEOUT", "30"))

if not BREVO_API_KEY:
    print("ERROR: BREVO_API_KEY is not set. Put it in .env or environment variables.")
    sys.exit(2)
if not TO_EMAIL:
    print("ERROR: ALERT_EMAIL or TEST_EMAIL is not set. Put it in .env or environment variables.")
    sys.exit(2)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

def build_test_html(hostname: str) -> str:
    now = datetime.utcnow().isoformat() + "Z"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>Test email from Monitoring System</h2>
        <p><strong>Host:</strong> {hostname}</p>
        <p><strong>Time (UTC):</strong> {now}</p>
        <p>This is a <em>test</em> message to verify Brevo API integration.</p>
        <hr/>
        <small>If you received this — Brevo integration works ✅</small>
      </body>
    </html>
    """
    return html

def send_test_email(to_email: str):
    hostname = os.getenv("TEST_HOST", "test-host")
    subject = os.getenv("TEST_SUBJECT", f"[Test] Monitoring email from {hostname}")
    html_content = build_test_html(hostname)

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        resp = requests.post(BREVO_URL, headers=headers, json=payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"Network error sending email: {e}")
        return False

    if resp.status_code in (200, 201):
        print(f"OK: Brevo accepted the request ({resp.status_code}).")
        # print response JSON for debugging
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print("No JSON body in response.")
        return True
    else:
        print(f"ERROR: Brevo API returned status {resp.status_code}")
        print("Response body:", resp.text)
        return False

if __name__ == "__main__":
    print("Sending test email via Brevo to:", TO_EMAIL)
    ok = send_test_email(TO_EMAIL)
    if ok:
        print("Done. Check the recipient inbox (and Brevo transactional logs).")
    else:
        print("Failed to send test email. See errors above.")
        sys.exit(1)
