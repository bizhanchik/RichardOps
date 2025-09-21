# Analytics Features Documentation

## Overview

The backend now includes comprehensive analytics capabilities for generating summaries, reports, and detecting anomalies in your monitoring system. These features help you understand system performance, identify issues, and get actionable insights.

## 🚀 New Features

### 1. Summary and Reporting Service
- **System Summaries**: Comprehensive overviews of system metrics, alerts, events, logs, and containers
- **Performance Reports**: Detailed analysis with trends, utilization patterns, and recommendations
- **Multiple Time Periods**: Support for 1h, 6h, 12h, 24h, 7d, and 30d periods

### 2. Anomaly Detection Service
- **Metric Spikes**: Detects sudden increases in CPU, memory, and disk usage
- **IP Request Anomalies**: Identifies suspicious request patterns from single IPs
- **Error Rate Detection**: Monitors container error rates
- **Event Anomalies**: Detects unusual Docker event patterns
- **Container Issues**: Identifies restart loops and performance problems

### 3. Analytics API Endpoints
- RESTful API endpoints for accessing all analytics features
- Comprehensive response models with structured data
- Filtering and customization options

## 📊 API Endpoints

### System Summary
```
GET /analytics/summary?period=24h
```
Get a comprehensive system summary for the specified time period.

**Parameters:**
- `period` (optional): Time period - `1h`, `6h`, `12h`, `24h`, `7d`, `30d` (default: `24h`)

**Response:**
```json
{
  "period": {
    "name": "Last 24 Hours",
    "hours": 24
  },
  "metrics": {
    "cpu_usage": {"avg": 45.2, "max": 78.1, "min": 12.3},
    "memory_usage": {"avg": 62.1, "max": 89.5, "min": 34.2},
    "disk_usage": {"avg": 23.4, "max": 45.6, "min": 18.9}
  },
  "alerts": {
    "total": 15,
    "critical": 3,
    "warning": 8,
    "info": 4
  },
  "events": {
    "total": 156,
    "errors": 2,
    "warnings": 12
  },
  "logs": {
    "total": 10240,
    "errors": 45,
    "warnings": 123
  },
  "containers": {
    "total": 8,
    "running": 6,
    "stopped": 2
  },
  "generated_at": "2025-01-21T10:30:00Z"
}
```

### Performance Report
```
GET /analytics/performance-report?period=24h
```
Get a detailed performance analysis report.

**Parameters:**
- `period` (optional): Time period - `1h`, `6h`, `12h`, `24h`, `7d`, `30d` (default: `24h`)

**Response:**
```json
{
  "period": {
    "name": "Last 24 Hours",
    "hours": 24
  },
  "performance_analysis": {
    "cpu_trends": "Stable with occasional spikes",
    "memory_trends": "Gradually increasing",
    "disk_trends": "Stable"
  },
  "utilization_patterns": {
    "peak_hours": ["09:00-11:00", "14:00-16:00"],
    "low_usage_periods": ["02:00-06:00"]
  },
  "recommendations": [
    "Consider scaling up during peak hours",
    "Monitor memory usage trends",
    "Optimize disk I/O operations"
  ],
  "generated_at": "2025-01-21T10:30:00Z"
}
```

### Anomaly Detection
```
GET /analytics/anomalies?lookback_hours=1&severity_filter=HIGH
```
Detect anomalies in the system.

**Parameters:**
- `lookback_hours` (optional): Hours to look back (1-168, default: 1)
- `severity_filter` (optional): Filter by severity - `LOW`, `MEDIUM`, `HIGH`
- `type_filter` (optional): Filter by anomaly type

**Response:**
```json
[
  {
    "type": "cpu_spike",
    "severity": "HIGH",
    "timestamp": "2025-01-21T10:25:00Z",
    "description": "CPU usage spiked to 95% (baseline: 45%)",
    "details": {
      "current_usage": 95.2,
      "baseline": 45.0,
      "spike_percentage": 111.1
    },
    "affected_resource": "container_web_1",
    "confidence": 0.92
  }
]
```

### Anomaly Summary
```
GET /analytics/anomalies/summary?hours=24
```
Get a summary of anomalies detected.

**Parameters:**
- `hours` (optional): Hours to look back (1-720, default: 24)

