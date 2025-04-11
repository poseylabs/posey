from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from app.config import logger, db, Base
from app.config.logging import setup_logging
from app.config.settings import settings
from app.routers import (
    conversations, docs, embeddings, 
    health, mcp, projects, users
)
from app.routers.orchestrator import posey
from contextlib import asynccontextmanager
import json
# from app.middleware.rate_limit import RateLimitMiddleware
from app.models.schemas import Base
from app.middleware.auth import AuthMiddleware
from app.utils.serializers import serialize_response, PoseyJSONEncoder
from app.utils.connection import verify_connections
from app.config.defaults import LLM_CONFIG
import logging

# Override settings if needed for debugging
settings.LOG_LEVEL = "DEBUG"

# Configure logging with DEBUG level
setup_logging(settings.LOG_LEVEL)
logger.info(f"Starting Posey Agents API with log level: {settings.LOG_LEVEL}")
logger.info("Setting package loggers to DEBUG level")

# Set specific loggers to DEBUG level
for module in ["app.orchestrators", "app.utils.agent", "app.utils.message_handler"]:
    logging.getLogger(module).setLevel(logging.DEBUG)

# Parse JSON strings if needed
def parse_json_env(value, default=None):
    if isinstance(value, str):
        try:
            return json.loads(value)
        finally:
            return value

ALLOWED_ORIGINS = parse_json_env(settings.ALLOWED_ORIGINS, ["*"])
ALLOWED_HOSTS = parse_json_env(settings.ALLOWED_HOSTS, ["*"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    try:
        logger.info("[LIFESPAN] Startup initiated.")
        
        # Initialize database connections
        logger.info("[LIFESPAN] Attempting db.connect_all()...")
        await db.connect_all()
        logger.info("[LIFESPAN] db.connect_all() completed.")
        
        # Explicitly log Qdrant client status AFTER connect_all
        if db._qdrant_client:
            logger.info(f"[LIFESPAN] db._qdrant_client is SET after connect_all. Type: {type(db._qdrant_client)}")
        else:
            logger.error("[LIFESPAN] db._qdrant_client is NONE after connect_all.")
            # Optionally raise here again if it should definitely be set
            # raise RuntimeError("Qdrant client not set after connect_all in lifespan")

        # Create tables using the engine
        logger.info("[LIFESPAN] Attempting DB table creation...")
        async with db.async_engine.begin() as conn:
            # Just create tables - init.py handles drops if needed
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[LIFESPAN] DB table creation completed.")
        
        # --> Add logging HERE <--
        logger.info(f"[LIFESPAN] DB instance ID: {id(db)}")
        # Check internal attributes directly to avoid triggering property errors
        logger.info(f"[LIFESPAN] Postgres pool initialized: {hasattr(db, '_pg_pool') and db._pg_pool is not None}")
        logger.info(f"[LIFESPAN] Couchbase cluster initialized: {hasattr(db, '_cb_cluster') and db._cb_cluster is not None}")
        logger.info(f"[LIFESPAN] Qdrant client initialized: {hasattr(db, '_qdrant_client') and db._qdrant_client is not None}")

        # --> ADD LOG LINE HERE <--
        logger.info("Verifying database connections after initialization...")
        # Verify connections
        connection_status = await verify_connections(LLM_CONFIG)
        for service, status in connection_status.items():
            if status:
                logger.info(f"Successfully connected to {service}")
            else:
                logger.error(f"Failed to connect to {service}")
        
        logger.info("Database connections established")
        
        logger.info("[LIFESPAN] Startup sequence fully completed. Ready for requests.")
        
        yield
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        logger.info("Shutting down...")
        try:
            await db.close_all()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Initialize app
app = FastAPI(
    title="Posey Agents API",
    description="API for managing Posey AI agents and tasks",
    version="0.1.0",
    lifespan=lifespan
)

# Add debug middleware first
@app.middleware("http")
async def debug_request(request: Request, call_next):
    response = await call_next(request)
    return response

# Add auth middleware before CORS
app.add_middleware(AuthMiddleware)

# Then configure CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[] # Prefer regex for wildcard domains
    allow_origin_regex=r"https?://((localhost|127\.0\.0\.1)|[a-zA-Z0-9-]+\.posey\.ai)(:[0-9]+)?",  # Allow localhost, 127.0.0.1, and *.posey.ai (http/https)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

# Then add rate limiting (if needed)
# app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Add exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle exceptions and ensure proper serialization"""
    error_response = {
        "status": "error",
        "message": str(exc),
        "type": exc.__class__.__name__
    }
    
    return JSONResponse(
        status_code=500,
        content=serialize_response(error_response)
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Agent Backend!"}

app.include_router(posey.router)
app.include_router(docs.router)
app.include_router(health.router)
app.include_router(embeddings.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(conversations.router)
app.include_router(mcp.router)


@app.middleware("http")
async def debug_request(request: Request, call_next):
    response = await call_next(request)
    return response
