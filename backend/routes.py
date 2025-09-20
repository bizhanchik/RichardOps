from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field

from database import get_db_session
from db_models import (
    MetricsModel, DockerEventsModel, ContainerLogsModel, AlertsModel
)

# Pydantic response models
class MetricResponse(BaseModel):
    timestamp: str
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    network_rx: Optional[int]
    network_tx: Optional[int]
    tcp_connections: Optional[int]

class DockerEventResponse(BaseModel):
    timestamp: str
    type: Optional[str]
    action: Optional[str]
    container: Optional[str]
    image: Optional[str]

class LogEntryResponse(BaseModel):
    timestamp: str
    container: Optional[str]
    message: Optional[str]

class AlertResponse(BaseModel):
    id: int
    timestamp: str
    severity: str
    type: Optional[str]
    message: Optional[str]
    score: Optional[float]
    resolved: bool

# Create router
router = APIRouter()

@router.get("/metrics/recent", response_model=List[MetricResponse])
async def get_recent_metrics(
    limit: int = Query(default=50, le=1000, description="Number of recent metrics to return"),
    db: AsyncSession = Depends(get_db_session)
) -> List[MetricResponse]:
    """
    Returns the last N metrics (default 50).
    Order by timestamp descending, then reverse in the response so newest is last.
    """
    try:
        # Query metrics ordered by timestamp descending
        query = select(MetricsModel).order_by(desc(MetricsModel.timestamp)).limit(limit)
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        # Convert to response models and reverse so newest is last
        metrics_list = []
        for metric in reversed(metrics):
            metrics_list.append(MetricResponse(
                timestamp=metric.timestamp.isoformat(),
                cpu_usage=float(metric.cpu_usage) if metric.cpu_usage is not None else None,
                memory_usage=float(metric.memory_usage) if metric.memory_usage is not None else None,
                disk_usage=float(metric.disk_usage) if metric.disk_usage is not None else None,
                network_rx=metric.network_rx,
                network_tx=metric.network_tx,
                tcp_connections=metric.tcp_connections
            ))
        
        return metrics_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.get("/metrics/range", response_model=List[MetricResponse])
async def get_metrics_range(
    period: str = Query(default="1h", description="Time period: 1h, 6h, or 12h"),
    db: AsyncSession = Depends(get_db_session)
) -> List[MetricResponse]:
    """
    Returns metrics for time ranges:
    - ?period=1h → last 1 hour
    - ?period=6h → last 6 hours  
    - ?period=12h → last 12 hours
    Default period is 1h if not specified.
    """
    try:
        # Parse period and calculate time threshold
        period_hours = {
            "1h": 1,
            "6h": 6,
            "12h": 12
        }
        
        if period not in period_hours:
            raise HTTPException(status_code=400, detail="Invalid period. Use 1h, 6h, or 12h")
        
        hours = period_hours[period]
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Query metrics within the time range
        query = select(MetricsModel).where(
            MetricsModel.timestamp >= time_threshold
        ).order_by(MetricsModel.timestamp)
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        # Convert to response models
        metrics_list = []
        for metric in metrics:
            metrics_list.append(MetricResponse(
                timestamp=metric.timestamp.isoformat(),
                cpu_usage=float(metric.cpu_usage) if metric.cpu_usage is not None else None,
                memory_usage=float(metric.memory_usage) if metric.memory_usage is not None else None,
                disk_usage=float(metric.disk_usage) if metric.disk_usage is not None else None,
                network_rx=metric.network_rx,
                network_tx=metric.network_tx,
                tcp_connections=metric.tcp_connections
            ))
        
        return metrics_list
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics range: {str(e)}")

@router.get("/events/recent", response_model=List[DockerEventResponse])
async def get_recent_events(
    limit: int = Query(default=50, le=1000, description="Number of recent events to return"),
    db: AsyncSession = Depends(get_db_session)
) -> List[DockerEventResponse]:
    """
    Returns last N docker events (default 50).
    Ordered by timestamp descending.
    """
    try:
        # Query events ordered by timestamp descending
        query = select(DockerEventsModel).order_by(desc(DockerEventsModel.timestamp)).limit(limit)
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Convert to response models
        events_list = []
        for event in events:
            events_list.append(DockerEventResponse(
                timestamp=event.timestamp.isoformat(),
                type=event.type,
                action=event.action,
                container=event.container,
                image=event.image
            ))
        
        return events_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving events: {str(e)}")

@router.get("/logs/search", response_model=List[LogEntryResponse])
async def search_logs(
    q: str = Query(..., description="Search query for log messages"),
    limit: int = Query(default=50, le=1000, description="Number of results to return"),
    db: AsyncSession = Depends(get_db_session)
) -> List[LogEntryResponse]:
    """
    GET /logs/search?q=error&limit=50
    Performs case-insensitive LIKE search in container_logs.message.
    Return last N results ordered by timestamp descending.
    """
    try:
        # Build query with case-insensitive search
        query = select(ContainerLogsModel).where(
            ContainerLogsModel.message.ilike(f"%{q}%")
        ).order_by(desc(ContainerLogsModel.timestamp)).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Convert to response models
        logs_list = []
        for log in logs:
            logs_list.append(LogEntryResponse(
                timestamp=log.timestamp.isoformat(),
                container=log.container,
                message=log.message
            ))
        
        return logs_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching logs: {str(e)}")

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    limit: int = Query(default=50, le=1000, description="Number of alerts to return"),
    db: AsyncSession = Depends(get_db_session)
) -> List[AlertResponse]:
    """
    Returns all alerts (default 50), ordered by timestamp descending.
    Each alert includes: id, timestamp, severity, type, message, score, resolved.
    """
    try:
        # Query alerts ordered by timestamp descending
        query = select(AlertsModel).order_by(desc(AlertsModel.timestamp)).limit(limit)
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        # Convert to response models
        alerts_list = []
        for alert in alerts:
            alerts_list.append(AlertResponse(
                id=alert.id,
                timestamp=alert.timestamp.isoformat(),
                severity=alert.severity,
                type=alert.type,
                message=alert.message,
                score=float(alert.score) if alert.score is not None else None,
                resolved=alert.resolved
            ))
        
        return alerts_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")