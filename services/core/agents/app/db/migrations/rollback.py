from app.config.settings import settings
MIGRATIONS_DIR = settings.MIGRATIONS_DIR

async def rollback_migration(conn, version: int) -> bool:
    """Rollback a specific migration version"""
    try:
        # Start transaction
        async with conn.transaction():
            # Get rollback SQL
            rollback_file = f"{version:03d}_rollback.sql"
            rollback_path = MIGRATIONS_DIR / rollback_file
            
            if not rollback_path.exists():
                raise Exception(f"Rollback file {rollback_file} not found")
                
            # Execute rollback
            rollback_sql = rollback_path.read_text()
            await conn.execute(rollback_sql)
            
            # Update schema_migrations
            await conn.execute(
                "DELETE FROM schema_migrations WHERE version = $1",
                version
            )
            
        return True
    except Exception as e:
        logger.error(f"Migration rollback failed: {str(e)}")
        raise 
