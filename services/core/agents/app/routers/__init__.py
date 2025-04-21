"""Initialize the routers package and expose router objects."""

from .conversations import router as conversations_router
from .docs import router as docs_router
from .embeddings import router as embeddings_router
from .health import router as health_router
from .mcp import router as mcp_router
from .projects import router as projects_router
from .users import router as users_router
from .admin import router as admin_router
from .orchestrator.posey import router as posey_router

__all__ = [
    "conversations_router",
    "docs_router",
    "embeddings_router",
    "health_router",
    "mcp_router",
    "projects_router",
    "users_router",
    "admin_router",
    "posey_router",
] 