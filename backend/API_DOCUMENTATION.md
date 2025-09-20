# RichardOps Backend API Documentation

## Overview

This document provides comprehensive API documentation for the RichardOps monitoring and security system backend. The API includes endpoints for monitoring data ingestion, alerts management, and natural language processing (NLP) capabilities.

**Base URL:** `http://localhost:8000`

## Table of Contents

1. [Authentication](#authentication)
2. [Core Monitoring Endpoints](#core-monitoring-endpoints)
3. [NLP Endpoints](#nlp-endpoints)
4. [System Health Endpoints](#system-health-endpoints)
5. [Error Handling](#error-handling)
6. [Request/Response Examples](#request-response-examples)

---

## Authentication

Most endpoints require HMAC signature authentication for security:

- **Header:** `X-Agent-Signature`
- **Header:** `X-Agent-Timestamp`
- **Secret:** Set via `INGEST_SECRET` environment variable

---

## Core Monitoring Endpoints

### 1. Ingest Monitoring Data

**Endpoint:** `POST /ingest`

**Description:** Ingests monitoring data from Docker containers, metrics, and events.

**Headers:**
- `X-Agent-Signature` (required): HMAC signature
- `X-Agent-Timestamp` (required): Unix timestamp
- `Content-Type: application/json`

**Request Body:**
```json
{
  "container_logs": [
    {
      "container": "webapp",
      "message": "Application started successfully",
      "timestamp": "2024-01-20T10:30:00Z",
      "level": "INFO"
    }
  ],
  "docker_events": [
    {
      "type": "container",
      "action": "start",
      "container": "webapp",
      "timestamp": "2024-01-20T10:30:00Z"
    }
  ],
  "metrics": [
    {
      "container": "webapp",
      "cpu_usage": 45.2,
      "memory_usage": 512.5,
      "timestamp": "2024-01-20T10:30:00Z"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Data ingested successfully",
  "processed": {
    "container_logs": 1,
    "docker_events": 1,
    "metrics": 1
  },
  "alerts_generated": 0
}
```

### 2. Get Current Alerts

**Endpoint:** `GET /alerts`

**Description:** Retrieves current alerts with optional filtering.

**Query Parameters:**
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `status` (optional): Filter by status (active, resolved)
- `limit` (optional): Limit number of results (default: 100)

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "severity": "high",
      "message": "High CPU usage detected",
      "container": "webapp",
      "timestamp": "2024-01-20T10:30:00Z",
      "status": "active"
    }
  ],
  "total_count": 1,
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 0,
    "low": 0
  }
}
```

---

## NLP Endpoints

### Basic NLP Endpoints

#### 1. Test NLP Embedding

**Endpoint:** `POST /nlp/test`

**Description:** Test endpoint for generating text embeddings.

**Request Body:**
```json
{
  "text": "Show me all error logs from the last hour"
}
```

**Response:**
```json
{
  "text": "Show me all error logs from the last hour",
  "embedding": [0.1234, -0.5678, 0.9012, ...]
}
```

#### 2. Process Text

**Endpoint:** `POST /nlp/process`

**Description:** Simple text processing for testing NLP functionality.

**Request Body:**
```json
{
  "text": "Hello, are you working?"
}
```

**Response:**
```json
{
  "input_text": "Hello, are you working?",
  "output_text": "Hello! I received your message: 'Hello, are you working?' and I'm processing it through the NLP pipeline.",
  "status": "success"
}
```

### Advanced NLP Query System

#### 1. Process Natural Language Query

**Endpoint:** `POST /api/nlp/query`

**Description:** Process natural language security queries and return structured results.

**Request Body:**
```json
{
  "query": "Show me all failed logins in the last hour",
  "user_context": {
    "user_id": "admin",
    "timezone": "UTC"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "intent": "search_logs",
    "data": [
      {
        "container": "auth-service",
        "message": "Failed login attempt for user admin",
        "timestamp": "2024-01-20T10:25:00Z",
        "level": "ERROR"
      }
    ],
    "summary": "Found 1 failed login attempts in the last hour",
    "categories": {
      "ERROR": 1,
      "WARN": 0,
      "INFO": 0
    }
  },
  "processing_time_ms": 45.67,
  "metadata": {
    "query_processed_at": "2024-01-20T10:30:00Z",
    "confidence": 0.95,
    "intent": "search_logs",
    "entities_found": 2
  }
}
```

**Supported Query Types:**
- **Search Logs:** "Show me ERROR logs from container webapp"
- **Show Alerts:** "Display all critical alerts from today"
- **Generate Reports:** "Create weekly security summary"
- **Investigate:** "Investigate suspicious activity in the last 24 hours"
- **Analyze Trends:** "Show login trends this week"

#### 2. Get Query Suggestions

**Endpoint:** `GET /api/nlp/suggestions`

**Description:** Get query suggestions for autocomplete functionality.

**Query Parameters:**
- `partial_query` (optional): Partial query for filtering suggestions

**Response:**
```json
{
  "success": true,
  "suggestions": [
    "Show me all failed logins in the last hour",
    "Generate weekly security summary",
    "What assets did IP address 192.168.1.100 target?",
    "Show critical alerts from today",
    "Find all ERROR logs from container webapp"
  ]
}
```

#### 3. Get System Status

**Endpoint:** `GET /api/nlp/status`

**Description:** Get the status of the NLP query system.

**Response:**
```json
{
  "success": true,
  "status": {
    "nlp_system": "operational",
    "query_parser": "ready",
    "database": "connected",
    "last_query_processed": "2024-01-20T10:29:45Z",
    "total_queries_processed": 1247,
    "average_processing_time_ms": 52.3,
    "system_health": {
      "parser": "healthy",
      "translator": "healthy",
      "database": "healthy"
    }
  }
}
```

#### 4. Get Example Queries

**Endpoint:** `GET /api/nlp/examples`

**Description:** Get categorized example queries for different use cases.

**Response:**
```json
{
  "success": true,
  "examples": {
    "log_search": [
      "Show me all ERROR logs from the last hour",
      "Find logs containing 'database connection failed'",
      "Display logs from container nginx today"
    ],
    "security_analysis": [
      "Show failed login attempts this week",
      "Find suspicious IP addresses",
      "Investigate authentication failures"
    ],
    "reporting": [
      "Generate monthly security report",
      "Create Docker events summary for last week",
      "Show system performance trends"
    ],
    "alerts": [
      "Display all critical alerts",
      "Show unresolved high severity alerts",
      "Find alerts from container webapp"
    ]
  }
}
```

#### 5. Test NLP System

**Endpoint:** `POST /api/nlp/test`

**Description:** Run comprehensive tests on the NLP system.

**Request Body:**
```json
{
  "test_type": "basic"
}
```

**Response:**
```json
{
  "success": true,
  "test_results": [
    {
      "test_name": "Query Parser Test",
      "status": "passed",
      "execution_time_ms": 12.5,
      "details": "Successfully parsed 10 test queries"
    },
    {
      "test_name": "Database Connection Test",
      "status": "passed",
      "execution_time_ms": 8.2,
      "details": "Database connection successful"
    }
  ]
}
```

#### 6. NLP Health Check

**Endpoint:** `GET /api/nlp/health`

**Description:** Health check specifically for NLP components.

**Response:**
```json
{
  "success": true,
  "health": "healthy",
  "checks": {
    "nlp_model": "operational",
    "query_parser": "operational",
    "query_translator": "operational",
    "database_connection": "operational"
  },
  "timestamp": 1705747800.123
}
```

---

## System Health Endpoints

### 1. Health Check

**Endpoint:** `GET /healthz`

**Description:** Basic health check for the entire system.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "uptime_seconds": 3600
}
```

### 2. Readiness Check

**Endpoint:** `GET /readiness`

**Description:** Readiness check to determine if the system is ready to serve requests.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "connected",
    "nlp_system": "initialized",
    "rules_engine": "loaded"
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 3. Root Endpoint

**Endpoint:** `GET /`

**Description:** Basic API information.

**Response:**
```json
{
  "message": "RichardOps Monitoring Backend API",
  "version": "1.0.0",
  "status": "operational"
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-20T10:30:00Z",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common HTTP Status Codes

- **200 OK:** Request successful
- **400 Bad Request:** Invalid request data
- **401 Unauthorized:** Authentication failed
- **403 Forbidden:** Access denied
- **404 Not Found:** Endpoint not found
- **422 Unprocessable Entity:** Validation error
- **500 Internal Server Error:** Server error

### NLP-Specific Error Codes

- `NLP_PARSE_ERROR`: Failed to parse natural language query
- `NLP_TRANSLATION_ERROR`: Failed to translate query to database query
- `NLP_EXECUTION_ERROR`: Failed to execute translated query
- `NLP_SYSTEM_UNAVAILABLE`: NLP system is not available

---

## Request/Response Examples

### Example 1: Natural Language Security Query

**Request:**
```bash
curl -X POST "http://localhost:8000/api/nlp/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all critical alerts from the last 24 hours",
    "user_context": {"user_id": "security_analyst"}
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "intent": "show_alerts",
    "data": [
      {
        "id": 123,
        "severity": "critical",
        "message": "Multiple failed login attempts detected",
        "container": "auth-service",
        "timestamp": "2024-01-20T09:15:00Z",
        "status": "active"
      }
    ],
    "summary": "Found 1 critical alerts in the last 24 hours",
    "priority_breakdown": {
      "critical": 1,
      "high": 0,
      "medium": 0,
      "low": 0
    }
  },
  "processing_time_ms": 67.89
}
```

### Example 2: Log Search Query

**Request:**
```bash
curl -X POST "http://localhost:8000/api/nlp/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all database connection errors from webapp container today"
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "intent": "search_logs",
    "data": [
      {
        "container": "webapp",
        "message": "Database connection failed: timeout after 30s",
        "timestamp": "2024-01-20T08:45:00Z",
        "level": "ERROR"
      }
    ],
    "summary": "Found 1 database connection errors from webapp container today",
    "categories": {
      "ERROR": 1,
      "WARN": 0,
      "INFO": 0
    }
  },
  "processing_time_ms": 34.12
}
```

---

## Frontend Integration Notes

### 1. Authentication Setup

For frontend applications, implement HMAC signature generation:

```javascript
// Example HMAC signature generation
const crypto = require('crypto');

