import os
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from couchbase.options import ClusterOptions
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Create logger
logger = logging.getLogger(__name__)

# Initialize database connections as None
cluster = None
bucket = None
collection = None
QDRANT_CLIENT = None

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "logger"
]
