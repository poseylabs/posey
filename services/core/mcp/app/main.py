from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
import asyncio
import logging
from app.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncIterator
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle"""
    try:
        logger.info("Starting MCP server...")
        yield {}
    finally:
        logger.info("Shutting down MCP server...")

# Create FastAPI app
app = FastAPI(
    title="Posey MCP Server",
    lifespan=app_lifespan
)

# Create MCP server instance
mcp = FastMCP("posey-mcp")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register tool handler with MCP
@mcp.tool()
async def tool_handler(tool_name: str, **params) -> Dict[str, Any]:
    """Generic handler for all tool calls"""
    async with httpx.AsyncClient(timeout=settings.DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(
                f"{settings.AGENTS_SERVICE_URL}/mcp/tool/{tool_name}",
                json=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "error": f"Tool call failed: {str(e)}",
                "status": "error"
            }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/mcp/run")
async def run_tool(tool_name: str, params: Dict[str, Any]):
    """Endpoint to run MCP tools"""
    return await tool_handler(tool_name, **params)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    ) 
