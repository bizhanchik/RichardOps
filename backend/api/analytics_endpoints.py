"""
Analytics API Endpoints

This module provides API endpoints for:
- System summaries and reports
- Anomaly detection and alerts
- Performance analytics
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from database import get_db_session
from services.summary_service import summary_service
from services.anomaly_detection import anomaly_detector, Anomaly

# Pydantic response models
class SummaryResponse(BaseModel):
    period: Dict[str, Any]
    metrics: Dict[str, Any]
    alerts: Dict[str, Any]
    events: Dict[str, Any]
    logs: Dict[str, Any]
    containers: Dict[str, Any]
    generated_at: str

class PerformanceReportResponse(BaseModel):
    period: Dict[str, Any]
    performance_analysis: Dict[str, Any]
    utilization_patterns: Dict[str, Any]
    recommendations: List[str]
    generated_at: str

class AnomalyResponse(BaseModel):
    type: str
    severity: str
    timestamp: str
    description: str
    details: Dict[str, Any]
    affected_resource: Optional[str] = None
    confidence: float = 1.0

class AnomalySummaryResponse(BaseModel):
    total_anomalies: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    affected_resources: List[str]
    recent_anomalies: List[Dict[str, Any]]
    generated_at: str

# Create router
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])

@analytics_router.get("/summary", response_model=SummaryResponse)
async def get_system_summary(
    period: str = Query(
        default="24h", 
        description="Time period: 1h, 6h, 12h, 24h, 7d, 30d"
    ),
    db: AsyncSession = Depends(get_db_session)
) -> SummaryResponse:
    """
    Get a comprehensive system summary for the specified time period.
    
    Available periods:
    - 1h: Last Hour
    - 6h: Last 6 Hours
    - 12h: Last 12 Hours
    - 24h: Last 24 Hours (default)
    - 7d: Last 7 Days
    - 30d: Last 30 Days
    """
    try:
        summary_data = await summary_service.generate_system_summary(db, period)
        return SummaryResponse(**summary_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@analytics_router.get("/performance-report", response_model=PerformanceReportResponse)
async def get_performance_report(
    period: str = Query(
        default="24h", 
        description="Time period: 1h, 6h, 12h, 24h, 7d, 30d"
    ),
    db: AsyncSession = Depends(get_db_session)
) -> PerformanceReportResponse:
    """
    Get a detailed performance analysis report for the specified time period.
    
    Includes:
    - Performance trends analysis
    - Resource utilization patterns
    - Performance recommendations
    """
    try:
        report_data = await summary_service.generate_performance_report(db, period)
        return PerformanceReportResponse(**report_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating performance report: {str(e)}")

@analytics_router.get("/anomalies", response_model=List[AnomalyResponse])
async def detect_anomalies(
    lookback_hours: int = Query(
        default=1, 
        ge=1, 
        le=168, 
        description="Hours to look back for anomaly detection (1-168)"
    ),
    severity_filter: Optional[str] = Query(
        default=None,
        description="Filter by severity: LOW, MEDIUM, HIGH"
    ),
    type_filter: Optional[str] = Query(
        default=None,
        description="Filter by anomaly type"
    ),
    db: AsyncSession = Depends(get_db_session)
) -> List[AnomalyResponse]:
    """
    Detect anomalies in the system for the specified time period.
    
    Detects:
    - CPU, memory, disk usage spikes
    - High request volumes from single IPs
    - High error rates in containers
    - Unusual Docker event patterns
    - TCP connection spikes
    """
    try:
        anomalies = await anomaly_detector.detect_all_anomalies(db, lookback_hours)
        
        # Apply filters
        if severity_filter:
            severity_filter = severity_filter.upper()
            if severity_filter not in ["LOW", "MEDIUM", "HIGH"]:
                raise HTTPException(status_code=400, detail="Invalid severity filter")
            anomalies = [a for a in anomalies if a.severity == severity_filter]
        
        if type_filter:
            anomalies = [a for a in anomalies if a.type == type_filter]
        
        # Convert to response models
        return [
            AnomalyResponse(
                type=anomaly.type,
                severity=anomaly.severity,
                timestamp=anomaly.timestamp.isoformat(),
                description=anomaly.description,
                details=anomaly.details,
                affected_resource=anomaly.affected_resource,
                confidence=anomaly.confidence
            )
            for anomaly in anomalies
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")

@analytics_router.get("/anomalies/summary", response_model=AnomalySummaryResponse)
async def get_anomaly_summary(
    hours: int = Query(
        default=24, 
        ge=1, 
        le=720, 
        description="Hours to look back for anomaly summary (1-720)"
    ),
    db: AsyncSession = Depends(get_db_session)
) -> AnomalySummaryResponse:
    """
    Get a summary of anomalies detected in the specified time period.
    
    Provides:
    - Total anomaly count
    - Breakdown by type and severity
    - List of affected resources
    - Recent anomalies
    """
    try:
        summary_data = await anomaly_detector.get_anomaly_summary(db, hours)
        return AnomalySummaryResponse(**summary_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating anomaly summary: {str(e)}")

@analytics_router.get("/anomalies/types")
async def get_anomaly_types() -> Dict[str, Any]:
    """
    Get information about available anomaly types and their descriptions.
    """
    return {
        "anomaly_types": {
            "cpu_spike": {
                "description": "Sudden increase in CPU usage",
                "severity_levels": ["MEDIUM", "HIGH"],
                "threshold": "30% increase from baseline"
            },
            "memory_spike": {
                "description": "Sudden increase in memory usage",
                "severity_levels": ["MEDIUM", "HIGH"],
                "threshold": "25% increase from baseline"
            },
            "disk_spike": {
                "description": "Sudden increase in disk usage",
                "severity_levels": ["LOW", "MEDIUM"],
                "threshold": "20% increase from baseline"
            },
            "ip_request_spike": {
                "description": "Too many requests from a single IP address",
                "severity_levels": ["MEDIUM", "HIGH"],
                "threshold": "100+ requests per hour"
            },
            "high_error_rate": {
                "description": "High error rate in container logs",
                "severity_levels": ["MEDIUM", "HIGH"],
                "threshold": "10%+ error rate"
            },
            "container_restart_loop": {
                "description": "Container restarting frequently",
                "severity_levels": ["HIGH"],
                "threshold": "5+ restarts in monitoring period"
            },
            "high_event_volume": {
                "description": "High volume of Docker events",
                "severity_levels": ["MEDIUM"],
                "threshold": "100+ events in monitoring period"
            },
            "connection_spike": {
                "description": "Sudden increase in TCP connections",
                "severity_levels": ["MEDIUM", "HIGH"],
                "threshold": "500+ new connections"
            }
        },
        "severity_levels": {
            "LOW": "Minor issues that should be monitored",
            "MEDIUM": "Moderate issues that may require attention",
            "HIGH": "Critical issues that require immediate attention"
        }
    }

@analytics_router.get("/health")
async def analytics_health_check() -> Dict[str, str]:
    """Health check endpoint for analytics services"""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Additional endpoints for specific analytics

@analytics_router.get("/metrics/trends")
async def get_metrics_trends(
    period: str = Query(default="24h", description="Time period for trend analysis"),
    metric_type: Optional[str] = Query(default=None, description="Specific metric: cpu, memory, disk"),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get detailed metrics trends analysis.
    """
    try:
        # This could be expanded to provide more detailed trend analysis
        summary_data = await summary_service.generate_system_summary(db, period)
        
        metrics_data = summary_data.get("metrics", {})
        
        if metric_type:
            if metric_type in ["cpu", "memory", "disk"]:
                key = f"{metric_type}_usage"
                if key in metrics_data:
                    return {
                        "metric_type": metric_type,
                        "period": period,
                        "data": metrics_data[key],
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    raise HTTPException(status_code=404, detail=f"No data found for metric: {metric_type}")
            else:
                raise HTTPException(status_code=400, detail="Invalid metric type. Use: cpu, memory, disk")
        
        return {
            "period": period,
            "all_metrics": metrics_data,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics trends: {str(e)}")

@analytics_router.get("/containers/analysis")
async def get_container_analysis(
    period: str = Query(default="24h", description="Time period for analysis"),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get detailed container analysis including performance and anomalies.
    """
    try:
        # Get summary data
        summary_data = await summary_service.generate_system_summary(db, period)
        
        # Get anomalies related to containers
        anomalies = await anomaly_detector.detect_all_anomalies(db, 24)  # Last 24 hours
        container_anomalies = [a for a in anomalies if a.affected_resource and not a.affected_resource.startswith("system_")]
        
        return {
            "period": period,
            "containers_summary": summary_data.get("containers", {}),
            "events_summary": summary_data.get("events", {}),
            "logs_summary": summary_data.get("logs", {}),
            "container_anomalies": [
                {
                    "type": a.type,
                    "severity": a.severity,
                    "description": a.description,
                    "affected_resource": a.affected_resource,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in container_anomalies
            ],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting container analysis: {str(e)}")