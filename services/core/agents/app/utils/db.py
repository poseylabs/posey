from contextlib import contextmanager
from contextlib import asynccontextmanager
from app.config import logger
from app.config.settings import settings
from app.config.database import Database

# Use settings object instead of direct imports
POSTGRES_DB_POSEY = settings.POSTGRES_DB_POSEY
POSTGRES_USER = settings.POSTGRES_USER
POSTGRES_PASSWORD = settings.POSTGRES_PASSWORD
POSTGRES_HOST = settings.POSTGRES_HOST
POSTGRES_PORT = settings.POSTGRES_PORT

COUCHBASE_URL = settings.COUCHBASE_URL
COUCHBASE_USER = settings.COUCHBASE_USER
COUCHBASE_PASSWORD = settings.COUCHBASE_PASSWORD
COUCHBASE_BUCKET = settings.COUCHBASE_BUCKET

QDRANT_URL = settings.QDRANT_URL
QDRANT_PORT = settings.QDRANT_PORT

# Initialize database
db = Database()

@asynccontextmanager
async def get_db():
    """Get database connection"""
    try:
        await db.test_connections()
        yield db
    finally:
        await db.close_all()

# For synchronous connections (if needed)
@contextmanager
def get_db_connection():
    if not db.pg_pool:
        raise RuntimeError("PostgreSQL connection pool not initialized")
    conn = db.pg_pool.getconn()
    try:
        yield conn
    finally:
        db.pg_pool.putconn(conn)

# Export commonly used items
__all__ = ['db', 'get_db', 'logger']
