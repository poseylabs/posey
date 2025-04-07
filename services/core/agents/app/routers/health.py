from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict
import asyncio
import psutil
from app.config import logger, db
from app.models.responses import StandardResponse
from app.utils.response_utils import standardize_response

router = APIRouter(
    prefix="/health",
    tags=["health"],
    redirect_slashes=False  # Prevent redirects for trailing slashes
)

# Initialize database - REMOVED: Use shared db instance from app.config
# db = Database()

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
    """Health check endpoint - returns healthy overall,
       but reports actual DB connection statuses."""
    # Run checks concurrently with timeout
    postgres_ok, couchbase_ok, qdrant_ok = await asyncio.gather(
        check_db_with_timeout(check_postgres),
        check_db_with_timeout(check_couchbase),
        check_db_with_timeout(check_qdrant),
        return_exceptions=True # Allow individual checks to fail without stopping others
    )

    # Log errors if checks failed (gather returns exception objects if return_exceptions=True)
    if isinstance(postgres_ok, Exception):
        logger.error(f"Postgres check gather error: {postgres_ok}")
        postgres_ok = False
    if isinstance(couchbase_ok, Exception):
        logger.error(f"Couchbase check gather error: {couchbase_ok}")
        couchbase_ok = False
    if isinstance(qdrant_ok, Exception):
        logger.error(f"Qdrant check gather error: {qdrant_ok}")
        qdrant_ok = False

    # Determine overall status - keeping 'healthy' for now as per original docstring
    overall_status = "healthy"
    # Optional: Change logic if overall status should depend on DBs
    # if not all([postgres_ok, couchbase_ok, qdrant_ok]):
    #     overall_status = "degraded"

    return HealthStatus(
        status=overall_status,
        postgres=bool(postgres_ok),
        couchbase=bool(couchbase_ok),
        qdrant=bool(qdrant_ok),
        system={
            'memory_used': psutil.Process().memory_info().rss / 1024 / 1024,
            'cpu_percent': psutil.cpu_percent()
        }
    )
