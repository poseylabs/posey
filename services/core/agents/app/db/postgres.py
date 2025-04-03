import asyncpg
from app.config import logger, settings

async def get_pool():
    """Create and return a connection pool"""
    try:
        logger.info(f"Creating database pool with DSN: {settings.POSTGRES_DSN_POSEY}")
        
        pool = await asyncpg.create_pool(
            dsn=settings.POSTGRES_DSN_POSEY,
            min_size=2,
            max_size=10,
            command_timeout=60,
            # Optional: Add SSL context if needed
            # ssl=ssl_context,
        )
        
        # Test the connection
        async with pool.acquire() as conn:
            await conn.execute('SELECT 1')
            logger.info("Database connection successful")
            
        return pool
    except Exception as e:
        logger.error(f"Error creating database pool: {str(e)}")
        raise

async def close_pool(pool):
    """Close the connection pool"""
    if pool:
        await pool.close() 
