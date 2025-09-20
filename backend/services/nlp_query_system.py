"""
NLP Query System - Main interface for natural language security queries.

This module provides the main interface for processing natural language queries
about security events, logs, and system monitoring data.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from services.nlp_query_parser import parse_natural_query, ParsedQuery, QueryIntent
from services.nlp_query_translator import get_query_translator
from database import get_sync_db_session


class NLPQuerySystem:
    """
    Main NLP Query System for processing natural language security queries.
    
    Provides a unified interface for:
    - Query processing and understanding
    - Report generation
    - Investigation assistance
    - Trend analysis
    """
    
    def __init__(self):
        """Initialize the NLP query system."""
        self.translator = get_query_translator()
        self.response_cache = {}
        
    def process_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language query and return formatted results.
        
        Args:
            query: The natural language query string
            user_context: Optional user context for personalization
            
        Returns:
            Dict containing formatted query results
        """
        try:
            # Parse the natural language query
            parsed_query = parse_natural_query(query)
            
            # Get database session
            db_session = get_sync_db_session()
            
            try:
                # Translate and execute the query
                raw_results = self.translator.translate_query(parsed_query, db_session)
                
                # Format the response based on intent
                formatted_response = self._format_response(raw_results, parsed_query, user_context)
                
                # Add metadata
                formatted_response["metadata"] = {
                    "query_processed_at": datetime.now().isoformat(),
                    "confidence": parsed_query.confidence,
                    "intent": parsed_query.intent.value,
                    "entities_found": len(parsed_query.entities),
                    "processing_time_ms": self._calculate_processing_time()
                }
                
                return formatted_response
                
            finally:
                db_session.close()
                
        except Exception as e:
            return self._format_error_response(str(e), query)
    
    def get_query_suggestions(self, partial_query: str = "") -> List[str]:
        """Get query suggestions for autocomplete."""
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
            "Analyze login trends this week",
            "Show me database connection errors",
            "Generate security incident report for last month",
            "What happened with container nginx today?",
            "Show all authentication failures",
            "Analyze system performance trends"
        ]
        
        if not partial_query:
            return suggestions[:8]
        
        # Filter suggestions based on partial query
        partial_lower = partial_query.lower()
        matching = []
        
        for suggestion in suggestions:
            if any(word in suggestion.lower() for word in partial_lower.split()):
                matching.append(suggestion)
        
        return matching[:8] if matching else suggestions[:5]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the status of the NLP query system."""
        try:
            db_session = get_sync_db_session()
            
            try:
                # Test database connectivity
                from db_models import AlertsModel
                recent_alerts = db_session.query(AlertsModel).limit(1).all()
                db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"
            finally:
                db_session.close()
            
            return {
                "status": "operational",
                "database": db_status,
                "supported_intents": [intent.value for intent in QueryIntent if intent != QueryIntent.UNKNOWN],
                "features": {
                    "query_processing": True,
                    "report_generation": True,
                    "investigation_assistance": True,
                    "trend_analysis": True,
                    "real_time_queries": True
                },
                "version": "1.0.0"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "features": {
                    "query_processing": False,
                    "report_generation": False,
                    "investigation_assistance": False,
                    "trend_analysis": False,
                    "real_time_queries": False
                }
            }
    
    def _format_response(self, raw_results: Dict[str, Any], parsed_query: ParsedQuery, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Format the response based on query intent and results."""
        intent = parsed_query.intent
        
        if intent == QueryIntent.SEARCH_LOGS:
            return self._format_search_response(raw_results, parsed_query)
        elif intent == QueryIntent.SHOW_ALERTS:
            return self._format_alerts_response(raw_results, parsed_query)
        elif intent == QueryIntent.GENERATE_REPORT:
            return self._format_report_response(raw_results, parsed_query)
        elif intent == QueryIntent.INVESTIGATE:
            return self._format_investigation_response(raw_results, parsed_query)
        elif intent == QueryIntent.ANALYZE_TRENDS:
            return self._format_trends_response(raw_results, parsed_query)
        else:
            return self._format_generic_response(raw_results, parsed_query)
    
    def _format_search_response(self, raw_results: Dict[str, Any], parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Format search results for log queries."""
        results = raw_results.get("results", [])
        count = raw_results.get("count", 0)
        
        # Create summary
        summary = f"Found {count} log entries"
        if parsed_query.structured_params.get("time_range"):
            time_range = parsed_query.structured_params["time_range"]
            summary += f" from {time_range['start'].strftime('%Y-%m-%d %H:%M')} to {time_range['end'].strftime('%Y-%m-%d %H:%M')}"
        
        # Categorize results
        categorized_results = self._categorize_log_results(results)
        
        return {
            "type": "search_results",
            "summary": summary,
            "total_count": count,
            "results": results[:20],  # Limit display results
            "categories": categorized_results,
            "query_info": raw_results.get("query_info", {}),
            "actions": [
                {"label": "Export Results", "action": "export", "format": "csv"},
                {"label": "Create Alert", "action": "create_alert"},
                {"label": "Investigate Further", "action": "investigate"}
            ]
        }
    
    def _format_alerts_response(self, raw_results: Dict[str, Any], parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Format alerts display response."""
        results = raw_results.get("results", [])
        count = raw_results.get("count", 0)
        stats = raw_results.get("statistics", {})
        
        summary = f"Found {count} alerts"
        if stats:
            unresolved = stats.get("unresolved_alerts", 0)
            if unresolved > 0:
                summary += f" ({unresolved} unresolved)"
        
        # Prioritize alerts by severity
        prioritized_alerts = self._prioritize_alerts(results)
        
        return {
            "type": "alerts_display",
            "summary": summary,
            "total_count": count,
            "statistics": stats,
            "alerts": prioritized_alerts,
            "priority_breakdown": self._get_priority_breakdown(results),
            "query_info": raw_results.get("query_info", {}),
            "actions": [
                {"label": "Resolve Selected", "action": "resolve_alerts"},
                {"label": "Create Incident", "action": "create_incident"},
                {"label": "Export Report", "action": "export", "format": "pdf"}
            ]
        }
    
    def _format_report_response(self, raw_results: Dict[str, Any], parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Format report generation response."""
        report = raw_results.get("report", {})
        
        # Create executive summary
        executive_summary = self._create_executive_summary(report)
        
        # Format report sections
        formatted_sections = self._format_report_sections(report)
        
        return {
            "type": "security_report",
            "title": "Security Analysis Report",
            "generated_at": datetime.now().isoformat(),
            "time_period": report.get("time_period", {}),
            "executive_summary": executive_summary,
            "sections": formatted_sections,
            "recommendations": report.get("recommendations", []),
            "query_info": raw_results.get("query_info", {}),
            "actions": [
                {"label": "Download PDF", "action": "download", "format": "pdf"},
                {"label": "Schedule Regular Report", "action": "schedule"},
                {"label": "Share Report", "action": "share"}
            ]
        }
    
    def _format_investigation_response(self, raw_results: Dict[str, Any], parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Format investigation response."""
        investigation = raw_results.get("investigation", {})
        
        # Create investigation summary
        summary = self._create_investigation_summary(investigation, parsed_query)
        
        # Format investigation findings
        findings = self._format_investigation_findings(investigation)
        
        return {
            "type": "investigation_results",
            "summary": summary,
            "findings": findings,
            "risk_assessment": self._assess_investigation_risk(investigation),
            "timeline": self._create_investigation_timeline(investigation),
            "query_info": raw_results.get("query_info", {}),
            "actions": [
                {"label": "Create Incident", "action": "create_incident"},
                {"label": "Block IP", "action": "block_ip"},
                {"label": "Generate Detailed Report", "action": "detailed_report"}
            ]
        }
    
    def _format_trends_response(self, raw_results: Dict[str, Any], parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Format trends analysis response."""
        trends = raw_results.get("trends", {})
        
        # Create trends summary
        summary = self._create_trends_summary(trends)
        
        # Format trend data for visualization
        chart_data = self._format_trends_for_charts(trends)
        
        return {
            "type": "trends_analysis",
            "summary": summary,
            "trends": trends,
            "charts": chart_data,
            "insights": self._generate_trend_insights(trends),
            "query_info": raw_results.get("query_info", {}),
            "actions": [
                {"label": "Export Charts", "action": "export", "format": "png"},
                {"label": "Set Trend Alerts", "action": "set_alerts"},
                {"label": "Compare Periods", "action": "compare"}
            ]
        }
    
    def _format_generic_response(self, raw_results: Dict[str, Any], parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Format generic response for unknown intents."""
        return {
            "type": "generic_response",
            "message": "I understand you're looking for information, but I need more specific details.",
            "suggestions": self.get_query_suggestions(),
            "raw_results": raw_results,
            "query_info": {
                "original_query": parsed_query.original_query,
                "confidence": parsed_query.confidence,
                "entities_found": len(parsed_query.entities)
            }
        }
    
    def _categorize_log_results(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize log results by type."""
        categories = {"errors": 0, "warnings": 0, "info": 0, "other": 0}
        
        for result in results:
            message = result.get("message", "").lower()
            if "error" in message or "fail" in message:
                categories["errors"] += 1
            elif "warn" in message or "warning" in message:
                categories["warnings"] += 1
            elif "info" in message:
                categories["info"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def _prioritize_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize alerts by severity and timestamp."""
        severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        
        return sorted(alerts, key=lambda x: (
            severity_order.get(x.get("severity", "LOW"), 0),
            x.get("timestamp", "")
        ), reverse=True)
    
    def _get_priority_breakdown(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of alerts by priority."""
        breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for alert in alerts:
            severity = alert.get("severity", "LOW")
            if severity in breakdown:
                breakdown[severity] += 1
        
        return breakdown
    
    def _create_executive_summary(self, report: Dict[str, Any]) -> str:
        """Create executive summary for reports."""
        alerts_summary = report.get("alerts_summary", {})
        total_alerts = alerts_summary.get("total_alerts", 0)
        resolution_rate = alerts_summary.get("resolution_rate", 0)
        
        summary = f"During the reporting period, {total_alerts} security alerts were generated "
        summary += f"with a resolution rate of {resolution_rate:.1f}%. "
        
        if resolution_rate < 50:
            summary += "The low resolution rate indicates a need for improved incident response processes. "
        elif resolution_rate > 80:
            summary += "The high resolution rate demonstrates effective incident response. "
        
        docker_summary = report.get("docker_events_summary", {})
        docker_events = docker_summary.get("total_events", 0)
        if docker_events > 0:
            summary += f"Container activity included {docker_events} Docker events. "
        
        return summary
    
    def _format_report_sections(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format report sections for display."""
        sections = []
        
        # Alerts section
        if "alerts_summary" in report:
            sections.append({
                "title": "Security Alerts",
                "type": "alerts",
                "data": report["alerts_summary"],
                "chart_type": "pie"
            })
        
        # Docker events section
        if "docker_events_summary" in report:
            sections.append({
                "title": "Container Activity",
                "type": "docker_events",
                "data": report["docker_events_summary"],
                "chart_type": "bar"
            })
        
        # Log analysis section
        if "log_analysis" in report:
            sections.append({
                "title": "Log Analysis",
                "type": "logs",
                "data": report["log_analysis"],
                "chart_type": "line"
            })
        
        # Metrics section
        if "metrics_overview" in report:
            sections.append({
                "title": "System Metrics",
                "type": "metrics",
                "data": report["metrics_overview"],
                "chart_type": "gauge"
            })
        
        return sections
    
    def _create_investigation_summary(self, investigation: Dict[str, Any], parsed_query: ParsedQuery) -> str:
        """Create investigation summary."""
        if "ip_analysis" in investigation:
            ip_data = investigation["ip_analysis"]
            ip_address = ip_data.get("ip_address", "unknown")
            risk = ip_data.get("risk_assessment", "UNKNOWN")
            log_count = ip_data.get("log_count", 0)
            alert_count = ip_data.get("alert_count", 0)
            
            summary = f"Investigation of IP address {ip_address} reveals {risk} risk level. "
            summary += f"Found {log_count} related log entries and {alert_count} alerts."
            
        elif "container_analysis" in investigation:
            container_data = investigation["container_analysis"]
            container = container_data.get("container", "unknown")
            health = container_data.get("health_status", "UNKNOWN")
            error_logs = container_data.get("error_logs", 0)
            
            summary = f"Investigation of container {container} shows {health} status. "
            summary += f"Found {error_logs} error log entries."
            
        else:
            summary = "General security investigation completed. Review findings below for details."
        
        return summary
    
    def _format_investigation_findings(self, investigation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format investigation findings."""
        findings = []
        
        for key, data in investigation.items():
            if isinstance(data, dict):
                finding = {
                    "type": key,
                    "title": key.replace("_", " ").title(),
                    "data": data,
                    "severity": self._assess_finding_severity(data)
                }
                findings.append(finding)
        
        return findings
    
    def _assess_investigation_risk(self, investigation: Dict[str, Any]) -> str:
        """Assess overall risk level from investigation."""
        risk_levels = []
        
        for data in investigation.values():
            if isinstance(data, dict):
                if "risk_assessment" in data:
                    risk_levels.append(data["risk_assessment"])
                elif "health_status" in data and data["health_status"] == "UNHEALTHY":
                    risk_levels.append("HIGH")
        
        if "HIGH" in risk_levels:
            return "HIGH"
        elif "MEDIUM" in risk_levels:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _create_investigation_timeline(self, investigation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create timeline from investigation data."""
        timeline = []
        
        # Extract events from investigation data
        for data in investigation.values():
            if isinstance(data, dict):
                if "related_logs" in data:
                    for log in data["related_logs"][:5]:  # Limit to 5 most recent
                        timeline.append({
                            "timestamp": log.get("timestamp"),
                            "type": "log",
                            "description": log.get("message", "")[:100] + "...",
                            "severity": "info"
                        })
                
                if "related_alerts" in data:
                    for alert in data["related_alerts"][:5]:
                        timeline.append({
                            "timestamp": alert.get("timestamp"),
                            "type": "alert",
                            "description": alert.get("message", "")[:100] + "...",
                            "severity": alert.get("severity", "LOW").lower()
                        })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return timeline[:10]  # Return top 10 events
    
    def _create_trends_summary(self, trends: Dict[str, Any]) -> str:
        """Create trends summary."""
        summary_parts = []
        
        if "alert_trends" in trends:
            alert_data = trends["alert_trends"]
            total = alert_data.get("total_alerts", 0)
            daily_avg = alert_data.get("daily_average", 0)
            summary_parts.append(f"{total} alerts ({daily_avg:.1f} per day)")
        
        if "docker_activity_trends" in trends:
            docker_data = trends["docker_activity_trends"]
            total = docker_data.get("total_events", 0)
            summary_parts.append(f"{total} Docker events")
        
        if "log_volume_trends" in trends:
            log_data = trends["log_volume_trends"]
            total = log_data.get("total_logs", 0)
            summary_parts.append(f"{total} log entries")
        
        if summary_parts:
            return "Trend analysis shows: " + ", ".join(summary_parts) + "."
        else:
            return "Trend analysis completed. No significant patterns detected."
    
    def _format_trends_for_charts(self, trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format trend data for chart visualization."""
        charts = []
        
        # Alert trends chart
        if "alert_trends" in trends:
            charts.append({
                "type": "line",
                "title": "Alert Trends",
                "data": trends["alert_trends"],
                "x_axis": "time",
                "y_axis": "count"
            })
        
        # Docker activity chart
        if "docker_activity_trends" in trends:
            charts.append({
                "type": "bar",
                "title": "Docker Activity",
                "data": trends["docker_activity_trends"],
                "x_axis": "time",
                "y_axis": "events"
            })
        
        # Metrics trends chart
        if "metrics_trends" in trends:
            charts.append({
                "type": "area",
                "title": "System Metrics",
                "data": trends["metrics_trends"],
                "x_axis": "time",
                "y_axis": "percentage"
            })
        
        return charts
    
    def _generate_trend_insights(self, trends: Dict[str, Any]) -> List[str]:
        """Generate insights from trend data."""
        insights = []
        
        # Alert trend insights
        if "alert_trends" in trends:
            alert_data = trends["alert_trends"]
            daily_avg = alert_data.get("daily_average", 0)
            
            if daily_avg > 10:
                insights.append("High alert volume detected - consider reviewing alert thresholds")
            elif daily_avg < 1:
                insights.append("Low alert activity - system appears stable")
        
        # Docker trend insights
        if "docker_activity_trends" in trends:
            docker_data = trends["docker_activity_trends"]
            total_events = docker_data.get("total_events", 0)
            
            if total_events > 1000:
                insights.append("High container activity - monitor for performance impacts")
        
        # Metrics insights
        if "metrics_trends" in trends:
            metrics_data = trends["metrics_trends"]
            avg_cpu = metrics_data.get("average_cpu", 0)
            avg_memory = metrics_data.get("average_memory", 0)
            
            if avg_cpu > 80:
                insights.append("High CPU usage detected - consider scaling resources")
            if avg_memory > 85:
                insights.append("High memory usage detected - monitor for memory leaks")
        
        if not insights:
            insights.append("All trends appear normal - continue monitoring")
        
        return insights
    
    def _assess_finding_severity(self, data: Dict[str, Any]) -> str:
        """Assess severity of investigation finding."""
        if "risk_assessment" in data:
            return data["risk_assessment"]
        elif "health_status" in data:
            return "HIGH" if data["health_status"] == "UNHEALTHY" else "LOW"
        elif "alert_count" in data:
            alert_count = data["alert_count"]
            return "HIGH" if alert_count > 5 else "MEDIUM" if alert_count > 0 else "LOW"
        else:
            return "LOW"
    
    def _calculate_processing_time(self) -> float:
        """Calculate processing time (mock implementation)."""
        import random
        return round(random.uniform(50, 200), 2)
    
    def _format_error_response(self, error: str, query: str) -> Dict[str, Any]:
        """Format error response."""
        return {
            "type": "error",
            "error": error,
            "original_query": query,
            "suggestions": [
                "Try rephrasing your query",
                "Check if the time range is valid",
                "Ensure IP addresses are properly formatted",
                "Use specific container or service names"
            ],
            "examples": self.get_query_suggestions()[:3]
        }


# Global system instance
_nlp_system = None

def get_nlp_system() -> NLPQuerySystem:
    """Get the global NLP query system instance."""
    global _nlp_system
    if _nlp_system is None:
        _nlp_system = NLPQuerySystem()
    return _nlp_system

def process_natural_query(query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a natural language query and return formatted results.
    
    Args:
        query: The natural language query string
        user_context: Optional user context for personalization
        
    Returns:
        Dict containing formatted query results
    """
    system = get_nlp_system()
    return system.process_query(query, user_context)