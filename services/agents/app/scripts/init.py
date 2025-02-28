import os
import asyncio
from app.config import logger
from app.db.migrate import run_all_migrations
from app.db.drop import drop_all_tables
from app.db.connection import db

async def init_db():
    """Initialize database with migrations"""
    try:
        logger.info("Starting database initialization...")
        
        # Initialize database connections
        await db.connect()
        logger.info("Database connections established")
        
        try:
            # Drop tables if requested
            if os.getenv('DROP_TABLES', 'false').lower() == 'true':
                logger.warning("DROP_TABLES is enabled - dropping all tables...")
                await drop_all_tables()
                logger.info("All tables dropped successfully")
            
            # Run migrations if enabled
            if os.getenv('RUN_MIGRATIONS', 'false').lower() == 'true':
                logger.info("Running migrations...")
                await run_all_migrations()
                logger.info("Migrations completed successfully")
                
            logger.info("Database initialization completed successfully")
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(init_db())
