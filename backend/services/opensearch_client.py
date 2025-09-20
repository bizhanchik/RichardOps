"""
OpenSearch Client Service

This module provides OpenSearch connection management and configuration
for log indexing, searching, and aggregation operations.
"""

import os
import logging
from typing import Optional, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import ConnectionError, RequestError

logger = logging.getLogger(__name__)


class OpenSearchConfig:
    """OpenSearch configuration settings"""
    
    def __init__(self):
        self.host = os.getenv("OPENSEARCH_HOST", "localhost")
        self.port = int(os.getenv("OPENSEARCH_PORT", "9200"))
        self.username = os.getenv("OPENSEARCH_USERNAME", "admin")
        self.password = os.getenv("OPENSEARCH_PASSWORD", "admin")
        self.use_ssl = os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true"
        self.verify_certs = os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() == "true"
        self.ca_certs_path = os.getenv("OPENSEARCH_CA_CERTS")
        
        # Index settings
        self.logs_index = os.getenv("OPENSEARCH_LOGS_INDEX", "monitoring-logs")
        self.alerts_index = os.getenv("OPENSEARCH_ALERTS_INDEX", "monitoring-alerts")
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get OpenSearch connection parameters"""
        params = {
            "hosts": [{"host": self.host, "port": self.port}],
            "http_auth": (self.username, self.password),
            "use_ssl": self.use_ssl,
            "verify_certs": self.verify_certs,
            "connection_class": RequestsHttpConnection,
            "timeout": 30,
            "max_retries": 3,
            "retry_on_timeout": True
        }
        
        if self.ca_certs_path:
            params["ca_certs"] = self.ca_certs_path
            
        return params


class OpenSearchClient:
    """OpenSearch client wrapper with connection management"""
    
    def __init__(self, config: Optional[OpenSearchConfig] = None):
        self.config = config or OpenSearchConfig()
        self._client: Optional[OpenSearch] = None
        self._connected = False
        
    @property
    def client(self) -> OpenSearch:
        """Get OpenSearch client instance, creating connection if needed"""
        if self._client is None:
            self.connect()
        return self._client
    
    def connect(self) -> bool:
        """Establish connection to OpenSearch"""
        try:
            connection_params = self.config.get_connection_params()
            self._client = OpenSearch(**connection_params)
            
            # Test connection
            info = self._client.info()
            logger.info(f"Connected to OpenSearch: {info.get('version', {}).get('number', 'unknown')}")
            self._connected = True
            return True
            
        except ConnectionError as e:
            logger.error(f"Failed to connect to OpenSearch: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to OpenSearch: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to OpenSearch"""
        if not self._connected or self._client is None:
            return False
            
        try:
            self._client.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    def disconnect(self):
        """Close OpenSearch connection"""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"Error closing OpenSearch connection: {e}")
            finally:
                self._client = None
                self._connected = False
    
    def create_index(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """Create an index with the specified mapping"""
        try:
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} already exists")
                return True
                
            response = self.client.indices.create(
                index=index_name,
                body=mapping
            )
            
            if response.get("acknowledged"):
                logger.info(f"Successfully created index: {index_name}")
                return True
            else:
                logger.error(f"Failed to create index {index_name}: {response}")
                return False
                
        except RequestError as e:
            logger.error(f"Request error creating index {index_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating index {index_name}: {e}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        try:
            if not self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist")
                return True
                
            response = self.client.indices.delete(index=index_name)
            
            if response.get("acknowledged"):
                logger.info(f"Successfully deleted index: {index_name}")
                return True
            else:
                logger.error(f"Failed to delete index {index_name}: {response}")
                return False
                
        except RequestError as e:
            logger.error(f"Request error deleting index {index_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting index {index_name}: {e}")
            return False


# Global OpenSearch client instance
_opensearch_client: Optional[OpenSearchClient] = None


def get_opensearch_client() -> OpenSearchClient:
    """Get the global OpenSearch client instance"""
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = OpenSearchClient()
    return _opensearch_client


def initialize_opensearch() -> bool:
    """Initialize OpenSearch connection and create required indices"""
    client = get_opensearch_client()
    
    if not client.connect():
        logger.warning("OpenSearch connection failed - running in fallback mode")
        return False
    
    # Create logs index
    logs_mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "host": {"type": "keyword"},
                "server_id": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "owner_team": {"type": "keyword"},
                "container": {"type": "keyword"},
                "message": {"type": "text", "analyzer": "standard"},
                "log_level": {"type": "keyword"},
                "event_type": {"type": "keyword"},
                "score": {"type": "float"},
                "metrics": {
                    "properties": {
                        "cpu_usage": {"type": "float"},
                        "memory_usage": {"type": "float"},
                        "disk_usage": {"type": "float"},
                        "network_rx": {"type": "long"},
                        "network_tx": {"type": "long"},
                        "tcp_connections": {"type": "integer"}
                    }
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "5s"
        }
    }
    
    # Create alerts index
    alerts_mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "alert_id": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "alert_type": {"type": "keyword"},
                "attack_type": {"type": "keyword"},
                "confidence": {"type": "float"},
                "message": {"type": "text", "analyzer": "standard"},
                "evidence": {"type": "text"},
                "recommended_action": {"type": "text"},
                "container": {"type": "keyword"},
                "host": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "processed_at": {"type": "date"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "1s"
        }
    }
    
    # Create indices
    logs_created = client.create_index(client.config.logs_index, logs_mapping)
    alerts_created = client.create_index(client.config.alerts_index, alerts_mapping)
    
    if logs_created and alerts_created:
        logger.info("OpenSearch indices initialized successfully")
        return True
    else:
        logger.error("Failed to initialize some OpenSearch indices")
        return False


def cleanup_opensearch():
    """Cleanup OpenSearch connection"""
    global _opensearch_client
    if _opensearch_client:
        _opensearch_client.disconnect()
        _opensearch_client = None