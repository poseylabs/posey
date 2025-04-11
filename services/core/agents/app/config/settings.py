"""
Configuration settings module for the Posey Agents service.
Provides environment-based configuration, database connection settings,
and various application parameters using Pydantic for validation.
"""

import os
import logging
import secrets
import asyncio
import json
from datetime import datetime

from typing import Optional, List, Annotated, ClassVar, TypedDict
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from app.config.defaults import LLM_CONFIG
from sqlalchemy import Column, DateTime, Boolean

# Create logger
logger = logging.getLogger(__name__)

class CommaSeparatedStrings:
    """Pydantic custom type for handling comma-separated string lists.
    
    Allows values to be provided as either a list of strings or a single
    comma-separated string, and serializes to a comma-separated string.
    """
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: type[str] | None,
        _handler: GetJsonSchemaHandler,
    ) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.list_schema(core_schema.str_schema()),
                core_schema.str_schema(),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: ','.join(x) if isinstance(x, list) else x
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'comma-separated'}

CommaSeparatedList = Annotated[List[str], CommaSeparatedStrings]

class APISettings(BaseSettings):
    """Configuration for API hosts and CORS settings."""
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["*"]

class SecuritySettings(BaseSettings):
    """Configuration for JWT authentication and token settings."""
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_TOKEN_EXPIRE_MINUTES: int = 60

class MediaLimits(TypedDict):
    """Typed dictionary for media generation limits."""
    default_daily_limit: int
    max_daily_limit: int
    providers: List[str]

class MediaGenerationConfig(TypedDict):
    """Typed dictionary for media generation configuration."""
    image: MediaLimits
    video: MediaLimits
    audio: MediaLimits

