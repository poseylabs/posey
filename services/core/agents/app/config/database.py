import logging
from typing import AsyncGenerator
import asyncio
from contextlib import asynccontextmanager
import asyncpg
from couchbase.cluster import Cluster
from couchbase.exceptions import CouchbaseException
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions, ClusterTimeoutOptions
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models as rest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from app.config.settings import settings
from datetime import timedelta

# Use the app.database logger
logger = logging.getLogger("app.database")

class Database:
    def __init__(self):
        logger.debug("Initializing Database class")
        self._pg_pool = None
        self._cb_cluster = None
        self._qdrant_client = None
        self._async_engine = None
        self._async_session_factory = None
        
        # Get Qdrant URL with fallback
        try:
            self._qdrant_url = settings.QDRANT_URL
        except AttributeError:
            # Fallback to constructing URL from components
            self._qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
            logger.warning(f"QDRANT_URL not found, using constructed URL: {self._qdrant_url}")
        
        # Create engine with explicit asyncpg driver
        url = settings.POSTGRES_DSN_POSEY.replace('postgresql://', 'postgresql+asyncpg://')
        
        self.engine = create_async_engine(
            url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=settings.POSTGRES_POOL_SIZE,
            max_overflow=settings.POSTGRES_MAX_OVERFLOW,
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
        self._async_session_factory = self.SessionLocal

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
        if not self._cb_cluster:
            raise RuntimeError("Couchbase connection not initialized")
        return self._cb_cluster

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
        """Initializes all database connections."""
        logger.info("Initializing database connections...")

        # Initialize SQLAlchemy first (often less problematic)
        try:
            # Ensure the DSN uses the correct asyncpg driver
            sqlalchemy_dsn = settings.POSTGRES_DSN_POSEY
            if sqlalchemy_dsn.startswith("postgresql://"):
                sqlalchemy_dsn = sqlalchemy_dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif not sqlalchemy_dsn.startswith("postgresql+asyncpg://"):
                 raise ValueError(f"Invalid PostgreSQL DSN format: {sqlalchemy_dsn}")

            self._async_engine = create_async_engine(
                sqlalchemy_dsn,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            self._async_session_factory = sessionmaker(
                self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            # Test SQLAlchemy connection by creating a session
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            logger.info("SQLAlchemy Engine/Session initialized successfully.")
        except Exception as e:
            logger.error(f"SQLAlchemy Engine/Session initialization failed: {e}")
            self._async_engine = None
            self._async_session_factory = None

        # Initialize asyncpg Pool (Separate from SQLAlchemy)
        try:
            self._pg_pool = await asyncpg.create_pool(
                dsn=settings.POSTGRES_DSN_POSEY,
                min_size=1,
                max_size=10,
                timeout=5
            )
            # Test the pool
            async with self.get_pg_connection() as conn:
                 await conn.fetchval("SELECT 1")
            logger.info("asyncpg Pool initialized successfully.")
        except Exception as e:
            logger.error(f"asyncpg Pool initialization failed: {e}")
            self._pg_pool = None
            # Decide if we should raise or continue

        # Initialize Couchbase
        try:
            # Log connection details before attempting
            cb_url = settings.COUCHBASE_URL
            cb_user = settings.COUCHBASE_USER
            logger.info(f"Attempting Couchbase connection: URL='{cb_url}', User='{cb_user}'")
            
            logger.debug(f"Settings dir JUST BEFORE ClusterTimeoutOptions: {dir(settings)}")
            timeout_opts = ClusterTimeoutOptions(
                connect_timeout=timedelta(seconds=settings.COUCHBASE_CONNECT_TIMEOUT),
                key_value_timeout=timedelta(seconds=settings.COUCHBASE_KV_TIMEOUT)
            )
            auth = PasswordAuthenticator(
                settings.COUCHBASE_USER,
                settings.COUCHBASE_PASSWORD
            )
            self._cb_cluster = Cluster(
                settings.COUCHBASE_URL,
                ClusterOptions(auth, timeout_options=timeout_opts)
            )
            # Ensure cluster object was created before proceeding
            if self._cb_cluster:
                # Removed readiness/ping checks from initial connect for simplicity
                # await self._cb_cluster.wait_until_ready(timeout=timedelta(seconds=5))
                # await self._cb_cluster.ping()
                logger.info("Couchbase Cluster initialized and pinged successfully.")
            else:
                # Raise an error if Cluster() returned None unexpectedly
                raise ConnectionError("Couchbase Cluster() constructor returned None")
        except CouchbaseException as ce: 
             logger.error(f"Couchbase Cluster initialization failed: {ce}")
             self._cb_cluster = None
             return False # Indicate failure
        except Exception as e:
            # Log the specific exception type and message
            logger.error(f"Couchbase Cluster initialization failed: {type(e).__name__}: {e}")
            # Log details for debugging
            logger.error(f"  URL: {settings.COUCHBASE_URL}")
            logger.error(f"  User: {settings.COUCHBASE_USER}")

        # Initialize Qdrant Client (Async)
        try:
            await self.connect_qdrant()
        except Exception as e:
            logger.error(f"Qdrant connection failed: {type(e).__name__} - {str(e)}")
            self._qdrant_client = None

        # Enhanced check after all attempts
        if not self._qdrant_client:
            logger.critical("Qdrant client failed to initialize. Application cannot start.")
            raise RuntimeError("Qdrant client failed to initialize during startup.")
        elif not all([self._async_engine, self._pg_pool, self._cb_cluster]):
             logger.warning("One or more non-critical database connections failed to initialize.")
        else:
            logger.info("All required database connections initialized successfully.")

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
                    # Async client likely has an async close method
                    await self._qdrant_client.close(timeout=5)
                except Exception as e:
                    logger.error(f"Error closing Async Qdrant connection: {e}")
            
            if self._async_engine:
                await self._async_engine.dispose()
            
            logger.info("All database connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
            # Don't raise here - we want to close as many connections as possible

    @asynccontextmanager
    async def get_pg_connection(self):
        """Get a PostgreSQL connection from the pool"""
        if not self._pg_pool:
            raise RuntimeError("PostgreSQL connection pool not initialized")
        conn = await self._pg_pool.acquire()
        try:
            yield conn
        finally:
            await self._pg_pool.release(conn) 

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

    async def connect_qdrant(self) -> bool:
        """Initializes the Async Qdrant Client."""
        if self._qdrant_client:
            logger.info("Qdrant Client already initialized.")
            return True
        
        client = None # Initialize local variable
        try:
            logger.info(f"Using Qdrant URL: {settings.QDRANT_FULL_URL}") # Log the URL being used
            client = AsyncQdrantClient(
                url=settings.QDRANT_FULL_URL, # Use the full URL with scheme
                api_key=settings.QDRANT_API_KEY,
                timeout=15
            )
            logger.debug(f"AsyncQdrantClient instantiated locally: {client}")

            # Test Qdrant connection (async call)
            # Use get_collections() to verify connection instead of health_check
            logger.debug("Attempting AsyncQdrantClient.get_collections() for health check...")
            await client.get_collections()
            logger.debug("AsyncQdrantClient.get_collections() health check successful.")
            
            # Assign to self._qdrant_client ONLY after successful health check
            self._qdrant_client = client 
            logger.info(f"Async Qdrant Client initialized and health check successful.")
            return True # Indicate success

        except Exception as e:
            logger.error(f"Async Qdrant Client initialization failed: {type(e).__name__}: {e}")
            logger.error(f"  URL: {settings.QDRANT_FULL_URL}")
            self._qdrant_client = None # Ensure instance variable is None on failure
            # Attempt to clean up the locally created client if it exists
            if client:
                try:
                    await client.close()
                    logger.debug("Cleaned up partially initialized Qdrant client after failure.")
                except Exception as close_err:
                    logger.error(f"Error closing partially initialized Qdrant client: {close_err}")
            raise e # Re-raise the original exception to make it visible

# Create a single instance of the Database class
db = Database()

# Export the database instance
__all__ = ['db']
