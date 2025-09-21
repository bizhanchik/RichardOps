#!/usr/bin/env python3
"""
Direct Message-to-Function Mapping System

This bypasses the complex intent classification system and directly maps
user messages to appropriate functions based on simple keyword matching.
"""

import re
from typing import Dict, Any, Callable, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class MessagePattern:
    """Represents a message pattern and its associated function."""
    keywords: List[str]  # Keywords that must be present
    function_name: str   # Function to call
    priority: int = 1    # Higher priority patterns are checked first
    description: str = ""


class DirectMessageMapper:
    """Simple, reliable message-to-function mapper."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> List[MessagePattern]:
        """Initialize all message patterns."""
        return [
            # Log-related patterns (highest priority)
            MessagePattern(
                keywords=["recent", "logs"],
                function_name="fetch_latest_logs",
                priority=10,
                description="Show recent logs"
            ),
            MessagePattern(
                keywords=["show", "logs"],
                function_name="fetch_latest_logs", 
                priority=9,
                description="Show logs"
            ),
            MessagePattern(
                keywords=["get", "logs"],
                function_name="fetch_latest_logs",
                priority=9,
                description="Get logs"
            ),
            MessagePattern(
                keywords=["latest", "logs"],
                function_name="fetch_latest_logs",
                priority=9,
                description="Latest logs"
            ),
            MessagePattern(
                keywords=["all", "logs"],
                function_name="fetch_all_logs",
                priority=8,
                description="All logs"
            ),
            MessagePattern(
                keywords=["logs", "last", "hour"],
                function_name="fetch_logs_last_hour",
                priority=8,
                description="Logs from last hour"
            ),
            MessagePattern(
                keywords=["error", "logs"],
                function_name="fetch_logs_by_message_pattern",
                priority=8,
                description="Error logs"
            ),
            MessagePattern(
                keywords=["container", "logs"],
                function_name="fetch_logs_by_container",
                priority=8,
                description="Container logs"
            ),
            
            # Alert-related patterns
            MessagePattern(
                keywords=["show", "alerts"],
                function_name="_handle_show_alerts",
                priority=7,
                description="Show alerts"
            ),
            MessagePattern(
                keywords=["get", "alerts"],
                function_name="_handle_show_alerts",
                priority=7,
                description="Get alerts"
            ),
            MessagePattern(
                keywords=["alerts"],
                function_name="_handle_show_alerts",
                priority=6,
                description="Alerts"
            ),
            
            # Analytics patterns
            MessagePattern(
                keywords=["system", "summary"],
                function_name="_handle_analytics_summary",
                priority=7,
                description="System summary"
            ),
            MessagePattern(
                keywords=["anomalies"],
                function_name="_handle_analytics_anomalies",
                priority=7,
                description="Anomalies"
            ),
            MessagePattern(
                keywords=["performance"],
                function_name="_handle_analytics_performance",
                priority=7,
                description="Performance analytics"
            ),
            MessagePattern(
                keywords=["metrics"],
                function_name="_handle_analytics_metrics",
                priority=7,
                description="System metrics"
            ),
            
            # Report patterns
            MessagePattern(
                keywords=["generate", "report"],
                function_name="_handle_generate_report",
                priority=6,
                description="Generate report"
            ),
            MessagePattern(
                keywords=["create", "report"],
                function_name="_handle_generate_report",
                priority=6,
                description="Create report"
            ),
            
            # Investigation patterns
            MessagePattern(
                keywords=["investigate"],
                function_name="_handle_investigate",
                priority=6,
                description="Investigate"
            ),
            MessagePattern(
                keywords=["analyze", "trends"],
                function_name="_handle_analyze_trends",
                priority=6,
                description="Analyze trends"
            ),
        ]
    
    def map_message_to_function(self, message: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Map a user message directly to a function name and parameters.
        
        Args:
            message: User's natural language message
            
        Returns:
            Tuple of (function_name, parameters) or None if no match
        """
        message_lower = message.lower().strip()
        
        # Sort patterns by priority (highest first)
        sorted_patterns = sorted(self.patterns, key=lambda p: p.priority, reverse=True)
        
        for pattern in sorted_patterns:
            if self._matches_pattern(message_lower, pattern):
                params = self._extract_parameters(message_lower, pattern)
                return pattern.function_name, params
        
        return None
    
    def _matches_pattern(self, message: str, pattern: MessagePattern) -> bool:
        """Check if message matches the pattern."""
        # All keywords must be present in the message
        return all(keyword in message for keyword in pattern.keywords)
    
    def _extract_parameters(self, message: str, pattern: MessagePattern) -> Dict[str, Any]:
        """Extract parameters from the message based on the pattern."""
        params = {}
        
        # Extract common parameters
        if "error" in message:
            params["pattern"] = "error"
        elif "warning" in message:
            params["pattern"] = "warning"
        elif "info" in message:
            params["pattern"] = "info"
        
        # Extract container name if mentioned
        container_match = re.search(r'container[:\s]+([a-zA-Z0-9_-]+)', message)
        if container_match:
            params["container"] = container_match.group(1)
        
        # Extract IP address if mentioned
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', message)
        if ip_match:
            params["ip_address"] = ip_match.group(0)
        
        # Extract time-related parameters
        if "last hour" in message or "past hour" in message:
            params["time_range"] = "last_hour"
        elif "today" in message:
            params["time_range"] = "today"
        elif "yesterday" in message:
            params["time_range"] = "yesterday"
        elif "week" in message:
            params["time_range"] = "week"
        elif "month" in message:
            params["time_range"] = "month"
        
        # Extract limit if mentioned
        limit_match = re.search(r'(?:last|recent|top)\s+(\d+)', message)
        if limit_match:
            params["limit"] = int(limit_match.group(1))
        elif "recent" in message:
            params["limit"] = 50  # Default for recent
        
        return params
    
    def get_available_patterns(self) -> List[str]:
        """Get list of available patterns for debugging."""
        return [f"{p.description}: {' + '.join(p.keywords)}" for p in self.patterns]


# Global instance
_direct_mapper = None

def get_direct_mapper() -> DirectMessageMapper:
    """Get the global direct message mapper instance."""
    global _direct_mapper
    if _direct_mapper is None:
        _direct_mapper = DirectMessageMapper()
    return _direct_mapper


def reset_direct_mapper():
    """Reset the global mapper instance."""
    global _direct_mapper
    _direct_mapper = None


if __name__ == "__main__":
    # Test the mapper
    mapper = DirectMessageMapper()
    
    test_messages = [
        "show me recent logs",
        "get latest logs", 
        "show all logs",
        "container logs for web-server",
        "error logs from last hour",
        "show alerts",
        "system summary",
        "performance metrics",
        "investigate IP 192.168.1.100"
    ]
    
    print("Testing Direct Message Mapper:")
    print("=" * 50)
    
    for msg in test_messages:
        result = mapper.map_message_to_function(msg)
        if result:
            func_name, params = result
            print(f"✅ '{msg}' -> {func_name}")
            if params:
                print(f"   Parameters: {params}")
        else:
            print(f"❌ '{msg}' -> No match")
        print()