class Settings(BaseSettings):
    """Main configuration settings for the application."""
    # TODO: This needs to be more restrictive before production
    ALLOWED_HOSTS: List[str] = Field(default=["*"])
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:5173",
            "http://localhost:5555",
            "http://localhost:8000",
            "http://localhost:8888",
            "http://localhost:9999",
        ]
    )

    # Debug settings
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB_POSEY: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DSN_POSEY: str = ""
    POSTGRES_POOL_SIZE: int = 5
    POSTGRES_MAX_OVERFLOW: int = 10

    # Feature flags
    run_migrations: bool = True
    drop_tables: bool = False
    run_seeds: bool = False
    download_embeddings: bool = False

    # CORS settings
    ALLOWED_ORIGINS: list = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        """Configuration for Pydantic settings."""
        env_file = ".env"
        case_sensitive = False

    # App Settings
    SYSTEM_VERSION: str = "1.0.0-beta.1"
    LOG_LEVEL: str = "INFO"

    # Runtime Settings
    NODE_ENV: str = "development"

    # Database Settings - PostgreSQL
    POSTGRES_CONNECTION_URI: Optional[str] = None

    # Database Settings - Couchbase
    COUCHBASE_SCOPE: str = "_default"
    COUCHBASE_COLLECTION: str = "_default"
    COUCHBASE_ADMIN_URL: str = "http://localhost:8091"
    COUCHBASE_URL: str = "couchbase"
    COUCHBASE_BUCKET: str = "posey"
    COUCHBASE_PASSWORD: str = "NKJLHUYTUYKU^G&HP&LI^GY"
    COUCHBASE_USER: str = "pocketdb"
    COUCHBASE_CONNECT_TIMEOUT: int = 5 # Added default timeout
    COUCHBASE_KV_TIMEOUT: int = 5 # Added default timeout
    MIGRATIONS_DIR: ClassVar[Path] = Path("/app/service/app/db/migrations")

    # Database Settings - Qdrant
    QDRANT_URL: Optional[str] = None
    QDRANT_PORT: int = 6333 # Default REST port
    QDRANT_GRPC_PORT: int = 6334 # Default gRPC port
    QDRANT_HOST: str = "posey-qdrant" # Default to Kubernetes service name
    ENABLE_QDRANT: bool = True

    # API Settings
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # Service Settings
    VOYAGER_PORT: Optional[int] = None
    VOYAGER_DOMAIN: Optional[str] = None

    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = LLM_CONFIG["default"]["model"]

    # Memory Settings
    MEMORY_RETENTION_DAYS: int = 30

    # Build Settings
    DOCKER_BUILDKIT: Optional[str] = None


    # Locale Settings
    DEFAULT_LANGUAGE: str = "en"
    DEFAULT_TIMEZONE: str = "America/Los_Angeles"
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_COUNTRY: str = "US"
    DEFAULT_STATE: str = "WA"

    # Integration Settings
    NEXT_PUBLIC_FLUX_API_URL: Optional[str] = None
    NEXT_PUBLIC_FLUX_API_KEY: Optional[str] = None
    STABLE_DIFFUSION_API_KEY: Optional[str] = None
    STABLE_DIFFUSION_TOKEN: Optional[str] = None
    STABLE_DIFFUSION_API_URL: Optional[str] = None
    NEXT_PUBLIC_OPENAI_MODEL: Optional[str] = None

    # Python Settings
    PYTHONDONTWRITEBYTECODE: Optional[str] = 1
    PYTHONUNBUFFERED: Optional[str] = 1
    PYTHONPATH: Optional[str] = "/app/service"

    # Storage Settings
    DO_STORAGE_BUCKET: Optional[str] = None
    DO_STORAGE_BUCKET_KEY: Optional[str] = None
    DO_STORAGE_BUCKET_SECRET: Optional[str] = None
    DO_STORAGE_ORIGIN_ENDPOINT: Optional[str] = None
    DO_STORAGE_CDN_ENDPOINT: Optional[str] = None
    DO_STORAGE_REGION: Optional[str] = None

    # JWT Settings
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Media Generation Settings
    MEDIA_GENERATION: ClassVar[MediaGenerationConfig] = {
        "image": {
            "default_daily_limit": 50,
            "max_daily_limit": 100,
            "providers": ["flux", "stability", "dalle"]
        },
        "video": {
            "default_daily_limit": 10,
            "max_daily_limit": 20,
            "providers": ["runway", "stable-video"]
        },
        "audio": {
            "default_daily_limit": 20,
            "max_daily_limit": 40,
            "providers": ["musicgen", "audiocraft"]
        }
    }

    # Add to existing settings
    VOYAGER_URL: str = "http://posey-voyager:7777"

    EMBEDDING_DIMENSIONS: int = 1536  # Default dimension for text embeddings

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.POSTGRES_DSN_POSEY:
            self.POSTGRES_DSN_POSEY = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB_POSEY}"

    def get_qdrant_url(self) -> str:
        """Construct Qdrant URL from host and port if not provided directly"""
        if self.QDRANT_HOST:
            return self.QDRANT_HOST
        
        if self.QDRANT_URL:
            url = self.QDRANT_URL
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            if ':' not in url.split('/')[-1] and self.QDRANT_PORT:
                url = f"{url}:{self.QDRANT_PORT}"
            return url
        
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    @property
    def QDRANT_FULL_URL(self) -> str:
        """Get the full Qdrant URL"""
        return self.get_qdrant_url()

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Get the allowed origins list"""
        origins = os.getenv('ALLOWED_ORIGINS', '["http://localhost:8888"]')
        try:
            if isinstance(origins, str):
                if origins.startswith('['):
                    return json.loads(origins)
                return origins.split(',')
            return origins
        except json.JSONDecodeError:
            return origins.split(',') if origins else ["http://localhost:8888"]

@lru_cache()
def get_settings() -> Settings:
    env_file = ".env"
    logger.debug(f"Loading settings from {env_file}")
    return Settings(_env_file=env_file)

# Export a single settings instance
settings = get_settings()

# Database connection strings
def get_postgres_url() -> str:
    """Get PostgreSQL connection URL"""
    return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB_POSEY}"

def get_couchbase_connection_string() -> str:
    """Get Couchbase connection string"""
    return f"couchbase://{settings.COUCHBASE_URL}"

# Add query logging middleware
class QueryLoggingMiddleware:
    async def log_query(self, query: str, params: tuple):
        logger.debug(f"SQL: {query}, params: {params}")

# Add connection pooling metrics
class ConnectionMetrics:
    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.query_count = 0

# Add database backup utility
async def backup_database():
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/postgres_{timestamp}.sql"
    
    process = await asyncio.create_subprocess_exec(
        "pg_dump", 
        "-h", settings.POSTGRES_HOST,
        "-U", settings.POSTGRES_USER,
        "-d", settings.POSTGRES_DB_POSEY,
        "-f", backup_path,
        env={"PGPASSWORD": settings.POSTGRES_PASSWORD}
    )
    await process.wait()

# Make settings and utility functions accessible when importing from this module
__all__ = ["settings", "get_settings", "get_postgres_url", "get_couchbase_connection_string"]

# Add common model mixins
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class SoftDeleteMixin:
    deleted_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False)

# Add or update these settings
LOG_LEVEL = "DEBUG"  # Make sure this is set to DEBUG
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
