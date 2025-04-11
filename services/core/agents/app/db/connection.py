from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, Dict, Any
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
from qdrant_client import QdrantClient
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions, ClusterTimeoutOptions
import asyncpg
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from datetime import timedelta

from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    _pool = None  # Add class variable for pool

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._session: Optional[AsyncSession] = None
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._cb_cluster = None
        self._qdrant_client = None
        self.is_connected = False

    def _create_engine(self):
        """Create SQLAlchemy engine"""
        if not self._engine:
            # Ensure DSN uses asyncpg driver
            dsn = settings.POSTGRES_DSN_POSEY
            if not dsn.startswith('postgresql+asyncpg://'):
                dsn = dsn.replace('postgresql://', 'postgresql+asyncpg://')

            self._engine = create_async_engine(
                dsn,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                future=True  # Use SQLAlchemy 2.0 style
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session"""
        if not self._engine:
            self._create_engine()

        if self._session is None:
            async with self._session_factory() as session:
                try:
                    yield session
                except Exception as e:
                    await session.rollback()
                    raise e
                finally:
                    await session.close()
        else:
            yield self._session

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1))
    async def connect(self):
        """Connect to database"""
        if self.is_connected:
            return

        try:
            logger.info("Initializing database connections...")
            
            # Parse and reconstruct the DSN properly
            base_dsn = settings.POSTGRES_DSN_POSEY
            # Remove any protocol prefix and query params
            base_dsn = base_dsn.replace('postgresql://', '').replace('postgresql+asyncpg://', '')
            main_part = base_dsn.split('?')[0]
            
            # Create clean DSNs
            asyncpg_dsn = f"postgresql://{main_part}"
            logger.info(f"Using asyncpg DSN: {asyncpg_dsn}")
            
            self._pg_pool = await asyncpg.create_pool(
                dsn=asyncpg_dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )

            # Test connection
            async with self._pg_pool.acquire() as conn:
                await conn.execute('SELECT 1')
            
            # Create SQLAlchemy engine with asyncpg
            sqlalchemy_dsn = f"postgresql+asyncpg://{main_part}"
            logger.info(f"Using SQLAlchemy DSN: {sqlalchemy_dsn}")
            
            self._engine = create_async_engine(
                sqlalchemy_dsn,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=10,
                connect_args={
                    "host": settings.POSTGRES_HOST  # Force TCP/IP connection
                }
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.is_connected = True
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            await self.disconnect()
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
    async def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            # Convert SQLAlchemy DSN to asyncpg format
            dsn = settings.POSTGRES_DSN_POSEY.replace('postgresql+asyncpg://', 'postgresql://')
            logger.info(f"Connecting to PostgreSQL: {dsn}")
            
            # Create asyncpg pool
            self._pg_pool = await asyncpg.create_pool(
                dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )

            # Test connection
            async with self._pg_pool.acquire() as conn:
                await conn.execute('SELECT 1')
            logger.info("PostgreSQL connection established")
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise

    async def connect_all(self):
        """Initialize all database connections."""
        if self.is_connected:
            logger.info("Database connections already initialized.")
            return

        logger.info("Initializing all database connections...")
        try:
            # Initialize connections concurrently
            await asyncio.gather(
                self._init_postgres(),
                self._init_couchbase(),
                self._init_qdrant()
            )
            self.is_connected = True
            logger.info("All database connections initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize all database connections: {e}")
            # Attempt to close any connections that might have been opened
            await self.disconnect() 
            raise # Re-raise the exception to signal failure

    async def _init_couchbase(self):
        """Initialize Couchbase connection"""
        try:
            # Construct proper Couchbase URL
            cb_url = f"{settings.COUCHBASE_URL}"
            logger.info(f"Connecting to Couchbase: {cb_url}")
            
            auth = PasswordAuthenticator(
                settings.COUCHBASE_USER,
                settings.COUCHBASE_PASSWORD
            )

            timeout_opts = ClusterTimeoutOptions(
                connect_timeout=timedelta(seconds=5),
                key_value_timeout=timedelta(seconds=5)
            )

            self._cb_cluster = Cluster(
                cb_url,
                ClusterOptions(auth, timeout_options=timeout_opts)
            )
            
            # Open bucket to verify connection and auth
            bucket = self._cb_cluster.bucket(settings.COUCHBASE_BUCKET)
            bucket.scope(settings.COUCHBASE_SCOPE).collection(settings.COUCHBASE_COLLECTION)
            logger.info("Couchbase connection established")
            
        except Exception as e:
            logger.error(f"Couchbase connection failed: {e}")
            raise

    async def _init_qdrant(self):
        """Initialize Qdrant connection"""
        try:
            # Ensure host is just the hostname, not a URL
            host = settings.QDRANT_HOST.replace('http://', '').replace('https://', '')
            grpc_port = settings.QDRANT_PORT # Already defaults to 6333
            logger.info(f"Connecting to Qdrant via gRPC: host='{host}', port={grpc_port}")
            
            self._qdrant_client = QdrantClient(
                host=host,
                grpc_port=grpc_port,
                prefer_grpc=True, # Explicitly prefer gRPC
                timeout=5.0
            )
            
            # Test connection
            self._qdrant_client.get_collections()
            logger.info("Qdrant connection established via gRPC")
            
        except Exception as e:
            logger.error(f"Qdrant gRPC connection failed: {e}")
            raise

    async def disconnect(self):
        """Disconnect from database"""
        try:
            if self._pg_pool:
                await self._pg_pool.close()
            
            if self._cb_cluster:
                self._cb_cluster.close()
            
            # Qdrant client doesn't have an async close method
            if self._qdrant_client:
                self._qdrant_client.close()
                
            if self._engine:
                await self._engine.dispose()
            self.is_connected = False
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
            raise

    # Add connection metrics
    async def get_pool_stats(self) -> Dict[str, int]:
        return {
            "size": self._pg_pool.get_size(),
            "free": self._pg_pool.get_free_size(),
            "used": self._pg_pool.get_used_size()
        }

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get a SQLAlchemy session"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
            
        async with self._session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    @asynccontextmanager
    async def get_pg_conn(self):
        """Get a PostgreSQL connection"""
        if not self._pg_pool:
            raise RuntimeError("PostgreSQL not initialized")
            
        async with self._pg_pool.acquire() as conn:
            yield conn

    @property
    def qdrant(self):
        """Get Qdrant client"""
        if not self._qdrant_client:
            raise RuntimeError("Qdrant not initialized")
        return self._qdrant_client

    @property
    def couchbase(self):
        """Get Couchbase cluster"""
        if not self._cb_cluster:
            raise RuntimeError("Couchbase not initialized")
        return self._cb_cluster

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            # Convert SQLAlchemy DSN to asyncpg format
            dsn = settings.POSTGRES_DSN_POSEY.replace('postgresql+asyncpg://', 'postgresql://')
            cls._pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
        return cls._pool

    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            try:
                yield conn
            finally:
                await conn.close()

    @classmethod
    async def close_all(cls):
        if cls._pool:
            await cls._pool.close()

    async def increment_media_usage(
        self, 
        agent_id: UUID, 
        media_type: str,
        prompt: str,
        result_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Increment media usage and log history"""
        async with self.get_session() as session:
            async with session.begin():
                # Update usage count
                await session.execute("""
                    UPDATE agents 
                    SET media_generation_config = jsonb_set(
                        media_generation_config,
                        ARRAY[%s, 'used_today'],
                        (COALESCE((media_generation_config->%s->>'used_today')::int, 0) + 1)::text::jsonb
                    )
                    WHERE id = %s
                """, (f"{media_type}_generation", f"{media_type}_generation", agent_id))

                # Log history
                await session.execute("""
                    INSERT INTO media_generation_history 
                    (agent_id, media_type, prompt, result_url, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (agent_id, media_type, prompt, result_url, metadata or {}))

    async def check_media_quota(self, agent_id: UUID, media_type: str) -> bool:
        """Check if agent has exceeded media quota"""
        async with self.get_session() as session:
            result = await session.execute("""
                SELECT media_generation_config->%s 
                FROM agents WHERE id = %s
            """, (f"{media_type}_generation", agent_id))
            config = result.scalar()
            
            if not config:
                return False
                
            used = config.get('used_today', 0)
            limit = config.get('daily_limit', 0)
            return used < limit

async def check_postgres_connection(max_retries=5, retry_delay=5) -> bool:
    """Check if PostgreSQL is ready to accept connections"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to connect to PostgreSQL")
            logger.info(f"Connection details:")
            logger.info(f"  Host: {settings.POSTGRES_HOST}")
            logger.info(f"  Port: {settings.POSTGRES_PORT}")
            logger.info(f"  Database: {settings.POSTGRES_DB_POSEY}")
            logger.info(f"  User: {settings.POSTGRES_USER}")
            logger.info(f"  DSN: {settings.POSTGRES_DSN_POSEY}")
            
            # Use the DSN directly
            dsn = settings.POSTGRES_DSN_POSEY.replace('postgresql+asyncpg://', 'postgresql://')
            logger.info(f"Using DSN: {dsn}")
            
            conn = await asyncpg.connect(dsn=dsn)
            await conn.execute('SELECT 1')  # Verify we can execute queries
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before next attempt...")
                await asyncio.sleep(retry_delay)
            continue
    
    logger.error("All connection attempts failed")
    return False

# Create global database instance
db = Database()

# Export database instance
__all__ = ['db']
