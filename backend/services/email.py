"""
Email service module for sending alerts using Brevo (Sendinblue) API.
"""

import os
import requests
from typing import Dict, Any


def send_alert_email(subject: str, content: str, to_email: str) -> None:
    """
    Send an alert email using Brevo (Sendinblue) API.
    
    Args:
        subject: Email subject line
        content: HTML email content
        to_email: Recipient email address
        
    Raises:
        ValueError: If BREVO_API_KEY is not set
        requests.RequestException: If the API request fails
        Exception: If the response status is not 200
    """
    # Get API key from environment
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        raise ValueError("BREVO_API_KEY environment variable is not set")
    
    # Brevo API endpoint
    url = "https://api.brevo.com/v3/smtp/email"
    
    # Request headers
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    sender_email = os.environ.get("ALERT_SENDER_EMAIL")

    # Email payload
    payload = {
        "sender": {
            "name": "Monitoring Bot",
            "email": sender_email
        },
        "to": [
            {
                "email": to_email
            }
        ],
        "subject": subject,
        "htmlContent": content
    }
    
    # Send the email
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Check if request was successful
        if response.status_code != 201:  # Brevo returns 201 for successful email creation
            raise Exception(
                f"Failed to send email. Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to send email via Brevo API: {str(e)}")


def format_alert_email_content(
    host: str,
    server_id: str = None,
    env: str = None,
    alerts: list = None,
    score: float = 0.0
) -> str:
    """
    Format the HTML content for alert emails.
    
    Args:
        host: Server hostname
        server_id: Server ID (optional)
        env: Environment (optional)
        alerts: List of alert strings
        score: Alert score
        
    Returns:
        Formatted HTML email content
    """
    alerts = alerts or []
    
    # Build alert list HTML
    alert_items = ""
    for alert in alerts:
        alert_items += f"<li style='margin: 5px 0; color: #d32f2f;'><strong>{alert}</strong></li>"
    
    # Determine severity color based on score
    if score >= 0.5:
        severity_color = "#d32f2f"  # Red
        severity_text = "HIGH"
    elif score >= 0.3:
        severity_color = "#f57c00"  # Orange
        severity_text = "MEDIUM"
    else:
        severity_color = "#388e3c"  # Green
        severity_text = "LOW"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Server Alert</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; border-left: 4px solid {severity_color}; padding: 20px; margin-bottom: 20px;">
            <h1 style="color: {severity_color}; margin: 0 0 10px 0;">🚨 Server Alert - {severity_text} Severity</h1>
            <p style="margin: 0; font-size: 16px;">Alert detected on server <strong>{host}</strong></p>
        </div>
        
        <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
            <h2 style="color: #333; margin-top: 0;">Server Information</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; width: 30%;">Host:</td>
                    <td style="padding: 8px 0;">{host}</td>
                </tr>
                {f'<tr><td style="padding: 8px 0; font-weight: bold;">Server ID:</td><td style="padding: 8px 0;">{server_id}</td></tr>' if server_id else ''}
                {f'<tr><td style="padding: 8px 0; font-weight: bold;">Environment:</td><td style="padding: 8px 0;">{env}</td></tr>' if env else ''}
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Alert Score:</td>
                    <td style="padding: 8px 0; color: {severity_color}; font-weight: bold;">{score:.2f}</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 5px; padding: 20px;">
            <h2 style="color: #333; margin-top: 0;">Active Alerts</h2>
            <ul style="margin: 0; padding-left: 20px;">
                {alert_items}
            </ul>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
            <p>This is an automated alert from the Monitoring System. Please investigate the server immediately.</p>
            <p>Generated at: {host} monitoring system</p>
        </div>
    </body>
    </html>
    """
    
    return html_content