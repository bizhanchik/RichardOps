# Go Monitoring Agent v2.0

A comprehensive Go-based security monitoring agent that collects system metrics, monitors Docker events and logs, detects security threats, and sends data to a remote server with enhanced HMAC authentication.

## Features

### Core Monitoring
- **System Metrics Collection**: CPU usage, memory usage, disk usage, network I/O rates, TCP connections
- **Docker Integration**: Real-time event monitoring and log streaming for running containers
- **Secure Communication**: Enhanced HMAC-SHA256 signed payloads with timestamp verification
- **Reliable Delivery**: HTTP client with exponential backoff retry logic and disk-persisted queuing

### 🔒 Security Features
- **Local Security Signals**: Auth log parsing with brute force detection
- **CPU Anomaly Detection**: Baseline calculation with z-score analysis
- **Container Security**: Shell execution detection in Docker containers
- **Attack Simulation**: Testing mode for security alert validation
- **Sensitive Data Masking**: Automatic redaction of passwords, tokens, and secrets

### 🛡️ Reliability Features
- **Graceful Shutdown**: SIGINT/SIGTERM handling with clean resource cleanup
- **Disk Persistence**: Failed payloads saved to disk with automatic rotation
- **Health Monitoring**: HTTP endpoints for status and metrics
- **Degraded Mode**: Continues operation when Docker is unavailable

### 📊 Enhanced Monitoring
- **Alert Scoring**: Weighted scoring system for security events
- **Metadata Enrichment**: Environment, team, and server identification
- **Log Truncation**: Configurable limits with sensitive data protection
- **Baseline Tracking**: Statistical analysis for anomaly detection

## Installation

1. Ensure you have Go 1.21+ installed
2. Clone or download the source code
3. Install dependencies:
   ```bash
   go mod tidy
   ```

## Usage

### Command Line Flags

#### Core Configuration
- `--server-url`: Server URL for sending payloads (required)
- `--secret`: Shared secret for HMAC signing (required)  
- `--interval`: Interval in seconds between payload sends (default: 30)
- `--tail-lines`: Number of initial log lines to tail per container (default: 100)

#### Security Configuration
- `--auth-window-seconds`: Window for auth failure detection (default: 300)
- `--cpu-spike-pct`: CPU percentage threshold for spike detection (default: 85.0)
- `--failed-auth-threshold`: Failed auth attempts threshold (default: 20)
- `--baseline-samples`: Number of samples for CPU baseline (default: 12)
- `--simulate-attack`: Enable attack simulation mode (default: false)

#### Metadata Configuration
- `--env`: Environment identifier (prod/stage/dev)
- `--owner-team`: Owner team name
- `--server-id`: Server identifier
- `--max-log-entries`: Maximum log entries to keep (default: 500)

### Environment Variables

All command line flags can also be set via environment variables:

#### Core Variables
- `SERVER_URL`: Server URL
- `SECRET`: Shared secret
- `INTERVAL`: Send interval in seconds
- `TAIL_LINES`: Log tail lines

#### Security Variables
- `AUTH_WINDOW_SECONDS`: Auth failure detection window
- `CPU_SPIKE_PCT`: CPU spike threshold percentage
- `FAILED_AUTH_THRESHOLD`: Failed auth attempts threshold
- `BASELINE_SAMPLES`: CPU baseline sample count
- `SIMULATE_ATTACK`: Enable attack simulation (true/false)

#### Metadata Variables
- `ENV`: Environment identifier
- `OWNER_TEAM`: Owner team name
- `SERVER_ID`: Server identifier
- `MAX_LOG_ENTRIES`: Maximum log entries

### Example Usage

```bash
# Basic usage with security monitoring
./monitoring-agent \
  --server-url https://api.example.com/ingest \
  --secret mysecretkey \
  --interval 60 \
  --env prod \
  --owner-team security \
  --server-id web-01

# Attack simulation for testing
./monitoring-agent \
  --server-url https://api.example.com/ingest \
  --secret mysecretkey \
  --simulate-attack \
  --failed-auth-threshold 5 \
  --cpu-spike-pct 80

# Environment variable configuration
export SERVER_URL="https://api.example.com/ingest"
export SECRET="mysecretkey"
export ENV="prod"
export OWNER_TEAM="payments"
export SERVER_ID="srv-123"
./monitoring-agent

# High-security configuration
./monitoring-agent \
  --server-url https://api.example.com/ingest \
  --secret mysecretkey \
  --auth-window-seconds 180 \
  --failed-auth-threshold 10 \
  --cpu-spike-pct 75 \
  --baseline-samples 20
```

## Build

```bash
go build -o monitoring-agent main.go
```

## Testing

Run the comprehensive unit test suite:

