"""
Enhanced Anomaly Detection Service

This service provides advanced functionality to detect various types of anomalies in the monitoring data:
- Intelligent spike detection using statistical analysis (CPU, memory, disk usage, TCP connections)
- Adaptive thresholds based on historical patterns and time-of-day variations
- Multi-window analysis for better context and reduced false positives
- Confidence scoring based on data quality and statistical significance
- Too many requests from a single IP address
- Unusual patterns in container logs and events
- Performance degradation detection with trend analysis
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
import math
import numpy as np

from db_models import (
    MetricsModel, DockerEventsModel, ContainerLogsModel, AlertsModel
)

logger = logging.getLogger(__name__)

@dataclass
class AnomalyThresholds:
    """Enhanced configuration for anomaly detection thresholds"""
    # Statistical thresholds (z-score based)
    cpu_spike_zscore: float = 2.0  # Standard deviations from mean
    memory_spike_zscore: float = 2.0  # Standard deviations from mean
    disk_spike_zscore: float = 1.8  # Standard deviations from mean
    connection_spike_zscore: float = 2.5  # Standard deviations from mean
    
    # Percentage-based thresholds (fallback for low data scenarios)
    cpu_spike_threshold: float = 30.0  # % increase from baseline
    memory_spike_threshold: float = 25.0  # % increase from baseline
    disk_spike_threshold: float = 20.0  # % increase from baseline
    connection_spike_threshold: int = 500  # new connections threshold
    
    # Minimum data requirements for statistical analysis
    min_baseline_samples: int = 10  # Minimum samples for reliable statistics
    min_recent_samples: int = 5  # Minimum recent samples
    
    # Confidence thresholds
    min_confidence: float = 0.7  # Minimum confidence to report anomaly
    high_confidence: float = 0.9  # Threshold for high confidence anomalies
    
    # Other thresholds
    ip_request_threshold: int = 100  # requests per hour from single IP
    error_rate_threshold: float = 10.0  # % error rate
    event_volume_threshold: int = 100  # events per period
    container_restart_threshold: int = 5  # restarts per period
    
    # Time-based analysis
    baseline_hours: int = 24  # Hours of historical data for baseline
    comparison_windows: List[int] = None  # Multiple comparison windows
    
    def __post_init__(self):
        if self.comparison_windows is None:
            self.comparison_windows = [1, 3, 6]  # 1h, 3h, 6h windows

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
    """Enhanced service for detecting anomalies in monitoring data using statistical analysis"""
    
    def __init__(self, thresholds: Optional[AnomalyThresholds] = None):
        self.thresholds = thresholds or AnomalyThresholds()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical measures for a dataset"""
        if not values or len(values) < 2:
            return {"mean": 0, "std": 0, "median": 0, "q75": 0, "q95": 0}
        
        try:
            values_array = np.array(values)
            return {
                "mean": float(np.mean(values_array)),
                "std": float(np.std(values_array, ddof=1)),
                "median": float(np.median(values_array)),
                "q75": float(np.percentile(values_array, 75)),
                "q95": float(np.percentile(values_array, 95)),
                "min": float(np.min(values_array)),
                "max": float(np.max(values_array))
            }
        except Exception as e:
            self.logger.warning(f"Error calculating statistics: {e}")
            return {"mean": 0, "std": 0, "median": 0, "q75": 0, "q95": 0}
    
    def _calculate_zscore(self, value: float, baseline_stats: Dict[str, float]) -> float:
        """Calculate z-score for a value against baseline statistics"""
        if baseline_stats["std"] == 0:
            return 0.0
        return abs(value - baseline_stats["mean"]) / baseline_stats["std"]
    
    def _calculate_confidence(self, 
                            zscore: float, 
                            baseline_samples: int, 
                            recent_samples: int,
                            trend_consistency: float = 1.0) -> float:
        """Calculate confidence score for an anomaly detection"""
        # Base confidence from z-score (sigmoid function)
        zscore_confidence = 1 / (1 + math.exp(-zscore + 2))
        
        # Sample size confidence
        baseline_confidence = min(baseline_samples / 50, 1.0)  # Max confidence at 50+ samples
        recent_confidence = min(recent_samples / 10, 1.0)  # Max confidence at 10+ samples
        sample_confidence = (baseline_confidence + recent_confidence) / 2
        
        # Overall confidence
        confidence = zscore_confidence * sample_confidence * trend_consistency
        return min(confidence, 1.0)
    
    def _detect_trend(self, values: List[float], window_size: int = 5) -> Dict[str, Any]:
        """Detect trend in time series data"""
        if len(values) < window_size:
            return {"trend": "insufficient_data", "slope": 0, "consistency": 0}
        
        try:
            # Calculate moving averages
            moving_avgs = []
            for i in range(len(values) - window_size + 1):
                avg = sum(values[i:i + window_size]) / window_size
                moving_avgs.append(avg)
            
            if len(moving_avgs) < 2:
                return {"trend": "insufficient_data", "slope": 0, "consistency": 0}
            
            # Calculate slope using linear regression
            x = np.arange(len(moving_avgs))
            y = np.array(moving_avgs)
            slope = np.polyfit(x, y, 1)[0]
            
            # Determine trend direction and consistency
            if abs(slope) < 0.1:
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
            
            # Calculate consistency (how well data fits the trend)
            predicted = np.polyval([slope, moving_avgs[0]], x)
            mse = np.mean((y - predicted) ** 2)
            consistency = max(0, 1 - (mse / np.var(y)) if np.var(y) > 0 else 0)
            
            return {
                "trend": trend,
                "slope": float(slope),
                "consistency": float(consistency)
            }
        except Exception as e:
            self.logger.warning(f"Error detecting trend: {e}")
            return {"trend": "error", "slope": 0, "consistency": 0}
    
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
        """Detect sudden spikes in system metrics using advanced statistical analysis"""
        anomalies = []
        
        try:
            # Get extended baseline for better statistical analysis
            baseline_start = start_time - timedelta(hours=self.thresholds.baseline_hours)
            recent_start = start_time
            
            # Get all historical metrics for baseline
            baseline_query = select(MetricsModel).where(
                and_(
                    MetricsModel.timestamp >= baseline_start,
                    MetricsModel.timestamp < recent_start
                )
            ).order_by(MetricsModel.timestamp)
            
            baseline_result = await db.execute(baseline_query)
            baseline_metrics = baseline_result.scalars().all()
            
            # Get recent metrics for comparison
            recent_query = select(MetricsModel).where(
                MetricsModel.timestamp >= recent_start
            ).order_by(MetricsModel.timestamp)
            
            recent_result = await db.execute(recent_query)
            recent_metrics = recent_result.scalars().all()
            
            if (len(baseline_metrics) < self.thresholds.min_baseline_samples or 
                len(recent_metrics) < self.thresholds.min_recent_samples):
                self.logger.warning(f"Insufficient data for statistical analysis: "
                                  f"baseline={len(baseline_metrics)}, recent={len(recent_metrics)}")
                return anomalies
            
            # Analyze each metric type
            metric_analyses = await self._analyze_metrics_statistically(
                baseline_metrics, recent_metrics
            )
            
            # Generate anomalies based on statistical analysis
            for metric_name, analysis in metric_analyses.items():
                if analysis["anomaly_detected"]:
                    anomaly = self._create_metric_anomaly(metric_name, analysis)
                    if anomaly and anomaly.confidence >= self.thresholds.min_confidence:
                        anomalies.append(anomaly)
            
        except Exception as e:
            self.logger.error(f"Error detecting metric spikes: {str(e)}")
        
        return anomalies
    
    async def _analyze_metrics_statistically(
        self, 
        baseline_metrics: List, 
        recent_metrics: List
    ) -> Dict[str, Dict[str, Any]]:
        """Perform statistical analysis on metrics to detect anomalies"""
        analyses = {}
        
        # Define metrics to analyze
        metrics_config = {
            "cpu_usage": {
                "zscore_threshold": self.thresholds.cpu_spike_zscore,
                "percentage_threshold": self.thresholds.cpu_spike_threshold,
                "resource_name": "system_cpu"
            },
            "memory_usage": {
                "zscore_threshold": self.thresholds.memory_spike_zscore,
                "percentage_threshold": self.thresholds.memory_spike_threshold,
                "resource_name": "system_memory"
            },
            "disk_usage": {
                "zscore_threshold": self.thresholds.disk_spike_zscore,
                "percentage_threshold": self.thresholds.disk_spike_threshold,
                "resource_name": "system_disk"
            },
            "tcp_connections": {
                "zscore_threshold": self.thresholds.connection_spike_zscore,
                "percentage_threshold": None,  # Use absolute threshold
                "resource_name": "network_connections"
            }
        }
        
        for metric_name, config in metrics_config.items():
            try:
                # Extract metric values
                baseline_values = [
                    float(getattr(m, metric_name)) 
                    for m in baseline_metrics 
                    if getattr(m, metric_name) is not None
                ]
                recent_values = [
                    float(getattr(m, metric_name)) 
                    for m in recent_metrics 
                    if getattr(m, metric_name) is not None
                ]
                
                if not baseline_values or not recent_values:
                    continue
                
                # Calculate baseline statistics
                baseline_stats = self._calculate_statistics(baseline_values)
                recent_stats = self._calculate_statistics(recent_values)
                
                # Detect trend in recent data
                trend_analysis = self._detect_trend(recent_values)
                
                # Calculate z-score for recent average
                recent_avg = recent_stats["mean"]
                zscore = self._calculate_zscore(recent_avg, baseline_stats)
                
                # Multi-window analysis for better context
                window_anomalies = []
                for window_hours in self.thresholds.comparison_windows:
                    window_analysis = await self._analyze_metric_window(
                        baseline_metrics, recent_metrics, metric_name, window_hours
                    )
                    window_anomalies.append(window_analysis)
                
                # Determine if anomaly exists
                anomaly_detected = False
                detection_method = "none"
                
                # Primary detection: Z-score based
                if zscore >= config["zscore_threshold"]:
                    anomaly_detected = True
                    detection_method = "zscore"
                
                # Fallback detection: Percentage based (for low variance scenarios)
                elif (config["percentage_threshold"] and baseline_stats["mean"] > 0):
                    percentage_increase = ((recent_avg - baseline_stats["mean"]) / baseline_stats["mean"]) * 100
                    if percentage_increase > config["percentage_threshold"]:
                        anomaly_detected = True
                        detection_method = "percentage"
                
                # Special handling for TCP connections (absolute threshold)
                elif metric_name == "tcp_connections":
                    conn_increase = recent_avg - baseline_stats["mean"]
                    if conn_increase > self.thresholds.connection_spike_threshold:
                        anomaly_detected = True
                        detection_method = "absolute"
                
                # Calculate confidence
                confidence = self._calculate_confidence(
                    zscore, 
                    len(baseline_values), 
                    len(recent_values),
                    trend_analysis["consistency"]
                )
                
                # Determine severity based on z-score and confidence
                severity = self._determine_severity(zscore, confidence, metric_name)
                
                analyses[metric_name] = {
                    "anomaly_detected": anomaly_detected,
                    "detection_method": detection_method,
                    "zscore": zscore,
                    "confidence": confidence,
                    "severity": severity,
                    "baseline_stats": baseline_stats,
                    "recent_stats": recent_stats,
                    "trend_analysis": trend_analysis,
                    "window_anomalies": window_anomalies,
                    "resource_name": config["resource_name"],
                    "baseline_samples": len(baseline_values),
                    "recent_samples": len(recent_values)
                }
                
            except Exception as e:
                self.logger.warning(f"Error analyzing {metric_name}: {e}")
                continue
        
        return analyses
    
    async def _analyze_metric_window(
        self, 
        baseline_metrics: List, 
        recent_metrics: List, 
        metric_name: str, 
        window_hours: int
    ) -> Dict[str, Any]:
        """Analyze a specific time window for additional context"""
        try:
            # Get metrics for the specific window
            window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)
            window_metrics = [
                m for m in recent_metrics 
                if m.timestamp >= window_start
            ]
            
            if not window_metrics:
                return {"window_hours": window_hours, "anomaly": False}
            
            window_values = [
                float(getattr(m, metric_name)) 
                for m in window_metrics 
                if getattr(m, metric_name) is not None
            ]
            
            if not window_values:
                return {"window_hours": window_hours, "anomaly": False}
            
            # Compare window average to baseline
            baseline_values = [
                float(getattr(m, metric_name)) 
                for m in baseline_metrics 
                if getattr(m, metric_name) is not None
            ]
            
            if not baseline_values:
                return {"window_hours": window_hours, "anomaly": False}
            
            baseline_stats = self._calculate_statistics(baseline_values)
            window_avg = statistics.mean(window_values)
            zscore = self._calculate_zscore(window_avg, baseline_stats)
            
            return {
                "window_hours": window_hours,
                "anomaly": zscore >= 1.5,  # Lower threshold for window analysis
                "zscore": zscore,
                "window_avg": window_avg,
                "baseline_avg": baseline_stats["mean"]
            }
            
        except Exception as e:
            self.logger.warning(f"Error analyzing {window_hours}h window for {metric_name}: {e}")
            return {"window_hours": window_hours, "anomaly": False}
    
    def _determine_severity(self, zscore: float, confidence: float, metric_name: str) -> str:
        """Determine severity based on z-score, confidence, and metric type"""
        # High severity thresholds
        high_zscore_threshold = 3.0
        critical_zscore_threshold = 4.0
        
        # Adjust thresholds based on metric type
        if metric_name == "cpu_usage":
            high_zscore_threshold = 2.5
            critical_zscore_threshold = 3.5
        elif metric_name == "memory_usage":
            high_zscore_threshold = 2.5
            critical_zscore_threshold = 3.5
        elif metric_name == "tcp_connections":
            high_zscore_threshold = 3.0
            critical_zscore_threshold = 4.5
        
        # Determine severity
        if zscore >= critical_zscore_threshold and confidence >= self.thresholds.high_confidence:
            return "HIGH"
        elif zscore >= high_zscore_threshold and confidence >= 0.8:
            return "HIGH"
        elif zscore >= 2.0 and confidence >= 0.7:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _create_metric_anomaly(self, metric_name: str, analysis: Dict[str, Any]) -> Optional[Anomaly]:
        """Create an anomaly object from metric analysis"""
        try:
            baseline_stats = analysis["baseline_stats"]
            recent_stats = analysis["recent_stats"]
            trend_analysis = analysis["trend_analysis"]
            
            # Calculate percentage change
            if baseline_stats["mean"] > 0:
                percentage_change = ((recent_stats["mean"] - baseline_stats["mean"]) / baseline_stats["mean"]) * 100
            else:
                percentage_change = 0
            
            # Create description based on detection method
            if analysis["detection_method"] == "zscore":
                description = (f"{metric_name.replace('_', ' ').title()} anomaly detected: "
                             f"{analysis['zscore']:.1f} standard deviations above baseline")
            elif analysis["detection_method"] == "percentage":
                description = (f"{metric_name.replace('_', ' ').title()} spike detected: "
                             f"{percentage_change:.1f}% increase from baseline")
            elif analysis["detection_method"] == "absolute":
                increase = recent_stats["mean"] - baseline_stats["mean"]
                description = (f"{metric_name.replace('_', ' ').title()} spike detected: "
                             f"{int(increase)} increase from baseline")
            else:
                description = f"{metric_name.replace('_', ' ').title()} anomaly detected"
            
            # Add trend information to description
            if trend_analysis["trend"] == "increasing":
                description += f" (trending upward)"
            elif trend_analysis["trend"] == "decreasing":
                description += f" (trending downward)"
            
            return Anomaly(
                type=f"{metric_name}_spike",
                severity=analysis["severity"],
                timestamp=datetime.now(timezone.utc),
                description=description,
                details={
                    "detection_method": analysis["detection_method"],
                    "zscore": round(analysis["zscore"], 2),
                    "baseline_mean": round(baseline_stats["mean"], 2),
                    "baseline_std": round(baseline_stats["std"], 2),
                    "recent_mean": round(recent_stats["mean"], 2),
                    "recent_std": round(recent_stats["std"], 2),
                    "percentage_change": round(percentage_change, 2),
                    "trend": trend_analysis["trend"],
                    "trend_slope": round(trend_analysis["slope"], 4),
                    "trend_consistency": round(trend_analysis["consistency"], 2),
                    "baseline_samples": analysis["baseline_samples"],
                    "recent_samples": analysis["recent_samples"],
                    "window_anomalies": analysis["window_anomalies"]
                },
                affected_resource=analysis["resource_name"],
                confidence=analysis["confidence"]
            )
            
        except Exception as e:
            self.logger.error(f"Error creating anomaly for {metric_name}: {e}")
            return None
    
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