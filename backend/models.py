from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SystemMetrics(BaseModel):
    """System performance metrics matching Go agent's SystemMetrics struct."""
    
    model_config = ConfigDict(extra="allow")
    
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_rx_bytes_per_sec: int
    network_tx_bytes_per_sec: int
    tcp_connections: int


class DockerEvent(BaseModel):
    """Docker event matching Go agent's DockerEvent struct."""
    
    model_config = ConfigDict(extra="allow")
    
    type: str
    action: str
    container: str
    image: str
    timestamp: datetime


class LogEntry(BaseModel):
    """Container log entry matching Go agent's LogEntry struct."""
    
    model_config = ConfigDict(extra="allow")
    
    container: str
    message: str
    timestamp: datetime


class Payload(BaseModel):
    """
    Complete monitoring payload matching Go agent's Payload struct.
    
    This model mirrors exactly the Go struct:
    - Host: string (required)
    - ServerID: string (optional)
    - Env: string (optional) 
    - OwnerTeam: string (optional)
    - Timestamp: time.Time (required)
    - Metrics: SystemMetrics (required)
    - DockerEvents: []DockerEvent (required, can be empty)
    - Logs: []LogEntry (required, can be empty)
    - LocalAlerts: []string (required, can be empty)
    - Score: float64 (required)
    """
    
    model_config = ConfigDict(extra="allow")
    
    host: str
    server_id: Optional[str] = None
    env: Optional[str] = None
    owner_team: Optional[str] = None
    timestamp: datetime
    metrics: SystemMetrics
    docker_events: List[DockerEvent] = []
    logs: List[LogEntry] = []
    local_alerts: List[str] = []
    score: float


class HealthStatus(BaseModel):
    """Health status response model."""
    
    status: str
    timestamp: str
    service: str


class IngestResponse(BaseModel):
    """Response model for the /ingest endpoint."""
    
    status: str
    message: str
    timestamp: str