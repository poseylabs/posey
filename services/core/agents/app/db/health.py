from typing import Dict, Any
import asyncpg
from app.config import settings, logger
from app.db.connection import DatabaseConnection

async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and basic functionality"""
    status = {
        "postgres": {
            "connected": False,
            "pool_size": 0,
            "active_connections": 0,
            "latency_ms": 0
        },
        "migrations": {
            "applied_count": 0,
            "pending_count": 0,
            "last_applied": None
        }
    }
    
    try:
        # Check PostgreSQL
        conn = await asyncpg.connect(settings.POSTGRES_DSN_POSEY)
        await conn.execute("SELECT 1")
        status["postgres"]["connected"] = True
        
        # Check migrations
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM schema_migrations"
        )
        status["migrations"]["applied_count"] = result
        
        # Check connection pool
        pool = await DatabaseConnection.get_pool()
        status["postgres"]["pool_size"] = pool.get_size()
        status["postgres"]["active_connections"] = pool.get_used_size()
        
        await conn.close()
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
    
    return status 
