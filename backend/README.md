# Monitoring Data Ingestion Backend

A FastAPI backend service designed to receive monitoring data from Go agents. This service provides endpoints for data ingestion, health checks, and logging capabilities.

## Features

- **Data Ingestion**: Receives JSON payloads from Go monitoring agents
- **Data Validation**: Uses Pydantic models to validate incoming data
- **Logging**: Pretty-prints data to console and logs to files
- **Health Checks**: Built-in health endpoint for monitoring
- **Docker Support**: Containerized deployment with Docker Compose
- **Persistent Logs**: Volume mounting for log persistence

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Docker Compose setup
├── README.md           # This file
└── logs/               # Log files (created automatically)
    └── ingest.log      # Structured log output
```

## API Endpoints

### POST /ingest
Receives monitoring data from Go agents.

**Request Body**: JSON payload matching the Go agent's `Payload` struct
**Response**: Success message with timestamp

### GET /healthz
Health check endpoint.

**Response**: 
```json
{
  "status": "ok",
  "timestamp": "2024-01-20T12:34:56.789Z",
  "service": "monitoring-backend"
}
```

### GET /
Root endpoint with API information.

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Start the service**:
   ```bash
   cd backend
   docker-compose up --build
   ```

2. **The service will be available at**: `http://localhost:8000`

3. **View logs**:
   ```bash
   docker-compose logs -f monitoring-backend
   ```

4. **Stop the service**:
   ```bash
   docker-compose down
   ```

### Option 2: Local Development

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **The service will be available at**: `http://localhost:8000`

## Testing the API

### Health Check
```bash
curl http://localhost:8000/healthz
```

### Send Monitoring Data
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "host": "server1",
    "server_id": "srv-001",
    "env": "production",
    "owner_team": "devops",
    "timestamp": "2024-01-20T12:34:56Z",
    "metrics": {
      "cpu_usage": 42.5,
      "memory_usage": 70.1,
      "disk_usage": 55.3,
      "network_rx_bytes_per_sec": 12345,
      "network_tx_bytes_per_sec": 6789,
      "tcp_connections": 12
    },
    "docker_events": [
      {
        "type": "container",
        "action": "start",
        "container": "web-app",
        "image": "nginx:latest",
        "timestamp": "2024-01-20T12:34:56Z"
      }
    ],
    "logs": [
      {
        "container": "web-app",
        "message": "Server started successfully",
        "timestamp": "2024-01-20T12:34:56Z"
      }
    ],
    "local_alerts": ["CPU_SPIKE"],
    "score": 0.7
  }'
```

### Minimal Test Payload
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "host": "test-server",
    "timestamp": "2024-01-20T12:34:56Z",
    "metrics": {
      "cpu_usage": 25.0,
      "memory_usage": 60.0,
      "disk_usage": 45.0,
      "network_rx_bytes_per_sec": 1000,
      "network_tx_bytes_per_sec": 500,
      "tcp_connections": 5
    },
    "docker_events": [],
    "logs": [],
    "local_alerts": [],
    "score": 0.5
  }'
```

## Data Models

The backend uses Pydantic models that exactly mirror the Go agent's struct definitions:

- **Payload**: Main monitoring data structure
- **SystemMetrics**: CPU, memory, disk, and network metrics
- **DockerEvent**: Docker container events
- **LogEntry**: Container log entries

All models support extra fields (`extra="allow"`) to accommodate future extensions.

## Logging

The service provides two types of logging:

1. **Console Output**: Pretty-printed, human-readable format
2. **File Logging**: Structured JSON format in `logs/ingest.log`

### Console Output Example
```
================================================================================
📊 MONITORING DATA RECEIVED - 2024-01-20T12:34:56.789Z
================================================================================
🖥️  Host: server1
🆔 Server ID: srv-001
🌍 Environment: production
👥 Owner Team: devops
⏰ Timestamp: 2024-01-20T12:34:56Z
📈 Score: 0.7

📊 SYSTEM METRICS:
  CPU Usage: 42.5%
  Memory Usage: 70.1%
  Disk Usage: 55.3%
  Network RX: 12,345 bytes/sec
  Network TX: 6,789 bytes/sec
  TCP Connections: 12

🚨 LOCAL ALERTS (1):
  ⚠️  CPU_SPIKE
================================================================================
```

## Docker Configuration

### Dockerfile Features
- Python 3.11 slim base image
- Non-root user for security
- Health check endpoint
- Optimized layer caching

### Docker Compose Features
- Port mapping (8000:8000)
- Volume mounting for persistent logs
- Health checks
- Automatic restart policy
- Custom network

## Development

### Adding New Endpoints
1. Add new endpoint functions to `main.py`
2. Create corresponding Pydantic models in `models.py` if needed
3. Update this README with endpoint documentation

### Modifying Data Models
1. Update models in `models.py`
2. Ensure compatibility with Go agent struct definitions
3. Test with sample payloads

### Environment Variables
The service can be configured with environment variables:
- `PYTHONPATH`: Python module path (set to `/app` in container)

## Production Considerations

### Security
- No authentication currently implemented (ready for future auth headers)
- Runs as non-root user in container
- Input validation via Pydantic models

### Monitoring
- Health check endpoint at `/healthz`
- Structured logging for monitoring integration
- Docker health checks configured

### Scaling
- Stateless design allows horizontal scaling
- Persistent logs via volume mounts
- Ready for load balancer integration

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Change port in docker-compose.yml or stop conflicting service
   docker-compose down
   lsof -ti:8000 | xargs kill -9
   ```

2. **Permission issues with logs**:
   ```bash
   # Ensure logs directory is writable
   mkdir -p logs
   chmod 755 logs
   ```

3. **Container build fails**:
   ```bash
   # Clean build
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

### Viewing Logs
```bash
# Docker logs
docker-compose logs -f monitoring-backend

# File logs
tail -f logs/ingest.log

# Pretty print JSON logs
tail -f logs/ingest.log | jq .
```

## Integration with Go Agent

The backend is designed to work seamlessly with the Go monitoring agent. Ensure your Go agent is configured to send POST requests to:

```
http://your-backend-host:8000/ingest
```

The Go agent's `Payload` struct should match the Pydantic models defined in `models.py`.

## License

This project is part of the RichardOps monitoring system.