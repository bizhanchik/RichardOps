"""
NLP Query API Endpoints

This module provides REST API endpoints for the NLP query system,
allowing users to interact with the natural language security query
capabilities through HTTP requests.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import time

from services.simple_nlp_system import get_simple_nlp_system
from services.improved_intent_classifier import reset_improved_classifier
from services.nlp_query_parser import reset_nlp_parser


# Create FastAPI router for NLP endpoints
nlp_router = APIRouter(prefix="/api/nlp", tags=["nlp"])


# Pydantic models for request/response
class NLPQueryRequest(BaseModel):
    """Request model for NLP query processing."""
    query: str = Field(..., description="Natural language query to process")
    user_context: Optional[Dict[str, Any]] = Field(default={}, description="Optional user context")


class NLPQueryResponse(BaseModel):
    """Response model for NLP query processing."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None


class SuggestionsResponse(BaseModel):
    """Response model for query suggestions."""
    success: bool
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Response model for system status."""
    success: bool
    status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExamplesResponse(BaseModel):
    """Response model for example queries."""
    success: bool
    examples: Optional[Dict[str, List[str]]] = None
    error: Optional[str] = None


class TestRequest(BaseModel):
    """Request model for system testing."""
    test_type: str = Field(default="basic", description="Type of test to run: basic, advanced, or all")


class TestResponse(BaseModel):
    """Response model for system testing."""
    success: bool
    test_results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    success: bool
    health: Optional[str] = None
    checks: Optional[Dict[str, str]] = None
    timestamp: Optional[float] = None
    error: Optional[str] = None


@nlp_router.post("/query", response_model=NLPQueryResponse)
async def process_nlp_query(request: NLPQueryRequest) -> NLPQueryResponse:
    """
    Process a natural language query.
    
    Args:
        request: NLP query request containing the query and optional user context
        
    Returns:
        NLPQueryResponse with processing results
    """
    try:
        # Process the query using simple mapping system
        start_time = time.time()
        nlp_system = get_simple_nlp_system()
        result = nlp_system.process_query(request.query)
        processing_time = (time.time() - start_time) * 1000
        
        return NLPQueryResponse(
            success=True,
            result=result,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        return NLPQueryResponse(
            success=False,
            error=str(e)
        )


@nlp_router.get("/suggestions", response_model=SuggestionsResponse)
async def get_query_suggestions(
    partial_query: Optional[str] = Query(default="", description="Optional partial query for filtering suggestions")
) -> SuggestionsResponse:
    """
    Get query suggestions for autocomplete.
    
    Args:
        partial_query: Optional partial query for filtering suggestions
        
    Returns:
        SuggestionsResponse with query suggestions
    """
    try:
        nlp_system = get_simple_nlp_system()
        # Simple system doesn't filter by partial query, just returns all suggestions
        suggestions = nlp_system._get_query_suggestions()
        
        return SuggestionsResponse(
            success=True,
            suggestions=suggestions
        )
        
    except Exception as e:
        return SuggestionsResponse(
            success=False,
            error=str(e)
        )


@nlp_router.get("/status", response_model=StatusResponse)
async def get_system_status() -> StatusResponse:
    """
    Get the status of the NLP query system.
    
    Returns:
        StatusResponse with system status information
    """
    try:
        nlp_system = get_simple_nlp_system()
        status = nlp_system.get_system_status()
        
        return StatusResponse(
            success=True,
            status=status
        )
        
    except Exception as e:
        return StatusResponse(
            success=False,
            error=str(e)
        )


@nlp_router.get("/examples", response_model=ExamplesResponse)
async def get_example_queries() -> ExamplesResponse:
    """
    Get example queries for different use cases.
    
    Returns:
        ExamplesResponse with categorized example queries
    """
    try:
        examples = {
            "query_processing": [
                "Show me all failed logins in the last hour",
                "Find ERROR logs from container webapp",
                "Show critical alerts from today",
                "Display all authentication failures",
                "Show me database connection errors"
            ],
            "report_generation": [
                "Generate weekly security summary",
                "Create monthly Docker events report",
                "Generate security incident report for last month",
                "Show system performance summary for this week"
            ],
            "investigation": [
                "What assets did IP address 192.168.1.100 target?",
                "Investigate suspicious activity from 10.0.0.50",
                "What happened with container nginx today?",
                "Analyze failed login attempts from external IPs",
                "Investigate database connection failures"
            ],
            "trend_analysis": [
                "Analyze login trends this week",
                "Show container resource usage trends",
                "Analyze alert patterns over the last month",
                "Show database performance trends"
            ]
        }
        
        return ExamplesResponse(
            success=True,
            examples=examples
        )
        
    except Exception as e:
        return ExamplesResponse(
            success=False,
            error=str(e)
        )


@nlp_router.post("/test", response_model=TestResponse)
async def test_nlp_system(request: TestRequest) -> TestResponse:
    """
    Test the NLP system with predefined queries.
    
    Args:
        request: Test request specifying the type of test to run
        
    Returns:
        TestResponse with test results
    """
    try:
        nlp_system = get_nlp_system()
        
        # Define test queries
        basic_queries = [
            "Show me all failed logins in the last hour",
            "Generate weekly security summary",
            "What assets did IP address 192.168.1.100 target?"
        ]
        
        advanced_queries = [
            "Show all unresolved high severity alerts",
            "Analyze login trends this week",
            "Find all containers that had failures yesterday",
            "Generate security incident report for last month"
        ]
        
        # Select queries based on test type
        if request.test_type == 'basic':
            test_queries = basic_queries
        elif request.test_type == 'advanced':
            test_queries = advanced_queries
        else:  # 'all'
            test_queries = basic_queries + advanced_queries
        
        # Run tests
        test_results = []
        for query in test_queries:
            start_time = time.time()
            try:
                result = nlp_system.process_query(query)
                processing_time = (time.time() - start_time) * 1000
                
                test_results.append({
                    "query": query,
                    "success": True,
                    "processing_time_ms": round(processing_time, 2),
                    "intent": result.get("metadata", {}).get("intent", "unknown"),
                    "confidence": result.get("metadata", {}).get("confidence", 0.0),
                    "results_count": len(result.get("results", []))
                })
                
            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                test_results.append({
                    "query": query,
                    "success": False,
                    "processing_time_ms": round(processing_time, 2),
                    "error": str(e)
                })
        
        return TestResponse(
            success=True,
            test_results=test_results
        )
        
    except Exception as e:
        return TestResponse(
            success=False,
            error=str(e)
        )


@nlp_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for the NLP system.
    
    Returns:
        HealthResponse with health status and checks
    """
    try:
        nlp_system = get_nlp_system()
        
        # Perform health checks
        checks = {}
        overall_health = "healthy"
        
        # Test basic query processing
        try:
            test_result = nlp_system.process_query("test query")
            checks["query_processing"] = "healthy"
        except Exception as e:
            checks["query_processing"] = f"unhealthy: {str(e)}"
            overall_health = "degraded"
        
        # Test system status
        try:
            status = nlp_system.get_system_status()
            if status.get('status') == 'operational':
                checks["system_status"] = "healthy"
            else:
                checks["system_status"] = "degraded"
                overall_health = "degraded"
        except Exception as e:
            checks["system_status"] = f"unhealthy: {str(e)}"
            overall_health = "unhealthy"
        
        # Test suggestions
        try:
            suggestions = nlp_system.get_query_suggestions()
            if suggestions:
                checks["suggestions"] = "healthy"
            else:
                checks["suggestions"] = "degraded"
        except Exception as e:
            checks["suggestions"] = f"unhealthy: {str(e)}"
            overall_health = "degraded"
        
        return HealthResponse(
            success=True,
            health=overall_health,
            checks=checks,
            timestamp=time.time()
        )
        
    except Exception as e:
        return HealthResponse(
            success=False,
            health="unhealthy",
            error=str(e),
            timestamp=time.time()
        )


class ResetResponse(BaseModel):
    """Response model for cache reset."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


@nlp_router.post("/reset", response_model=ResetResponse)
async def reset_nlp_cache() -> ResetResponse:
    """
    Reset the NLP system cache to pick up new training examples.
    
    This endpoint clears all cached classifier instances, forcing them
    to reload with the latest training data.
    
    Returns:
        ResetResponse indicating success or failure
    """
    try:
        # Reset the improved intent classifier cache
        reset_improved_classifier()
        
        # Reset the NLP parser cache
        reset_nlp_parser()
        
        return ResetResponse(
            success=True,
            message="NLP cache reset successfully. New training examples will be loaded on next query."
        )
        
    except Exception as e:
        return ResetResponse(
            success=False,
            error=f"Failed to reset NLP cache: {str(e)}"
        )