**Response:**
```json
{
  "total_anomalies": 12,
  "by_type": {
    "cpu_spike": 4,
    "memory_spike": 2,
    "ip_request_spike": 3,
    "high_error_rate": 2,
    "container_restart_loop": 1
  },
  "by_severity": {
    "HIGH": 3,
    "MEDIUM": 6,
    "LOW": 3
  },
  "affected_resources": [
    "container_web_1",
    "container_db_1",
    "container_cache_1"
  ],
  "recent_anomalies": [...],
  "generated_at": "2025-01-21T10:30:00Z"
}
```

### Anomaly Types Information
```
GET /analytics/anomalies/types
```
Get information about available anomaly types and their descriptions.

### Health Check
```
GET /analytics/health
```
Health check endpoint for analytics services.

### Metrics Trends
```
GET /analytics/metrics/trends?period=24h&metric_type=cpu
```
Get detailed metrics trends analysis.

**Parameters:**
- `period` (optional): Time period (default: `24h`)
- `metric_type` (optional): Specific metric - `cpu`, `memory`, `disk`

### Container Analysis
```
GET /analytics/containers/analysis?period=24h
```
Get detailed container analysis including performance and anomalies.

## 🔍 Anomaly Types

### Metric Anomalies
- **CPU Spike**: Sudden increase in CPU usage (>30% from baseline)
- **Memory Spike**: Sudden increase in memory usage (>25% from baseline)
- **Disk Spike**: Sudden increase in disk usage (>20% from baseline)

### Request Anomalies
- **IP Request Spike**: Too many requests from a single IP (>100 requests/hour)

### Container Anomalies
- **High Error Rate**: High error rate in container logs (>10%)
- **Container Restart Loop**: Container restarting frequently (>5 restarts)

### System Anomalies
- **High Event Volume**: High volume of Docker events (>100 events)
- **Connection Spike**: Sudden increase in TCP connections (>500 new connections)

## 🎯 Severity Levels

- **LOW**: Minor issues that should be monitored
- **MEDIUM**: Moderate issues that may require attention
- **HIGH**: Critical issues that require immediate attention

## 🛠️ Implementation Details

### Services
- **SummaryService** (`services/summary_service.py`): Handles system summaries and performance reports
- **AnomalyDetectionService** (`services/anomaly_detection.py`): Handles anomaly detection and analysis

### API Endpoints
- **Analytics Router** (`api/analytics_endpoints.py`): RESTful API endpoints for all analytics features

### Integration
The analytics services are integrated into the main FastAPI application and can be accessed through the `/analytics` prefix.

## 🚀 Usage Examples

### Get System Summary
```bash
curl "http://localhost:8000/analytics/summary?period=24h"
```

### Detect Recent Anomalies
```bash
curl "http://localhost:8000/analytics/anomalies?lookback_hours=6&severity_filter=HIGH"
```

### Get Performance Report
```bash
curl "http://localhost:8000/analytics/performance-report?period=7d"
```

### Monitor Container Health
```bash
curl "http://localhost:8000/analytics/containers/analysis?period=12h"
```

## 📈 Benefits

1. **Proactive Monitoring**: Detect issues before they become critical
2. **Performance Insights**: Understand system behavior and trends
3. **Automated Analysis**: Reduce manual monitoring overhead
4. **Actionable Alerts**: Get specific recommendations for improvements
5. **Historical Analysis**: Track performance over different time periods
6. **Resource Optimization**: Identify underutilized or overloaded resources

## 🔧 Configuration

Anomaly detection thresholds can be customized in the `AnomalyThresholds` class:

```python
@dataclass
class AnomalyThresholds:
    cpu_spike_threshold: float = 30.0  # % increase from baseline
    memory_spike_threshold: float = 25.0  # % increase from baseline
    disk_spike_threshold: float = 20.0  # % increase from baseline
    ip_request_threshold: int = 100  # requests per hour from single IP
    error_rate_threshold: float = 10.0  # % error rate
    event_volume_threshold: int = 100  # events per period
    container_restart_threshold: int = 5  # restarts per period
    connection_spike_threshold: int = 500  # new connections threshold
```

## 🧪 Testing

Run the test suite to verify all analytics features:

```bash
python test_analytics_services.py
```

This will test:
- Service functionality
- API endpoint imports
- Response model structures
- Service integration

## 📝 Notes

- All timestamps are in UTC format
- The services require a database connection for full functionality
- Anomaly detection uses statistical analysis to identify unusual patterns
- Performance reports include actionable recommendations
- All endpoints support CORS for frontend integration