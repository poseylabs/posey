from sqlalchemy import text
from app.config import logger
from app.db.connection import db

async def drop_all_tables():
    """Drop all tables in the database"""
    try:
        async with db.get_pg_conn() as conn:
            # Get list of all tables
            result = await conn.fetch("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = [r['tablename'] for r in result]

            # Drop each table
            for table in tables:
                logger.info(f"Dropping table: {table}")
                await conn.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
            
            logger.info("All tables dropped successfully")

    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        raise 
