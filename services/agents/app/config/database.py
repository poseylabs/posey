import logging
from typing import AsyncGenerator
import asyncio
from contextlib import asynccontextmanager
import asyncpg
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions, ClusterTimeoutOptions
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import asyncpg
from sqlalchemy.engine.url import make_url
from app.config.settings import settings

# Use the app.database logger
logger = logging.getLogger("app.database")

class Database:
    def __init__(self):
        logger.debug("Initializing Database class")
        self._pg_pool = None
        self._cb_cluster = None
        self._qdrant_client = None
        self._async_session = None
        self._async_engine = None
        self._async_session_factory = None
        
        # Get Qdrant URL with fallback
        try:
            self._qdrant_url = settings.QDRANT_FULL_URL
        except AttributeError:
            # Fallback to constructing URL from components
            self._qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
            logger.warning(f"QDRANT_FULL_URL not found, using constructed URL: {self._qdrant_url}")
        
        # Create engine with explicit asyncpg driver
        url = settings.POSTGRES_DSN_POSEY.replace('postgresql://', 'postgresql+asyncpg://')
        
        self.engine = create_async_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={
                "server_settings": {
                    "application_name": "posey-agents"
                }
            }
        )
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @property
    def pool(self):
        """Getter for PostgreSQL connection pool"""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized. Call connect_all() first.")
        return self._pool

    @property
    def pg_pool(self):
        """PostgreSQL connection pool"""
        return self._pg_pool

    @property
    def cb_cluster(self):
        """Getter for Couchbase cluster"""
        if not self._cb_cluster:
            raise RuntimeError("Couchbase cluster not initialized. Call connect_all() first.")
        return self._cb_cluster

    @cb_cluster.setter
    def cb_cluster(self, value):
        """Setter for Couchbase cluster"""
        self._cb_cluster = value

    @property
    def qdrant_client(self):
        """Getter for qdrant client"""
        if not self._qdrant_client:
            raise RuntimeError("Qdrant client not initialized. Call connect_all() first.")
        return self._qdrant_client

    @qdrant_client.setter
    def qdrant_client(self, value):
        """Setter for qdrant client"""
        self._qdrant_client = value

    @property
    def qdrant_url(self):
        """Getter for Qdrant URL"""
        return self._qdrant_url

    @qdrant_url.setter
    def qdrant_url(self, value):
        """Setter for Qdrant URL"""
        self._qdrant_url = value
    
    @property
    def postgres_pool(self):
        """Getter for PostgreSQL connection pool"""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized. Call connect_all() first.")
        return self._pool
    
    @property
    def couchbase(self):
        if not self._collection:
            raise RuntimeError("Couchbase connection not initialized")
        return self._collection

    @property
    def postgres(self):
        if not self._pool:
            raise RuntimeError("PostgreSQL connection not initialized")
        return self._pool

    @property
    def collection(self):
        """Getter for Couchbase collection"""
        if not self._collection:
            raise RuntimeError("Couchbase collection not initialized. Call connect_all() first.")
        return self._collection

    @property
    def qdrant(self):
        """Getter for Qdrant client"""
        if not self._qdrant_client:
            raise RuntimeError("Qdrant client not initialized. Call connect_all() first.")
        return self._qdrant_client
        
    @property
    def couchbase_collection(self):
        """Getter for Couchbase collection"""
        if not self._collection:
            raise RuntimeError("Couchbase collection not initialized. Call connect_all() first.")
        return self._collection

    @property
    def async_session(self):
        """Getter for SQLAlchemy async session"""
        if not self._async_session:
            raise RuntimeError("SQLAlchemy session not initialized. Call connect_all() first.")
        return self._async_session

    async def connect_all(self):
        """Initialize all database connections"""
        logger.info("Initializing database connections...")
        
        # Parse and reconstruct the DSN for asyncpg
        base_dsn = settings.POSTGRES_DSN_POSEY
        # Remove any protocol prefix and query params
        base_dsn = base_dsn.replace('postgresql://', '').replace('postgresql+asyncpg://', '')
        main_part = base_dsn.split('?')[0]
        
        # Create SQLAlchemy engine with asyncpg
        sqlalchemy_dsn = f"postgresql+asyncpg://{main_part}"
        
        # Create async engine
        self._async_engine = create_async_engine(
            sqlalchemy_dsn,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
            connect_args={
                "host": settings.POSTGRES_HOST  # Force TCP/IP connection
            }
        )

        # Create async session factory
        self._async_session_factory = sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @property
    def async_engine(self):
        if not self._async_engine:
            raise RuntimeError("Database engine not initialized. Call connect_all() first.")
        return self._async_engine

    @property
    def async_session(self):
        if not self._async_session:
            raise RuntimeError("SQLAlchemy session not initialized")
        return self._async_session

    async def test_connections(self) -> bool:
        """Test all database connections"""
        success = True
        
        # Test PostgreSQL
        try:
            await self._test_postgres_connection()
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {type(e).__name__} - {str(e)}")
            success = False

        # Test Couchbase
        try:
            await self._test_couchbase_connection()
        except Exception as e:
            logger.error(f"Couchbase connection failed: {type(e).__name__} - {str(e)}")
            success = False

        # Test Qdrant
        try:
            await self._test_qdrant_connection()
        except Exception as e:
            logger.error(f"Qdrant connection failed: {type(e).__name__} - {str(e)}")
            success = False

        return success

    async def _test_postgres_connection(self):
        """Test PostgreSQL connection"""
        try:
            logger.info("Attempting PostgreSQL connection with:")
            logger.info(f"  Host: {settings.POSTGRES_HOST}")
            logger.info(f"  Port: {settings.POSTGRES_PORT}")
            logger.info(f"  Database: {settings.POSTGRES_DB_POSEY}")
            logger.info(f"  User: {settings.POSTGRES_USER}")
            logger.info(f"  DSN: {settings.POSTGRES_DSN_POSEY}")
            
            def connect():
                self._pg_pool = asyncpg.create_pool(
                    dsn=settings.POSTGRES_DSN_POSEY,
                    min_size=1,
                    max_size=10,
                    timeout=5
                )
            
            # Run the sync code in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, connect)
            logger.info("PostgreSQL connection established successfully")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {type(e).__name__} - {str(e)}")
            logger.error(f"PostgreSQL DSN: {settings.POSTGRES_DSN_POSEY}")
            self._pg_pool = None
            raise

    async def _test_couchbase_connection(self):
        """Test Couchbase connection"""
        try:
            logger.info("Attempting Couchbase connection with:")
            logger.info(f"  URL: {settings.COUCHBASE_URL}")
            logger.info(f"  Bucket: {settings.COUCHBASE_BUCKET}")
            logger.info(f"  User: {settings.COUCHBASE_USER}")
            
            def connect():
                from datetime import timedelta
                timeout_opts = ClusterTimeoutOptions(
                    connect_timeout=timedelta(seconds=5),
                    key_value_timeout=timedelta(seconds=5)
                )
                
                auth = PasswordAuthenticator(
                    settings.COUCHBASE_USER,
                    settings.COUCHBASE_PASSWORD
                )
                
                self._cb_cluster = Cluster(
                    settings.COUCHBASE_URL,
                    ClusterOptions(auth, timeout_options=timeout_opts)
                )
                self._cb_cluster.ping()
            
            # Run the sync code in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, connect)
            logger.info("Couchbase connection established successfully")
        except Exception as e:
            logger.error(f"Couchbase connection failed: {type(e).__name__} - {str(e)}")
            self._cb_cluster = None
            raise

    async def _test_qdrant_connection(self):
        """Test Qdrant connection"""
        logger.info("Attempting Qdrant connection with:")
        logger.info(f"  URL: {settings.QDRANT_FULL_URL}")
        logger.info(f"  Port: {settings.QDRANT_PORT}")
        
        def connect():
            self._qdrant_client = QdrantClient(
                url=settings.QDRANT_FULL_URL,
                timeout=5
            )
            collections = self._qdrant_client.get_collections()
            return collections
        
        # Run the sync code in a thread pool
        loop = asyncio.get_event_loop()
        collections = await loop.run_in_executor(None, connect)
        logger.info(f"Qdrant connection established successfully. Collections: {collections}")

    async def close_all(self):
        """Close all database connections"""
        try:
            if self.pg_pool:
                logger.info("Closing PostgreSQL connection pool")
                await self.pg_pool.close()
            
            if self._cb_cluster:
                logger.info("Closing Couchbase connection")
                self._cb_cluster.close()
            
            if self._qdrant_client:
                logger.info("Closing Qdrant connection")
                try:
                    await self._qdrant_client.close()
                except Exception as e:
                    logger.error(f"Error closing Qdrant connection: {e}")
            
            if self._async_engine:
                await self._async_engine.dispose()
            
            logger.info("All database connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
            # Don't raise here - we want to close as many connections as possible

    @asynccontextmanager
    async def get_pg_connection(self):
        """Get a PostgreSQL connection from the pool"""
        if not self.pg_pool:
            raise RuntimeError("PostgreSQL connection pool not initialized")
        conn = await self.pg_pool.acquire()
        try:
            yield conn
        finally:
            await self.pg_pool.release(conn) 

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self._async_session() as session:
            try:
                yield session
            finally:
                await session.close()

    async def connect(self):
        """Connect to database"""
        # Create tables if they don't exist
        # Note: In production, use alembic migrations instead
        from app.models.db import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self):
        """Disconnect from database"""
        await self.engine.dispose()

    def get_session(self):
        """Get an async session"""
        if not self._async_session_factory:
            raise RuntimeError("Database not initialized. Call connect_all() first.")
        return self._async_session_factory()

# Create a single instance of the Database class
db = Database()

# Export the database instance
__all__ = ['db']
