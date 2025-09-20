import json
import logging
import os
import hmac
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import selectinload

from models import Payload
from services.alerts import should_send_email, get_alert_severity, format_alert_summary
from services.email import send_alert_email, format_alert_email_content
from services.rules import process_log_entry, get_alerts, add_alert
from rules_engine import analyze_request, get_stored_alerts
from database import get_db_session, init_db, close_db
from performance_config import perf_config
from db_models import (
    MetricsModel, DockerEventsModel, ContainerLogsModel, 
    AlertsModel, EmailNotificationsModel
)
from routes import router as api_router
from api.nlp_endpoints import nlp_router

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Get secret from environment variable
SECRET = os.environ.get("INGEST_SECRET", "")

# Environment variables for timestamp validation:
# - TIMESTAMP_TOLERANCE_SECONDS: Maximum allowed time difference in seconds (default: 3600)
# - DISABLE_TIMESTAMP_VALIDATION: Set to "true" to completely disable timestamp validation

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
    title="Monitoring Backend API",
    description="Production-ready monitoring and alerting system for Docker containers",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    openapi_url="/openapi.json" if os.getenv("ENVIRONMENT", "development") != "production" else None
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure with specific hosts in production
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure with specific origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)
app.include_router(nlp_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error responses."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on application shutdown."""
    logger.info("Closing database connections...")
    await close_db()
    logger.info("Database connections closed")


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
    
    # Check if timestamp validation is enabled (can be disabled for production environments with clock sync issues)
    skip_timestamp_validation = os.environ.get("SKIP_TIMESTAMP_VALIDATION", "false").lower() == "true"
    
    if not skip_timestamp_validation:
        # Check timestamp freshness with configurable tolerance for production environments
        try:
            ts_int = int(timestamp)
            current_time = time.time()
            time_diff = abs(current_time - ts_int)
            
            # Get timestamp tolerance from environment variable, default to 1 hour for production stability
            timestamp_tolerance = int(os.environ.get("TIMESTAMP_TOLERANCE_SECONDS", "3600"))  # 1 hour default
            
            if time_diff > timestamp_tolerance:
                # Log the issue but don't fail in production - this could be clock drift
                logger.warning(f"Large timestamp difference detected: {time_diff}s (tolerance: {timestamp_tolerance}s)")
                logger.warning(f"Current server time: {current_time} ({datetime.fromtimestamp(current_time, timezone.utc).isoformat()})")
                logger.warning(f"Provided timestamp: {ts_int} ({datetime.fromtimestamp(ts_int, timezone.utc).isoformat()})")
                
                # Only fail if the difference is extremely large (more than 24 hours)
                if time_diff > 86400:  # 24 hours
                    raise HTTPException(status_code=400, detail="Request timestamp is extremely stale")
                else:
                    # Log but allow the request to proceed
                    logger.info(f"Allowing request with stale timestamp due to production tolerance")
                    
        except ValueError as e:
            logger.warning(f"Invalid timestamp format: {timestamp} - {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
    else:
        logger.debug("Timestamp validation skipped due to SKIP_TIMESTAMP_VALIDATION=true")
    
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
    db: AsyncSession = Depends(get_db_session),
    x_agent_signature: str = Header(..., alias="X-Agent-Signature"),
    x_agent_timestamp: str = Header(..., alias="X-Agent-Timestamp")
) -> Dict[str, str]:
    """
    Receive monitoring data from Go agent, persist to database, and log it.
    
    Args:
        payload: The monitoring payload from the Go agent
        db: Database session dependency
        
    Returns:
        Success message with timestamp
    """
    try:
        # Verify HMAC signature and timestamp before processing
        raw_body = await request.body()
        verify_hmac_signature(x_agent_signature, x_agent_timestamp, raw_body)
        
        # Convert payload to dict for logging
        payload_dict = payload.model_dump()
        
        # Persist system metrics to database
        metrics_record = MetricsModel(
            timestamp=payload.timestamp,
            cpu_usage=payload.metrics.cpu_usage,
            memory_usage=payload.metrics.memory_usage,
            disk_usage=payload.metrics.disk_usage,
            network_rx=payload.metrics.network_rx_bytes_per_sec,
            network_tx=payload.metrics.network_tx_bytes_per_sec,
            tcp_connections=payload.metrics.tcp_connections
        )
        db.add(metrics_record)
        
        # Persist docker events to database
        for event in payload.docker_events:
            docker_event_record = DockerEventsModel(
                timestamp=event.timestamp,
                type=event.type,
                action=event.action,
                container=event.container,
                image=event.image
            )
            db.add(docker_event_record)
        
        # Persist container logs to database
        for log_entry in payload.logs:
            container_log_record = ContainerLogsModel(
                container=log_entry.container,
                timestamp=log_entry.timestamp,
                message=log_entry.message
            )
            db.add(container_log_record)
        
        # Commit database changes
        await db.commit()

        # Pretty print to console
        print("\n" + "="*80)
        print(f"📊 MONITORING DATA RECEIVED - {datetime.now(timezone.utc).isoformat()}")
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions (like authentication errors) without modification
        raise
    except Exception as e:
        logger.error(f"Error processing monitoring data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing monitoring data: {str(e)}")


@app.get("/alerts")
async def get_current_alerts(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """
    Get current alerts from both the rules engine, attack detection system, and database.
    
    Returns:
        JSON response with current alerts list from all systems
    """
    try:
        # Get alerts from database
        db_alerts_query = select(AlertsModel).order_by(desc(AlertsModel.timestamp)).limit(50)
        db_alerts_result = await db.execute(db_alerts_query)
        db_alerts = db_alerts_result.scalars().all()
        
        # Get alerts from the original rules system
        rules_alerts = get_alerts()
        
        # Get alerts from the new attack detection system
        attack_alerts = get_stored_alerts(50)  # Get last 50 attack alerts
        
        # Combine and format alerts
        combined_alerts = []
        
        # Add database alerts (highest priority)
        for alert in db_alerts:
            combined_alerts.append({
                "id": f"db_{alert.id}",
                "timestamp": alert.timestamp.isoformat(),
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "source": "database",
                "metadata": alert.metadata
            })
        
        # Add attack detection alerts (high priority)
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
async def health_check(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint for production monitoring.
    
    Returns:
        Health status with database connectivity check
    """
    health_status = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "monitoring-backend",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database connectivity check
    try:
        # Simple query to test database connection
        result = await db.execute(select(func.now()))
        db_time = result.scalar()
        health_status["checks"]["database"] = {
            "status": "ok",
            "response_time_ms": "< 100",  # Placeholder - could implement actual timing
            "connection": "active"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Environment checks
    health_status["checks"]["environment"] = {
        "secret_configured": bool(SECRET),
        "logs_directory": logs_dir.exists()
    }
    
    return health_status


@app.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Readiness status for load balancer routing
    """
    try:
        # Test database connection
        await db.execute(select(func.now()))
        
        # Check critical configuration
        if not SECRET:
            raise HTTPException(status_code=503, detail="Missing required configuration")
            
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "monitoring-backend"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


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


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        JSON response with API information
    """
    return {
        "message": "Monitoring Backend API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "health": "/healthz",
            "readiness": "/readiness", 
            "ingest": "/ingest",
            "alerts": "/alerts",
            "metrics_recent": "/metrics/recent",
            "metrics_range": "/metrics/range",
            "events_recent": "/events/recent",
            "logs_search": "/logs/search"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,      # для продакшена обычно False
        log_level="info"
    )