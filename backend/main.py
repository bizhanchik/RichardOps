import json
import logging
import os
import hmac
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from models import Payload
from services.alerts import should_send_email, get_alert_severity, format_alert_summary
from services.email import send_alert_email, format_alert_email_content
from services.rules import process_log_entry, get_alerts, add_alert
from rules_engine import analyze_request, get_stored_alerts

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Get secret from environment variable
SECRET = os.environ.get("INGEST_SECRET", "")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(logs_dir / "ingest.log", mode="a")  # File output
    ]
)

logger = logging.getLogger("monitoring-backend")

# Configure dedicated alerts logger for structured JSON logging
alerts_logger = logging.getLogger("alerts")
alerts_logger.setLevel(logging.INFO)
alerts_handler = logging.FileHandler(logs_dir / "alerts.log", mode="a")
alerts_handler.setFormatter(logging.Formatter("%(message)s"))  # JSON only, no extra formatting
alerts_logger.addHandler(alerts_handler)
alerts_logger.propagate = False  # Don't propagate to root logger

# Create FastAPI app
app = FastAPI(
    title="Monitoring Data Ingestion API",
    description="FastAPI backend to receive monitoring data from Go agent",
    version="1.0.0"
)


# Fixed: HMAC signature and timestamp verification function
def verify_hmac_signature(signature: str, timestamp: str, body: bytes) -> None:
    """
    Verify HMAC signature and timestamp for request authentication.
    
    Args:
        signature: The X-Agent-Signature header value
        timestamp: The X-Agent-Timestamp header value  
        body: Raw request body bytes
        
    Raises:
        HTTPException: If timestamp is stale or signature is invalid
    """
    if not SECRET:
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    # Check timestamp freshness (within 120 seconds)
    try:
        ts_int = int(timestamp)
        if abs(time.time() - ts_int) > 120:
            raise HTTPException(status_code=400, detail="Request timestamp is stale")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")
    
    # Compute expected HMAC signature
    message = f"{timestamp}.{body.decode()}".encode()
    expected_signature = hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()
    
    # Remove 'sha256=' prefix if present and compare
    provided_signature = signature.replace("sha256=", "")
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


