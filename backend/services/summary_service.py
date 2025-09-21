"""
Summary and Report Generation Service

This service provides functionality to generate various types of summaries and reports
from the monitoring data including metrics, logs, events, and alerts.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func, and_, or_
from dataclasses import dataclass
import json
import logging

from db_models import (
    MetricsModel, DockerEventsModel, ContainerLogsModel, AlertsModel
)

logger = logging.getLogger(__name__)

@dataclass
class SummaryPeriod:
    """Represents a time period for summary generation"""
    hours: int
    name: str
    
    @property
    def start_time(self) -> datetime:
        return datetime.now(timezone.utc) - timedelta(hours=self.hours)

# Predefined summary periods
SUMMARY_PERIODS = {
    "1h": SummaryPeriod(1, "Last Hour"),
    "6h": SummaryPeriod(6, "Last 6 Hours"), 
    "12h": SummaryPeriod(12, "Last 12 Hours"),
    "24h": SummaryPeriod(24, "Last 24 Hours"),
    "7d": SummaryPeriod(168, "Last 7 Days"),
    "30d": SummaryPeriod(720, "Last 30 Days")
}

class SummaryService:
    """Service for generating summaries and reports from monitoring data"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _get_period_info(self, period: str) -> SummaryPeriod:
        """
        Get period information for the specified period.
        
        Args:
            period: Time period string
            
        Returns:
            SummaryPeriod object containing period information
        """
        if period not in SUMMARY_PERIODS:
            raise ValueError(f"Invalid period: {period}. Must be one of {list(SUMMARY_PERIODS.keys())}")
        
        return SUMMARY_PERIODS[period]

    async def generate_system_summary(
        self, 
        db: AsyncSession, 
        period: str = "24h"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive system summary for the specified period
        
        Args:
            db: Database session
            period: Time period (1h, 6h, 12h, 24h, 7d, 30d)
            
        Returns:
            Dictionary containing system summary data
        """
        try:
            summary_period = self._get_period_info(period)
            start_time = summary_period.start_time
            
            # Generate all summary components
            metrics_summary = await self._get_metrics_summary(db, start_time)
            alerts_summary = await self._get_alerts_summary(db, start_time)
            events_summary = await self._get_events_summary(db, start_time)
            logs_summary = await self._get_logs_summary(db, start_time)
            containers_summary = await self._get_containers_summary(db, start_time)
            
            return {
                "period": {
                    "name": summary_period.name,
                    "hours": summary_period.hours,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat()
                },
                "metrics": metrics_summary,
                "alerts": alerts_summary,
                "events": events_summary,
                "logs": logs_summary,
                "containers": containers_summary,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating system summary: {str(e)}")
            raise
    
    async def _get_metrics_summary(self, db: AsyncSession, start_time: datetime) -> Dict[str, Any]:
        """Generate metrics summary"""
        try:
            # Get metrics data for the period
            query = select(MetricsModel).where(
                MetricsModel.timestamp >= start_time
            ).order_by(desc(MetricsModel.timestamp))
            
            result = await db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {"status": "no_data", "count": 0}
            
            # Calculate statistics
            cpu_values = [float(m.cpu_usage) for m in metrics if m.cpu_usage is not None]
            memory_values = [float(m.memory_usage) for m in metrics if m.memory_usage is not None]
            disk_values = [float(m.disk_usage) for m in metrics if m.disk_usage is not None]
            
            return {
                "count": len(metrics),
                "cpu_usage": self._calculate_stats(cpu_values),
                "memory_usage": self._calculate_stats(memory_values),
                "disk_usage": self._calculate_stats(disk_values),
                "latest": {
                    "timestamp": metrics[0].timestamp.isoformat(),
                    "cpu_usage": float(metrics[0].cpu_usage) if metrics[0].cpu_usage else None,
                    "memory_usage": float(metrics[0].memory_usage) if metrics[0].memory_usage else None,
                    "disk_usage": float(metrics[0].disk_usage) if metrics[0].disk_usage else None,
                    "tcp_connections": metrics[0].tcp_connections
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_alerts_summary(self, db: AsyncSession, start_time: datetime) -> Dict[str, Any]:
        """Generate alerts summary"""
        try:
            # Get alerts for the period
            query = select(AlertsModel).where(
                AlertsModel.timestamp >= start_time
            )
            
            result = await db.execute(query)
            alerts = result.scalars().all()
            
            # Count by severity
            severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            resolved_count = 0
            unresolved_count = 0
            
            for alert in alerts:
                severity_counts[alert.severity] += 1
                if alert.resolved:
                    resolved_count += 1
                else:
                    unresolved_count += 1
            
            # Get recent unresolved alerts
            recent_unresolved_query = select(AlertsModel).where(
                and_(
                    AlertsModel.timestamp >= start_time,
                    AlertsModel.resolved == False
                )
            ).order_by(desc(AlertsModel.timestamp)).limit(5)
            
            recent_result = await db.execute(recent_unresolved_query)
            recent_unresolved = recent_result.scalars().all()
            
            return {
                "total_count": len(alerts),
                "severity_breakdown": severity_counts,
                "resolved_count": resolved_count,
                "unresolved_count": unresolved_count,
                "recent_unresolved": [
                    {
                        "id": alert.id,
                        "timestamp": alert.timestamp.isoformat(),
                        "severity": alert.severity,
                        "type": alert.type,
                        "message": alert.message[:100] + "..." if len(alert.message or "") > 100 else alert.message
                    }
                    for alert in recent_unresolved
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting alerts summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_events_summary(self, db: AsyncSession, start_time: datetime) -> Dict[str, Any]:
        """Generate Docker events summary"""
        try:
            # Get events for the period
            query = select(DockerEventsModel).where(
                DockerEventsModel.timestamp >= start_time
            )
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            # Count by action type
            action_counts = {}
            container_events = {}
            
            for event in events:
                action = event.action or "unknown"
                action_counts[action] = action_counts.get(action, 0) + 1
                
                container = event.container or "unknown"
                if container not in container_events:
                    container_events[container] = 0
                container_events[container] += 1
            
            # Get most active containers
            most_active_containers = sorted(
                container_events.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            return {
                "total_count": len(events),
                "action_breakdown": action_counts,
                "most_active_containers": [
                    {"container": container, "event_count": count}
                    for container, count in most_active_containers
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting events summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_logs_summary(self, db: AsyncSession, start_time: datetime) -> Dict[str, Any]:
        """Generate logs summary"""
        try:
            # Get log count for the period
            count_query = select(func.count(ContainerLogsModel.id)).where(
                ContainerLogsModel.timestamp >= start_time
            )
            
            count_result = await db.execute(count_query)
            total_logs = count_result.scalar()
            
            # Get logs by container
            container_query = select(
                ContainerLogsModel.container,
                func.count(ContainerLogsModel.id).label('log_count')
            ).where(
                ContainerLogsModel.timestamp >= start_time
            ).group_by(ContainerLogsModel.container).order_by(
                desc(func.count(ContainerLogsModel.id))
            ).limit(10)
            
            container_result = await db.execute(container_query)
            container_logs = container_result.all()
            
            return {
                "total_count": total_logs,
                "logs_by_container": [
                    {"container": row.container, "log_count": row.log_count}
                    for row in container_logs
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting logs summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_containers_summary(self, db: AsyncSession, start_time: datetime) -> Dict[str, Any]:
        """Generate containers summary"""
        try:
            # Get unique containers from events
            events_query = select(DockerEventsModel.container).where(
                and_(
                    DockerEventsModel.timestamp >= start_time,
                    DockerEventsModel.container.isnot(None)
                )
            ).distinct()
            
            events_result = await db.execute(events_query)
            containers_with_events = {row[0] for row in events_result.all()}
            
            # Get unique containers from logs
            logs_query = select(ContainerLogsModel.container).where(
                and_(
                    ContainerLogsModel.timestamp >= start_time,
                    ContainerLogsModel.container.isnot(None)
                )
            ).distinct()
            
            logs_result = await db.execute(logs_query)
            containers_with_logs = {row[0] for row in logs_result.all()}
            
            all_containers = containers_with_events.union(containers_with_logs)
            
            return {
                "total_active_containers": len(all_containers),
                "containers_with_events": len(containers_with_events),
                "containers_with_logs": len(containers_with_logs),
                "container_list": list(all_containers)[:20]  # Limit to first 20
            }
            
        except Exception as e:
            self.logger.error(f"Error getting containers summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of values"""
        if not values:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}
        
        return {
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "avg": round(sum(values) / len(values), 2),
            "count": len(values)
        }
    
    async def generate_performance_report(
        self, 
        db: AsyncSession, 
        period: str = "24h"
    ) -> Dict[str, Any]:
        """
        Generate a detailed performance report
        
        Args:
            db: Database session
            period: Time period for the report
            
        Returns:
            Dictionary containing performance report data
        """
        try:
            if period not in SUMMARY_PERIODS:
                raise ValueError(f"Invalid period: {period}")
            
            summary_period = SUMMARY_PERIODS[period]
            start_time = summary_period.start_time
            
            # Get detailed metrics analysis
            metrics_query = select(MetricsModel).where(
                MetricsModel.timestamp >= start_time
            ).order_by(MetricsModel.timestamp)
            
            result = await db.execute(metrics_query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {"status": "no_data", "period": summary_period.name}
            
            # Analyze performance trends
            performance_analysis = self._analyze_performance_trends(metrics)
            
            # Get resource utilization patterns
            utilization_patterns = self._analyze_utilization_patterns(metrics)
            
            # Get performance recommendations
            recommendations = self._generate_performance_recommendations(metrics)
            
            return {
                "period": {
                    "name": summary_period.name,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat()
                },
                "performance_analysis": performance_analysis,
                "utilization_patterns": utilization_patterns,
                "recommendations": recommendations,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {str(e)}")
            raise
    
    def _analyze_performance_trends(self, metrics: List[MetricsModel]) -> Dict[str, Any]:
        """Analyze performance trends from metrics data"""
        if len(metrics) < 2:
            return {"status": "insufficient_data"}
        
        # Calculate trends for each metric
        cpu_values = [float(m.cpu_usage) for m in metrics if m.cpu_usage is not None]
        memory_values = [float(m.memory_usage) for m in metrics if m.memory_usage is not None]
        disk_values = [float(m.disk_usage) for m in metrics if m.disk_usage is not None]
        
        def calculate_trend(values: List[float]) -> str:
            if len(values) < 2:
                return "stable"
            
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            diff_percent = ((second_avg - first_avg) / first_avg) * 100
            
            if diff_percent > 10:
                return "increasing"
            elif diff_percent < -10:
                return "decreasing"
            else:
                return "stable"
        
        return {
            "cpu_trend": calculate_trend(cpu_values),
            "memory_trend": calculate_trend(memory_values),
            "disk_trend": calculate_trend(disk_values),
            "data_points": len(metrics)
        }
    
    def _analyze_utilization_patterns(self, metrics: List[MetricsModel]) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        cpu_values = [float(m.cpu_usage) for m in metrics if m.cpu_usage is not None]
        memory_values = [float(m.memory_usage) for m in metrics if m.memory_usage is not None]
        disk_values = [float(m.disk_usage) for m in metrics if m.disk_usage is not None]
        
        def analyze_pattern(values: List[float], name: str) -> Dict[str, Any]:
            if not values:
                return {"status": "no_data"}
            
            high_usage_count = sum(1 for v in values if v > 80)
            medium_usage_count = sum(1 for v in values if 50 <= v <= 80)
            low_usage_count = sum(1 for v in values if v < 50)
            
            return {
                "high_usage_periods": high_usage_count,
                "medium_usage_periods": medium_usage_count,
                "low_usage_periods": low_usage_count,
                "peak_usage": max(values),
                "average_usage": round(sum(values) / len(values), 2)
            }
        
        return {
            "cpu": analyze_pattern(cpu_values, "CPU"),
            "memory": analyze_pattern(memory_values, "Memory"),
            "disk": analyze_pattern(disk_values, "Disk")
        }
    
    def _generate_performance_recommendations(self, metrics: List[MetricsModel]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        if not metrics:
            return ["No metrics data available for recommendations"]
        
        # Analyze latest metrics
        latest = metrics[-1]
        
        # CPU recommendations
        if latest.cpu_usage and float(latest.cpu_usage) > 90:
            recommendations.append("High CPU usage detected. Consider scaling up or optimizing CPU-intensive processes.")
        elif latest.cpu_usage and float(latest.cpu_usage) < 10:
            recommendations.append("Low CPU usage detected. Consider scaling down to optimize costs.")
        
        # Memory recommendations
        if latest.memory_usage and float(latest.memory_usage) > 85:
            recommendations.append("High memory usage detected. Consider increasing memory allocation or optimizing memory usage.")
        
        # Disk recommendations
        if latest.disk_usage and float(latest.disk_usage) > 90:
            recommendations.append("High disk usage detected. Consider cleaning up disk space or expanding storage.")
        
        # TCP connections
        if latest.tcp_connections and latest.tcp_connections > 1000:
            recommendations.append("High number of TCP connections detected. Monitor for potential connection leaks.")
        
        if not recommendations:
            recommendations.append("System performance appears to be within normal parameters.")
        
        return recommendations

    # Synchronous wrapper methods for NLP query translator compatibility
    def get_performance_report(self, db_session: Session, period: str = "24h") -> Dict[str, Any]:
        """
        Synchronous wrapper for generate_performance_report.
        Used by NLP query translator which operates with sync database sessions.
        
        Args:
            db_session: Synchronous database session
            period: Time period for the report
            
        Returns:
            Dictionary containing performance report data
        """
        try:
            if period not in SUMMARY_PERIODS:
                raise ValueError(f"Invalid period: {period}")
            
            summary_period = SUMMARY_PERIODS[period]
            start_time = summary_period.start_time
            
            # Get detailed metrics analysis using sync session
            metrics_query = select(MetricsModel).where(
                MetricsModel.timestamp >= start_time
            ).order_by(MetricsModel.timestamp)
            
            result = db_session.execute(metrics_query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "status": "no_data", 
                    "period": summary_period.name,
                    "message": f"No performance data available for the {summary_period.name.lower()}"
                }
            
            # Analyze performance trends
            performance_analysis = self._analyze_performance_trends(metrics)
            
            # Get resource utilization patterns
            utilization_patterns = self._analyze_utilization_patterns(metrics)
            
            # Get performance recommendations
            recommendations = self._generate_performance_recommendations(metrics)
            
            return {
                "status": "success",
                "period": {
                    "name": summary_period.name,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat()
                },
                "performance_analysis": performance_analysis,
                "utilization_patterns": utilization_patterns,
                "recommendations": recommendations,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to generate performance report"
            }

    def get_system_summary(self, db_session: Session, period: str = "24h") -> Dict[str, Any]:
        """
        Synchronous wrapper for generate_system_summary.
        Used by NLP query translator which operates with sync database sessions.
        
        Args:
            db_session: Synchronous database session
            period: Time period for the summary
            
        Returns:
            Dictionary containing system summary data
        """
        try:
            summary_period = self._get_period_info(period)
            start_time = summary_period.start_time
            
            # Generate all summary components using sync session
            metrics_summary = self._get_metrics_summary_sync(db_session, start_time)
            alerts_summary = self._get_alerts_summary_sync(db_session, start_time)
            events_summary = self._get_events_summary_sync(db_session, start_time)
            logs_summary = self._get_logs_summary_sync(db_session, start_time)
            containers_summary = self._get_containers_summary_sync(db_session, start_time)
            
            return {
                "status": "success",
                "period": {
                    "name": summary_period.name,
                    "hours": summary_period.hours,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat()
                },
                "metrics": metrics_summary,
                "alerts": alerts_summary,
                "events": events_summary,
                "logs": logs_summary,
                "containers": containers_summary,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating system summary: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to generate system summary"
            }

    def _get_metrics_summary_sync(self, db_session: Session, start_time: datetime) -> Dict[str, Any]:
        """Synchronous version of _get_metrics_summary"""
        try:
            # Get metrics data for the period
            query = select(MetricsModel).where(
                MetricsModel.timestamp >= start_time
            ).order_by(desc(MetricsModel.timestamp))
            
            result = db_session.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {"status": "no_data", "count": 0}
            
            # Calculate statistics
            cpu_values = [float(m.cpu_usage) for m in metrics if m.cpu_usage is not None]
            memory_values = [float(m.memory_usage) for m in metrics if m.memory_usage is not None]
            disk_values = [float(m.disk_usage) for m in metrics if m.disk_usage is not None]
            
            return {
                "count": len(metrics),
                "cpu_usage": self._calculate_stats(cpu_values),
                "memory_usage": self._calculate_stats(memory_values),
                "disk_usage": self._calculate_stats(disk_values),
                "latest": {
                    "timestamp": metrics[0].timestamp.isoformat(),
                    "cpu_usage": float(metrics[0].cpu_usage) if metrics[0].cpu_usage else None,
                    "memory_usage": float(metrics[0].memory_usage) if metrics[0].memory_usage else None,
                    "disk_usage": float(metrics[0].disk_usage) if metrics[0].disk_usage else None,
                    "tcp_connections": metrics[0].tcp_connections
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_alerts_summary_sync(self, db_session: Session, start_time: datetime) -> Dict[str, Any]:
        """Synchronous version of _get_alerts_summary"""
        try:
            # Get alerts for the period
            query = select(AlertsModel).where(
                AlertsModel.timestamp >= start_time
            )
            
            result = db_session.execute(query)
            alerts = result.scalars().all()
            
            # Count by severity
            severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            resolved_count = 0
            unresolved_count = 0
            
            for alert in alerts:
                severity_counts[alert.severity] += 1
                if alert.resolved:
                    resolved_count += 1
                else:
                    unresolved_count += 1
            
            # Get recent unresolved alerts
            recent_unresolved_query = select(AlertsModel).where(
                and_(
                    AlertsModel.timestamp >= start_time,
                    AlertsModel.resolved == False
                )
            ).order_by(desc(AlertsModel.timestamp)).limit(5)
            
            recent_result = db_session.execute(recent_unresolved_query)
            recent_unresolved = recent_result.scalars().all()
            
            return {
                "total_count": len(alerts),
                "severity_breakdown": severity_counts,
                "resolved_count": resolved_count,
                "unresolved_count": unresolved_count,
                "recent_unresolved": [
                    {
                        "id": alert.id,
                        "timestamp": alert.timestamp.isoformat(),
                        "severity": alert.severity,
                        "type": alert.type,
                        "message": alert.message[:100] + "..." if len(alert.message or "") > 100 else alert.message
                    }
                    for alert in recent_unresolved
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting alerts summary: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_events_summary_sync(self, db_session: Session, start_time: datetime) -> Dict[str, Any]:
        """Synchronous version of _get_events_summary"""
        try:
            # Get events for the period
            query = select(DockerEventsModel).where(
                DockerEventsModel.timestamp >= start_time
            )
            
            result = db_session.execute(query)
            events = result.scalars().all()
            
            # Count by action type
            action_counts = {}
            container_events = {}
            
            for event in events:
                action = event.action or "unknown"
                action_counts[action] = action_counts.get(action, 0) + 1
                
                container = event.container or "unknown"
                if container not in container_events:
                    container_events[container] = 0
                container_events[container] += 1
            
            # Get most active containers
            most_active_containers = sorted(
                container_events.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            return {
                "total_count": len(events),
                "action_breakdown": action_counts,
                "most_active_containers": [
                    {"container": container, "event_count": count}
                    for container, count in most_active_containers
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting events summary: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_logs_summary_sync(self, db_session: Session, start_time: datetime) -> Dict[str, Any]:
        """Synchronous version of _get_logs_summary"""
        try:
            # Get log count for the period
            count_query = select(func.count(ContainerLogsModel.id)).where(
                ContainerLogsModel.timestamp >= start_time
            )
            
            count_result = db_session.execute(count_query)
            total_logs = count_result.scalar()
            
            # Get logs by container
            container_query = select(
                ContainerLogsModel.container,
                func.count(ContainerLogsModel.id).label('log_count')
            ).where(
                ContainerLogsModel.timestamp >= start_time
            ).group_by(ContainerLogsModel.container).order_by(
                desc(func.count(ContainerLogsModel.id))
            ).limit(10)
            
            container_result = db_session.execute(container_query)
            container_logs = container_result.all()
            
            return {
                "total_count": total_logs,
                "logs_by_container": [
                    {"container": row.container, "log_count": row.log_count}
                    for row in container_logs
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting logs summary: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_containers_summary_sync(self, db_session: Session, start_time: datetime) -> Dict[str, Any]:
        """Synchronous version of _get_containers_summary"""
        try:
            # Get unique containers from events
            events_query = select(DockerEventsModel.container).where(
                and_(
                    DockerEventsModel.timestamp >= start_time,
                    DockerEventsModel.container.isnot(None)
                )
            ).distinct()
            
            events_result = db_session.execute(events_query)
            containers_with_events = {row[0] for row in events_result.all()}
            
            # Get unique containers from logs
            logs_query = select(ContainerLogsModel.container).where(
                and_(
                    ContainerLogsModel.timestamp >= start_time,
                    ContainerLogsModel.container.isnot(None)
                )
            ).distinct()
            
            logs_result = db_session.execute(logs_query)
            containers_with_logs = {row[0] for row in logs_result.all()}
            
            all_containers = containers_with_events.union(containers_with_logs)
            
            return {
                "total_active_containers": len(all_containers),
                "containers_with_events": len(containers_with_events),
                "containers_with_logs": len(containers_with_logs),
                "container_list": list(all_containers)[:20]  # Limit to first 20
            }
            
        except Exception as e:
            self.logger.error(f"Error getting containers summary: {str(e)}")
            return {"status": "error", "message": str(e)}

# Create a global instance
summary_service = SummaryService()