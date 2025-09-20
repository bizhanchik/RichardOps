"""
Alert service module for determining when to send email notifications.
"""

from typing import List

# Define critical alerts that should trigger email notifications
CRITICAL_ALERTS = [
    "CPU_SPIKE",
    "BRUTE_FORCE", 
    "SHELL_IN_CONTAINER"
]


def should_send_email(alerts: List[str]) -> bool:
    """
    Determine if an email alert should be sent based on the list of alerts.
    
    This function checks if any of the provided alerts match the critical alert types.
    For BRUTE_FORCE alerts, it performs a prefix match to handle IP-specific alerts
    like "BRUTE_FORCE:192.168.1.100".
    
    Args:
        alerts: List of alert strings from the monitoring payload
        
    Returns:
        True if any alert matches critical alert criteria, False otherwise
    """
    if not alerts:
        return False
    
    for alert in alerts:
        # Check for exact matches first
        if alert in CRITICAL_ALERTS:
            return True
        
        # Check for prefix matches (e.g., "BRUTE_FORCE:IP" matches "BRUTE_FORCE")
        for critical_alert in CRITICAL_ALERTS:
            if alert.startswith(f"{critical_alert}:"):
                return True
    
    return False


def get_alert_severity(alerts: List[str]) -> str:
    """
    Determine the severity level based on the types of alerts present.
    
    Args:
        alerts: List of alert strings
        
    Returns:
        Severity level as string: "HIGH", "MEDIUM", or "LOW"
    """
    if not alerts:
        return "LOW"
    
    # Count different types of critical alerts
    critical_count = 0
    has_shell_access = False
    has_brute_force = False
    
    for alert in alerts:
        if alert == "SHELL_IN_CONTAINER":
            has_shell_access = True
            critical_count += 1
        elif alert.startswith("BRUTE_FORCE"):
            has_brute_force = True
            critical_count += 1
        elif alert in CRITICAL_ALERTS:
            critical_count += 1
    
    # Determine severity based on alert types and count
    if has_shell_access or critical_count >= 2:
        return "HIGH"
    elif has_brute_force or critical_count >= 1:
        return "MEDIUM"
    else:
        return "LOW"


def format_alert_summary(alerts: List[str]) -> str:
    """
    Create a human-readable summary of alerts for email content.
    
    Args:
        alerts: List of alert strings
        
    Returns:
        Formatted string summarizing the alerts
    """
    if not alerts:
        return "No active alerts"
    
    alert_counts = {}
    brute_force_ips = []
    
    for alert in alerts:
        if alert.startswith("BRUTE_FORCE:"):
            ip = alert.split(":", 1)[1]
            brute_force_ips.append(ip)
            alert_type = "BRUTE_FORCE"
        else:
            alert_type = alert
        
        alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
    
    summary_parts = []
    
    for alert_type, count in alert_counts.items():
        if alert_type == "BRUTE_FORCE" and brute_force_ips:
            if count == 1:
                summary_parts.append(f"Brute force attack from {brute_force_ips[0]}")
            else:
                summary_parts.append(f"Brute force attacks from {count} IPs: {', '.join(brute_force_ips[:3])}{'...' if len(brute_force_ips) > 3 else ''}")
        elif alert_type == "CPU_SPIKE":
            summary_parts.append(f"CPU usage spike detected")
        elif alert_type == "SHELL_IN_CONTAINER":
            summary_parts.append(f"Shell access detected in container")
        else:
            if count == 1:
                summary_parts.append(f"{alert_type.replace('_', ' ').title()}")
            else:
                summary_parts.append(f"{alert_type.replace('_', ' ').title()} ({count} occurrences)")
    
    return "; ".join(summary_parts)