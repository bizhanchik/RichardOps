from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, 
    Numeric, String, Text, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import BIGINT
from sqlalchemy.orm import relationship
from database import Base


class MetricsModel(Base):
    """SQLAlchemy model for system metrics table."""
    
    __tablename__ = "metrics"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    cpu_usage = Column(Numeric(5, 2))
    memory_usage = Column(Numeric(5, 2))
    disk_usage = Column(Numeric(5, 2))
    network_rx = Column(BigInteger)
    network_tx = Column(BigInteger)
    tcp_connections = Column(Integer)
    
    # Index for efficient time-based queries
    __table_args__ = (
        Index('idx_metrics_timestamp_desc', 'timestamp', postgresql_using='btree'),
    )


class DockerEventsModel(Base):
    """SQLAlchemy model for docker events table."""
    
    __tablename__ = "docker_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    type = Column(String(255))
    action = Column(Text)
    container = Column(String(255))
    image = Column(String(255))
    
    # Index for efficient time-based queries
    __table_args__ = (
        Index('idx_docker_events_timestamp_desc', 'timestamp', postgresql_using='btree'),
        Index('idx_docker_events_container', 'container'),
    )


class ContainerLogsModel(Base):
    """SQLAlchemy model for container logs table."""
    
    __tablename__ = "container_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    container = Column(String(255), index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    message = Column(Text)
    
    # Indexes for efficient queries (excluding GIN index which is handled separately)
    __table_args__ = (
        Index('idx_container_logs_timestamp_desc', 'timestamp', postgresql_using='btree'),
        Index('idx_container_logs_container_timestamp', 'container', 'timestamp'),
        # Note: GIN index for full-text search is created separately in database.py
        # to avoid duplicate index creation errors during startup
    )


class AlertsModel(Base):
    """SQLAlchemy model for alerts table."""
    
    __tablename__ = "alerts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    severity = Column(String(10), nullable=False)
    type = Column(String(100))
    message = Column(Text)
    score = Column(Numeric(4, 2))
    resolved = Column(Boolean, default=False, nullable=False)
    
    # Relationship to email notifications
    email_notifications = relationship(
        "EmailNotificationsModel", 
        back_populates="alert",
        cascade="all, delete-orphan"
    )
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH')", 
            name='check_severity_values'
        ),
        Index('idx_alerts_timestamp_desc', 'timestamp', postgresql_using='btree'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_resolved', 'resolved'),
        Index('idx_alerts_unresolved_timestamp', 'resolved', 'timestamp', 
              postgresql_where='resolved = false'),
    )


class EmailNotificationsModel(Base):
    """SQLAlchemy model for email notifications table."""
    
    __tablename__ = "email_notifications"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_id = Column(BigInteger, ForeignKey('alerts.id', ondelete='CASCADE'), nullable=False)
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255))
    status = Column(String(20), nullable=False)  # success/failed
    
    # Relationship to alerts
    alert = relationship("AlertsModel", back_populates="email_notifications")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed')", 
            name='check_status_values'
        ),
        Index('idx_email_notifications_alert_id', 'alert_id'),
        Index('idx_email_notifications_sent_at', 'sent_at'),
        Index('idx_email_notifications_status', 'status'),
    )