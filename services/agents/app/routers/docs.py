from fastapi import FastAPI, APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

app = FastAPI()

# Custom /docs route
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")

# Custom /openapi.json route
@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

router = APIRouter(
    prefix="/docs",
    tags=["documentation"],
    responses={404: {"description": "Not found"}},
)

@router.get("")
async def get_docs() -> Dict[str, Any]:
    """
    Get API documentation information.
    This is a placeholder - you can expand this to return actual API documentation.
    """
    return {
        "version": "1.0.0",
        "title": "Posey Agents API",
        "description": "API documentation for the Posey Agents service",
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Root endpoint - returns welcome message"
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint"
            },
            {
                "path": "/docs",
                "method": "GET",
                "description": "Get API documentation"
            }
        ]
    }

@router.get("/openapi")
async def get_openapi_docs() -> Dict[str, Any]:
    """
    Get OpenAPI documentation.
    This is a placeholder - you can expand this to return actual OpenAPI documentation.
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Posey Agents API",
            "version": "1.0.0",
            "description": "API for managing Posey AI agents and tasks"
        },
        "paths": {
            "/": {
                "get": {
                    "summary": "Root endpoint",
                    "description": "Returns welcome message",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "message": "Welcome to the Agent Backend!"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
