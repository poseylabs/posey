from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict
import asyncio
import psutil
from app.config.database import Database
from app.config import logger
from app.models.responses import StandardResponse
from app.utils.response_utils import standardize_response

router = APIRouter(
    prefix="/health",
    tags=["health"],
    redirect_slashes=False  # Prevent redirects for trailing slashes
)

# Initialize database
db = Database()

class HealthStatus(BaseModel):
    status: str
    error: Optional[str] = None
    postgres: bool
    couchbase: bool
    qdrant: bool
    system: dict

async def check_postgres():
    try:
        conn = db.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        finally:
            db.pool.putconn(conn)
    except Exception as e:
        logger.error(f"Postgres check failed: {str(e)}")
        return False

async def check_couchbase():
    try:
        result = db.cluster.ping()
        return bool(result)
    except Exception as e:
        logger.error(f"Couchbase check failed: {str(e)}")
        return False

async def check_qdrant():
    try:
        # Use the initialized Qdrant client
        response = await db.qdrant_client.get_collections()
        return bool(response)
    except Exception as e:
        logger.error(f"Qdrant check failed: {str(e)}")
        logger.info(f"Qdrant URL: {db.qdrant_url}")
        return False

async def check_db_with_timeout(check_func, timeout=15.0):
    try:
        return await asyncio.wait_for(check_func(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Timeout occurred while checking {check_func.__name__}")
        return False
    except Exception as e:
        logger.error(f"Error occurred while checking {check_func.__name__}: {str(e)}")
        return False

@router.get("", response_model=StandardResponse[HealthStatus])
@standardize_response
async def health_check(request: Request):
    """Health check endpoint - returns healthy even if databases are not connected"""
    return HealthStatus(
        status="healthy",
        postgres=False,  # We'll update these when databases are ready
        couchbase=False,
        qdrant=False,
        system={
            'memory_used': psutil.Process().memory_info().rss / 1024 / 1024,
            'cpu_percent': psutil.cpu_percent()
        }
    )
