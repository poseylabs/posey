from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import logfire
from pydantic_ai import Agent
from contextlib import asynccontextmanager
import json

from app.config import logger, db, Base
from app.config.defaults import LLM_CONFIG
from app.config.logging import setup_logging
from app.config.settings import settings
from app.middleware.auth import AuthMiddleware
from app.routers import (
    conversations_router,
    docs_router,
    embeddings_router,
    health_router,
    mcp_router,
    projects_router,
    users_router,
    admin_router,
    posey_router
)
from app.models.schemas import Base
from app.utils.serializers import serialize_response, PoseyJSONEncoder
from app.utils.connection import verify_connections
from app.utils.minion_registry import MinionRegistry


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
        
        # --- Logfire Configuration ---
        try:
            logfire.configure()
            logfire.instrument_httpx(capture_all=True) # Instrument httpx for LLM calls
            Agent.instrument_all() # Instrument all Pydantic AI agents globally
            logger.info("[LIFESPAN] Logfire configured and instrumentation enabled.")
        except Exception as logfire_err:
            logger.error(f"[LIFESPAN] Failed to configure Logfire: {logfire_err}", exc_info=True)
            # Decide if this is fatal or just a warning
        # --- End Logfire --- 
        
        # Initialize database connections
        logger.info("[LIFESPAN] Attempting db.connect_all()...")
        await db.connect_all()
        logger.info("[LIFESPAN] db.connect_all() completed.")
        
        # Explicitly log Qdrant client status AFTER connect_all
        if hasattr(db, '_qdrant_client') and db._qdrant_client:
            logger.info(f"[LIFESPAN] db._qdrant_client is SET after connect_all. Type: {type(db._qdrant_client)}")
        else:
            logger.error("[LIFESPAN] db._qdrant_client is NONE after connect_all.")
            # Decide if this is fatal
            # raise RuntimeError("Qdrant client not set after connect_all in lifespan")

        # Create tables using the engine
        logger.info("[LIFESPAN] Attempting DB table creation...")
        async with db.async_engine.begin() as conn:
            # Just create tables - init.py handles drops if needed
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[LIFESPAN] DB table creation completed.")
        
        # Log connection details
        logger.info(f"[LIFESPAN] DB instance ID: {id(db)}")
        logger.info(f"[LIFESPAN] Postgres pool initialized: {hasattr(db, '_pg_pool') and db._pg_pool is not None}")
        logger.info(f"[LIFESPAN] Couchbase cluster initialized: {hasattr(db, '_cb_cluster') and db._cb_cluster is not None}")
        logger.info(f"[LIFESPAN] Qdrant client initialized: {hasattr(db, '_qdrant_client') and db._qdrant_client is not None}")

        # Verify connections
        logger.info("[LIFESPAN] Verifying database connections after initialization...")
        connection_status = await verify_connections(LLM_CONFIG) 
        for service, status in connection_status.items():
            if status:
                logger.info(f"[LIFESPAN] Successfully connected to {service}")
            else:
                logger.error(f"[LIFESPAN] Failed to connect to {service}")
        
        logger.info("[LIFESPAN] Database connections established")
        
        # Initialize MinionRegistry and store in app state
        logger.info("[LIFESPAN] Initializing MinionRegistry...")
        app.state.minion_registry = MinionRegistry() 
        logger.info("[LIFESPAN] MinionRegistry initialized and stored in app state")

        # ---> START: Pre-initialize active minions <---
        logger.info("[LIFESPAN] Pre-initializing active minions...")
        app.state.initialized_minions = {} # Store initialized minions here
        failed_minions_count = 0

        try:
            # Pass the main DBManager instance (db) to get_minions
            initialized_instances = await app.state.minion_registry.get_minions(db) 
            
            # Store the successfully initialized instances in app.state for easy access
            app.state.initialized_minions = initialized_instances
            
            # Log the outcome - get_minions already logs failures during its process
            if len(app.state.initialized_minions) == len(app.state.minion_registry._loaded_classes):
                 logger.info(f"[LIFESPAN] All {len(app.state.initialized_minions)} active minions initialized successfully.")
            else:
                 # Count failures by comparing loaded classes vs initialized instances
                 failed_minions_count = len(app.state.minion_registry._loaded_classes) - len(app.state.initialized_minions)
                 logger.warning(f"[LIFESPAN] Finished minion initialization. Success: {len(app.state.initialized_minions)}, Failures: {failed_minions_count}")
                 # Detailed failures are already logged within get_minions/get_minion

        except Exception as registry_e:
            logger.error(f"[LIFESPAN] Error during minion pre-initialization phase using get_minions: {registry_e}", exc_info=True)
            # Depending on severity, might want to raise here
            
        # ---> END: Pre-initialize active minions <---

        logger.info("[LIFESPAN] Startup sequence fully completed. Ready for requests.")
        
        yield
    except Exception as e:
        logger.error(f"[LIFESPAN] Startup failed critically: {e}", exc_info=True)
        # Depending on the error, you might want to prevent the app from starting
        raise
    finally:
        logger.info("Shutting down...")
        try:
            # Optional: Call registry cleanup if it exists and is needed
            if hasattr(app.state, 'minion_registry') and hasattr(app.state.minion_registry, 'cleanup'):
                 await app.state.minion_registry.cleanup()

            # Clear initialized minions if stored separately
            if hasattr(app.state, 'initialized_minions'):
                del app.state.initialized_minions
                
            await db.close_all()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

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

# --- Include Routers --- 
app.include_router(posey_router)
app.include_router(docs_router)
app.include_router(health_router)
app.include_router(embeddings_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(conversations_router)
app.include_router(mcp_router)
app.include_router(admin_router) # Include the admin router
# --- End Include Routers --- 
