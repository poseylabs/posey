from pathlib import Path
import asyncio
import re
from typing import List, Tuple, Optional
from datetime import datetime
import httpx
from asyncpg.exceptions import DuplicateTableError
import hashlib
import os
import glob
from sqlalchemy import text
from app.config import logger, settings
from app.db.connection import db

from app.config.settings import settings
from app.db.migrations.couchbase_setup import setup_couchbase
from app.db.migrations.qdrant_setup import setup_qdrant

class MigrationError(Exception):
    """Custom exception for migration errors"""
    pass

class Migration:
    """Represents a single database migration"""
    def __init__(self, version: int, name: str, path: Path):
        self.version = version
        self.name = name
        self.path = path
        self._sql: Optional[str] = None

    @property
    def sql(self) -> str:
        """Lazy load and cache the SQL content"""
        if self._sql is None:
            with open(self.path) as f:
                self._sql = f.read()
        return self._sql

    @classmethod
    def from_file(cls, file_path: Path) -> Optional['Migration']:
        """Create a Migration instance from a file path"""
        if not file_path.suffix == '.sql':
            return None
            
        match = re.match(r"(\d{3})_([\w_]+)\.sql", file_path.name)
        if not match:
            return None
            
        version = int(match.group(1))
        name = match.group(2)
        return cls(version, name, file_path)

class MigrationManager:
    """Manages database migrations"""
    def __init__(self):
        self.migrations_dir = Path(__file__).parent / "migrations"
        self._migrations: Optional[List[Migration]] = None

    @property
    def migrations(self) -> List[Migration]:
        """Lazy load and cache migrations"""
        if self._migrations is None:
            self._migrations = self._load_migrations()
        return self._migrations

    def _load_migrations(self) -> List[Migration]:
        """Load all migrations from the migrations directory"""
        migrations = []
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            if migration := Migration.from_file(file_path):
                migrations.append(migration)
        return sorted(migrations, key=lambda m: m.version)

    async def get_applied_versions(self, conn) -> set:
        """Get all applied migration versions"""
        try:
            result = await conn.fetch("""
                SELECT version FROM schema_migrations 
                ORDER BY version
            """)
            return {r['version'] for r in result}
        except Exception:
            return set()

    async def initialize_schema_migrations(self, conn):
        """Ensure schema_migrations table exists"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        """)

    async def apply_migration(self, conn, migration: Migration):
        """Apply a single migration"""
        try:
            async with conn.transaction():
                logger.info(f"Applying migration {migration.version}: {migration.name}")
                
                # Execute migration
                await conn.execute(migration.sql)
                
                # Record migration
                await conn.execute("""
                    INSERT INTO schema_migrations (version, name) 
                    VALUES ($1, $2)
                """, migration.version, migration.name)
                
                logger.info(f"Successfully applied migration {migration.version}")
                
        except DuplicateTableError as e:
            logger.warning(f"Object already exists in migration {migration.version}: {str(e)}")
            # Still record migration as applied
            await conn.execute("""
                INSERT INTO schema_migrations (version, name) 
                VALUES ($1, $2)
                ON CONFLICT (version) DO NOTHING
            """, migration.version, migration.name)
        except Exception as e:
            logger.error(f"Error applying migration {migration.version}: {str(e)}")
            raise MigrationError(f"Migration {migration.version} failed: {str(e)}")

    # Add migration dependencies
    async def check_dependencies(self, migration: Migration) -> bool:
        """Check if migration dependencies are satisfied"""
        if hasattr(migration, 'depends_on'):
            for dep_version in migration.depends_on:
                if dep_version not in await self.get_applied_versions():
                    raise MigrationError(f"Missing dependency: {dep_version}")

    # Add dry run capability
    async def dry_run(self, migration: Migration) -> bool:
        """Test migration without applying changes"""
        async with db.get_pg_conn() as conn:
            async with conn.transaction() as txn:
                await conn.execute(migration.sql)
                await txn.rollback()
                return True

    async def run_migrations(self):
        """Run all pending migrations"""
        try:
            async with db.get_pg_conn() as conn:
                # Initialize schema_migrations table
                await self.initialize_schema_migrations(conn)
                
                # Get applied migrations
                applied_versions = await self.get_applied_versions(conn)
                
                # Apply pending migrations
                for migration in self.migrations:
                    if migration.version not in applied_versions:
                        await self.apply_migration(conn, migration)
                        
            logger.info("All migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Migration error: {str(e)}")
            raise

