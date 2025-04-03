import os
import sys
import asyncio
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config import settings, logger
from app.db.connection import check_postgres_connection

async def main():
    logger.info(f"Checking PostgreSQL connection to {settings.POSTGRES_HOST}...")
    
    try:
        # Try to connect to PostgreSQL
        if await check_postgres_connection():
            logger.info("PostgreSQL connection successful!")
            return True
        else:
            logger.error("PostgreSQL connection failed")
            return False
    except Exception as e:
        logger.error(f"Error checking PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