function generateSignature(timestamp, body, secret) {
  const message = timestamp + body;
  return crypto.createHmac('sha256', secret).update(message).digest('hex');
}
```

### 2. NLP Query Interface

Recommended frontend implementation for NLP queries:

```javascript
// Example NLP query function
async function queryNLP(query, userContext = {}) {
  const response = await fetch('/api/nlp/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      user_context: userContext
    })
  });
  
  return await response.json();
}
```

### 3. Autocomplete Integration

Use the suggestions endpoint for query autocomplete:

```javascript
// Example autocomplete function
async function getQuerySuggestions(partialQuery = '') {
  const response = await fetch(`/api/nlp/suggestions?partial_query=${encodeURIComponent(partialQuery)}`);
  const data = await response.json();
  return data.suggestions || [];
}
```

### 4. Real-time Updates

Consider implementing WebSocket connections for real-time alerts and log updates (WebSocket endpoints to be implemented in future versions).

---

## Rate Limiting

- **NLP Queries:** 100 requests per minute per IP
- **Monitoring Data Ingestion:** 1000 requests per minute per authenticated source
- **Health Checks:** No rate limiting

---

## API Versioning

Current API version: **v1.0.0**

Future versions will be accessible via `/api/v2/` prefix when available.

---

## Support

For API support and questions:
- Check the `/docs` endpoint for interactive API documentation (development mode only)
- Review logs in the `logs/` directory for debugging
- Monitor system health via `/healthz` and `/readiness` endpoints