async def wait_for_services():
    """Wait for required services to be ready"""
    retries = 5
    backoff = 2
    
    # Wait for PostgreSQL
    while retries > 0:
        try:
            async with db.get_pg_conn() as conn:
                await conn.execute('SELECT 1')
                logger.info("PostgreSQL is ready")
                break
        except Exception as e:
            logger.warning(f"Waiting for PostgreSQL... ({retries} retries left)")
            retries -= 1
            if retries == 0:
                raise Exception("PostgreSQL failed to become ready")
            await asyncio.sleep(backoff)
            backoff *= 2

    # Wait for Qdrant
    retries = 5
    backoff = 2
    while retries > 0:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.QDRANT_FULL_URL}/collections")
                if response.status_code == 200:
                    logger.info("Qdrant is ready")
                    break
        except Exception:
            logger.warning(f"Waiting for Qdrant... ({retries} retries left)")
            retries -= 1
            if retries == 0:
                raise Exception("Qdrant failed to become ready")
            await asyncio.sleep(backoff)
            backoff *= 2

async def run_all_migrations():
    """Run all database migrations"""
    try:
        logger.info("Starting database migrations...")
        migrations_dir = settings.MIGRATIONS_DIR
        
        if not migrations_dir.exists():
            logger.error(f"Migrations directory not found: {migrations_dir}")
            raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

        # Get all .sql files in migrations directory
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
        
        if not migration_files:
            logger.warning("No migration files found")
            return

        async with db.session() as session:
            for migration_file in migration_files:
                logger.info(f"Running migration: {migration_file}")
                
                try:
                    # Read and execute migration file
                    with open(migration_file, 'r') as f:
                        sql = f.read()
                        
                    def split_sql(sql):
                        """Split SQL while preserving dollar-quoted blocks and statements"""
                        statements = []
                        current = []
                        in_dollar_quote = False
                        dollar_quote_tag = ''
                        
                        for line in sql.splitlines():
                            line = line.strip()
                            if not line or line.startswith('--'):
                                continue
                                
                            # Handle dollar quoting
                            if not in_dollar_quote and '$$' in line:
                                in_dollar_quote = True
                                current.append(line)
                                continue
                            elif in_dollar_quote and '$$' in line:
                                in_dollar_quote = False
                                current.append(line)
                                if line.rstrip().endswith(';'):
                                    statements.append('\n'.join(current))
                                    current = []
                                continue
                            
                            if in_dollar_quote:
                                current.append(line)
                                continue
                                
                            current.append(line)
                            if line.rstrip().endswith(';'):
                                statements.append('\n'.join(current))
                                current = []
                                
                        if current:
                            statements.append('\n'.join(current))
                            
                        return statements
                        
                    statements = split_sql(sql)
                    
                    # Execute the entire migration file as a single transaction
                    async with session.begin():
                        conn = await session.connection()
                        # Execute each statement separately
                        for statement in statements:
                            if statement.strip():  # Skip empty statements
                                await conn.execute(text(statement))
                    
                except Exception as e:
                    logger.error(f"Migration failed: {migration_file}")
                    logger.error(f"Error: {e}")
                    raise

        logger.info("All migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        raise

async def get_migration_version():
    """Get current database migration version"""
    try:
        async with db.session() as session:
            result = await session.execute(text("""
                SELECT version 
                FROM schema_migrations
                ORDER BY version DESC 
                LIMIT 1
            """))
            version = result.scalar()
            return version or 0
            
    except Exception:
        return 0

# Add versioning to track applied migrations
async def get_applied_migrations(conn) -> List[int]:
    """Get list of already applied migration versions"""
    try:
        result = await conn.fetch(
            "SELECT version FROM schema_migrations ORDER BY version"
        )
        return [r['version'] for r in result]
    except Exception:
        return []

# Add checksum validation
async def validate_migration(conn, version: int, name: str, content: str):
    """Validate migration hasn't been modified after being applied"""
    checksum = hashlib.md5(content.encode()).hexdigest()
    result = await conn.fetchrow(
        "SELECT checksum FROM schema_migrations WHERE version = $1",
        version
    )
    if result and result['checksum'] != checksum:
        raise Exception(f"Migration {version}_{name} has been modified after being applied")

if __name__ == "__main__":
    asyncio.run(run_all_migrations())
