"""
Log Search and Analytics API Routes

This module provides REST API endpoints for searching, filtering,
and analyzing logs and alerts using OpenSearch.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, validator

from services.log_search import get_log_search_service, LogFilterHelpers
from services.log_indexer import get_log_indexer

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/logs", tags=["logs"])


# Request/Response Models
class LogSearchRequest(BaseModel):
    """Request model for log search"""
    query: Optional[str] = Field(None, description="Full-text search query")
    start_time: Optional[datetime] = Field(None, description="Start time for search range")
    end_time: Optional[datetime] = Field(None, description="End time for search range")
    containers: Optional[List[str]] = Field(None, description="Container names to filter by")
    hosts: Optional[List[str]] = Field(None, description="Host names to filter by")
    environments: Optional[List[str]] = Field(None, description="Environments to filter by")
    log_levels: Optional[List[str]] = Field(None, description="Log levels to filter by")
    size: int = Field(100, ge=1, le=1000, description="Number of results to return")
    from_: int = Field(0, ge=0, alias="from", description="Starting offset for pagination")
    sort_field: str = Field("timestamp", description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    
    @validator('log_levels')
    def validate_log_levels(cls, v):
        if v is None:
            return v
        valid_levels = ["ERROR", "WARN", "INFO", "DEBUG", "FATAL", "TRACE"]
        return [level.upper() for level in v if level.upper() in valid_levels]


class AlertSearchRequest(BaseModel):
    """Request model for alert search"""
    query: Optional[str] = Field(None, description="Full-text search query")
    start_time: Optional[datetime] = Field(None, description="Start time for search range")
    end_time: Optional[datetime] = Field(None, description="End time for search range")
    severities: Optional[List[str]] = Field(None, description="Alert severities to filter by")
    alert_types: Optional[List[str]] = Field(None, description="Alert types to filter by")
    containers: Optional[List[str]] = Field(None, description="Container names to filter by")
    hosts: Optional[List[str]] = Field(None, description="Host names to filter by")
    size: int = Field(100, ge=1, le=1000, description="Number of results to return")
    from_: int = Field(0, ge=0, alias="from", description="Starting offset for pagination")
    
    @validator('severities')
    def validate_severities(cls, v):
        if v is None:
            return v
        valid_severities = ["HIGH", "MEDIUM", "LOW", "CRITICAL"]
        return [sev.upper() for sev in v if sev.upper() in valid_severities]


class LogSearchResponse(BaseModel):
    """Response model for log search"""
    total: int = Field(description="Total number of matching logs")
    total_relation: str = Field(description="Relation of total count (eq, gte)")
    max_score: Optional[float] = Field(description="Maximum relevance score")
    documents: List[Dict[str, Any]] = Field(description="Log documents")
    took: int = Field(description="Time taken for search in milliseconds")
    fallback: bool = Field(False, description="Whether fallback mode was used")


class AggregationResponse(BaseModel):
    """Response model for aggregations"""
    total_logs: Optional[int] = Field(description="Total number of logs")
    total_alerts: Optional[int] = Field(description="Total number of alerts")
    aggregations: Dict[str, Any] = Field(description="Aggregation results")


class QuickFilterResponse(BaseModel):
    """Response model for quick filter options"""
    containers: List[str] = Field(description="Available container names")
    hosts: List[str] = Field(description="Available host names")
    environments: List[str] = Field(description="Available environments")
    log_levels: List[str] = Field(description="Available log levels")
    severities: List[str] = Field(description="Available alert severities")


# API Endpoints
@router.post("/search", response_model=LogSearchResponse)
async def search_logs(request: LogSearchRequest):
    """
    Search logs with comprehensive filtering options
    
    This endpoint allows you to search through logs using:
    - Full-text search across log messages
    - Time range filtering
    - Container, host, and environment filtering
    - Log level filtering
    - Pagination and sorting
    """
    try:
        search_service = get_log_search_service()
        
        result = search_service.search_logs(
            query=request.query,
            start_time=request.start_time,
            end_time=request.end_time,
            containers=request.containers,
            hosts=request.hosts,
            environments=request.environments,
            log_levels=request.log_levels,
            size=request.size,
            from_=request.from_,
            sort_field=request.sort_field,
            sort_order=request.sort_order
        )
        
        return LogSearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in log search endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during log search")


@router.post("/alerts/search", response_model=LogSearchResponse)
async def search_alerts(request: AlertSearchRequest):
    """
    Search alerts with filtering options
    
    This endpoint allows you to search through security alerts using:
    - Full-text search across alert messages and evidence
    - Time range filtering
    - Severity and alert type filtering
    - Container and host filtering
    - Pagination
    """
    try:
        search_service = get_log_search_service()
        
        result = search_service.search_alerts(
            query=request.query,
            start_time=request.start_time,
            end_time=request.end_time,
            severities=request.severities,
            alert_types=request.alert_types,
            containers=request.containers,
            hosts=request.hosts,
            size=request.size,
            from_=request.from_
        )
        
        return LogSearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in alert search endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during alert search")


@router.get("/search/quick")
async def quick_search_logs(
    q: Optional[str] = Query(None, description="Quick search query"),
    hours: int = Query(24, ge=1, le=168, description="Hours to search back"),
    level: Optional[str] = Query(None, description="Log level filter (comma-separated)"),
    container: Optional[str] = Query(None, description="Container name filter"),
    size: int = Query(50, ge=1, le=500, description="Number of results")
):
    """
    Quick log search with simplified parameters
    
    This is a simplified endpoint for quick searches with common filters.
    """
    try:
        search_service = get_log_search_service()
        
        # Calculate time range
        start_time, end_time = LogFilterHelpers.get_time_range_last_hours(hours)
        
        # Parse log levels
        log_levels = LogFilterHelpers.parse_log_level_filter(level) if level else None
        
        # Parse containers
        containers = [container] if container else None
        
        result = search_service.search_logs(
            query=q,
            start_time=start_time,
            end_time=end_time,
            log_levels=log_levels,
            containers=containers,
            size=size
        )
        
        return LogSearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in quick search endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during quick search")


@router.get("/analytics/logs", response_model=AggregationResponse)
async def get_log_analytics(
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze"),
    interval: str = Query("1h", pattern="^(1m|5m|15m|30m|1h|6h|12h|1d)$", description="Time interval")
):
    """
    Get log analytics and aggregations
    
    This endpoint provides analytics data for logs including:
    - Log volume over time
    - Distribution by log level
    - Top containers and hosts
    - Environment breakdown
    """
    try:
        search_service = get_log_search_service()
        
        # Calculate time range
        start_time, end_time = LogFilterHelpers.get_time_range_last_hours(hours)
        
        result = search_service.get_log_aggregations(
            start_time=start_time,
            end_time=end_time,
            interval=interval
        )
        
        return AggregationResponse(
            total_logs=result.get("total_logs"),
            aggregations=result.get("aggregations", {})
        )
        
    except Exception as e:
        logger.error(f"Error in log analytics endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analytics")


@router.get("/analytics/alerts", response_model=AggregationResponse)
async def get_alert_analytics(
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze"),
    interval: str = Query("1h", pattern="^(1m|5m|15m|30m|1h|6h|12h|1d)$", description="Time interval")
):
    """
    Get alert analytics and aggregations
    
    This endpoint provides analytics data for alerts including:
    - Alert volume over time
    - Distribution by severity
    - Top alert types and attack types
    - Container and host breakdown
    """
    try:
        search_service = get_log_search_service()
        
        # Calculate time range
        start_time, end_time = LogFilterHelpers.get_time_range_last_hours(hours)
        
        result = search_service.get_alert_aggregations(
            start_time=start_time,
            end_time=end_time,
            interval=interval
        )
        
        return AggregationResponse(
            total_alerts=result.get("total_alerts"),
            aggregations=result.get("aggregations", {})
        )
        
    except Exception as e:
        logger.error(f"Error in alert analytics endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analytics")


@router.get("/filters", response_model=QuickFilterResponse)
async def get_filter_options():
    """
    Get available filter options for the UI
    
    This endpoint returns the available values for various filters
    to help build dynamic filter UIs.
    """
    try:
        search_service = get_log_search_service()
        
        # Get recent data to extract filter options
        recent_logs = search_service.search_logs(
            start_time=datetime.now() - timedelta(days=7),
            size=1000
        )
        
        recent_alerts = search_service.search_alerts(
            start_time=datetime.now() - timedelta(days=7),
            size=1000
        )
        
        # Extract unique values
        containers = set()
        hosts = set()
        environments = set()
        log_levels = set()
        severities = set()
        
        # Process logs
        for doc in recent_logs.get("documents", []):
            if doc.get("container"):
                containers.add(doc["container"])
            if doc.get("host"):
                hosts.add(doc["host"])
            if doc.get("environment"):
                environments.add(doc["environment"])
            if doc.get("log_level"):
                log_levels.add(doc["log_level"])
        
        # Process alerts
        for doc in recent_alerts.get("documents", []):
            if doc.get("container"):
                containers.add(doc["container"])
            if doc.get("host"):
                hosts.add(doc["host"])
            if doc.get("severity"):
                severities.add(doc["severity"])
        
        return QuickFilterResponse(
            containers=sorted(list(containers)),
            hosts=sorted(list(hosts)),
            environments=sorted(list(environments)),
            log_levels=sorted(list(log_levels)),
            severities=sorted(list(severities))
        )
        
    except Exception as e:
        logger.error(f"Error in filter options endpoint: {e}")
        # Return default options on error
        return QuickFilterResponse(
            containers=[],
            hosts=[],
            environments=["production", "staging", "development"],
            log_levels=["ERROR", "WARN", "INFO", "DEBUG"],
            severities=["HIGH", "MEDIUM", "LOW"]
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the log search service
    
    Returns the status of OpenSearch connectivity and service availability.
    """
    try:
        search_service = get_log_search_service()
        indexer = get_log_indexer()
        
        search_status = search_service.get_status()
        indexer_status = indexer.get_status()
        
        search_available = search_status["connected"]
        indexer_available = indexer_status["connected"]
        
        # Determine overall status - degraded if OpenSearch unavailable but API functional
        if search_available and indexer_available:
            status = "healthy"
        elif not search_available and not indexer_available:
            status = "degraded"  # OpenSearch unavailable, fallback mode active
        else:
            status = "degraded"  # Partial availability
            
        return {
            "status": status,
            "search_service": search_status,
            "indexer_service": indexer_status,
            "opensearch_status": "connected" if (search_available and indexer_available) else "disconnected",
            "fallback_mode": search_status["fallback_mode"] or indexer_status["fallback_mode"],
            "message": "OpenSearch unavailable, using fallback mode" if not (search_available and indexer_available) else "All services operational",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Time range helper endpoints
@router.get("/time-ranges/last-hours/{hours}")
async def get_time_range_last_hours(hours: int):
    """Get time range for the last N hours"""
    start_time, end_time = LogFilterHelpers.get_time_range_last_hours(hours)
    return {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "description": f"Last {hours} hours"
    }


@router.get("/time-ranges/last-days/{days}")
async def get_time_range_last_days(days: int):
    """Get time range for the last N days"""
    start_time, end_time = LogFilterHelpers.get_time_range_last_days(days)
    return {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "description": f"Last {days} days"
    }


@router.get("/time-ranges/today")
async def get_time_range_today():
    """Get time range for today"""
    start_time, end_time = LogFilterHelpers.get_time_range_today()
    return {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "description": "Today"
    }