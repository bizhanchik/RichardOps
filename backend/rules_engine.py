"""
Rules Engine module for analyzing HTTP requests and detecting security attacks.

This module provides functionality to:
- Analyze HTTP request logs and events for suspicious patterns
- Detect various attack types: fuzzing/probing, open redirect, path traversal, 
  template injection, SQL injection, XSS, null byte injection, long input overflow,
  credential brute force, and other attacks
- Assign confidence scores and generate email alerts for high-confidence threats
- Return structured analysis results following a specific JSON schema
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
from urllib.parse import unquote

# Global in-memory alert store (max 100 entries)
ATTACK_ALERTS: deque = deque(maxlen=100)

# Configure logger
logger = logging.getLogger("rules_engine")

# Attack pattern definitions with compiled regex for performance
ATTACK_PATTERNS = {
    "path_traversal": [
        re.compile(r"\.\.[\\/]", re.IGNORECASE),
        re.compile(r"\.\.%2f", re.IGNORECASE),
        re.compile(r"\.\.%5c", re.IGNORECASE),
        re.compile(r"\.\.%252f", re.IGNORECASE),
        re.compile(r"\.\.%255c", re.IGNORECASE),
        re.compile(r"\.\.[\\/].*?etc[\\/]passwd", re.IGNORECASE),
        re.compile(r"\.\.[\\/].*?windows[\\/]system32", re.IGNORECASE),
        re.compile(r"\.\.[\\/].*?boot\.ini", re.IGNORECASE),
    ],
    
    "sql_injection": [
        re.compile(r"'\s*or\s*'1'\s*=\s*'1", re.IGNORECASE),
        re.compile(r"'\s*or\s*1\s*=\s*1", re.IGNORECASE),
        re.compile(r"union\s+select", re.IGNORECASE),
        re.compile(r"drop\s+table", re.IGNORECASE),
        re.compile(r"insert\s+into", re.IGNORECASE),
        re.compile(r"delete\s+from", re.IGNORECASE),
        re.compile(r"update\s+.*\s+set", re.IGNORECASE),
        re.compile(r"exec\s*\(", re.IGNORECASE),
        re.compile(r"sp_executesql", re.IGNORECASE),
        re.compile(r"xp_cmdshell", re.IGNORECASE),
        re.compile(r";\s*drop\s+", re.IGNORECASE),
        re.compile(r"'\s*;\s*--", re.IGNORECASE),
        re.compile(r"'\s*#", re.IGNORECASE),
    ],
    
    "xss": [
        re.compile(r"<script[^>]*>", re.IGNORECASE),
        re.compile(r"</script>", re.IGNORECASE),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe[^>]*>", re.IGNORECASE),
        re.compile(r"<object[^>]*>", re.IGNORECASE),
        re.compile(r"<embed[^>]*>", re.IGNORECASE),
        re.compile(r"<img[^>]*onerror", re.IGNORECASE),
        re.compile(r"<svg[^>]*onload", re.IGNORECASE),
        re.compile(r"alert\s*\(", re.IGNORECASE),
        re.compile(r"document\.cookie", re.IGNORECASE),
        re.compile(r"eval\s*\(", re.IGNORECASE),
    ],
    
    "template_injection": [
        re.compile(r"\{\{.*?\}\}", re.IGNORECASE),
        re.compile(r"\{\{.*?7\*7.*?\}\}", re.IGNORECASE),
        re.compile(r"\{\{.*?config.*?\}\}", re.IGNORECASE),
        re.compile(r"\{\{.*?request.*?\}\}", re.IGNORECASE),
        re.compile(r"\{\{.*?self.*?\}\}", re.IGNORECASE),
        re.compile(r"\$\{.*?\}", re.IGNORECASE),
        re.compile(r"\$\{.*?java\.lang.*?\}", re.IGNORECASE),
        re.compile(r"<%.*?%>", re.IGNORECASE),
        re.compile(r"#\{.*?\}", re.IGNORECASE),
    ],
    
    "null_byte_injection": [
        re.compile(r"%00", re.IGNORECASE),
        re.compile(r"\\x00", re.IGNORECASE),
        re.compile(r"\\0", re.IGNORECASE),
        re.compile(r"\x00"),
    ],
    
    "open_redirect": [
        re.compile(r"redirect.*?=.*?https?://", re.IGNORECASE),
        re.compile(r"url.*?=.*?https?://", re.IGNORECASE),
        re.compile(r"return.*?=.*?https?://", re.IGNORECASE),
        re.compile(r"next.*?=.*?https?://", re.IGNORECASE),
        re.compile(r"goto.*?=.*?https?://", re.IGNORECASE),
        re.compile(r"target.*?=.*?https?://", re.IGNORECASE),
        re.compile(r"destination.*?=.*?https?://", re.IGNORECASE),
    ],
    
    "fuzzing_probing": [
        re.compile(r"/\.well-known/", re.IGNORECASE),
        re.compile(r"/admin", re.IGNORECASE),
        re.compile(r"/wp-admin", re.IGNORECASE),
        re.compile(r"/phpmyadmin", re.IGNORECASE),
        re.compile(r"/config\.php", re.IGNORECASE),
        re.compile(r"/\.env", re.IGNORECASE),
        re.compile(r"/\.git/", re.IGNORECASE),
        re.compile(r"/backup", re.IGNORECASE),
        re.compile(r"/test", re.IGNORECASE),
        re.compile(r"/debug", re.IGNORECASE),
        re.compile(r"/api/v\d+", re.IGNORECASE),
        re.compile(r"/robots\.txt", re.IGNORECASE),
        re.compile(r"/sitemap\.xml", re.IGNORECASE),
        re.compile(r"/(aaa\d+|CONNECT|[A-Z]{3,})", re.IGNORECASE),
    ],
    
    "credential_brute_force": [
        re.compile(r"authentication\s+failed", re.IGNORECASE),
        re.compile(r"password\s+authentication\s+failed", re.IGNORECASE),
        re.compile(r"invalid\s+credentials", re.IGNORECASE),
        re.compile(r"login\s+failed", re.IGNORECASE),
        re.compile(r"unauthorized", re.IGNORECASE),
        re.compile(r"access\s+denied", re.IGNORECASE),
        re.compile(r"forbidden", re.IGNORECASE),
    ],
}

# Long input patterns
LONG_INPUT_THRESHOLD = 1000  # Characters
EXTREMELY_LONG_THRESHOLD = 5000  # Characters


def extract_evidence_from_text(text: str, attack_type: str) -> List[str]:
    """
    Extract specific evidence patterns from text based on attack type.
    
    Args:
        text: The text to analyze
        attack_type: The type of attack to look for evidence
        
    Returns:
        List of evidence strings found
    """
    evidence = []
    
    if attack_type in ATTACK_PATTERNS:
        for pattern in ATTACK_PATTERNS[attack_type]:
            matches = pattern.findall(text)
            if matches:
                # Add unique matches to evidence
                for match in matches:
                    if isinstance(match, tuple):
                        match = ''.join(match)
                    if match and match not in evidence:
                        evidence.append(match[:100])  # Limit evidence length
    
    return evidence


def calculate_confidence(attack_type: str, evidence: List[str], text: str) -> float:
    """
    Calculate confidence score based on attack type, evidence, and context.
    
    Args:
        attack_type: The detected attack type
        evidence: List of evidence found
        text: The original text being analyzed
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    base_confidence = 0.3
    
    # Evidence count factor
    evidence_factor = min(len(evidence) * 0.2, 0.4)
    
    # Attack type specific adjustments
    type_multipliers = {
        "sql_injection": 1.2,
        "xss": 1.1,
        "path_traversal": 1.15,
        "template_injection": 1.1,
        "null_byte_injection": 1.3,
        "open_redirect": 1.0,
        "fuzzing_probing": 0.8,
        "credential_brute_force": 0.9,
        "long_input_overflow": 0.7,
        "other": 0.6,
    }
    
    multiplier = type_multipliers.get(attack_type, 0.8)
    
    # Length factor for certain attacks
    length_factor = 0.0
    if len(text) > EXTREMELY_LONG_THRESHOLD:
        length_factor = 0.2
    elif len(text) > LONG_INPUT_THRESHOLD:
        length_factor = 0.1
    
    # Calculate final confidence
    confidence = (base_confidence + evidence_factor + length_factor) * multiplier
    
    # Cap at 1.0
    return min(confidence, 1.0)


