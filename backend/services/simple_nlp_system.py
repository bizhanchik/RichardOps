#!/usr/bin/env python3
"""
Simple NLP System using Direct Message Mapping

This replaces the complex intent classification system with a simple,
reliable direct mapping approach.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from services.direct_message_mapper import get_direct_mapper
from services.nlp_query_translator import get_query_translator
from database import get_sync_db_session


class SimpleNLPSystem:
    """Simple NLP system using direct message mapping."""
    
    def __init__(self):
        self.mapper = get_direct_mapper()
        self.translator = get_query_translator()
        self.response_cache = {}
    
    def process_query(self, query: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Process a natural language query using direct mapping.
        
        Args:
            query: Natural language query string
            use_cache: Whether to use response caching
            
        Returns:
            Dictionary containing results, metadata, and status
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if use_cache and query in self.response_cache:
                cached_result = self.response_cache[query].copy()
                cached_result["from_cache"] = True
                cached_result["processing_time_ms"] = (time.time() - start_time) * 1000
                return cached_result
            
            # Use direct mapping to find function
            mapping_result = self.mapper.map_message_to_function(query)
            
            if not mapping_result:
                return {
                    "status": "error",
                    "error": "Could not understand the query. Please try rephrasing.",
                    "query": query,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "suggestions": self._get_query_suggestions()
                }
            
            function_name, parameters = mapping_result
            
            # Get database session
            try:
                db_session = get_sync_db_session()
            except Exception as e:
                return {
                    "status": "error", 
                    "error": f"Database connection failed: {str(e)}",
                    "query": query,
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
            
            # Execute the mapped function
            result = self._execute_function(function_name, parameters, db_session)
            
            # Add metadata
            result.update({
                "query": query,
                "function_used": function_name,
                "parameters": parameters,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "from_cache": False
            })
            
            # Cache successful results
            if use_cache and result.get("status") != "error":
                self.response_cache[query] = result.copy()
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Processing failed: {str(e)}",
                "query": query,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
    
    def _execute_function(self, function_name: str, parameters: Dict[str, Any], db_session) -> Dict[str, Any]:
        """Execute the mapped function with parameters."""
        
        try:
            # Get the function from translator
            if hasattr(self.translator, function_name):
                func = getattr(self.translator, function_name)
                
                # Handle different function signatures
                if function_name.startswith('fetch_'):
                    # Direct fetch functions
                    if function_name == "fetch_latest_logs":
                        limit = parameters.get("limit", 50)
                        return func(db_session, limit=limit)
                    
                    elif function_name == "fetch_all_logs":
                        limit = parameters.get("limit", 1000)
                        offset = parameters.get("offset", 0)
                        return func(db_session, limit=limit, offset=offset)
                    
                    elif function_name == "fetch_logs_by_message_pattern":
                        pattern = parameters.get("pattern", "error")
                        limit = parameters.get("limit", 1000)
                        return func(db_session, pattern, limit=limit)
                    
                    elif function_name == "fetch_logs_by_container":
                        container = parameters.get("container", "")
                        limit = parameters.get("limit", 1000)
                        return func(db_session, container, limit=limit)
                    
                    elif function_name == "fetch_logs_last_hour":
                        limit = parameters.get("limit", 1000)
                        return func(db_session, limit=limit)
                    
                    else:
                        # Generic fetch function call
                        return func(db_session)
                
                elif function_name.startswith('_handle_'):
                    # Handler functions need a ParsedQuery object
                    parsed_query = self._create_parsed_query(parameters)
                    return func(parsed_query, db_session)
                
                else:
                    # Generic function call
                    return func(db_session)
            
            else:
                return {
                    "status": "error",
                    "error": f"Function '{function_name}' not found",
                    "results": [],
                    "count": 0
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Function execution failed: {str(e)}",
                "results": [],
                "count": 0
            }
    
    def _create_parsed_query(self, parameters: Dict[str, Any]) -> object:
        """Create a minimal ParsedQuery object for handler functions."""
        
        class MockParsedQuery:
            def __init__(self, params):
                self.entities = []
                self.time_range = None
                self.parameters = params
                
                # Set time range if specified
                if "time_range" in params:
                    time_range_str = params["time_range"]
                    if time_range_str == "last_hour":
                        from datetime import datetime, timedelta, timezone
                        now = datetime.now(timezone.utc)
                        self.time_range = {
                            "start": now - timedelta(hours=1),
                            "end": now
                        }
                    elif time_range_str == "today":
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc)
                        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        self.time_range = {
                            "start": start_of_day,
                            "end": now
                        }
                
                # Add entities based on parameters
                if "container" in params:
                    self.entities.append({
                        "type": "container",
                        "value": params["container"]
                    })
                
                if "ip_address" in params:
                    self.entities.append({
                        "type": "ip_address", 
                        "value": params["ip_address"]
                    })
        
        return MockParsedQuery(parameters)
    
    def _get_query_suggestions(self) -> list:
        """Get query suggestions for users."""
        return [
            "show me recent logs",
            "get latest logs", 
            "show alerts",
            "system summary",
            "performance metrics",
            "error logs from last hour",
            "container logs",
            "investigate IP address"
        ]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information."""
        try:
            db_session = get_sync_db_session()
            
            return {
                "status": "operational",
                "database_connected": True,
                "available_functions": len(self.mapper.patterns),
                "cache_size": len(self.response_cache),
                "supported_queries": self._get_query_suggestions(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "status": "degraded",
                "database_connected": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def clear_cache(self):
        """Clear the response cache."""
        self.response_cache.clear()


# Global instance
_simple_nlp_system = None

def get_simple_nlp_system() -> SimpleNLPSystem:
    """Get the global simple NLP system instance."""
    global _simple_nlp_system
    if _simple_nlp_system is None:
        _simple_nlp_system = SimpleNLPSystem()
    return _simple_nlp_system


def reset_simple_nlp_system():
    """Reset the global simple NLP system instance."""
    global _simple_nlp_system
    _simple_nlp_system = None


if __name__ == "__main__":
    # Test the simple NLP system
    nlp = SimpleNLPSystem()
    
    test_queries = [
        "show me recent logs",
        "get latest logs",
        "show alerts", 
        "system summary",
        "error logs from last hour",
        "container logs for web-server"
    ]
    
    print("Testing Simple NLP System:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = nlp.process_query(query)
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Function: {result.get('function_used', 'none')}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        else:
            print(f"Results: {result.get('count', 0)} items")