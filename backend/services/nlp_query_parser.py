"""
NLP Query Parser for natural language security and log analysis queries.

This module provides intelligent parsing of natural language queries into structured
database queries for security monitoring, log analysis, and investigation tasks.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from nlp_model import get_embedding


class QueryIntent(Enum):
    """Types of query intents the system can handle."""
    SEARCH_LOGS = "search_logs"
    GENERATE_REPORT = "generate_report"
    INVESTIGATE = "investigate"
    SHOW_ALERTS = "show_alerts"
    ANALYZE_TRENDS = "analyze_trends"
    ANALYTICS_SUMMARY = "analytics_summary"
    ANALYTICS_ANOMALIES = "analytics_anomalies"
    ANALYTICS_PERFORMANCE = "analytics_performance"
    ANALYTICS_METRICS = "analytics_metrics"
    UNKNOWN = "unknown"


class EntityType(Enum):
    """Types of entities that can be extracted from queries."""
    TIME_RANGE = "time_range"
    IP_ADDRESS = "ip_address"
    ASSET_NAME = "asset_name"
    LOG_LEVEL = "log_level"
    EVENT_TYPE = "event_type"
    CONTAINER_NAME = "container_name"
    SEVERITY = "severity"
    STATUS = "status"


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from a query."""
    type: EntityType
    value: str
    confidence: float
    original_text: str


@dataclass
class ParsedQuery:
    """Represents a parsed natural language query."""
    intent: QueryIntent
    entities: List[ExtractedEntity]
    confidence: float
    original_query: str
    structured_params: Dict[str, Any]


