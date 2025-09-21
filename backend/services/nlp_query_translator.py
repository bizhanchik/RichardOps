"""
NLP Query Translator for converting parsed natural language queries into database queries.

This module translates structured NLP queries into SQL queries and other data source 
queries for security monitoring and log analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.orm import Session

from db_models import (
    ContainerLogsModel, DockerEventsModel, AlertsModel, 
    MetricsModel, EmailNotificationsModel
)
from services.nlp_query_parser import ParsedQuery, QueryIntent, EntityType
from services.summary_service import summary_service
from services.anomaly_detection import anomaly_detector


class QueryTranslator:
    """
    Translates parsed NLP queries into database queries for various data sources.
    
    Supports SQL queries for PostgreSQL and aggregation queries for reporting 
    and analytics.
    """
    
    def __init__(self):
        """Initialize the query translator with intent handlers."""
        self.model_mapping = {
            "logs": ContainerLogsModel,
            "container_logs": ContainerLogsModel,
            "docker_events": DockerEventsModel,
            "alerts": AlertsModel,
            "metrics": MetricsModel,
            "notifications": EmailNotificationsModel
        }
        
        # Map query intents to handler methods
        self.intent_handlers = {
            QueryIntent.SEARCH_LOGS: self._handle_search_logs,
            QueryIntent.SHOW_ALERTS: self._handle_show_alerts,
            QueryIntent.GENERATE_REPORT: self._handle_generate_report,
            QueryIntent.INVESTIGATE: self._handle_investigate,
            QueryIntent.ANALYZE_TRENDS: self._handle_analyze_trends,
            QueryIntent.ANALYTICS_SUMMARY: self._handle_analytics_summary,
            QueryIntent.ANALYTICS_ANOMALIES: self._handle_analytics_anomalies,
            QueryIntent.ANALYTICS_PERFORMANCE: self._handle_analytics_performance,
            QueryIntent.ANALYTICS_METRICS: self._handle_analytics_metrics
        }
    
    def fetch_all_logs(self, db_session: Session, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """
        Simple function to fetch all logs without any filtering.
        
        Args:
            db_session: Database session
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with logs data and metadata
        """
        try:
            # Get total count
            total_count = db_session.query(ContainerLogsModel).count()
            
            # Fetch logs with limit and offset
            logs = db_session.query(ContainerLogsModel)\
                .order_by(desc(ContainerLogsModel.timestamp))\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return {
                "success": True,
                "data": {
                    "logs": [self._serialize_result(log) for log in logs],
                    "count": len(logs),
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(logs) < total_count
                },
                "metadata": {
                    "query_type": "fetch_all_logs",
                    "processing_time_ms": 0,
                    "confidence": 1.0
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch logs: {str(e)}",
                "data": {"logs": [], "count": 0}
            }
    
    def fetch_logs_by_message_pattern(self, db_session: Session, pattern: str, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """
        Simple function to fetch logs by message pattern.
        
        Args:
            db_session: Database session
            pattern: Pattern to search for in log messages
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with logs data and metadata
        """
        try:
            # Get total count for this pattern
            total_count = db_session.query(ContainerLogsModel)\
                .filter(ContainerLogsModel.message.ilike(f"%{pattern}%"))\
                .count()
            
            # Fetch logs with pattern filter
            logs = db_session.query(ContainerLogsModel)\
                .filter(ContainerLogsModel.message.ilike(f"%{pattern}%"))\
                .order_by(desc(ContainerLogsModel.timestamp))\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return {
                "success": True,
                "data": {
                    "logs": [self._serialize_result(log) for log in logs],
                    "count": len(logs),
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "pattern_filter": pattern,
                    "has_more": offset + len(logs) < total_count
                },
                "metadata": {
                    "query_type": "fetch_logs_by_message_pattern",
                    "processing_time_ms": 0,
                    "confidence": 1.0
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch logs by pattern: {str(e)}",
                "data": {"logs": [], "count": 0}
            }
    
    def fetch_logs_by_container(self, db_session: Session, container: str, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """
        Simple function to fetch logs by container name.
        
        Args:
            db_session: Database session
            container: Container name or partial name
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with logs data and metadata
        """
        try:
            # Get total count for this container
            total_count = db_session.query(ContainerLogsModel)\
                .filter(ContainerLogsModel.container.ilike(f"%{container}%"))\
                .count()
            
            # Fetch logs with container filter
            logs = db_session.query(ContainerLogsModel)\
                .filter(ContainerLogsModel.container.ilike(f"%{container}%"))\
                .order_by(desc(ContainerLogsModel.timestamp))\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return {
                "success": True,
                "data": {
                    "logs": [self._serialize_result(log) for log in logs],
                    "count": len(logs),
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "container_filter": container,
                    "has_more": offset + len(logs) < total_count
                },
                "metadata": {
                    "query_type": "fetch_logs_by_container",
                    "processing_time_ms": 0,
                    "confidence": 1.0
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch logs by container: {str(e)}",
                "data": {"logs": [], "count": 0}
            }
    
    def fetch_latest_logs(self, db_session: Session, limit: int = 50) -> Dict[str, Any]:
        """
        Fetch the most recent logs ordered by timestamp.
        
        Args:
            db_session: SQLAlchemy database session
            limit: Maximum number of logs to return (default: 50)
            
        Returns:
            Dict containing success status, logs data, and metadata
        """
        try:
            # Query for the most recent logs ordered by timestamp descending
            query = db_session.query(ContainerLogsModel).order_by(desc(ContainerLogsModel.timestamp))
            
            # Get total count
            total_count = query.count()
            
            # Apply limit
            logs = query.limit(limit).all()
            
            # Serialize results
            serialized_logs = [self._serialize_result(log) for log in logs]
            
            return {
                "success": True,
                "data": {
                    "logs": serialized_logs,
                    "count": len(serialized_logs),
                    "total_count": total_count,
                    "limit": limit,
                    "offset": 0,
                    "has_more": len(serialized_logs) < total_count
                },
                "metadata": {
                    "query_type": "fetch_latest_logs",
                    "processing_time_ms": 0,
                    "confidence": 1.0
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch latest logs: {str(e)}",
                "data": {"logs": [], "count": 0, "total_count": 0}
            }
    
    def fetch_logs_last_hour(self, db_session: Session, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """
        Fetch all logs from the last hour.
        
        Args:
            db_session: SQLAlchemy database session
            limit: Maximum number of logs to return (default: 1000)
            offset: Number of logs to skip (default: 0)
            
        Returns:
            Dict containing success status, logs data, and metadata
        """
        try:
            # Calculate time one hour ago
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            # Query for logs from the last hour
            query = db_session.query(ContainerLogsModel).filter(
                ContainerLogsModel.timestamp >= one_hour_ago
            ).order_by(desc(ContainerLogsModel.timestamp))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            logs = query.offset(offset).limit(limit).all()
            
            # Serialize results
            serialized_logs = [self._serialize_result(log) for log in logs]
            
            return {
                "success": True,
                "data": {
                    "logs": serialized_logs,
                    "count": len(serialized_logs),
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "time_filter": {
                        "start_time": one_hour_ago.isoformat(),
                        "end_time": datetime.utcnow().isoformat(),
                        "duration": "1 hour"
                    },
                    "has_more": offset + len(serialized_logs) < total_count
                },
                "metadata": {
                    "query_type": "fetch_logs_last_hour",
                    "processing_time_ms": 0,
                    "confidence": 1.0
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch logs from last hour: {str(e)}",
                "data": {"logs": [], "count": 0, "total_count": 0}
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
        """Handle log search queries using PostgreSQL."""
        try:
            # Check for time-based queries first
            original_query = parsed_query.original_query.lower()
            
            # Check for latest logs patterns
            latest_patterns = [
                "latest logs", "recent logs", "newest logs", "most recent logs",
                "show latest logs", "get latest logs", "display latest logs",
                "show recent logs", "get recent logs", "display recent logs",
                "latest 50", "recent 50", "last 50"
            ]
            
            # Check for last hour patterns
            last_hour_patterns = [
                "last hour", "past hour", "previous hour", "logs from last hour",
                "logs from past hour", "logs from previous hour", "hour ago",
                "logs in the last hour", "logs in the past hour"
            ]
            
            # Check for container-specific patterns
            container_patterns = [
                "container logs", "logs from container", "logs for container",
                "show container", "get container", "display container",
                "container logs for", "logs from container", "container"
            ]
            
            # Handle time-based queries
            if any(pattern in original_query for pattern in latest_patterns):
                result = self.fetch_latest_logs(db_session, limit=50)
                if result.get("success", False):
                    return {
                        "intent": "search_logs",
                        "results": result["data"]["logs"],
                        "count": result["data"]["total_count"],
                        "data_source": "postgresql",
                        "query_info": {
                            "query_type": "latest_logs",
                            "limit": 50,
                            "confidence": 1.0,
                            "table_queried": "container_logs"
                        }
                    }
                else:
                    return {
                        "intent": "search_logs",
                        "error": f"Failed to fetch latest logs: {result.get('error', 'Unknown error')}",
                        "results": [],
                        "count": 0,
                        "fallback_attempted": True
                    }
            
            if any(pattern in original_query for pattern in last_hour_patterns):
                result = self.fetch_logs_last_hour(db_session, limit=1000)
                if result.get("success", False):
                    return {
                        "intent": "search_logs",
                        "results": result["data"]["logs"],
                        "count": result["data"]["total_count"],
                        "data_source": "postgresql",
                        "query_info": {
                            "query_type": "logs_last_hour",
                            "time_filter": result["data"]["time_filter"],
                            "confidence": 1.0,
                            "table_queried": "container_logs"
                        }
                    }
                else:
                    return {
                        "intent": "search_logs",
                        "error": f"Failed to fetch last hour logs: {result.get('error', 'Unknown error')}",
                        "results": [],
                        "count": 0,
                        "fallback_attempted": True
                    }
            
            # Handle container-specific queries with direct routing
            if any(pattern in original_query for pattern in container_patterns):
                # Extract container name from the query
                container_name = self._extract_container_name_from_query(original_query)
                if container_name:
                    result = self.fetch_logs_by_container(db_session, container_name, limit=100)
                    if result.get("success", False):
                        return {
                            "intent": "search_logs",
                            "results": result["data"]["logs"],
                            "count": result["data"]["total_count"],
                            "data_source": "postgresql",
                            "query_info": {
                                "query_type": "container_logs",
                                "container": container_name,
                                "confidence": 0.9,
                                "table_queried": "container_logs"
                            }
                        }
                    else:
                        return {
                            "intent": "search_logs",
                            "error": f"Failed to fetch container logs: {result.get('error', 'Unknown error')}",
                            "results": [],
                            "count": 0,
                            "fallback_attempted": True
                        }
            
            # Check if this is a simple "show all logs" type query
            show_all_patterns = [
                "show all logs", "display all logs", "get all logs", "list all logs",
                "show every log", "display every log", "get every log", "list every log",
                "show me all logs", "show me every log", "all logs", "every log"
            ]
            
            # Check for specific entity filters
            has_container_filter = any(entity.type == EntityType.CONTAINER_NAME for entity in parsed_query.entities)
            has_level_filter = any(entity.type == EntityType.LOG_LEVEL for entity in parsed_query.entities)
            
            # Use simple functions for common queries
            if any(pattern in original_query for pattern in show_all_patterns):
                if has_container_filter:
                    # Get container name from entities
                    container_entity = next((entity for entity in parsed_query.entities if entity.type == EntityType.CONTAINER_NAME), None)
                    if container_entity:
                        result = self.fetch_logs_by_container(db_session, container_entity.value, limit=100)
                        return {
                            "intent": "search_logs",
                            "results": result["data"]["logs"],
                            "count": result["data"]["total_count"],
                            "data_source": "postgresql",
                            "query_info": {
                                "query_type": "simple_container_filter",
                                "container": container_entity.value,
                                "confidence": 1.0,
                                "table_queried": "container_logs"
                            }
                        }
                elif has_level_filter:
                    # Get level from entities and search in message content
                    level_entity = next((entity for entity in parsed_query.entities if entity.type == EntityType.LOG_LEVEL), None)
                    if level_entity:
                        result = self.fetch_logs_by_message_pattern(db_session, level_entity.value, limit=100)
                        return {
                            "intent": "search_logs",
                            "results": result["data"]["logs"],
                            "count": result["data"]["total_count"],
                            "data_source": "postgresql",
                            "query_info": {
                                "query_type": "simple_message_pattern",
                                "pattern": level_entity.value,
                                "confidence": 1.0,
                                "table_queried": "container_logs"
                            }
                        }
                else:
                    # Simple fetch all logs
                    result = self.fetch_all_logs(db_session, limit=100)
                    return {
                        "intent": "search_logs",
                        "results": result["data"]["logs"],
                        "count": result["data"]["total_count"],
                        "data_source": "postgresql",
                        "query_info": {
                            "query_type": "simple_fetch_all",
                            "confidence": 1.0,
                            "table_queried": "container_logs"
                        }
                    }
            
            # Fall back to complex filtering for specific searches
            # Determine which table to query
            model = self._determine_log_table(parsed_query)
            
            # Build base query
            query = db_session.query(model)
            
            # Apply filters
            query = self._apply_filters(query, parsed_query, model)
            
            # Apply time range filter
            query = self._apply_time_filter(query, parsed_query, model)
            
            # Order by timestamp descending
            query = query.order_by(desc(model.timestamp))
            
            # Get total count
            total_count = query.count()
            
            # Limit results for display
            results = query.limit(100).all()
            
            # Serialize results
            serialized_results = [self._serialize_result(result) for result in results]
            
            return {
                "intent": "search_logs",
                "results": serialized_results,
                "count": total_count,
                "data_source": "postgresql",
                "query_info": {
                    "filters_applied": self._get_applied_filters(parsed_query),
                    "time_range": parsed_query.structured_params.get("time_range"),
                    "confidence": parsed_query.confidence,
                    "table_queried": model.__tablename__
                }
            }
            
        except Exception as e:
            return {
                "intent": "search_logs",
                "error": f"PostgreSQL query failed: {str(e)}",
                "results": [],
                "count": 0,
                "fallback_attempted": True
            }
    
    def _handle_show_alerts(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle alert queries using PostgreSQL."""
        try:
            # Build base query for alerts
            query = db_session.query(AlertsModel)
            
            # Apply severity filter
            severity_entities = [e for e in parsed_query.entities if e.type == EntityType.SEVERITY]
            if severity_entities:
                severities = [e.value.upper() for e in severity_entities]
                query = query.filter(AlertsModel.severity.in_(severities))
            
            # Apply filters
            query = self._apply_filters(query, parsed_query, AlertsModel)
            
            # Apply time range filter
            query = self._apply_time_filter(query, parsed_query, AlertsModel)
            
            # Order by timestamp descending
            query = query.order_by(desc(AlertsModel.timestamp))
            
            # Get total count
            total_count = query.count()
            
            # Limit results for display
            results = query.limit(50).all()
            
            # Serialize results
            serialized_results = [self._serialize_result(result) for result in results]
            
            return {
                "intent": "show_alerts",
                "results": serialized_results,
                "count": total_count,
                "data_source": "postgresql",
                "query_info": {
                    "filters_applied": self._get_applied_filters(parsed_query),
                    "time_range": parsed_query.structured_params.get("time_range"),
                    "confidence": parsed_query.confidence,
                    "table_queried": "alerts"
                }
            }
            
        except Exception as e:
            return {
                "intent": "show_alerts",
                "error": f"PostgreSQL query failed: {str(e)}",
                "results": [],
                "count": 0,
                "fallback_attempted": True
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
        
        # Add text search for specific queries only (not general "show all logs" type queries)
        search_terms = self._extract_search_terms(parsed_query.original_query)
        meaningful_search_terms = self._filter_meaningful_search_terms(search_terms, parsed_query.original_query)
        
        if meaningful_search_terms and hasattr(model, 'message'):
            search_conditions = []
            for term in meaningful_search_terms:
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
    
    def _filter_meaningful_search_terms(self, search_terms: List[str], original_query: str) -> List[str]:
        """Filter out generic log-related terms that shouldn't trigger text search."""
        # Generic terms that indicate "show all" rather than specific search
        generic_terms = {
            "logs", "log", "entries", "entry", "events", "event", "data", "records", 
            "record", "messages", "message", "items", "item", "everything", "every",
            "container", "containers", "docker", "system"
        }
        
        # If the query contains words like "all", "every", "everything" and only generic terms,
        # it's likely a "show all" query rather than a specific search
        query_lower = original_query.lower()
        has_show_all_intent = any(word in query_lower for word in ["all", "every", "everything"])
        
        # Filter out generic terms
        meaningful_terms = [term for term in search_terms if term not in generic_terms]
        
        # If we have show-all intent and only generic terms remain, return empty list
        if has_show_all_intent and not meaningful_terms:
            return []
        
        return meaningful_terms
    
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
    
    def _extract_container_name_from_query(self, query: str) -> Optional[str]:
        """
        Extract container name from natural language query.
        
        Args:
            query: The natural language query string
            
        Returns:
            Container name if found, None otherwise
        """
        import re
        
        # Common patterns for container names in queries
        patterns = [
            r'container\s+([a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9])',  # "container webapp"
            r'from\s+container\s+([a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9])',  # "from container webapp"
            r'for\s+container\s+([a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9])',  # "for container webapp"
            r'([a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9])\s+container',  # "webapp container"
            r'logs\s+([a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9])',  # "logs webapp"
            r'show\s+([a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9])',  # "show webapp"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                container_name = match.group(1)
                # Filter out common words that aren't container names
                if container_name.lower() not in ['logs', 'all', 'recent', 'latest', 'show', 'get', 'display', 'from', 'for', 'the', 'a', 'an']:
                    return container_name
        
        return None

    def _handle_analytics_summary(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle analytics summary requests."""
        try:
            # Extract time period from query
            time_period = "24h"  # default
            if parsed_query.time_range:
                if "week" in parsed_query.original_query.lower():
                    time_period = "7d"
                elif "month" in parsed_query.original_query.lower():
                    time_period = "30d"
                elif "hour" in parsed_query.original_query.lower():
                    time_period = "1h"
            
            # Get summary from analytics service
            summary = summary_service.get_system_summary(db_session, time_period)
            
            return {
                "success": True,
                "data": summary,
                "query_type": "analytics_summary",
                "message": f"System summary for the last {time_period}",
                "metadata": {
                    "time_period": time_period,
                    "query": parsed_query.original_query
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_type": "analytics_summary",
                "message": "Failed to generate analytics summary"
            }

    def _handle_analytics_anomalies(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle anomaly detection requests."""
        try:
            # Extract time period and severity from query
            time_period = "24h"  # default
            severity = None
            
            if parsed_query.time_range:
                if "week" in parsed_query.original_query.lower():
                    time_period = "7d"
                elif "month" in parsed_query.original_query.lower():
                    time_period = "30d"
                elif "hour" in parsed_query.original_query.lower():
                    time_period = "1h"
            
            # Extract severity from query
            query_lower = parsed_query.original_query.lower()
            if "critical" in query_lower:
                severity = "critical"
            elif "high" in query_lower:
                severity = "high"
            elif "medium" in query_lower:
                severity = "medium"
            elif "low" in query_lower:
                severity = "low"
            
            # Get anomalies from detection service
            anomalies = anomaly_detector.detect_anomalies(time_period, severity)
            
            return {
                "success": True,
                "data": anomalies,
                "query_type": "analytics_anomalies",
                "message": f"Anomalies detected in the last {time_period}",
                "metadata": {
                    "time_period": time_period,
                    "severity_filter": severity,
                    "query": parsed_query.original_query
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_type": "analytics_anomalies",
                "message": "Failed to detect anomalies"
            }

    def _handle_analytics_performance(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle performance analytics requests."""
        try:
            # Extract time period from query
            time_period = "24h"  # default
            if parsed_query.time_range:
                if "week" in parsed_query.original_query.lower():
                    time_period = "7d"
                elif "month" in parsed_query.original_query.lower():
                    time_period = "30d"
                elif "hour" in parsed_query.original_query.lower():
                    time_period = "1h"
            
            # Get performance report from analytics service
            performance = summary_service.get_performance_report(db_session, time_period)
            
            return {
                "success": True,
                "data": performance,
                "query_type": "analytics_performance",
                "message": f"Performance report for the last {time_period}",
                "metadata": {
                    "time_period": time_period,
                    "query": parsed_query.original_query
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_type": "analytics_performance",
                "message": "Failed to generate performance report"
            }

    def _handle_analytics_metrics(self, parsed_query: ParsedQuery, db_session: Session) -> Dict[str, Any]:
        """Handle metrics analytics requests."""
        try:
            # Extract time period from query
            time_period = "24h"  # default
            if parsed_query.time_range:
                if "week" in parsed_query.original_query.lower():
                    time_period = "7d"
                elif "month" in parsed_query.original_query.lower():
                    time_period = "30d"
                elif "hour" in parsed_query.original_query.lower():
                    time_period = "1h"
            
            # Get detailed metrics from analytics service
            metrics = summary_service.get_detailed_metrics(time_period)
            
            return {
                "success": True,
                "data": metrics,
                "query_type": "analytics_metrics",
                "message": f"Detailed metrics for the last {time_period}",
                "metadata": {
                    "time_period": time_period,
                    "query": parsed_query.original_query
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_type": "analytics_metrics",
                "message": "Failed to retrieve metrics"
            }

    def _get_query_suggestions(self) -> List[str]:
        """Get query suggestions for unsupported intents."""
        return [
            "Show me all failed logins in the last hour",
            "Generate weekly security summary", 
            "What assets did IP address 192.168.1.100 target?",
            "Show critical alerts from today",
            "Find all ERROR logs from container webapp",
            "Investigate suspicious activity in the last 24 hours",
            "Give me a system summary for the last 24 hours",
            "Show me performance metrics for this week",
            "Detect anomalies in the last hour",
            "What are the critical anomalies today?"
        ]


# Global translator instance
_query_translator = None

def get_query_translator() -> QueryTranslator:
    """Get the global query translator instance."""
    global _query_translator
    if _query_translator is None:
        _query_translator = QueryTranslator()
    return _query_translator