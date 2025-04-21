import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create logger
logger = logging.getLogger(__name__)
cluster = None
bucket = None
collection = None

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "logger"
]
