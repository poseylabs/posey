from fastapi import APIRouter, HTTPException
from app.middleware.response import standardize_response
from app.config import logger, db
from app.db.migrations import MigrationManager
from app.db.migrations.qdrant_setup import setup_qdrant
from app.db.migrations.couchbase_setup import setup_couchbase
from app.db.postgres import get_pool

router = APIRouter(
    prefix="/migrations",
    tags=["migrations"]
)

@router.get("/run")
@standardize_response
async def run_migrations():
    """Run all pending migrations"""
    try:
        logger.info("Initializing database connection pool...")
        # Initialize the connection pool if not already done
        if not db.pool:
            pool = await get_pool()
            db.pool = pool  # This should now work with the proper Database class

        if not db.pool:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize database connection pool"
            )

        logger.info("Running migrations...")
        migration_manager = MigrationManager()
        await migration_manager.apply_migrations(db.pool)
        
        logger.info("Setting up Qdrant...")
        await setup_qdrant()
        
        logger.info("Setting up Couchbase...")
        await setup_couchbase()
        
        return {"message": "Migrations completed successfully"}
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db.pool:
            await db.pool.close()
            db.pool = None  # Clear the pool reference after closing
