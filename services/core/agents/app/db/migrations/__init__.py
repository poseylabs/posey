import os
import re
from typing import List, Tuple

from app.config import logger
from app.config.settings import settings


class MigrationManager:
    def __init__(self):
        self.migrations_path = os.path.dirname(__file__)
        
    def get_migrations(self) -> List[Tuple[int, str]]:
        """Get sorted list of migrations"""
        migration_files = []
        for filename in os.listdir(self.migrations_path):
            if match := re.match(r"V(\d+)__.*\.sql", filename):
                version = int(match.group(1))
                migration_files.append((version, filename))
        return sorted(migration_files)
    
    async def apply_migrations(self, db_pool):
        """Apply pending migrations"""
        
        logger.info("Applying migrations...")
        logger.info(f"POSTGRES_USER: {settings.POSTGRES_USER}")
        logger.info(f"POSTGRES_PASSWORD: {settings.POSTGRES_PASSWORD}")
        logger.info(f"POSTGRES_HOST: {settings.POSTGRES_HOST}")
        logger.info(f"POSTGRES_PORT: {settings.POSTGRES_PORT}")
        logger.info(f"POSTGRES_DB_POSEY: {settings.POSTGRES_DB_POSEY}")
        logger.info(f"POSTGRES_DSN_POSEY: {settings.POSTGRES_DSN_POSEY}")

        try:
            # Create migrations table if it doesn't exist
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Get applied migrations
                applied = await conn.fetch("SELECT version FROM schema_migrations")
                applied_versions = {row['version'] for row in applied}
                
                # Apply pending migrations
                for version, filename in self.get_migrations():
                    if version not in applied_versions:
                        migration_path = os.path.join(self.migrations_path, filename)
                        with open(migration_path) as f:
                            sql = f.read()
                            
                        async with conn.transaction():
                            await conn.execute(sql)
                            await conn.execute(
                                "INSERT INTO schema_migrations (version) VALUES ($1)",
                                version
                            )
                        logger.info(f"Applied migration {filename}")
                        
        except Exception as e:
            logger.error(f"Error applying migrations: {e}")
            raise
