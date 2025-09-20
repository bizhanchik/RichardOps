"""
Log Indexing Service

This module provides functionality to index logs and alerts into OpenSearch
for efficient searching, filtering, and aggregation.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from opensearchpy.exceptions import RequestError, ConnectionError

from .opensearch_client import get_opensearch_client
from .log_classifier import classify_log_message, classify_log_messages

logger = logging.getLogger(__name__)


class LogIndexer:
    """Service for indexing logs and alerts into OpenSearch"""
    
    def __init__(self):
        self.client = get_opensearch_client()
        self._fallback_mode = False
    
    def _check_connection(self) -> bool:
        """Check if OpenSearch is available"""
        if not self.client.is_connected():
            if not self._fallback_mode:
                logger.warning("OpenSearch not available, switching to fallback mode")
                self._fallback_mode = True
            return False
        
        if self._fallback_mode:
            logger.info("OpenSearch connection restored")
            self._fallback_mode = False
        return True
    
    def index_log_entry(self, log_data: Dict[str, Any]) -> bool:
        """
        Index a single log entry into OpenSearch
        
        Args:
            log_data: Dictionary containing log information
            
        Returns:
            bool: True if indexed successfully, False otherwise
        """
        if not self._check_connection():
            return False
        
        try:
            # Prepare document for indexing
            doc = {
                "timestamp": log_data.get("timestamp", datetime.now().isoformat()),
                "host": log_data.get("host"),
                "server_id": log_data.get("server_id"),
                "environment": log_data.get("environment"),
                "owner_team": log_data.get("owner_team"),
                "container": log_data.get("container"),
                "message": log_data.get("message"),
                "log_level": self._extract_log_level(log_data.get("message", "")),
                "event_type": log_data.get("event_type", "log_entry"),
                "score": log_data.get("score"),
                "metrics": log_data.get("metrics"),
                "indexed_at": datetime.now().isoformat()
            }
            
            # Remove None values
            doc = {k: v for k, v in doc.items() if v is not None}
            
            # Index the document
            response = self.client.client.index(
                index=self.client.config.logs_index,
                body=doc,
                refresh=True
            )
            
            if response.get("result") in ["created", "updated"]:
                logger.debug(f"Successfully indexed log entry: {response.get('_id')}")
                return True
            else:
                logger.warning(f"Unexpected response indexing log: {response}")
                return False
                
        except RequestError as e:
            logger.error(f"Request error indexing log entry: {e}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error indexing log entry: {e}")
            self._fallback_mode = True
            return False
        except Exception as e:
            logger.error(f"Unexpected error indexing log entry: {e}")
            return False
    
    def index_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Index an alert into OpenSearch
        
        Args:
            alert_data: Dictionary containing alert information
            
        Returns:
            bool: True if indexed successfully, False otherwise
        """
        if not self._check_connection():
            return False
        
        try:
            # Prepare alert document
            doc = {
                "timestamp": alert_data.get("timestamp", datetime.now().isoformat()),
                "alert_id": alert_data.get("id"),
                "severity": alert_data.get("severity"),
                "alert_type": alert_data.get("type"),
                "attack_type": alert_data.get("attack_type"),
                "confidence": alert_data.get("confidence"),
                "message": alert_data.get("message"),
                "evidence": alert_data.get("evidence"),
                "recommended_action": alert_data.get("recommended_action"),
                "container": alert_data.get("source", {}).get("container"),
                "host": alert_data.get("source", {}).get("host"),
                "environment": alert_data.get("source", {}).get("environment"),
                "processed_at": alert_data.get("processed_at", datetime.now().isoformat()),
                "indexed_at": datetime.now().isoformat()
            }
            
            # Remove None values
            doc = {k: v for k, v in doc.items() if v is not None}
            
            # Index the alert
            response = self.client.client.index(
                index=self.client.config.alerts_index,
                body=doc,
                refresh=True
            )
            
            if response.get("result") in ["created", "updated"]:
                logger.debug(f"Successfully indexed alert: {response.get('_id')}")
                return True
            else:
                logger.warning(f"Unexpected response indexing alert: {response}")
                return False
                
        except RequestError as e:
            logger.error(f"Request error indexing alert: {e}")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error indexing alert: {e}")
            self._fallback_mode = True
            return False
        except Exception as e:
            logger.error(f"Unexpected error indexing alert: {e}")
            return False
    
    def bulk_index_logs(self, logs: List[Dict[str, Any]]) -> int:
        """
        Bulk index multiple log entries with batch ML classification
        
        Args:
            logs: List of log dictionaries
            
        Returns:
            int: Number of successfully indexed logs
        """
        if not self._check_connection() or not logs:
            return 0
        
        try:
            # Extract all messages for batch classification
            messages = [log_data.get("message", "") for log_data in logs]
            
            # Perform batch ML classification for better performance
            try:
                classifications = classify_log_messages(messages)
            except Exception as e:
                logger.debug(f"Batch ML classification failed, using individual classification: {e}")
                # Fallback to individual classification
                classifications = [(self._extract_log_level(msg), 0.8) for msg in messages]
            
            # Prepare bulk request
            bulk_body = []
            for i, log_data in enumerate(logs):
                # Index action
                bulk_body.append({
                    "index": {
                        "_index": self.client.config.logs_index
                    }
                })
                
                # Get classification result
                log_level, confidence = classifications[i] if i < len(classifications) else ("INFO", 0.5)
                
                # Document
                doc = {
                    "timestamp": log_data.get("timestamp", datetime.now().isoformat()),
                    "host": log_data.get("host"),
                    "server_id": log_data.get("server_id"),
                    "environment": log_data.get("environment"),
                    "owner_team": log_data.get("owner_team"),
                    "container": log_data.get("container"),
                    "message": log_data.get("message"),
                    "log_level": log_level,
                    "classification_confidence": confidence,  # Add confidence score
                    "event_type": log_data.get("event_type", "log_entry"),
                    "score": log_data.get("score"),
                    "metrics": log_data.get("metrics"),
                    "indexed_at": datetime.now().isoformat()
                }
                
                # Remove None values
                doc = {k: v for k, v in doc.items() if v is not None}
                bulk_body.append(doc)
            
            # Execute bulk request
            response = self.client.client.bulk(
                body=bulk_body,
                refresh=True
            )
            
            # Count successful operations
            successful = 0
            if response.get("items"):
                for item in response["items"]:
                    if "index" in item and item["index"].get("status") in [200, 201]:
                        successful += 1
                    elif "index" in item:
                        logger.warning(f"Failed to index item: {item['index']}")
            
            logger.info(f"Bulk indexed {successful}/{len(logs)} log entries")
            return successful
            
        except RequestError as e:
            logger.error(f"Request error in bulk indexing: {e}")
            return 0
        except ConnectionError as e:
            logger.error(f"Connection error in bulk indexing: {e}")
            self._fallback_mode = True
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in bulk indexing: {e}")
            return 0
    
    def bulk_index_alerts(self, alerts: List[Dict[str, Any]]) -> int:
        """
        Bulk index multiple alerts
        
        Args:
            alerts: List of alert dictionaries
            
        Returns:
            int: Number of successfully indexed alerts
        """
        if not self._check_connection() or not alerts:
            return 0
        
        try:
            # Prepare bulk request
            bulk_body = []
            for alert_data in alerts:
                # Index action
                bulk_body.append({
                    "index": {
                        "_index": self.client.config.alerts_index
                    }
                })
                
                # Document
                doc = {
                    "timestamp": alert_data.get("timestamp", datetime.now().isoformat()),
                    "alert_id": alert_data.get("id"),
                    "severity": alert_data.get("severity"),
                    "alert_type": alert_data.get("type"),
                    "attack_type": alert_data.get("attack_type"),
                    "confidence": alert_data.get("confidence"),
                    "message": alert_data.get("message"),
                    "evidence": alert_data.get("evidence"),
                    "recommended_action": alert_data.get("recommended_action"),
                    "container": alert_data.get("source", {}).get("container"),
                    "host": alert_data.get("source", {}).get("host"),
                    "environment": alert_data.get("source", {}).get("environment"),
                    "processed_at": alert_data.get("processed_at", datetime.now().isoformat()),
                    "indexed_at": datetime.now().isoformat()
                }
                
                # Remove None values
                doc = {k: v for k, v in doc.items() if v is not None}
                bulk_body.append(doc)
            
            # Execute bulk request
            response = self.client.client.bulk(
                body=bulk_body,
                refresh=True
            )
            
            # Count successful operations
            successful = 0
            if response.get("items"):
                for item in response["items"]:
                    if "index" in item and item["index"].get("status") in [200, 201]:
                        successful += 1
                    elif "index" in item:
                        logger.warning(f"Failed to index alert: {item['index']}")
            
            logger.info(f"Bulk indexed {successful}/{len(alerts)} alerts")
            return successful
            
        except RequestError as e:
            logger.error(f"Request error in bulk alert indexing: {e}")
            return 0
        except ConnectionError as e:
            logger.error(f"Connection error in bulk alert indexing: {e}")
            self._fallback_mode = True
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in bulk alert indexing: {e}")
            return 0
    
    def _extract_log_level(self, message: str) -> Optional[str]:
        """
        Extract log level from message text using ML classification
        
        Args:
            message: Log message text
            
        Returns:
            str: Detected log level or None
        """
        if not message:
            return None
        
        try:
            # Use ML classifier for fast and accurate classification
            log_level, confidence = classify_log_message(message)
            
            # Only return result if confidence is reasonable
            if confidence > 0.3:
                return log_level
            else:
                return "INFO"  # Default fallback
                
        except Exception as e:
            logger.debug(f"ML classification failed for message, using fallback: {e}")
            # Fallback to simple rule-based approach
            message_upper = message.upper()
            
            if "ERROR" in message_upper or "FATAL" in message_upper:
                return "ERROR"
            elif "WARN" in message_upper:
                return "WARN"
            elif "DEBUG" in message_upper or "TRACE" in message_upper:
                return "DEBUG"
            else:
                return "INFO"
    
    def is_available(self) -> bool:
        """Check if the indexing service is available"""
        return self._check_connection()


# Global log indexer instance
_log_indexer: Optional[LogIndexer] = None


def get_log_indexer() -> LogIndexer:
    """Get the global log indexer instance"""
    global _log_indexer
    if _log_indexer is None:
        _log_indexer = LogIndexer()
    return _log_indexer