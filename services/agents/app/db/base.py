from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData, create_engine
from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Use naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Create base for all models
Base = declarative_base(metadata=metadata)

# Create automap base that inherits from our Base
AutomapBase = automap_base(metadata=metadata, declarative_base=Base)

# Parse and reconstruct the DSN for asyncpg
base_dsn = settings.POSTGRES_DSN_POSEY
# Remove any protocol prefix and query params
base_dsn = base_dsn.replace('postgresql://', '').replace('postgresql+asyncpg://', '')
main_part = base_dsn.split('?')[0]

# Create SQLAlchemy engine with asyncpg
sqlalchemy_dsn = f"postgresql+asyncpg://{main_part}"

# Create async engine
engine = create_async_engine(
    sqlalchemy_dsn,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "host": settings.POSTGRES_HOST  # Force TCP/IP connection
    }
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create sync engine for reflection with psycopg2
sync_engine = create_engine(
    settings.POSTGRES_DSN_POSEY.replace('postgresql+asyncpg', 'postgresql'),
    connect_args={
        "host": settings.POSTGRES_HOST  # Force TCP/IP connection
    }
)

# Export for use in models/schemas.py
__all__ = ['engine', 'metadata', 'sync_engine', 'Base', 'AutomapBase'] 
