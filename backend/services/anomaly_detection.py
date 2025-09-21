"""
Anomaly Detection Service

This service provides functionality to detect various types of anomalies in the monitoring data:
- Sudden spikes in metrics (CPU, memory, disk usage)
- Too many requests from a single IP address
- Unusual patterns in container logs and events
- Performance degradation detection
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_, text
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics
import logging
import re

from db_models import (
    MetricsModel, DockerEventsModel, ContainerLogsModel, AlertsModel
)

logger = logging.getLogger(__name__)

@dataclass
class AnomalyThresholds:
    """Configuration for anomaly detection thresholds"""
    cpu_spike_threshold: float = 30.0  # % increase from baseline
    memory_spike_threshold: float = 25.0  # % increase from baseline
    disk_spike_threshold: float = 20.0  # % increase from baseline
    ip_request_threshold: int = 100  # requests per hour from single IP
    error_rate_threshold: float = 10.0  # % error rate
    event_volume_threshold: int = 100  # events per period
    container_restart_threshold: int = 5  # restarts per period
    connection_spike_threshold: int = 500  # new connections threshold

@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    type: str
    severity: str  # LOW, MEDIUM, HIGH
    timestamp: datetime
    description: str
    details: Dict[str, Any]
    affected_resource: Optional[str] = None
    confidence: float = 1.0

class AnomalyDetectionService:
    """Service for detecting anomalies in monitoring data"""
    
    def __init__(self, thresholds: Optional[AnomalyThresholds] = None):
        self.thresholds = thresholds or AnomalyThresholds()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def detect_all_anomalies(
        self, 
        db: AsyncSession, 
        lookback_hours: int = 1
    ) -> List[Anomaly]:
        """
        Detect all types of anomalies in the specified time window
        
        Args:
            db: Database session
            lookback_hours: Hours to look back for anomaly detection
            
        Returns:
            List of detected anomalies
        """
        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
            anomalies = []
            
            # Detect metric spikes
            metric_anomalies = await self._detect_metric_spikes(db, start_time)
            anomalies.extend(metric_anomalies)
            
            # Detect IP-based anomalies (from logs)
            ip_anomalies = await self._detect_ip_anomalies(db, start_time)
            anomalies.extend(ip_anomalies)
            
            # Detect error rate anomalies
            error_anomalies = await self._detect_error_rate_anomalies(db, start_time)
            anomalies.extend(error_anomalies)
            
            # Detect container event anomalies
            event_anomalies = await self._detect_event_anomalies(db, start_time)
            anomalies.extend(event_anomalies)
            
            # Sort by severity and timestamp
            anomalies.sort(key=lambda x: (
                {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[x.severity],
                x.timestamp
            ), reverse=True)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            raise
    
    async def detect_metric_spikes(
        self, 
        db: AsyncSession, 
        lookback_hours: int = 1
    ) -> List[Anomaly]:
        """
        Public method to detect metric spikes
        
        Args:
            db: Database session
            lookback_hours: Hours to look back for anomaly detection
            
        Returns:
            List of metric spike anomalies
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        return await self._detect_metric_spikes(db, start_time)
    
    async def detect_ip_anomalies(
        self, 
        db: AsyncSession, 
        lookback_hours: int = 1
    ) -> List[Anomaly]:
        """
        Public method to detect IP-based anomalies
        
        Args:
            db: Database session
            lookback_hours: Hours to look back for anomaly detection
            
        Returns:
            List of IP-based anomalies
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        return await self._detect_ip_anomalies(db, start_time)
    
    async def detect_error_rate_anomalies(
        self, 
        db: AsyncSession, 
        lookback_hours: int = 1
    ) -> List[Anomaly]:
        """
        Public method to detect error rate anomalies
        
        Args:
            db: Database session
            lookback_hours: Hours to look back for anomaly detection
            
        Returns:
            List of error rate anomalies
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        return await self._detect_error_rate_anomalies(db, start_time)
    
    async def detect_event_anomalies(
        self, 
        db: AsyncSession, 
        lookback_hours: int = 1
    ) -> List[Anomaly]:
        """
        Public method to detect event anomalies
        
        Args:
            db: Database session
            lookback_hours: Hours to look back for anomaly detection
            
        Returns:
            List of event anomalies
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        return await self._detect_event_anomalies(db, start_time)
    
    async def _detect_metric_spikes(
        self, 
        db: AsyncSession, 
        start_time: datetime
    ) -> List[Anomaly]:
        """Detect sudden spikes in system metrics"""
        anomalies = []
        
        try:
            # Get recent metrics (last hour) and baseline (previous hour)
            recent_start = start_time
            baseline_start = start_time - timedelta(hours=1)
            
            # Get baseline metrics
            baseline_query = select(MetricsModel).where(
                and_(
                    MetricsModel.timestamp >= baseline_start,
                    MetricsModel.timestamp < recent_start
                )
            ).order_by(MetricsModel.timestamp)
            
            baseline_result = await db.execute(baseline_query)
            baseline_metrics = baseline_result.scalars().all()
            
            # Get recent metrics
            recent_query = select(MetricsModel).where(
                MetricsModel.timestamp >= recent_start
            ).order_by(MetricsModel.timestamp)
            
            recent_result = await db.execute(recent_query)
            recent_metrics = recent_result.scalars().all()
            
            if len(baseline_metrics) < 5 or len(recent_metrics) < 5:
                return anomalies  # Not enough data
            
            # Calculate baseline averages
            baseline_cpu = statistics.mean([float(m.cpu_usage) for m in baseline_metrics if m.cpu_usage])
            baseline_memory = statistics.mean([float(m.memory_usage) for m in baseline_metrics if m.memory_usage])
            baseline_disk = statistics.mean([float(m.disk_usage) for m in baseline_metrics if m.disk_usage])
            
            # Calculate recent averages
            recent_cpu = statistics.mean([float(m.cpu_usage) for m in recent_metrics if m.cpu_usage])
            recent_memory = statistics.mean([float(m.memory_usage) for m in recent_metrics if m.memory_usage])
            recent_disk = statistics.mean([float(m.disk_usage) for m in recent_metrics if m.disk_usage])
            
            # Check for CPU spikes
            if baseline_cpu > 0:
                cpu_increase = ((recent_cpu - baseline_cpu) / baseline_cpu) * 100
                if cpu_increase > self.thresholds.cpu_spike_threshold:
                    severity = "HIGH" if cpu_increase > 50 else "MEDIUM"
                    anomalies.append(Anomaly(
                        type="cpu_spike",
                        severity=severity,
                        timestamp=datetime.now(timezone.utc),
                        description=f"CPU usage spike detected: {cpu_increase:.1f}% increase",
                        details={
                            "baseline_cpu": round(baseline_cpu, 2),
                            "recent_cpu": round(recent_cpu, 2),
                            "increase_percent": round(cpu_increase, 2)
                        },
                        affected_resource="system_cpu"
                    ))
            
            # Check for Memory spikes
            if baseline_memory > 0:
                memory_increase = ((recent_memory - baseline_memory) / baseline_memory) * 100
                if memory_increase > self.thresholds.memory_spike_threshold:
                    severity = "HIGH" if memory_increase > 40 else "MEDIUM"
                    anomalies.append(Anomaly(
                        type="memory_spike",
                        severity=severity,
                        timestamp=datetime.now(timezone.utc),
                        description=f"Memory usage spike detected: {memory_increase:.1f}% increase",
                        details={
                            "baseline_memory": round(baseline_memory, 2),
                            "recent_memory": round(recent_memory, 2),
                            "increase_percent": round(memory_increase, 2)
                        },
                        affected_resource="system_memory"
                    ))
            
            # Check for Disk spikes
            if baseline_disk > 0:
                disk_increase = ((recent_disk - baseline_disk) / baseline_disk) * 100
                if disk_increase > self.thresholds.disk_spike_threshold:
                    severity = "MEDIUM" if disk_increase > 30 else "LOW"
                    anomalies.append(Anomaly(
                        type="disk_spike",
                        severity=severity,
                        timestamp=datetime.now(timezone.utc),
                        description=f"Disk usage spike detected: {disk_increase:.1f}% increase",
                        details={
                            "baseline_disk": round(baseline_disk, 2),
                            "recent_disk": round(recent_disk, 2),
                            "increase_percent": round(disk_increase, 2)
                        },
                        affected_resource="system_disk"
                    ))
            
            # Check for TCP connection spikes
            if recent_metrics and baseline_metrics:
                recent_connections = [m.tcp_connections for m in recent_metrics if m.tcp_connections]
                baseline_connections = [m.tcp_connections for m in baseline_metrics if m.tcp_connections]
                
                if recent_connections and baseline_connections:
                    recent_avg_conn = statistics.mean(recent_connections)
                    baseline_avg_conn = statistics.mean(baseline_connections)
                    
                    conn_increase = recent_avg_conn - baseline_avg_conn
                    if conn_increase > self.thresholds.connection_spike_threshold:
                        severity = "HIGH" if conn_increase > 1000 else "MEDIUM"
                        anomalies.append(Anomaly(
                            type="connection_spike",
                            severity=severity,
                            timestamp=datetime.now(timezone.utc),
                            description=f"TCP connection spike detected: {int(conn_increase)} new connections",
                            details={
                                "baseline_connections": int(baseline_avg_conn),
                                "recent_connections": int(recent_avg_conn),
                                "increase": int(conn_increase)
                            },
                            affected_resource="network_connections"
                        ))
            
        except Exception as e:
            self.logger.error(f"Error detecting metric spikes: {str(e)}")
        
        return anomalies
    
    async def _detect_ip_anomalies(
        self, 
        db: AsyncSession, 
        start_time: datetime
    ) -> List[Anomaly]:
        """Detect anomalies related to IP addresses (too many requests from single IP)"""
        anomalies = []
        
        try:
            # Extract IP addresses from container logs
            logs_query = select(ContainerLogsModel).where(
                ContainerLogsModel.timestamp >= start_time
            )
            
            result = await db.execute(logs_query)
            logs = result.scalars().all()
            
            # Extract IP addresses from log messages using regex
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ip_requests = defaultdict(list)
            
            for log in logs:
                if log.message:
                    ips = re.findall(ip_pattern, log.message)
                    for ip in ips:
                        # Filter out private/local IPs for external monitoring
                        if not self._is_private_ip(ip):
                            ip_requests[ip].append(log.timestamp)
            
            # Check for IPs with too many requests
            for ip, timestamps in ip_requests.items():
                request_count = len(timestamps)
                
                if request_count > self.thresholds.requests_per_ip_threshold:
                    # Calculate requests per hour
                    time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600
                    requests_per_hour = request_count / max(time_span_hours, 1)
                    
                    severity = "HIGH" if request_count > 500 else "MEDIUM"
                    anomalies.append(Anomaly(
                        type="ip_request_spike",
                        severity=severity,
                        timestamp=max(timestamps),
                        description=f"High request volume from IP {ip}: {request_count} requests",
                        details={
                            "ip_address": ip,
                            "total_requests": request_count,
                            "requests_per_hour": round(requests_per_hour, 2),
                            "time_span_hours": round(time_span_hours, 2),
                            "first_request": min(timestamps).isoformat(),
                            "last_request": max(timestamps).isoformat()
                        },
                        affected_resource=f"ip_{ip}"
                    ))
            
        except Exception as e:
            self.logger.error(f"Error detecting IP anomalies: {str(e)}")
        
        return anomalies
    
    async def _detect_error_rate_anomalies(
        self, 
        db: AsyncSession, 
        start_time: datetime
    ) -> List[Anomaly]:
        """Detect anomalies in error rates from logs"""
        anomalies = []
        
        try:
            # Get logs for the period
            logs_query = select(ContainerLogsModel).where(
                ContainerLogsModel.timestamp >= start_time
            )
            
            result = await db.execute(logs_query)
            logs = result.scalars().all()
            
            if not logs:
                return anomalies
            
            # Count error logs vs total logs by container
            container_stats = defaultdict(lambda: {"total": 0, "errors": 0})
            
            error_keywords = ["error", "exception", "failed", "fatal", "critical", "500", "404", "timeout"]
            
            for log in logs:
                container = log.container or "unknown"
                container_stats[container]["total"] += 1
                
                if log.message:
                    message_lower = log.message.lower()
                    if any(keyword in message_lower for keyword in error_keywords):
                        container_stats[container]["errors"] += 1
            
            # Check error rates for each container
            for container, stats in container_stats.items():
                if stats["total"] >= 10:  # Only check containers with sufficient logs
                    error_rate = (stats["errors"] / stats["total"]) * 100
                    
                    if error_rate > self.thresholds.error_rate_threshold:
                        severity = "HIGH" if error_rate > 25 else "MEDIUM"
                        anomalies.append(Anomaly(
                            type="high_error_rate",
                            severity=severity,
                            timestamp=datetime.now(timezone.utc),
                            description=f"High error rate in container {container}: {error_rate:.1f}%",
                            details={
                                "container": container,
                                "error_rate": round(error_rate, 2),
                                "total_logs": stats["total"],
                                "error_logs": stats["errors"]
                            },
                            affected_resource=container
                        ))
            
        except Exception as e:
            self.logger.error(f"Error detecting error rate anomalies: {str(e)}")
        
        return anomalies
    
    async def _detect_event_anomalies(
        self, 
        db: AsyncSession, 
        start_time: datetime
    ) -> List[Anomaly]:
        """Detect anomalies in Docker events"""
        anomalies = []
        
        try:
            # Get events for the period
            events_query = select(DockerEventsModel).where(
                DockerEventsModel.timestamp >= start_time
            )
            
            result = await db.execute(events_query)
            events = result.scalars().all()
            
            if not events:
                return anomalies
            
            # Count events by type and container
            event_counts = Counter()
            container_events = defaultdict(list)
            
            for event in events:
                event_type = f"{event.type}:{event.action}" if event.type and event.action else "unknown"
                event_counts[event_type] += 1
                
                if event.container:
                    container_events[event.container].append(event)
            
            # Check for unusual event patterns
            total_events = len(events)
            
            # Detect containers with too many restart events
            for container, container_event_list in container_events.items():
                restart_events = [e for e in container_event_list if e.action and "restart" in e.action.lower()]
                
                if len(restart_events) > 5:  # More than 5 restarts in the period
                    anomalies.append(Anomaly(
                        type="container_restart_loop",
                        severity="HIGH",
                        timestamp=max(e.timestamp for e in restart_events),
                        description=f"Container {container} restarted {len(restart_events)} times",
                        details={
                            "container": container,
                            "restart_count": len(restart_events),
                            "time_span": str(max(e.timestamp for e in restart_events) - min(e.timestamp for e in restart_events))
                        },
                        affected_resource=container
                    ))
            
            # Detect unusual event spikes
            if total_events > 100:  # High event volume
                anomalies.append(Anomaly(
                    type="high_event_volume",
                    severity="MEDIUM",
                    timestamp=datetime.now(timezone.utc),
                    description=f"High Docker event volume: {total_events} events",
                    details={
                        "total_events": total_events,
                        "top_event_types": dict(event_counts.most_common(5))
                    },
                    affected_resource="docker_events"
                ))
            
        except Exception as e:
            self.logger.error(f"Error detecting event anomalies: {str(e)}")
        
        return anomalies
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if an IP address is private/local"""
        try:
            parts = [int(x) for x in ip.split('.')]
            
            # Private IP ranges
            if parts[0] == 10:
                return True
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return True
            if parts[0] == 192 and parts[1] == 168:
                return True
            if parts[0] == 127:  # Localhost
                return True
            
            return False
        except:
            return True  # If we can't parse it, assume it's private
    
    async def get_anomaly_summary(
        self, 
        db: AsyncSession, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get a summary of anomalies detected in the specified time period
        
        Args:
            db: Database session
            hours: Hours to look back
            
        Returns:
            Dictionary containing anomaly summary
        """
        try:
            anomalies = await self.detect_all_anomalies(db, hours)
            
            # Group by type and severity
            by_type = defaultdict(int)
            by_severity = defaultdict(int)
            affected_resources = set()
            
            for anomaly in anomalies:
                by_type[anomaly.type] += 1
                by_severity[anomaly.severity] += 1
                if anomaly.affected_resource:
                    affected_resources.add(anomaly.affected_resource)
            
            return {
                "total_anomalies": len(anomalies),
                "by_type": dict(by_type),
                "by_severity": dict(by_severity),
                "affected_resources": list(affected_resources),
                "recent_anomalies": [
                    {
                        "type": a.type,
                        "severity": a.severity,
                        "timestamp": a.timestamp.isoformat(),
                        "description": a.description,
                        "affected_resource": a.affected_resource
                    }
                    for a in anomalies[:10]  # Last 10 anomalies
                ],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating anomaly summary: {str(e)}")
            raise

# Create a global instance
anomaly_detector = AnomalyDetectionService()