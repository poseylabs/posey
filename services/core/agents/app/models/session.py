"""Database session management."""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import db

@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get a database session as an async context manager."""
    session = db.async_session()
    try:
        yield session
    finally:
        await session.close() 
