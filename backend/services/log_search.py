"""
Log Search and Filtering Service

This module provides comprehensive search, filtering, and aggregation
capabilities for logs and alerts stored in OpenSearch.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from opensearchpy.exceptions import RequestError, ConnectionError

from .opensearch_client import get_opensearch_client

logger = logging.getLogger(__name__)


class LogSearchService:
    """Service for searching and filtering logs in OpenSearch"""
    
    def __init__(self):
        self.client = get_opensearch_client()
        self._fallback_mode = False
    
    def _check_connection(self) -> bool:
        """Check if OpenSearch is available"""
        if not self.client.is_connected():
            if not self._fallback_mode:
                logger.warning("OpenSearch not available for search operations")
                self._fallback_mode = True
            return False
        
        if self._fallback_mode:
            logger.info("OpenSearch connection restored for search")
            self._fallback_mode = False
        return True
    
    def search_logs(
        self,
        query: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        containers: Optional[List[str]] = None,
        hosts: Optional[List[str]] = None,
        environments: Optional[List[str]] = None,
        log_levels: Optional[List[str]] = None,
        size: int = 100,
        from_: int = 0,
        sort_field: str = "timestamp",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Search logs with comprehensive filtering options
        
        Args:
            query: Full-text search query
            start_time: Start time for time range filter
            end_time: End time for time range filter
            containers: List of container names to filter by
            hosts: List of host names to filter by
            environments: List of environments to filter by
            log_levels: List of log levels to filter by
            size: Number of results to return
            from_: Starting offset for pagination
            sort_field: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Dict containing search results and metadata
        """
        if not self._check_connection():
            return self._fallback_empty_result()
        
        try:
            # Build the search query
            search_body = self._build_search_query(
                query=query,
                start_time=start_time,
                end_time=end_time,
                containers=containers,
                hosts=hosts,
                environments=environments,
                log_levels=log_levels,
                size=size,
                from_=from_,
                sort_field=sort_field,
                sort_order=sort_order
            )
            
            # Execute search
            response = self.client.client.search(
                index=self.client.config.logs_index,
                body=search_body
            )
            
            # Process results
            return self._process_search_response(response)
            
        except RequestError as e:
            logger.error(f"Request error in log search: {e}")
            return self._fallback_empty_result()
        except ConnectionError as e:
            logger.error(f"Connection error in log search: {e}")
            self._fallback_mode = True
            return self._fallback_empty_result()
        except Exception as e:
            logger.error(f"Unexpected error in log search: {e}")
            return self._fallback_empty_result()
    
    def search_alerts(
        self,
        query: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severities: Optional[List[str]] = None,
        alert_types: Optional[List[str]] = None,
        containers: Optional[List[str]] = None,
        hosts: Optional[List[str]] = None,
        size: int = 100,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        Search alerts with filtering options
        
        Args:
            query: Full-text search query
            start_time: Start time for time range filter
            end_time: End time for time range filter
            severities: List of severity levels to filter by
            alert_types: List of alert types to filter by
            containers: List of container names to filter by
            hosts: List of host names to filter by
            size: Number of results to return
            from_: Starting offset for pagination
            
        Returns:
            Dict containing search results and metadata
        """
        if not self._check_connection():
            return self._fallback_empty_result()
        
        try:
            # Build the search query for alerts
            search_body = self._build_alert_search_query(
                query=query,
                start_time=start_time,
                end_time=end_time,
                severities=severities,
                alert_types=alert_types,
                containers=containers,
                hosts=hosts,
                size=size,
                from_=from_
            )
            
            # Execute search
            response = self.client.client.search(
                index=self.client.config.alerts_index,
                body=search_body
            )
            
            # Process results
            return self._process_search_response(response)
            
        except RequestError as e:
            logger.error(f"Request error in alert search: {e}")
            return self._fallback_empty_result()
        except ConnectionError as e:
            logger.error(f"Connection error in alert search: {e}")
            self._fallback_mode = True
            return self._fallback_empty_result()
        except Exception as e:
            logger.error(f"Unexpected error in alert search: {e}")
            return self._fallback_empty_result()
    
    def get_log_aggregations(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: str = "1h"
    ) -> Dict[str, Any]:
        """
        Get log aggregations for analytics and dashboards
        
        Args:
            start_time: Start time for aggregation
            end_time: End time for aggregation
            interval: Time interval for histogram aggregation
            
        Returns:
            Dict containing aggregation results
        """
        if not self._check_connection():
            return {"aggregations": {}}
        
        try:
            # Build aggregation query
            agg_body = {
                "size": 0,  # We only want aggregations, not documents
                "query": self._build_time_range_query(start_time, end_time),
                "aggs": {
                    "logs_over_time": {
                        "date_histogram": {
                            "field": "timestamp",
                            "fixed_interval": interval,
                            "min_doc_count": 0
                        }
                    },
                    "log_levels": {
                        "terms": {
                            "field": "log_level",
                            "size": 10
                        }
                    },
                    "containers": {
                        "terms": {
                            "field": "container",
                            "size": 20
                        }
                    },
                    "hosts": {
                        "terms": {
                            "field": "host",
                            "size": 20
                        }
                    },
                    "environments": {
                        "terms": {
                            "field": "environment",
                            "size": 10
                        }
                    }
                }
            }
            
            # Execute aggregation
            response = self.client.client.search(
                index=self.client.config.logs_index,
                body=agg_body
            )
            
            return {
                "total_logs": response["hits"]["total"]["value"],
                "aggregations": response.get("aggregations", {})
            }
            
        except Exception as e:
            logger.error(f"Error in log aggregations: {e}")
            return {"aggregations": {}}
    
    def get_alert_aggregations(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: str = "1h"
    ) -> Dict[str, Any]:
        """
        Get alert aggregations for analytics and dashboards
        
        Args:
            start_time: Start time for aggregation
            end_time: End time for aggregation
            interval: Time interval for histogram aggregation
            
        Returns:
            Dict containing aggregation results
        """
        if not self._check_connection():
            return {"aggregations": {}}
        
        try:
            # Build aggregation query
            agg_body = {
                "size": 0,
                "query": self._build_time_range_query(start_time, end_time),
                "aggs": {
                    "alerts_over_time": {
                        "date_histogram": {
                            "field": "timestamp",
                            "fixed_interval": interval,
                            "min_doc_count": 0
                        }
                    },
                    "severities": {
                        "terms": {
                            "field": "severity",
                            "size": 10
                        }
                    },
                    "alert_types": {
                        "terms": {
                            "field": "alert_type",
                            "size": 20
                        }
                    },
                    "attack_types": {
                        "terms": {
                            "field": "attack_type",
                            "size": 20
                        }
                    },
                    "containers": {
                        "terms": {
                            "field": "container",
                            "size": 20
                        }
                    }
                }
            }
            
            # Execute aggregation
            response = self.client.client.search(
                index=self.client.config.alerts_index,
                body=agg_body
            )
            
            return {
                "total_alerts": response["hits"]["total"]["value"],
                "aggregations": response.get("aggregations", {})
            }
            
        except Exception as e:
            logger.error(f"Error in alert aggregations: {e}")
            return {"aggregations": {}}
    
    def _build_search_query(
        self,
        query: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        containers: Optional[List[str]] = None,
        hosts: Optional[List[str]] = None,
        environments: Optional[List[str]] = None,
        log_levels: Optional[List[str]] = None,
        size: int = 100,
        from_: int = 0,
        sort_field: str = "timestamp",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Build OpenSearch query for log search"""
        
        # Start with match_all query
        bool_query = {"bool": {"must": []}}
        
        # Add full-text search if provided
        if query:
            bool_query["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["message^2", "container", "host"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Add time range filter
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            
            bool_query["bool"]["must"].append({
                "range": {"timestamp": time_range}
            })
        
        # Add filters
        filters = []
        
        if containers:
            filters.append({"terms": {"container": containers}})
        
        if hosts:
            filters.append({"terms": {"host": hosts}})
        
        if environments:
            filters.append({"terms": {"environment": environments}})
        
        if log_levels:
            filters.append({"terms": {"log_level": log_levels}})
        
        if filters:
            bool_query["bool"]["filter"] = filters
        
        # If no conditions, use match_all
        if not bool_query["bool"]["must"] and not bool_query["bool"].get("filter"):
            search_query = {"match_all": {}}
        else:
            search_query = bool_query
        
        return {
            "query": search_query,
            "size": size,
            "from": from_,
            "sort": [{sort_field: {"order": sort_order}}],
            "_source": {
                "excludes": ["indexed_at"]  # Exclude internal fields
            }
        }
    
    def _build_alert_search_query(
        self,
        query: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severities: Optional[List[str]] = None,
        alert_types: Optional[List[str]] = None,
        containers: Optional[List[str]] = None,
        hosts: Optional[List[str]] = None,
        size: int = 100,
        from_: int = 0
    ) -> Dict[str, Any]:
        """Build OpenSearch query for alert search"""
        
        bool_query = {"bool": {"must": []}}
        
        # Add full-text search if provided
        if query:
            bool_query["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["message^2", "evidence", "recommended_action"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Add time range filter
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            
            bool_query["bool"]["must"].append({
                "range": {"timestamp": time_range}
            })
        
        # Add filters
        filters = []
        
        if severities:
            filters.append({"terms": {"severity": severities}})
        
        if alert_types:
            filters.append({"terms": {"alert_type": alert_types}})
        
        if containers:
            filters.append({"terms": {"container": containers}})
        
        if hosts:
            filters.append({"terms": {"host": hosts}})
        
        if filters:
            bool_query["bool"]["filter"] = filters
        
        # If no conditions, use match_all
        if not bool_query["bool"]["must"] and not bool_query["bool"].get("filter"):
            search_query = {"match_all": {}}
        else:
            search_query = bool_query
        
        return {
            "query": search_query,
            "size": size,
            "from": from_,
            "sort": [{"timestamp": {"order": "desc"}}],
            "_source": {
                "excludes": ["indexed_at"]
            }
        }
    
    def _build_time_range_query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Build time range query"""
        if not start_time and not end_time:
            return {"match_all": {}}
        
        time_range = {}
        if start_time:
            time_range["gte"] = start_time.isoformat()
        if end_time:
            time_range["lte"] = end_time.isoformat()
        
        return {"range": {"timestamp": time_range}}
    
    def _process_search_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process OpenSearch response into standardized format"""
        hits = response.get("hits", {})
        total = hits.get("total", {})
        
        # Extract documents
        documents = []
        for hit in hits.get("hits", []):
            doc = hit["_source"]
            doc["_id"] = hit["_id"]
            doc["_score"] = hit.get("_score")
            documents.append(doc)
        
        return {
            "total": total.get("value", 0),
            "total_relation": total.get("relation", "eq"),
            "max_score": hits.get("max_score"),
            "documents": documents,
            "took": response.get("took", 0)
        }
    
    def _fallback_empty_result(self) -> Dict[str, Any]:
        """Return empty result when OpenSearch is unavailable"""
        return {
            "total": 0,
            "total_relation": "eq",
            "max_score": None,
            "documents": [],
            "took": 0,
            "fallback": True
        }
    
    def is_available(self) -> bool:
        """Check if the search service is available"""
        return self._check_connection()
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status information about the search service"""
        is_connected = self._check_connection()
        return {
            "connected": is_connected,
            "fallback_mode": self._fallback_mode,
            "service": "opensearch" if is_connected else "fallback"
        }


class LogFilterHelpers:
    """Helper functions for common log filtering operations"""
    
    @staticmethod
    def get_time_range_last_hours(hours: int) -> Tuple[datetime, datetime]:
        """Get time range for the last N hours"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return start_time, end_time
    
    @staticmethod
    def get_time_range_last_days(days: int) -> Tuple[datetime, datetime]:
        """Get time range for the last N days"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        return start_time, end_time
    
    @staticmethod
    def get_time_range_today() -> Tuple[datetime, datetime]:
        """Get time range for today"""
        now = datetime.now()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now
        return start_time, end_time
    
    @staticmethod
    def parse_log_level_filter(level_input: str) -> List[str]:
        """Parse log level filter input"""
        if not level_input:
            return []
        
        levels = [level.strip().upper() for level in level_input.split(",")]
        valid_levels = ["ERROR", "WARN", "INFO", "DEBUG", "FATAL", "TRACE"]
        return [level for level in levels if level in valid_levels]
    
    @staticmethod
    def parse_severity_filter(severity_input: str) -> List[str]:
        """Parse severity filter input"""
        if not severity_input:
            return []
        
        severities = [sev.strip().upper() for sev in severity_input.split(",")]
        valid_severities = ["HIGH", "MEDIUM", "LOW", "CRITICAL"]
        return [sev for sev in severities if sev in valid_severities]


# Global search service instance
_search_service: Optional[LogSearchService] = None


def get_log_search_service() -> LogSearchService:
    """Get the global log search service instance"""
    global _search_service
    if _search_service is None:
        _search_service = LogSearchService()
    return _search_service