class NLPQueryParser:
    """
    Advanced NLP query parser using sentence transformers and pattern matching.
    
    Combines semantic understanding with rule-based entity extraction for
    robust natural language query processing.
    """
    
    def __init__(self, use_improved_classifier: bool = True):
        """Initialize the NLP query parser with intent patterns and entity extractors."""
        self.intent_patterns = self._build_intent_patterns()
        self.entity_patterns = self._build_entity_patterns()
        self.time_patterns = self._build_time_patterns()
        self.use_improved_classifier = use_improved_classifier
        
        # Initialize improved classifier if enabled
        if self.use_improved_classifier:
            try:
                from services.improved_intent_classifier import get_improved_classifier
                self.improved_classifier = get_improved_classifier()
            except Exception as e:
                print(f"Warning: Could not initialize improved classifier: {e}")
                self.use_improved_classifier = False
                self.improved_classifier = None
        
    def _build_intent_patterns(self) -> Dict[QueryIntent, List[str]]:
        """Build patterns for intent classification with improved keywords."""
        return {
            QueryIntent.SEARCH_LOGS: [
                "show", "find", "search", "get", "list", "display", "retrieve", "fetch", "pull",
                "logs", "entries", "messages", "events", "records", "output", "recent", "latest",
                "container logs", "error logs", "access logs", "debug logs", "application logs"
            ],
            QueryIntent.GENERATE_REPORT: [
                "generate", "create", "build", "produce", "make", "compile", "export",
                "report", "summary", "analysis", "overview", "digest", "dashboard",
                "statistics", "breakdown", "recap", "document"
            ],
            QueryIntent.INVESTIGATE: [
                "investigate", "analyze", "examine", "track", "trace", "debug", "troubleshoot",
                "diagnose", "root cause", "why", "what happened", "what caused", "find out",
                "look into", "check", "verify", "inspect"
            ],
            QueryIntent.SHOW_ALERTS: [
                "alerts", "warnings", "notifications", "incidents", "alarms",
                "critical", "urgent", "problems", "issues", "failures", "errors",
                "anomalies", "exceptions", "faults", "outages"
            ],
            QueryIntent.ANALYZE_TRENDS: [
                "trends", "patterns", "statistics", "metrics", "analytics",
                "over time", "historical", "compare", "growth", "changes",
                "performance", "usage", "behavior", "evolution", "progression"
            ],
            QueryIntent.ANALYTICS_SUMMARY: [
                "summary", "overview", "status", "comprehensive", "system summary",
                "analytics summary", "daily summary", "weekly summary", "quick overview",
                "summarize", "provide overview", "system status"
            ],
            QueryIntent.ANALYTICS_ANOMALIES: [
                "anomalies", "anomaly", "unusual", "suspicious", "abnormal", "outliers",
                "irregular", "detect anomalies", "find anomalies", "unusual activity",
                "suspicious patterns", "abnormal behavior", "outlier detection"
            ],
            QueryIntent.ANALYTICS_PERFORMANCE: [
                "performance", "performing", "performance metrics", "performance report",
                "performance data", "performance analytics", "performance statistics",
                "performance insights", "resource utilization", "system performance"
            ],
            QueryIntent.ANALYTICS_METRICS: [
                "metrics", "metric", "measurements", "key metrics", "system metrics",
                "analytics metrics", "operational metrics", "metric data", "metric trends",
                "metric analysis", "metric dashboard"
            ]
        }
    
    def _build_entity_patterns(self) -> Dict[EntityType, List[str]]:
        """Build regex patterns for entity extraction."""
        return {
            EntityType.IP_ADDRESS: [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'  # IPv6
            ],
            EntityType.LOG_LEVEL: [
                r'\b(?:error|warn|warning|info|debug|trace|critical|fatal)\b',
                r'\b(?:ERROR|WARN|WARNING|INFO|DEBUG|TRACE|CRITICAL|FATAL)\b'
            ],
            EntityType.EVENT_TYPE: [
                r'\b(?:login|logout|authentication|access|connection|failure|success)\b',
                r'\b(?:docker|container|service|application|database|network)\b'
            ],
            EntityType.CONTAINER_NAME: [
                r'\b[a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9]\b(?=\s*container)',
                r'container\s+([a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9])'
            ],
            EntityType.SEVERITY: [
                r'\b(?:low|medium|high|critical)\b',
                r'\b(?:LOW|MEDIUM|HIGH|CRITICAL)\b'
            ],
            EntityType.STATUS: [
                r'\b(?:resolved|unresolved|open|closed|active|inactive)\b',
                r'\b(?:success|failed|pending|completed)\b'
            ]
        }
    
    def _build_time_patterns(self) -> Dict[str, str]:
        """Build patterns for time range extraction."""
        return {
            'last_hour': r'\b(?:last|past)\s+hour\b',
            'last_day': r'\b(?:last|past)\s+(?:day|24\s*hours?)\b',
            'last_week': r'\b(?:last|past)\s+week\b',
            'last_month': r'\b(?:last|past)\s+month\b',
            'today': r'\btoday\b',
            'yesterday': r'\byesterday\b',
            'this_week': r'\bthis\s+week\b',
            'this_month': r'\bthis\s+month\b',
            'specific_time': r'\b\d{1,2}:\d{2}\b',
            'specific_date': r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b'
        }
    
    def parse_query(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into structured components.
        
        Args:
            query: The natural language query string
            
        Returns:
            ParsedQuery: Structured representation of the query
        """
        query_lower = query.lower()
        
        # Classify intent using improved classifier if available
        if self.use_improved_classifier and self.improved_classifier:
            intent, intent_confidence = self.improved_classifier.classify_intent(query)
        else:
            intent, intent_confidence = self._classify_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Extract time range
        time_entity = self._extract_time_range(query_lower)
        if time_entity:
            entities.append(time_entity)
        
        # Build structured parameters
        structured_params = self._build_structured_params(intent, entities)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_confidence(intent_confidence, entities)
        
        return ParsedQuery(
            intent=intent,
            entities=entities,
            confidence=overall_confidence,
            original_query=query,
            structured_params=structured_params
        )
    
    def _classify_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """Classify the intent of a query with improved fallback logic."""
        query_lower = query.lower()
        
        # Try improved classifier first if available
        if self.use_improved_classifier and self.improved_classifier:
            try:
                intent, confidence = self.improved_classifier.classify_intent(query)
                
                # If confidence is very low, try keyword-based fallback
                if confidence < 0.3:
                    keyword_intent, keyword_confidence = self._classify_with_keywords(query_lower)
                    
                    # Use keyword result if it has higher confidence
                    if keyword_confidence > confidence:
                        return keyword_intent, keyword_confidence
                    
                    # If both are low confidence, provide helpful suggestions
                    if confidence < 0.2 and keyword_confidence < 0.2:
                        return QueryIntent.UNKNOWN, 0.1  # Very low confidence
                
                return intent, confidence
                
            except Exception as e:
                print(f"Error in improved classifier: {e}")
                # Fall back to keyword-based classification
                return self._classify_with_keywords(query_lower)
        
        # Use keyword-based classification as fallback
        return self._classify_with_keywords(query_lower)
    
    def _classify_with_keywords(self, query_lower: str) -> Tuple[QueryIntent, float]:
        """Classify intent using keyword-based approach with improved scoring."""
        intent_scores = {}
        
        # Calculate scores for each intent based on keyword matches
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matched_keywords = 0
            
            for pattern in patterns:
                if pattern in query_lower:
                    # Weight longer patterns more heavily
                    pattern_weight = len(pattern.split()) * 0.3 + 0.7
                    score += pattern_weight
                    matched_keywords += 1
            
            # Normalize score by number of patterns and add bonus for multiple matches
            if matched_keywords > 0:
                normalized_score = score / len(patterns)
                # Bonus for multiple keyword matches
                if matched_keywords > 1:
                    normalized_score *= (1 + (matched_keywords - 1) * 0.2)
                intent_scores[intent] = min(normalized_score, 1.0)
        
        # Special handling for domain-specific terms
        domain_boost = self._get_domain_context_boost(query_lower)
        for intent, boost in domain_boost.items():
            if intent in intent_scores:
                intent_scores[intent] = min(intent_scores[intent] + boost, 1.0)
        
        if not intent_scores:
            return QueryIntent.UNKNOWN, 0.0
        
        # Get the best intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]
        
        # Apply improved confidence thresholds
        if confidence < 0.15:
            return QueryIntent.UNKNOWN, confidence
        elif confidence < 0.3:
            # Low confidence - suggest alternatives
            return best_intent, confidence * 0.8
        else:
            return best_intent, min(confidence, 0.9)
    
    def _get_domain_context_boost(self, query_lower: str) -> Dict[QueryIntent, float]:
        """Provide domain-specific context boosts for better classification."""
        boosts = {}
        
        # Technical terms that strongly indicate specific intents
        technical_indicators = {
            # Log-related terms
            'log': QueryIntent.SEARCH_LOGS,
            'logs': QueryIntent.SEARCH_LOGS,
            'logging': QueryIntent.SEARCH_LOGS,
            'stdout': QueryIntent.SEARCH_LOGS,
            'stderr': QueryIntent.SEARCH_LOGS,
            'syslog': QueryIntent.SEARCH_LOGS,
            'journal': QueryIntent.SEARCH_LOGS,
            
            # Alert-related terms
            'alert': QueryIntent.SHOW_ALERTS,
            'alerts': QueryIntent.SHOW_ALERTS,
            'alarm': QueryIntent.SHOW_ALERTS,
            'alarms': QueryIntent.SHOW_ALERTS,
            'notification': QueryIntent.SHOW_ALERTS,
            'incident': QueryIntent.SHOW_ALERTS,
            'warning': QueryIntent.SHOW_ALERTS,
            'critical': QueryIntent.SHOW_ALERTS,
            
            # Investigation terms
            'debug': QueryIntent.INVESTIGATE,
            'troubleshoot': QueryIntent.INVESTIGATE,
            'diagnose': QueryIntent.INVESTIGATE,
            'root cause': QueryIntent.INVESTIGATE,
            'why': QueryIntent.INVESTIGATE,
            'what happened': QueryIntent.INVESTIGATE,
            'what caused': QueryIntent.INVESTIGATE,
            
            # Performance terms
            'performance': QueryIntent.ANALYTICS_PERFORMANCE,
            'cpu': QueryIntent.ANALYTICS_PERFORMANCE,
            'memory': QueryIntent.ANALYTICS_PERFORMANCE,
            'disk': QueryIntent.ANALYTICS_PERFORMANCE,
            'network': QueryIntent.ANALYTICS_PERFORMANCE,
            'latency': QueryIntent.ANALYTICS_PERFORMANCE,
            'throughput': QueryIntent.ANALYTICS_PERFORMANCE,
            'response time': QueryIntent.ANALYTICS_PERFORMANCE,
            
            # Metrics terms
            'metrics': QueryIntent.ANALYTICS_METRICS,
            'metric': QueryIntent.ANALYTICS_METRICS,
            'kpi': QueryIntent.ANALYTICS_METRICS,
            'measurement': QueryIntent.ANALYTICS_METRICS,
            'statistics': QueryIntent.ANALYTICS_METRICS,
            
            # Anomaly terms
            'anomaly': QueryIntent.ANALYTICS_ANOMALIES,
            'anomalies': QueryIntent.ANALYTICS_ANOMALIES,
            'unusual': QueryIntent.ANALYTICS_ANOMALIES,
            'suspicious': QueryIntent.ANALYTICS_ANOMALIES,
            'outlier': QueryIntent.ANALYTICS_ANOMALIES,
            'abnormal': QueryIntent.ANALYTICS_ANOMALIES,
            
            # Trend terms
            'trend': QueryIntent.ANALYZE_TRENDS,
            'trends': QueryIntent.ANALYZE_TRENDS,
            'pattern': QueryIntent.ANALYZE_TRENDS,
            'patterns': QueryIntent.ANALYZE_TRENDS,
            'over time': QueryIntent.ANALYZE_TRENDS,
            'historical': QueryIntent.ANALYZE_TRENDS,
            'compare': QueryIntent.ANALYZE_TRENDS,
            
            # Report terms
            'report': QueryIntent.GENERATE_REPORT,
            'generate': QueryIntent.GENERATE_REPORT,
            'create': QueryIntent.GENERATE_REPORT,
            'export': QueryIntent.GENERATE_REPORT,
            'compile': QueryIntent.GENERATE_REPORT,
            
            # Summary terms
            'summary': QueryIntent.ANALYTICS_SUMMARY,
            'overview': QueryIntent.ANALYTICS_SUMMARY,
            'status': QueryIntent.ANALYTICS_SUMMARY,
            'dashboard': QueryIntent.ANALYTICS_SUMMARY,
        }
        
        for term, intent in technical_indicators.items():
            if term in query_lower:
                boosts[intent] = boosts.get(intent, 0) + 0.2
        
        # Question words that indicate investigation
        question_words = ['why', 'what', 'how', 'when', 'where', 'who']
        if any(word in query_lower for word in question_words):
            boosts[QueryIntent.INVESTIGATE] = boosts.get(QueryIntent.INVESTIGATE, 0) + 0.15
        
        # Time-related terms that indicate trends
        time_terms = ['yesterday', 'today', 'last week', 'last month', 'recent', 'latest', 'current']
        if any(term in query_lower for term in time_terms):
            boosts[QueryIntent.ANALYZE_TRENDS] = boosts.get(QueryIntent.ANALYZE_TRENDS, 0) + 0.1
        
        return boosts

    def _extract_entities(self, query: str) -> List[ExtractedEntity]:
        """Extract entities from the query using pattern matching."""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    entity = ExtractedEntity(
                        type=entity_type,
                        value=match.group().lower(),
                        confidence=0.9,  # High confidence for regex matches
                        original_text=match.group()
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_time_range(self, query: str) -> Optional[ExtractedEntity]:
        """Extract time range from the query."""
        for time_type, pattern in self.time_patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return ExtractedEntity(
                    type=EntityType.TIME_RANGE,
                    value=time_type,
                    confidence=0.95,
                    original_text=match.group()
                )
        
        return None
    
    def _build_structured_params(self, intent: QueryIntent, entities: List[ExtractedEntity]) -> Dict[str, Any]:
        """Build structured parameters from intent and entities."""
        params = {
            "intent": intent.value,
            "filters": {},
            "time_range": None,
            "output_format": "json"
        }
        
        for entity in entities:
            if entity.type == EntityType.TIME_RANGE:
                params["time_range"] = self._convert_time_range(entity.value)
            elif entity.type == EntityType.IP_ADDRESS:
                params["filters"]["ip_address"] = entity.value
            elif entity.type == EntityType.LOG_LEVEL:
                params["filters"]["log_level"] = entity.value.upper()
            elif entity.type == EntityType.SEVERITY:
                params["filters"]["severity"] = entity.value.upper()
            elif entity.type == EntityType.CONTAINER_NAME:
                params["filters"]["container"] = entity.value
            elif entity.type == EntityType.EVENT_TYPE:
                params["filters"]["event_type"] = entity.value
            elif entity.type == EntityType.STATUS:
                params["filters"]["status"] = entity.value
        
        return params
    
    def _convert_time_range(self, time_value: str) -> Dict[str, datetime]:
        """Convert time range string to datetime objects."""
        now = datetime.now()
        
        if time_value == "last_hour":
            return {"start": now - timedelta(hours=1), "end": now}
        elif time_value == "last_day":
            return {"start": now - timedelta(days=1), "end": now}
        elif time_value == "last_week":
            return {"start": now - timedelta(weeks=1), "end": now}
        elif time_value == "last_month":
            return {"start": now - timedelta(days=30), "end": now}
        elif time_value == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return {"start": start_of_day, "end": now}
        elif time_value == "yesterday":
            yesterday = now - timedelta(days=1)
            start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return {"start": start_of_yesterday, "end": end_of_yesterday}
        elif time_value == "this_week":
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            return {"start": start_of_week, "end": now}
        elif time_value == "this_month":
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return {"start": start_of_month, "end": now}
        
        # Default to last hour if unknown
        return {"start": now - timedelta(hours=1), "end": now}
    
    def _calculate_confidence(self, intent_confidence: float, entities: List[ExtractedEntity]) -> float:
        """Calculate overall confidence score for the parsed query."""
        if not entities:
            return intent_confidence * 0.7  # Lower confidence without entities
        
        entity_confidence = sum(e.confidence for e in entities) / len(entities)
        return (intent_confidence + entity_confidence) / 2
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Get query suggestions based on partial input."""
        suggestions = [
            "Show me all failed logins in the last hour",
            "Generate weekly security summary",
            "What assets did IP address 192.168.1.100 target?",
            "Show critical alerts from today",
            "Find all ERROR logs from container webapp",
            "Investigate suspicious activity in the last 24 hours",
            "Generate monthly Docker events report",
            "Show all unresolved high severity alerts",
            "What containers had failures yesterday?",
            "Analyze login trends this week"
        ]
        
        if not partial_query:
            return suggestions[:5]
        
        # Simple matching for suggestions
        partial_lower = partial_query.lower()
        matching = [s for s in suggestions if any(word in s.lower() for word in partial_lower.split())]
        
        return matching[:5] if matching else suggestions[:3]


# Global parser instance
_nlp_parser = None

def get_nlp_parser() -> NLPQueryParser:
    """Get the global NLP query parser instance."""
    global _nlp_parser
    if _nlp_parser is None:
        _nlp_parser = NLPQueryParser()
    return _nlp_parser

def parse_natural_query(query: str) -> ParsedQuery:
    """
    Parse a natural language query into structured components.
    
    Args:
        query: The natural language query string
        
    Returns:
        ParsedQuery: Structured representation of the query
    """
    parser = get_nlp_parser()
    return parser.parse_query(query)