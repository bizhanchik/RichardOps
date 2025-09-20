"""
NLP Query Translator for converting parsed natural language queries into database queries.

This module translates structured NLP queries into SQL queries, OpenSearch queries,
and other data source queries for security monitoring and log analysis.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.orm import Session

from db_models import (
    ContainerLogsModel, DockerEventsModel, AlertsModel, 
    MetricsModel, EmailNotificationsModel
)
from services.nlp_query_parser import ParsedQuery, QueryIntent, EntityType


class QueryTranslator:
    """
    Translates parsed NLP queries into database queries for various data sources.
    
    Supports SQL queries for PostgreSQL, OpenSearch queries for log analysis,
    and aggregation queries for reporting and analytics.
    """
    
    def __init__(self):
        """Initialize the query translator."""
        self.model_mapping = {
            "logs": ContainerLogsModel,
            "container_logs": ContainerLogsModel,
            "docker_events": DockerEventsModel,
            "alerts": AlertsModel,
            "metrics": MetricsModel,
            "notifications": EmailNotificationsModel
        }
    
    def translate_query(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """
        Translate a parsed NLP query into executable database queries.
        
        Args:
            parsed_query: The parsed natural language query
            db_session: SQLAlchemy database session
            
        Returns:
            Dict containing query results and metadata
        """
        if parsed_query.intent == QueryIntent.SEARCH_LOGS:
            return self._handle_search_logs(parsed_query, db_session)
        elif parsed_query.intent == QueryIntent.SHOW_ALERTS:
            return self._handle_show_alerts(parsed_query, db_session)
        elif parsed_query.intent == QueryIntent.GENERATE_REPORT:
            return self._handle_generate_report(parsed_query, db_session)
        elif parsed_query.intent == QueryIntent.INVESTIGATE:
            return self._handle_investigate(parsed_query, db_session)
        elif parsed_query.intent == QueryIntent.ANALYZE_TRENDS:
            return self._handle_analyze_trends(parsed_query, db_session)
        else:
            return {
                "error": f"Unsupported query intent: {parsed_query.intent}",
                "suggestions": self._get_query_suggestions()
            }
    
    def _handle_search_logs(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle log search queries."""
        # Determine which table to query based on entities
        table_model = self._determine_log_table(parsed_query)
        
        # Build base query
        query = db_session.query(table_model)
        
        # Apply filters
        query = self._apply_filters(query, parsed_query, table_model)
        
        # Apply time range
        query = self._apply_time_filter(query, parsed_query, table_model)
        
        # Order by timestamp descending
        query = query.order_by(desc(table_model.timestamp))
        
        # Limit results
        query = query.limit(100)
        
        # Execute query
        results = query.all()
        
        return {
            "intent": "search_logs",
            "results": [self._serialize_result(result) for result in results],
            "count": len(results),
            "table": table_model.__tablename__,
            "query_info": {
                "filters_applied": self._get_applied_filters(parsed_query),
                "time_range": parsed_query.structured_params.get("time_range"),
                "confidence": parsed_query.confidence
            }
        }
    
    def _handle_show_alerts(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle alert display queries."""
        query = db_session.query(AlertsModel)
        
        # Apply filters
        filters = parsed_query.structured_params.get("filters", {})
        
        if "severity" in filters:
            query = query.filter(AlertsModel.severity == filters["severity"])
        
        if "status" in filters:
            if filters["status"] in ["resolved", "closed"]:
                query = query.filter(AlertsModel.resolved == True)
            elif filters["status"] in ["unresolved", "open", "active"]:
                query = query.filter(AlertsModel.resolved == False)
        
        # Apply time range
        query = self._apply_time_filter(query, parsed_query, AlertsModel)
        
        # Order by timestamp descending
        query = query.order_by(desc(AlertsModel.timestamp))
        
        # Limit results
        query = query.limit(50)
        
        results = query.all()
        
        # Get summary statistics
        stats = self._get_alert_statistics(db_session, parsed_query)
        
        return {
            "intent": "show_alerts",
            "results": [self._serialize_result(result) for result in results],
            "count": len(results),
            "statistics": stats,
            "query_info": {
                "filters_applied": self._get_applied_filters(parsed_query),
                "time_range": parsed_query.structured_params.get("time_range"),
                "confidence": parsed_query.confidence
            }
        }
    
    def _handle_generate_report(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle report generation queries."""
        time_range = parsed_query.structured_params.get("time_range")
        if not time_range:
            # Default to last week for reports
            from datetime import timedelta
            now = datetime.now()
            time_range = {"start": now - timedelta(weeks=1), "end": now}
        
        # Generate comprehensive security report
        report_data = {
            "report_type": "security_summary",
            "time_period": {
                "start": time_range["start"].isoformat(),
                "end": time_range["end"].isoformat()
            },
            "alerts_summary": self._generate_alerts_summary(db_session, time_range),
            "docker_events_summary": self._generate_docker_summary(db_session, time_range),
            "log_analysis": self._generate_log_analysis(db_session, time_range),
            "metrics_overview": self._generate_metrics_overview(db_session, time_range),
            "recommendations": self._generate_recommendations(db_session, time_range)
        }
        
        return {
            "intent": "generate_report",
            "report": report_data,
            "query_info": {
                "time_range": time_range,
                "confidence": parsed_query.confidence
            }
        }
    
    def _handle_investigate(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle investigation queries."""
        filters = parsed_query.structured_params.get("filters", {})
        investigation_results = {}
        
        # IP address investigation
        if "ip_address" in filters:
            ip_address = filters["ip_address"]
            investigation_results["ip_analysis"] = self._investigate_ip_address(
                db_session, ip_address, parsed_query
            )
        
        # Container investigation
        if "container" in filters:
            container = filters["container"]
            investigation_results["container_analysis"] = self._investigate_container(
                db_session, container, parsed_query
            )
        
        # General security investigation
        if not investigation_results:
            investigation_results["general_analysis"] = self._investigate_general_security(
                db_session, parsed_query
            )
        
        return {
            "intent": "investigate",
            "investigation": investigation_results,
            "query_info": {
                "filters_applied": self._get_applied_filters(parsed_query),
                "time_range": parsed_query.structured_params.get("time_range"),
                "confidence": parsed_query.confidence
            }
        }
    
    def _handle_analyze_trends(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle trend analysis queries."""
        time_range = parsed_query.structured_params.get("time_range")
        if not time_range:
            # Default to last month for trends
            from datetime import timedelta
            now = datetime.now()
            time_range = {"start": now - timedelta(days=30), "end": now}
        
        trends_data = {
            "alert_trends": self._analyze_alert_trends(db_session, time_range),
            "docker_activity_trends": self._analyze_docker_trends(db_session, time_range),
            "log_volume_trends": self._analyze_log_trends(db_session, time_range),
            "metrics_trends": self._analyze_metrics_trends(db_session, time_range)
        }
        
        return {
            "intent": "analyze_trends",
            "trends": trends_data,
            "query_info": {
                "time_range": time_range,
                "confidence": parsed_query.confidence
            }
        }
    
    def _determine_log_table(self, parsed_query: ParsedQuery) -> Any:
        """Determine which table to query based on the parsed query."""
        filters = parsed_query.structured_params.get("filters", {})
        
        # Check for container-specific queries
        if "container" in filters or any(e.type == EntityType.CONTAINER_NAME for e in parsed_query.entities):
            return ContainerLogsModel
        
        # Check for Docker event queries
        if "docker" in parsed_query.original_query.lower() or "event" in filters:
            return DockerEventsModel
        
        # Default to container logs
        return ContainerLogsModel
    
    def _apply_filters(self, query, parsed_query: ParsedQuery, model) -> Any:
        """Apply filters to the query based on parsed entities."""
        filters = parsed_query.structured_params.get("filters", {})
        
        if hasattr(model, 'container') and "container" in filters:
            query = query.filter(model.container.ilike(f"%{filters['container']}%"))
        
        if hasattr(model, 'message') and "log_level" in filters:
            log_level = filters["log_level"]
            query = query.filter(model.message.ilike(f"%{log_level}%"))
        
        if hasattr(model, 'severity') and "severity" in filters:
            query = query.filter(model.severity == filters["severity"])
        
        if hasattr(model, 'type') and "event_type" in filters:
            query = query.filter(model.type.ilike(f"%{filters['event_type']}%"))
        
        # Add text search for general queries
        search_terms = self._extract_search_terms(parsed_query.original_query)
        if search_terms and hasattr(model, 'message'):
            search_conditions = []
            for term in search_terms:
                search_conditions.append(model.message.ilike(f"%{term}%"))
            if search_conditions:
                query = query.filter(or_(*search_conditions))
        
        return query
    
    def _apply_time_filter(self, query, parsed_query: ParsedQuery, model) -> Any:
        """Apply time range filter to the query."""
        time_range = parsed_query.structured_params.get("time_range")
        if time_range and hasattr(model, 'timestamp'):
            query = query.filter(
                and_(
                    model.timestamp >= time_range["start"],
                    model.timestamp <= time_range["end"]
                )
            )
        return query
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract search terms from the original query."""
        # Remove common words and extract meaningful terms
        stop_words = {
            "show", "me", "all", "the", "in", "from", "with", "and", "or", "of",
            "to", "for", "on", "at", "by", "is", "are", "was", "were", "been",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "must", "shall", "a", "an", "this",
            "that", "these", "those"
        }
        
        words = query.lower().split()
        search_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Filter out time-related words that are already handled
        time_words = {"hour", "day", "week", "month", "today", "yesterday", "last", "past"}
        search_terms = [term for term in search_terms if term not in time_words]
        
        return search_terms[:5]  # Limit to 5 terms
    
    def _serialize_result(self, result) -> Dict[str, Any]:
        """Serialize a database result to a dictionary."""
        if hasattr(result, '__dict__'):
            data = {}
            for column in result.__table__.columns:
                value = getattr(result, column.name)
                if isinstance(value, datetime):
                    data[column.name] = value.isoformat()
                else:
                    data[column.name] = value
            return data
        return str(result)
    
    def _get_applied_filters(self, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Get a summary of applied filters."""
        return {
            "entities_found": len(parsed_query.entities),
            "entity_types": [e.type.value for e in parsed_query.entities],
            "filters": parsed_query.structured_params.get("filters", {}),
            "has_time_range": parsed_query.structured_params.get("time_range") is not None
        }
    
    def _get_alert_statistics(self, db_session: Session, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Get alert statistics for the given time range."""
        base_query = db_session.query(AlertsModel)
        base_query = self._apply_time_filter(base_query, parsed_query, AlertsModel)
        
        total_alerts = base_query.count()
        resolved_alerts = base_query.filter(AlertsModel.resolved == True).count()
        
        severity_counts = {}
        for severity in ["LOW", "MEDIUM", "HIGH"]:
            count = base_query.filter(AlertsModel.severity == severity).count()
            severity_counts[severity] = count
        
        return {
            "total_alerts": total_alerts,
            "resolved_alerts": resolved_alerts,
            "unresolved_alerts": total_alerts - resolved_alerts,
            "severity_breakdown": severity_counts,
            "resolution_rate": (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0
        }
    
    def _generate_alerts_summary(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate alerts summary for reports."""
        query = db_session.query(AlertsModel).filter(
            and_(
                AlertsModel.timestamp >= time_range["start"],
                AlertsModel.timestamp <= time_range["end"]
            )
        )
        
        total = query.count()
        by_severity = {}
        for severity in ["LOW", "MEDIUM", "HIGH"]:
            by_severity[severity] = query.filter(AlertsModel.severity == severity).count()
        
        resolved = query.filter(AlertsModel.resolved == True).count()
        
        return {
            "total_alerts": total,
            "by_severity": by_severity,
            "resolved": resolved,
            "unresolved": total - resolved,
            "resolution_rate": (resolved / total * 100) if total > 0 else 0
        }
    
    def _generate_docker_summary(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate Docker events summary for reports."""
        query = db_session.query(DockerEventsModel).filter(
            and_(
                DockerEventsModel.timestamp >= time_range["start"],
                DockerEventsModel.timestamp <= time_range["end"]
            )
        )
        
        total_events = query.count()
        
        # Count by action type
        action_counts = {}
        actions = db_session.query(DockerEventsModel.action).filter(
            and_(
                DockerEventsModel.timestamp >= time_range["start"],
                DockerEventsModel.timestamp <= time_range["end"]
            )
        ).distinct().all()
        
        for action_tuple in actions:
            action = action_tuple[0]
            if action:
                count = query.filter(DockerEventsModel.action == action).count()
                action_counts[action] = count
        
        return {
            "total_events": total_events,
            "by_action": action_counts,
            "unique_containers": query.with_entities(DockerEventsModel.container).distinct().count()
        }
    
    def _generate_log_analysis(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate log analysis for reports."""
        query = db_session.query(ContainerLogsModel).filter(
            and_(
                ContainerLogsModel.timestamp >= time_range["start"],
                ContainerLogsModel.timestamp <= time_range["end"]
            )
        )
        
        total_logs = query.count()
        unique_containers = query.with_entities(ContainerLogsModel.container).distinct().count()
        
        # Estimate log levels (simple keyword matching)
        error_logs = query.filter(ContainerLogsModel.message.ilike('%error%')).count()
        warn_logs = query.filter(ContainerLogsModel.message.ilike('%warn%')).count()
        
        return {
            "total_log_entries": total_logs,
            "unique_containers": unique_containers,
            "estimated_errors": error_logs,
            "estimated_warnings": warn_logs,
            "error_rate": (error_logs / total_logs * 100) if total_logs > 0 else 0
        }
    
    def _generate_metrics_overview(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate metrics overview for reports."""
        query = db_session.query(MetricsModel).filter(
            and_(
                MetricsModel.timestamp >= time_range["start"],
                MetricsModel.timestamp <= time_range["end"]
            )
        )
        
        if query.count() == 0:
            return {"message": "No metrics data available for this time period"}
        
        # Calculate averages
        avg_cpu = query.with_entities(func.avg(MetricsModel.cpu_usage)).scalar() or 0
        avg_memory = query.with_entities(func.avg(MetricsModel.memory_usage)).scalar() or 0
        avg_disk = query.with_entities(func.avg(MetricsModel.disk_usage)).scalar() or 0
        
        return {
            "average_cpu_usage": round(float(avg_cpu), 2),
            "average_memory_usage": round(float(avg_memory), 2),
            "average_disk_usage": round(float(avg_disk), 2),
            "data_points": query.count()
        }
    
    def _generate_recommendations(self, db_session: Session, time_range: Dict[str, datetime]) -> List[str]:
        """Generate security recommendations based on the data."""
        recommendations = []
        
        # Check for high alert volume
        alert_count = db_session.query(AlertsModel).filter(
            and_(
                AlertsModel.timestamp >= time_range["start"],
                AlertsModel.timestamp <= time_range["end"]
            )
        ).count()
        
        if alert_count > 100:
            recommendations.append("High alert volume detected. Consider reviewing alert thresholds.")
        
        # Check resolution rate
        resolved_count = db_session.query(AlertsModel).filter(
            and_(
                AlertsModel.timestamp >= time_range["start"],
                AlertsModel.timestamp <= time_range["end"],
                AlertsModel.resolved == True
            )
        ).count()
        
        if alert_count > 0 and (resolved_count / alert_count) < 0.5:
            recommendations.append("Low alert resolution rate. Consider improving incident response processes.")
        
        # Check for error patterns
        error_logs = db_session.query(ContainerLogsModel).filter(
            and_(
                ContainerLogsModel.timestamp >= time_range["start"],
                ContainerLogsModel.timestamp <= time_range["end"],
                ContainerLogsModel.message.ilike('%error%')
            )
        ).count()
        
        if error_logs > 50:
            recommendations.append("High error log volume detected. Review application health and error handling.")
        
        if not recommendations:
            recommendations.append("System appears to be operating normally. Continue monitoring.")
        
        return recommendations
    
    def _investigate_ip_address(self, db_session: Session, ip_address: str, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Investigate activities related to a specific IP address."""
        time_range = parsed_query.structured_params.get("time_range")
        
        # Search in container logs
        log_query = db_session.query(ContainerLogsModel)
        if time_range:
            log_query = log_query.filter(
                and_(
                    ContainerLogsModel.timestamp >= time_range["start"],
                    ContainerLogsModel.timestamp <= time_range["end"]
                )
            )
        
        ip_logs = log_query.filter(ContainerLogsModel.message.ilike(f'%{ip_address}%')).limit(20).all()
        
        # Search in alerts
        alert_query = db_session.query(AlertsModel)
        if time_range:
            alert_query = alert_query.filter(
                and_(
                    AlertsModel.timestamp >= time_range["start"],
                    AlertsModel.timestamp <= time_range["end"]
                )
            )
        
        ip_alerts = alert_query.filter(AlertsModel.message.ilike(f'%{ip_address}%')).limit(10).all()
        
        return {
            "ip_address": ip_address,
            "related_logs": [self._serialize_result(log) for log in ip_logs],
            "related_alerts": [self._serialize_result(alert) for alert in ip_alerts],
            "log_count": len(ip_logs),
            "alert_count": len(ip_alerts),
            "risk_assessment": "HIGH" if len(ip_alerts) > 0 else "MEDIUM" if len(ip_logs) > 5 else "LOW"
        }
    
    def _investigate_container(self, db_session: Session, container: str, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Investigate activities related to a specific container."""
        time_range = parsed_query.structured_params.get("time_range")
        
        # Container logs
        log_query = db_session.query(ContainerLogsModel).filter(
            ContainerLogsModel.container.ilike(f'%{container}%')
        )
        if time_range:
            log_query = log_query.filter(
                and_(
                    ContainerLogsModel.timestamp >= time_range["start"],
                    ContainerLogsModel.timestamp <= time_range["end"]
                )
            )
        
        container_logs = log_query.limit(20).all()
        error_logs = log_query.filter(ContainerLogsModel.message.ilike('%error%')).count()
        
        # Docker events
        event_query = db_session.query(DockerEventsModel).filter(
            DockerEventsModel.container.ilike(f'%{container}%')
        )
        if time_range:
            event_query = event_query.filter(
                and_(
                    DockerEventsModel.timestamp >= time_range["start"],
                    DockerEventsModel.timestamp <= time_range["end"]
                )
            )
        
        container_events = event_query.limit(10).all()
        
        return {
            "container": container,
            "recent_logs": [self._serialize_result(log) for log in container_logs],
            "recent_events": [self._serialize_result(event) for event in container_events],
            "total_logs": log_query.count(),
            "error_logs": error_logs,
            "health_status": "UNHEALTHY" if error_logs > 10 else "HEALTHY"
        }
    
    def _investigate_general_security(self, db_session: Session, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Perform general security investigation."""
        time_range = parsed_query.structured_params.get("time_range")
        
        # Recent high severity alerts
        alert_query = db_session.query(AlertsModel).filter(AlertsModel.severity == "HIGH")
        if time_range:
            alert_query = alert_query.filter(
                and_(
                    AlertsModel.timestamp >= time_range["start"],
                    AlertsModel.timestamp <= time_range["end"]
                )
            )
        
        high_alerts = alert_query.order_by(desc(AlertsModel.timestamp)).limit(5).all()
        
        # Recent error logs
        log_query = db_session.query(ContainerLogsModel).filter(
            ContainerLogsModel.message.ilike('%error%')
        )
        if time_range:
            log_query = log_query.filter(
                and_(
                    ContainerLogsModel.timestamp >= time_range["start"],
                    ContainerLogsModel.timestamp <= time_range["end"]
                )
            )
        
        error_logs = log_query.order_by(desc(ContainerLogsModel.timestamp)).limit(10).all()
        
        return {
            "high_severity_alerts": [self._serialize_result(alert) for alert in high_alerts],
            "recent_errors": [self._serialize_result(log) for log in error_logs],
            "security_score": self._calculate_security_score(db_session, time_range),
            "recommendations": [
                "Monitor high severity alerts closely",
                "Investigate recurring error patterns",
                "Review access logs for suspicious activity"
            ]
        }
    
    def _calculate_security_score(self, db_session: Session, time_range: Optional[Dict[str, datetime]]) -> int:
        """Calculate a simple security score (0-100)."""
        score = 100
        
        # Check alerts
        alert_query = db_session.query(AlertsModel)
        if time_range:
            alert_query = alert_query.filter(
                and_(
                    AlertsModel.timestamp >= time_range["start"],
                    AlertsModel.timestamp <= time_range["end"]
                )
            )
        
        high_alerts = alert_query.filter(AlertsModel.severity == "HIGH").count()
        medium_alerts = alert_query.filter(AlertsModel.severity == "MEDIUM").count()
        
        # Deduct points for alerts
        score -= high_alerts * 10
        score -= medium_alerts * 5
        
        # Check error rate
        if time_range:
            log_query = db_session.query(ContainerLogsModel).filter(
                and_(
                    ContainerLogsModel.timestamp >= time_range["start"],
                    ContainerLogsModel.timestamp <= time_range["end"]
                )
            )
            total_logs = log_query.count()
            error_logs = log_query.filter(ContainerLogsModel.message.ilike('%error%')).count()
            
            if total_logs > 0:
                error_rate = error_logs / total_logs
                score -= int(error_rate * 20)  # Deduct up to 20 points for high error rate
        
        return max(0, min(100, score))
    
    def _analyze_alert_trends(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Analyze alert trends over time."""
        # This is a simplified implementation
        # In a real system, you'd want to group by time periods and show trends
        
        query = db_session.query(AlertsModel).filter(
            and_(
                AlertsModel.timestamp >= time_range["start"],
                AlertsModel.timestamp <= time_range["end"]
            )
        )
        
        total_alerts = query.count()
        daily_average = total_alerts / max(1, (time_range["end"] - time_range["start"]).days)
        
        return {
            "total_alerts": total_alerts,
            "daily_average": round(daily_average, 2),
            "trend": "stable"  # Would calculate actual trend in real implementation
        }
    
    def _analyze_docker_trends(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Analyze Docker activity trends."""
        query = db_session.query(DockerEventsModel).filter(
            and_(
                DockerEventsModel.timestamp >= time_range["start"],
                DockerEventsModel.timestamp <= time_range["end"]
            )
        )
        
        total_events = query.count()
        daily_average = total_events / max(1, (time_range["end"] - time_range["start"]).days)
        
        return {
            "total_events": total_events,
            "daily_average": round(daily_average, 2),
            "trend": "stable"
        }
    
    def _analyze_log_trends(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Analyze log volume trends."""
        query = db_session.query(ContainerLogsModel).filter(
            and_(
                ContainerLogsModel.timestamp >= time_range["start"],
                ContainerLogsModel.timestamp <= time_range["end"]
            )
        )
        
        total_logs = query.count()
        daily_average = total_logs / max(1, (time_range["end"] - time_range["start"]).days)
        
        return {
            "total_logs": total_logs,
            "daily_average": round(daily_average, 2),
            "trend": "stable"
        }
    
    def _analyze_metrics_trends(self, db_session: Session, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Analyze system metrics trends."""
        query = db_session.query(MetricsModel).filter(
            and_(
                MetricsModel.timestamp >= time_range["start"],
                MetricsModel.timestamp <= time_range["end"]
            )
        )
        
        if query.count() == 0:
            return {"message": "No metrics data available"}
        
        avg_cpu = query.with_entities(func.avg(MetricsModel.cpu_usage)).scalar() or 0
        avg_memory = query.with_entities(func.avg(MetricsModel.memory_usage)).scalar() or 0
        
        return {
            "average_cpu": round(float(avg_cpu), 2),
            "average_memory": round(float(avg_memory), 2),
            "trend": "stable"
        }
    
    def _get_query_suggestions(self) -> List[str]:
        """Get query suggestions for unsupported intents."""
        return [
            "Try: 'Show me all failed logins in the last hour'",
            "Try: 'Generate weekly security summary'",
            "Try: 'What assets did IP address X.X.X.X target?'",
            "Try: 'Show critical alerts from today'",
            "Try: 'Analyze trends this month'"
        ]


# Global translator instance
_query_translator = None

def get_query_translator() -> QueryTranslator:
    """Get the global query translator instance."""
    global _query_translator
    if _query_translator is None:
        _query_translator = QueryTranslator()
    return _query_translator