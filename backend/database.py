import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy import text, create_engine
from typing import AsyncGenerator

logger = logging.getLogger("monitoring-backend")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Database configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://monitoring_user:monitoring_pass@localhost:5432/monitoring"
)

# Synchronous database URL for NLP system (uses psycopg2 instead of asyncpg)
SYNC_DATABASE_URL = os.environ.get(
    "SYNC_DATABASE_URL",
    "postgresql://monitoring_user:monitoring_pass@localhost:5432/monitoring"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging in development
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    connect_args={
        "server_settings": {
            "application_name": "monitoring-backend",
        }
    }
)

# Create synchronous engine for NLP system
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args={
        "application_name": "monitoring-backend-nlp",
    }
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create synchronous session factory for NLP system
sync_session_maker = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide database session for FastAPI endpoints.
    
    Yields:
        AsyncSession: Database session that will be automatically closed
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database by creating all tables and required extensions safely.
    This should be called on application startup.
    
    Note: Indexes are managed by Alembic migrations, not here, to avoid
    duplicate creation errors.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        from db_models import (
            MetricsModel, DockerEventsModel, ContainerLogsModel, 
            AlertsModel, EmailNotificationsModel
        )
        
        # Create all tables (this will skip existing tables)
        await conn.run_sync(Base.metadata.create_all)
        
        # Only create required extensions, not indexes (handled by migrations)
        await _create_required_extensions(conn)


async def _create_required_extensions(conn):
    """
    Create required PostgreSQL extensions safely.
    Extensions can be created multiple times without errors.
    """
    # Required extensions for the application
    extensions = [
        # Enable pg_trgm extension for trigram matching (needed for GIN indexes)
        "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
    ]
    
    for extension_sql in extensions:
        try:
            await conn.execute(text(extension_sql))
            logger.info(f"Successfully executed: {extension_sql.strip()}")
        except Exception as e:
            # Log the error but don't crash the application
            logger.warning(f"Extension creation warning: {e}")
            # Continue with other extensions


def get_sync_db_session() -> Session:
    """
    Get a synchronous database session for the NLP system.
    
    Returns:
        Session: Synchronous database session that should be closed after use
    """
    return sync_session_maker()


async def close_db():
    """
    Close database engines.
    This should be called on application shutdown.
    """
    await engine.dispose()
    sync_engine.dispose()