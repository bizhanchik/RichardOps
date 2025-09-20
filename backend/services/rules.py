"""
Rules Engine module for processing log entries and generating alerts.

This module provides functionality to:
- Parse log messages for suspicious patterns
- Generate alerts with severity levels
- Maintain an in-memory alert store
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

# Global in-memory alert store (max 100 entries)
ALERTS: deque = deque(maxlen=100)

# Compiled regex patterns for performance
SECURITY_PATTERNS = [
    re.compile(r"SECURITY ATTACK", re.IGNORECASE),
    re.compile(r"authentication failed", re.IGNORECASE),
    re.compile(r"password authentication failed", re.IGNORECASE),
]

ERROR_PATTERNS = [
    re.compile(r"\bERROR\b", re.IGNORECASE),
    re.compile(r"\bFATAL\b", re.IGNORECASE),
    re.compile(r"\bOOM\b", re.IGNORECASE),
    re.compile(r"Out of memory", re.IGNORECASE),
]

# Pattern for suspicious 404 paths - matches specific suspicious patterns with 404
SUSPICIOUS_404_PATTERN = re.compile(r"(?:(/aaa\d+|/CONNECT|/[A-Z]{3,}).*?404|404.*?(/aaa\d+|/CONNECT|/[A-Z]{3,}))", re.IGNORECASE)

WARN_PATTERN = re.compile(r"\bWARN\b", re.IGNORECASE)


def process_log_entry(entry: dict) -> Optional[Dict]:
    """
    Process a log entry and determine if it should generate an alert.
    
    Args:
        entry: Dictionary with fields 'container', 'message', 'timestamp'
        
    Returns:
        Alert dictionary with severity or None if no alert triggered
        
    Example:
        >>> entry = {
        ...     "container": "web-app",
        ...     "message": "ERROR: Database connection failed",
        ...     "timestamp": "2024-01-01T12:00:00Z"
        ... }
        >>> alert = process_log_entry(entry)
        >>> print(alert["severity"])
        HIGH
    """
    if not entry or "message" not in entry:
        return None
        
    message = entry["message"]
    
    # Check for HIGH severity patterns first
    
    # Security-related alerts
    for pattern in SECURITY_PATTERNS:
        if pattern.search(message):
            return {
                "timestamp": entry["timestamp"],
                "container": entry["container"],
                "message": entry["message"],
                "severity": "HIGH"
            }
    
    # Error-related alerts
    for pattern in ERROR_PATTERNS:
        if pattern.search(message):
            return {
                "timestamp": entry["timestamp"],
                "container": entry["container"],
                "message": entry["message"],
                "severity": "HIGH"
            }
    
    # Check for MEDIUM severity patterns
    
    # Suspicious 404 paths
    if SUSPICIOUS_404_PATTERN.search(message):
        return {
            "timestamp": entry["timestamp"],
            "container": entry["container"],
            "message": entry["message"],
            "severity": "MEDIUM"
        }
    
    # Check for LOW severity patterns
    
    # Warning messages
    if WARN_PATTERN.search(message):
        return {
            "timestamp": entry["timestamp"],
            "container": entry["container"],
            "message": entry["message"],
            "severity": "LOW"
        }
    
    # No alert triggered
    return None


def add_alert(alert: Dict) -> None:
    """
    Add an alert to the global alerts store.
    
    Args:
        alert: Alert dictionary with timestamp, container, message, severity
    """
    # Add current processing timestamp for tracking
    alert["processed_at"] = datetime.now().isoformat()
    ALERTS.append(alert)


def get_alerts() -> List[Dict]:
    """
    Get the current list of alerts.
    
    Returns:
        List of alert dictionaries, newest first
    """
    # Return alerts in reverse order (newest first)
    return list(reversed(ALERTS))


def clear_alerts() -> None:
    """
    Clear all alerts from the store.
    Used primarily for testing purposes.
    """
    ALERTS.clear()


def get_alerts_count() -> int:
    """
    Get the current number of alerts in the store.
    
    Returns:
        Number of alerts currently stored
    """
    return len(ALERTS)


def get_alerts_by_severity(severity: str) -> List[Dict]:
    """
    Get alerts filtered by severity level.
    
    Args:
        severity: Severity level to filter by ("HIGH", "MEDIUM", "LOW")
        
    Returns:
        List of alerts matching the specified severity
    """
    return [alert for alert in ALERTS if alert.get("severity") == severity]