@app.post("/ingest")
async def ingest_monitoring_data(
    request: Request,
    payload: Payload,
    x_agent_signature: str = Header(..., alias="X-Agent-Signature"),
    x_agent_timestamp: str = Header(..., alias="X-Agent-Timestamp")
) -> Dict[str, str]:
    """
    Receive monitoring data from Go agent and log it.
    
    Args:
        payload: The monitoring payload from the Go agent
        
    Returns:
        Success message with timestamp
    """
    try:
        # Fixed: Verify HMAC signature and timestamp before processing
        raw_body = await request.body()
        verify_hmac_signature(x_agent_signature, x_agent_timestamp, raw_body)
        
        # Convert payload to dict for logging
        payload_dict = payload.model_dump()
        
        # Pretty print to console
        print("\n" + "="*80)
        print(f"📊 MONITORING DATA RECEIVED - {datetime.now().isoformat()}")
        print("="*80)
        print(f"🖥️  Host: {payload.host}")
        print(f"🆔 Server ID: {payload.server_id or 'N/A'}")
        print(f"🌍 Environment: {payload.env or 'N/A'}")
        print(f"👥 Owner Team: {payload.owner_team or 'N/A'}")
        print(f"⏰ Timestamp: {payload.timestamp}")
        print(f"📈 Score: {payload.score}")
        
        # System Metrics
        print("\n📊 SYSTEM METRICS:")
        print(f"  CPU Usage: {payload.metrics.cpu_usage:.1f}%")
        print(f"  Memory Usage: {payload.metrics.memory_usage:.1f}%")
        print(f"  Disk Usage: {payload.metrics.disk_usage:.1f}%")
        print(f"  Network RX: {payload.metrics.network_rx_bytes_per_sec:,} bytes/sec")
        print(f"  Network TX: {payload.metrics.network_tx_bytes_per_sec:,} bytes/sec")
        print(f"  TCP Connections: {payload.metrics.tcp_connections}")
        
        # Docker Events
        if payload.docker_events:
            print(f"\n🐳 DOCKER EVENTS ({len(payload.docker_events)}):")
            for event in payload.docker_events:
                print(f"  {event.timestamp} - {event.type}/{event.action} - {event.container} ({event.image})")
        
        # Logs
        if payload.logs:
            print(f"\n📝 CONTAINER LOGS ({len(payload.logs)}):")
            for log_entry in payload.logs:
                print(f"  [{log_entry.container}] {log_entry.timestamp} - {log_entry.message[:100]}{'...' if len(log_entry.message) > 100 else ''}")
        
        # Local Alerts
        if payload.local_alerts:
            print(f"\n🚨 LOCAL ALERTS ({len(payload.local_alerts)}):")
            for alert in payload.local_alerts:
                print(f"  ⚠️  {alert}")
        
        print("="*80 + "\n")
        
        # Log to file (structured JSON) - convert datetime objects to ISO strings
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "monitoring_data_received",
            "payload": payload_dict
        }
        
        logger.info(f"Monitoring data received from {payload.host}: {json.dumps(log_entry, indent=2, default=json_serializer)}")
        
        # Analyze request through rules engine for attack detection
        attack_analysis = None
        try:
            # Prepare event data for rules engine analysis
            event_data = {
                "logs": [
                    {
                        "container": log.container,
                        "message": log.message,
                        "timestamp": log.timestamp.isoformat() if hasattr(log.timestamp, 'isoformat') else str(log.timestamp)
                    } for log in payload.logs
                ] if payload.logs else [],
                "docker_events": [
                    {
                        "type": event.type,
                        "action": event.action,
                        "container": event.container,
                        "image": event.image,
                        "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp)
                    } for event in payload.docker_events
                ] if payload.docker_events else [],
                "metrics": {
                    "cpu_usage": payload.metrics.cpu_usage,
                    "memory_usage": payload.metrics.memory_usage,
                    "disk_usage": payload.metrics.disk_usage,
                    "network_rx_bytes_per_sec": payload.metrics.network_rx_bytes_per_sec,
                    "network_tx_bytes_per_sec": payload.metrics.network_tx_bytes_per_sec,
                    "tcp_connections": payload.metrics.tcp_connections
                } if payload.metrics else {},
                "ip": request.client.host if hasattr(request, 'client') and request.client else "unknown"
            }
            
            # Analyze the event for attacks
            attack_analysis = analyze_request(event_data)
            
            # Log the analysis result (always log, even if no attack detected)
            if attack_analysis["attack_detected"]:
                logger.warning(f"SECURITY ALERT: {attack_analysis['attack_type']} detected with {attack_analysis['confidence']:.1%} confidence - {attack_analysis['explanation']}")
            else:
                logger.info(f"Security analysis completed - no threats detected")
            
            # Log all analysis results to dedicated alerts.log file as structured JSON
            alert_log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "security_analysis",
                "host": payload.host,
                "server_id": payload.server_id,
                "client_ip": event_data["ip"],
                "analysis": attack_analysis,
                "log_count": len(event_data["logs"]),
                "docker_events_count": len(event_data["docker_events"]),
                "has_metrics": bool(event_data["metrics"])
            }
            alerts_logger.info(json.dumps(alert_log_entry, default=json_serializer))
            
            # Send email alert if attack detected and confidence is high
            if attack_analysis["attack_detected"] and attack_analysis["email"]["should_send"]:
                try:
                    alert_email = os.environ.get("ALERT_EMAIL")
                    if alert_email:
                        # Use the email content generated by rules engine
                        send_alert_email(
                            attack_analysis["email"]["subject"],
                            attack_analysis["email"]["body"],
                            alert_email
                        )
                        logger.info(f"Security alert email sent to {alert_email} for {attack_analysis['attack_type']} attack")
                    else:
                        logger.warning("ALERT_EMAIL environment variable not set, skipping security alert email")
                except Exception as e:
                    logger.error(f"Failed to send security alert email: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in rules engine analysis: {str(e)}")
            attack_analysis = {
                "attack_detected": False,
                "attack_type": "none",
                "confidence": 0.0,
                "explanation": f"Analysis error: {str(e)}",
                "evidence": [],
                "recommended_action": "Check system logs for analysis errors.",
                "email": {"should_send": False, "recipients": [], "subject": "", "body": ""}
            }
        
        # Process logs through rules engine
        high_severity_alerts = []
        if payload.logs:
            for log in payload.logs:
                # Convert LogEntry to dict for rules processing
                log_dict = {
                    "container": log.container,
                    "message": log.message,
                    "timestamp": log.timestamp.isoformat() if hasattr(log.timestamp, 'isoformat') else str(log.timestamp)
                }
                
                # Process through rules engine
                alert = process_log_entry(log_dict)
                if alert:
                    # Add MEDIUM and HIGH severity alerts to the global store
                    if alert["severity"] in ["MEDIUM", "HIGH"]:
                        add_alert(alert)
                        logger.info(f"Alert generated: {alert['severity']} - {alert['container']} - {alert['message'][:100]}")
                    
                    # Track HIGH severity alerts for immediate email notification
                    if alert["severity"] == "HIGH":
                        high_severity_alerts.append(alert)
        
        # Send immediate email for HIGH severity alerts
        if high_severity_alerts:
            try:
                alert_email = os.environ.get("ALERT_EMAIL")
                if alert_email:
                    # Build email content for HIGH severity alerts
                    subject = f"🚨 HIGH SEVERITY Alert - Server {payload.host}"
                    alert_messages = [f"[{alert['container']}] {alert['message']}" for alert in high_severity_alerts]
                    content = format_alert_email_content(
                        host=payload.host,
                        server_id=payload.server_id,
                        env=payload.env,
                        alerts=alert_messages,
                        score=payload.score
                    )
                    
                    # Send the alert email
                    send_alert_email(subject, content, alert_email)
                    logger.info(f"HIGH severity alert email sent to {alert_email} for {len(high_severity_alerts)} alerts")
                else:
                    logger.warning("ALERT_EMAIL environment variable not set, skipping HIGH severity email notification")
            except Exception as e:
                logger.error(f"Failed to send HIGH severity alert email: {str(e)}")
        
        # Check if email alert should be sent
        if should_send_email(payload.local_alerts):
            try:
                # Get recipient email from environment variable
                alert_email = os.environ.get("ALERT_EMAIL")
                if alert_email:
                    # Build email content
                    subject = f"🚨 Server {payload.host} Alert"
                    content = format_alert_email_content(
                        host=payload.host,
                        server_id=payload.server_id,
                        env=payload.env,
                        alerts=payload.local_alerts,
                        score=payload.score
                    )
                    
                    # Send the alert email
                    send_alert_email(subject, content, alert_email)
                    logger.info(f"Alert email sent to {alert_email} for {payload.host}")
                else:
                    logger.warning("ALERT_EMAIL environment variable not set, skipping email notification")
            except Exception as e:
                logger.error(f"Failed to send alert email: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Monitoring data received from {payload.host}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing monitoring data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing monitoring data: {str(e)}")


