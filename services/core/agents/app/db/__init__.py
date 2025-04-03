from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import logger
from .connection import db

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with db.session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database connections"""
    try:
        await db.test_connections()
        logger.info("Database connections initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connections: {e}")
        raise

async def cleanup_db():
    """Cleanup database connections"""
    try:
        await db.close_all()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Failed to close database connections: {e}")
        raise

__all__ = ['db', 'get_db', 'init_db', 'cleanup_db', 'logger']

