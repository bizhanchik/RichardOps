import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Database configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql+asyncpg://monitoring_user:monitoring_pass@localhost:5432/monitoring"
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

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
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
        except Exception as e:
            await session.rollback()
            # Log the database error for debugging
            import logging
            logger = logging.getLogger("monitoring-backend")
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database by creating all tables.
    This should be called on application startup.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        from db_models import (
            MetricsModel, DockerEventsModel, ContainerLogsModel, 
            AlertsModel, EmailNotificationsModel
        )
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database engine.
    This should be called on application shutdown.
    """
    await engine.dispose()