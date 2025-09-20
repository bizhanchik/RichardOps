"""
Performance and scalability configuration for production deployment.
"""
import os
from typing import Dict, Any


class PerformanceConfig:
    """Configuration class for performance and scalability settings."""
    
    # Database connection pool settings
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour
    
    # Application server settings
    UVICORN_WORKERS = int(os.getenv("UVICORN_WORKERS", "4"))
    UVICORN_MAX_REQUESTS = int(os.getenv("UVICORN_MAX_REQUESTS", "1000"))
    UVICORN_MAX_REQUESTS_JITTER = int(os.getenv("UVICORN_MAX_REQUESTS_JITTER", "100"))
    
    # Request handling settings
    MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # 30 seconds
    
    # Caching settings
    ENABLE_RESPONSE_CACHE = os.getenv("ENABLE_RESPONSE_CACHE", "false").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # 1 minute
    
    # Monitoring and metrics
    METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    METRICS_ENDPOINT = os.getenv("METRICS_ENDPOINT", "/metrics")
    
    # Batch processing settings
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    BATCH_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "5"))  # 5 seconds
    
    @classmethod
    def get_uvicorn_config(cls) -> Dict[str, Any]:
        """Get UVicorn configuration for production."""
        return {
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "8000")),
            "workers": cls.UVICORN_WORKERS,
            "max_requests": cls.UVICORN_MAX_REQUESTS,
            "max_requests_jitter": cls.UVICORN_MAX_REQUESTS_JITTER,
            "timeout_keep_alive": 5,
            "timeout_graceful_shutdown": 30,
            "log_level": os.getenv("LOG_LEVEL", "info").lower(),
            "access_log": True,
            "use_colors": False,  # Better for production logs
            "reload": False  # Never reload in production
        }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration for production."""
        return {
            "pool_size": cls.DB_POOL_SIZE,
            "max_overflow": cls.DB_MAX_OVERFLOW,
            "pool_timeout": cls.DB_POOL_TIMEOUT,
            "pool_recycle": cls.DB_POOL_RECYCLE,
            "pool_pre_ping": True,  # Validate connections
            "echo": False,  # Disable SQL logging in production
            "connect_args": {
                "server_settings": {
                    "application_name": "monitoring-backend",
                    "jit": "off"  # Disable JIT for consistent performance
                },
                "command_timeout": cls.REQUEST_TIMEOUT,
                "connect_timeout": 10
            }
        }
    
    @classmethod
    def get_performance_summary(cls) -> Dict[str, Any]:
        """Get a summary of performance configuration."""
        return {
            "database": {
                "pool_size": cls.DB_POOL_SIZE,
                "max_overflow": cls.DB_MAX_OVERFLOW,
                "pool_timeout": cls.DB_POOL_TIMEOUT
            },
            "server": {
                "workers": cls.UVICORN_WORKERS,
                "max_requests": cls.UVICORN_MAX_REQUESTS,
                "request_timeout": cls.REQUEST_TIMEOUT
            },
            "features": {
                "caching_enabled": cls.ENABLE_RESPONSE_CACHE,
                "rate_limiting_enabled": cls.RATE_LIMIT_ENABLED,
                "metrics_enabled": cls.METRICS_ENABLED
            }
        }


# Global performance configuration instance
perf_config = PerformanceConfig()