```bash
go test -v
```

Tests cover:
- CPU baseline and z-score calculation
- Attack simulation behavior
- Alert scoring system
- Sensitive data masking
- Brute force detection

## Health Endpoints

The agent provides HTTP endpoints for monitoring:

### Health Status - `GET localhost:8081/healthz`
```json
{
  "uptime_seconds": 1234,
  "last_send_ok": "2025-01-15T10:30:00Z",
  "queue_length": 2
}
```

### Metrics Status - `GET localhost:8081/metrics`
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "local_alerts": ["CPU_SPIKE", "BRUTE_FORCE:192.168.1.100"]
}
```

## Enhanced JSON Payload Structure

```json
{
  "host": "web-01",
  "server_id": "srv-123",
  "env": "prod",
  "owner_team": "payments",
  "timestamp": "2025-01-15T10:30:00Z",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "network_rx_bytes_per_sec": 1024000,
    "network_tx_bytes_per_sec": 512000,
    "tcp_connections": 150
  },
  "docker_events": [
    {
      "type": "container",
      "action": "start",
      "container": "web-server",
      "image": "nginx:latest",
      "timestamp": "2025-01-15T10:29:45Z"
    }
  ],
  "logs": [
    {
      "container": "web-server",
      "message": "Server started on port 80",
      "timestamp": "2025-01-15T10:29:46Z"
    }
  ],
  "local_alerts": [
    "CPU_SPIKE",
    "BRUTE_FORCE:192.168.1.100",
    "SHELL_IN_CONTAINER"
  ],
  "score": 1.5
}
```

## HTTP Headers

The agent includes enhanced headers with each request:

- `Content-Type: application/json`
- `X-Agent-Signature: sha256=<hmac_signature>`
- `X-Agent-Timestamp: <unix_timestamp>`

The HMAC signature is calculated using SHA256 over `timestamp + "." + payload` with the configured shared secret.

## Security Alerts

### Alert Types
- **`CPU_SPIKE`**: CPU usage above threshold with high z-score (weight: 0.4)
- **`BRUTE_FORCE:<ip>`**: Failed auth attempts above threshold (weight: 0.5)
- **`SHELL_IN_CONTAINER`**: Shell execution detected in container (weight: 0.6)
- **`HTTP_5XX_SPIKE`**: HTTP 5xx error spike detected (weight: 0.25)

### Alert Scoring
Alerts are assigned numeric scores based on severity weights. Multiple alerts are cumulative.

## File Structure

```
go_client/
├── main.go           # Main application code
├── main_test.go      # Unit tests
├── go.mod           # Go module dependencies
├── README.md        # This documentation
├── CHANGELOG.md     # Version history
└── queue/           # Disk persistence directory (auto-created)
    ├── queue_*.jsonl # Persisted payload files
    └── ...
```

## Requirements

- Go 1.21+
- Docker daemon (optional - agent runs in degraded mode without it)
- Linux/macOS (auth log paths are platform-specific)
- Network access to the configured server URL
- Read access to system auth logs for security monitoring

## Error Handling & Reliability

- **Docker Unavailable**: Agent continues with system metrics only
- **Auth Logs Missing**: Security monitoring disabled with warning
- **Network Failures**: Exponential backoff retry with disk persistence
- **Invalid Configuration**: Exits with clear error messages
- **Resource Limits**: Bounded buffers prevent memory exhaustion
- **Graceful Shutdown**: Clean resource cleanup on SIGINT/SIGTERM

## Security Considerations

- All payloads are signed with enhanced HMAC-SHA256 (includes timestamp)
- Shared secret should be kept secure and rotated regularly
- Sensitive data is automatically masked in logs
- Agent requires minimal permissions (read-only system access)
- Clock drift detection prevents replay attacks
- Auth log monitoring requires appropriate file permissions

## Performance & Resource Usage

- **Lightweight**: Minimal CPU and memory footprint
- **Efficient**: Goroutine-based concurrent operations
- **Bounded**: All buffers have configurable size limits
- **Persistent**: Disk-based queue prevents data loss
- **Scalable**: Non-blocking operations on main thread
- **Configurable**: Adjustable intervals and thresholds

## Platform-Specific Notes

### Auth Log Paths
- **Debian/Ubuntu**: `/var/log/auth.log`
- **RHEL/CentOS**: `/var/log/secure`
- **Other**: Security monitoring disabled if neither found

### Docker Socket
- **Default**: `/var/run/docker.sock`
- **Permissions**: Agent user must have Docker socket access
- **Fallback**: Continues in degraded mode if Docker unavailable

---

**Version**: 2.0.0  
**Compatibility**: Go 1.21+  
**License**: MIT  
**Maintainer**: Security Operations Team