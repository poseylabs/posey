# Builtins
import logging as python_logging  # Rename to avoid confusion
# Configure logging first, before any other imports
python_logging.basicConfig(
    level=python_logging.INFO,  # Default to INFO until settings are loaded
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# External
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables before importing settings
load_dotenv()

# Internal
from .settings import Settings, settings
from app.config.logging import logger  # Import our custom logger
from .database import db
from .defaults import LLM_CONFIG

# Set log levels using Python's logging module
python_logging.getLogger('app').setLevel(python_logging.INFO)
python_logging.getLogger('app.utils').setLevel(python_logging.INFO)
python_logging.getLogger('app.routers').setLevel(python_logging.INFO)

# Set SQLAlchemy logging to ERROR level
python_logging.getLogger('sqlalchemy.engine').setLevel(python_logging.ERROR)

# Initialize settings
settings = Settings()

# Create SQLAlchemy base
Base = declarative_base()

__all__ = [
    'settings',
    'logger',
    'Base',
    'db',
    'LLM_CONFIG'
]