def analyze_single_log_entry(log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Analyze a single log entry for attack patterns.
    
    Args:
        log_entry: Dictionary containing log entry data
        
    Returns:
        Analysis result or None if no attack detected
    """
    if not log_entry or "message" not in log_entry:
        return None
    
    message = log_entry["message"]
    decoded_message = unquote(message)  # URL decode for better pattern matching
    
    # Check for each attack type
    for attack_type, patterns in ATTACK_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(decoded_message) or pattern.search(message):
                evidence = extract_evidence_from_text(decoded_message, attack_type)
                if not evidence:
                    evidence = extract_evidence_from_text(message, attack_type)
                
                confidence = calculate_confidence(attack_type, evidence, decoded_message)
                
                return {
                    "attack_type": attack_type,
                    "evidence": evidence,
                    "confidence": confidence,
                    "log_entry": log_entry
                }
    
    # Check for long input overflow
    if len(message) > LONG_INPUT_THRESHOLD:
        evidence = [f"Input length: {len(message)} characters"]
        confidence = calculate_confidence("long_input_overflow", evidence, message)
        
        return {
            "attack_type": "long_input_overflow",
            "evidence": evidence,
            "confidence": confidence,
            "log_entry": log_entry
        }
    
    return None


def generate_email_content(attack_type: str, confidence: float, evidence: List[str], 
                         explanation: str, recommended_action: str) -> Dict[str, Any]:
    """
    Generate email content for high-confidence attacks.
    
    Args:
        attack_type: The detected attack type
        confidence: Confidence score
        evidence: List of evidence
        explanation: Attack explanation
        recommended_action: Recommended action
        
    Returns:
        Email configuration dictionary
    """
    # Default recipients (should be configurable)
    recipients = ["security@company.com"]  # This should come from environment or config
    
    # Generate subject
    severity = "HIGH" if confidence >= 0.8 else "MEDIUM"
    subject = f"🚨 {severity} Security Alert: {attack_type.replace('_', ' ').title()} Detected"
    
    # Generate email body
    evidence_list = "\n".join([f"- {ev}" for ev in evidence[:5]])  # Limit to 5 pieces of evidence
    
    body = f"""Security Alert Detected

Attack Type: {attack_type.replace('_', ' ').title()}
Confidence Score: {confidence:.2f}
Severity: {severity}

Explanation:
{explanation}

Evidence Found:
{evidence_list}

Recommended Action:
{recommended_action}

Timestamp: {datetime.now().isoformat()}

This is an automated security alert. Please investigate immediately.
"""
    
    return {
        "should_send": True,
        "recipients": recipients,
        "subject": subject,
        "body": body
    }


def analyze_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single HTTP request log or batch of logs for security attacks.
    
    Args:
        event: Dictionary containing request/log data with fields like:
               - logs: List of log entries
               - docker_events: List of docker events  
               - metrics: System metrics
               - ip: Client IP (optional)
               
    Returns:
        Analysis result following the required JSON schema
    """
    # Initialize result structure
    result = {
        "attack_detected": False,
        "attack_type": "none",
        "confidence": 0.0,
        "explanation": "No suspicious patterns detected in the analyzed data.",
        "evidence": [],
        "recommended_action": "Continue normal monitoring.",
        "email": {
            "should_send": False,
            "recipients": [],
            "subject": "",
            "body": ""
        }
    }
    
    try:
        # Analyze logs if present
        if "logs" in event and event["logs"]:
            highest_confidence = 0.0
            best_match = None
            all_evidence = []
            
            for log_entry in event["logs"]:
                analysis = analyze_single_log_entry(log_entry)
                if analysis and analysis["confidence"] > highest_confidence:
                    highest_confidence = analysis["confidence"]
                    best_match = analysis
                    all_evidence.extend(analysis["evidence"])
            
            if best_match:
                attack_type = best_match["attack_type"]
                confidence = best_match["confidence"]
                
                # Update result
                result["attack_detected"] = True
                result["attack_type"] = attack_type
                result["confidence"] = confidence
                result["evidence"] = list(set(all_evidence))  # Remove duplicates
                
                # Generate explanation
                result["explanation"] = f"Detected {attack_type.replace('_', ' ')} attack pattern with {confidence:.1%} confidence. "
                result["explanation"] += f"Found {len(result['evidence'])} pieces of evidence in log entries."
                
                # Generate recommended action
                action_map = {
                    "sql_injection": "Block the source IP immediately and review database access logs. Check for data exfiltration.",
                    "xss": "Sanitize user inputs and implement Content Security Policy. Review affected pages.",
                    "path_traversal": "Block the source IP and audit file system access. Check for unauthorized file access.",
                    "template_injection": "Review template rendering code and block the source IP. Check for code execution.",
                    "null_byte_injection": "Block the source IP and review file handling code. Check for file system manipulation.",
                    "open_redirect": "Review redirect functionality and block malicious redirects. Check for phishing attempts.",
                    "fuzzing_probing": "Monitor the source IP for continued scanning. Consider rate limiting.",
                    "credential_brute_force": "Block the source IP temporarily and review authentication logs. Check for successful logins.",
                    "long_input_overflow": "Implement input length validation and monitor for buffer overflow attempts.",
                    "other": "Investigate the suspicious activity and consider blocking the source IP."
                }
                
                result["recommended_action"] = action_map.get(attack_type, "Investigate the detected pattern and take appropriate security measures.")
                
                # Generate email if confidence is high enough
                if confidence >= 0.7:
                    result["email"] = generate_email_content(
                        attack_type, confidence, result["evidence"],
                        result["explanation"], result["recommended_action"]
                    )
        
        # Store the alert in memory
        if result["attack_detected"]:
            alert_entry = {
                "timestamp": datetime.now().isoformat(),
                "analysis": result.copy(),
                "source_event": {
                    "log_count": len(event.get("logs", [])),
                    "has_docker_events": bool(event.get("docker_events")),
                    "has_metrics": bool(event.get("metrics")),
                    "client_ip": event.get("ip", "unknown")
                }
            }
            ATTACK_ALERTS.append(alert_entry)
            
            # Log the detection
            logger.warning(f"Attack detected: {result['attack_type']} (confidence: {result['confidence']:.2f}) - {result['explanation']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_request: {str(e)}")
        result["explanation"] = f"Error during analysis: {str(e)}"
        return result


def get_stored_alerts(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get stored attack alerts from memory.
    
    Args:
        limit: Maximum number of alerts to return
        
    Returns:
        List of stored alerts, newest first
    """
    alerts = list(ATTACK_ALERTS)
    alerts.reverse()  # Newest first
    return alerts[:limit]


def clear_stored_alerts() -> None:
    """
    Clear all stored alerts from memory.
    Used primarily for testing purposes.
    """
    ATTACK_ALERTS.clear()


def get_alerts_count() -> int:
    """
    Get the current number of stored alerts.
    
    Returns:
        Number of alerts currently stored
    """
    return len(ATTACK_ALERTS)