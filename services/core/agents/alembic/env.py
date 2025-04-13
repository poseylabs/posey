import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Customizations Start Here ---
# Add your model's MetaData object here
# for 'autogenerate' support

# Ensure the app directory is in the Python path
# Assumes alembic is run from the 'services/core/agents' directory
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))
sys.path.insert(0, APP_DIR)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))) # Add service root

# Import your Base and models
# Adjust the import path according to your project structure
from app.db.base import Base
# Import all models defined in app.db.models
# This ensures Alembic detects them for autogeneration
from app.db.models import * # noqa

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired: 
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# --- Customizations End Here ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    # Try to read from env var if it's the placeholder
    if url == '${POSTGRES_DSN_POSEY}':
        url = os.getenv('POSTGRES_DSN_POSEY')
        if not url:
            raise ValueError("POSTGRES_DSN_POSEY environment variable not set for offline mode.")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Prioritize external DSN for local runs, fallback to internal DSN for container runs
    db_url = os.getenv('POSTGRES_DSN_POSEY_EXTERNAL')
    using_external_db = True
    if not db_url:
        print("INFO: POSTGRES_DSN_POSEY_EXTERNAL not set, falling back to POSTGRES_DSN_POSEY")
        db_url = os.getenv('POSTGRES_DSN_POSEY')
        using_external_db = False

    if not db_url:
        raise ValueError("Neither POSTGRES_DSN_POSEY_EXTERNAL nor POSTGRES_DSN_POSEY environment variables are set for online mode.")
    else:
        # Mask credentials in log output for security
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(db_url)
            # Reconstruct URL masking password
            netloc_parts = parsed.netloc.split('@')
            if len(netloc_parts) > 1:
                auth_parts = netloc_parts[0].split(':')
                if len(auth_parts) > 1:
                    masked_netloc = f"{auth_parts[0]}:********@{netloc_parts[1]}"
                else:
                    masked_netloc = f"{auth_parts[0]}@********"
            else:
                masked_netloc = netloc_parts[0] # No auth info
            
            masked_url = urlunparse((parsed.scheme, masked_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
            print(f"INFO: Using {'external' if using_external_db else 'internal'} database URL: {masked_url}")
        except Exception:
             print(f"INFO: Using {'external' if using_external_db else 'internal'} database URL (credentials hidden).")


    # Create engine configuration dictionary programmatically
    # We no longer need engine_from_config here since we fetch the URL directly
    engine_config = {
        "sqlalchemy.url": db_url,
        # Add other engine options from alembic.ini if needed, e.g.:
        # "poolclass": pool.NullPool, # Example
    }

    connectable = engine_from_config(
        engine_config,
        prefix="sqlalchemy.", # Still useful for potential other options
        poolclass=pool.NullPool, # Ensure NullPool is used
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