@app.get("/alerts")
async def get_current_alerts() -> Dict[str, Any]:
    """
    Get current alerts from both the rules engine and attack detection system.
    
    Returns:
        JSON response with current alerts list from both systems
    """
    try:
        # Get alerts from the original rules system
        rules_alerts = get_alerts()
        
        # Get alerts from the new attack detection system
        attack_alerts = get_stored_alerts(50)  # Get last 50 attack alerts
        
        # Combine and format alerts
        combined_alerts = []
        
        # Add attack detection alerts (higher priority)
        for alert in attack_alerts:
            combined_alerts.append({
                "id": f"attack_{alert['timestamp']}",
                "timestamp": alert["timestamp"],
                "type": "security_attack",
                "attack_type": alert["analysis"]["attack_type"],
                "confidence": alert["analysis"]["confidence"],
                "severity": "HIGH" if alert["analysis"]["confidence"] >= 0.8 else "MEDIUM" if alert["analysis"]["confidence"] >= 0.7 else "LOW",
                "message": alert["analysis"]["explanation"],
                "evidence": alert["analysis"]["evidence"],
                "recommended_action": alert["analysis"]["recommended_action"],
                "source": {
                    "log_count": alert["source_event"]["log_count"],
                    "client_ip": alert["source_event"]["client_ip"]
                }
            })
        
        # Add original rules alerts
        for alert in rules_alerts:
            combined_alerts.append({
                "id": f"rule_{alert.get('processed_at', alert['timestamp'])}",
                "timestamp": alert["timestamp"],
                "type": "log_pattern",
                "attack_type": "log_anomaly",
                "confidence": 0.5,  # Default confidence for rule-based alerts
                "severity": alert["severity"],
                "message": alert["message"],
                "evidence": [alert["message"][:200]],  # First 200 chars as evidence
                "recommended_action": "Review log entry for potential issues",
                "source": {
                    "container": alert["container"]
                }
            })
        
        # Sort by timestamp (newest first)
        combined_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit to 100 most recent alerts
        combined_alerts = combined_alerts[:100]
        
        return {
            "status": "success",
            "count": len(combined_alerts),
            "alerts": combined_alerts,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "attack_alerts": len(attack_alerts),
                "rule_alerts": len(rules_alerts),
                "high_severity": len([a for a in combined_alerts if a["severity"] == "HIGH"]),
                "medium_severity": len([a for a in combined_alerts if a["severity"] == "MEDIUM"]),
                "low_severity": len([a for a in combined_alerts if a["severity"] == "LOW"])
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")


@app.get("/healthz")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Status OK message
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "monitoring-backend"
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with basic info.
    
    Returns:
        API information
    """
    return {
        "service": "Monitoring Data Ingestion API",
        "version": "1.0.0",
        "endpoints": {
            "ingest": "POST /ingest - Receive monitoring data",
            "alerts": "GET /alerts - Get current alerts",
            "health": "GET /healthz - Health check"
        }
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )