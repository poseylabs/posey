from fastapi import Request, Depends, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config.settings import settings
from app.config import logger

from typing import Optional, Dict, Any
from pydantic import BaseModel
import httpx
import json


AUTH_SERVICE_URL = settings.AUTH_SERVICE_INTERNAL_URL # Use the internal Docker service URL
SESSION_VERIFY_ENDPOINT = "/auth/session"

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        excluded_paths = ["/health", "/docs", "/openapi.json", "/openapi.json/", "/metrics"]
        if request.method == "OPTIONS" or request.url.path in excluded_paths:
            logger.debug(f"Skipping auth for path: {request.url.path}")
            return await call_next(request)

        logger.debug(f"AuthMiddleware running for: {request.url.path}")

        # --- Call Auth Service for Verification ---
        session_verify_url = f"{AUTH_SERVICE_URL}{SESSION_VERIFY_ENDPOINT}"
        
        # Forward relevant cookies from the incoming request
        cookies_to_forward = {}
        if "sAccessToken" in request.cookies:
            cookies_to_forward["sAccessToken"] = request.cookies["sAccessToken"]
        if "sIdRefreshToken" in request.cookies: # Forward refresh token if present
             cookies_to_forward["sIdRefreshToken"] = request.cookies["sIdRefreshToken"]
        # Add any other necessary cookies (e.g., anti-csrf? check ST docs/auth service)
        
        if not cookies_to_forward:
             logger.warning(f"No session cookies found for request: {request.url.path}")
             return JSONResponse(status_code=401, content={"detail": "Authentication required"})

        headers = {
            'Accept': 'application/json'
            # Forward other relevant headers? (e.g., origin?)
        }

        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Calling auth service: GET {session_verify_url}")
                response = await client.get(
                    session_verify_url,
                    cookies=cookies_to_forward,
                    headers=headers,
                    timeout=5.0 # Add a reasonable timeout
                )
                logger.debug(f"Auth service response status: {response.status_code}")

            if response.status_code == 200:
                auth_data = response.json()
                if auth_data.get("status") == "OK" and auth_data.get("user"):
                    user_data = auth_data["user"]
                    # Map received user data to request state
                    # Ensure keys match what get_current_user expects
                    user_state = {
                        "id": user_data.get("id"),
                        "email": user_data.get("email"),
                        "username": user_data.get("username"),
                        "role": user_data.get("role"),
                        # Add other fields if needed/provided by /auth/session
                        # "session": None, # We don't get the handle/payload here
                        # "tId": None,
                        # "rsub": None,
                    }
                    request.state.user = user_state
                    logger.debug(f"Auth successful via auth service. User: {user_state.get('id')}")
                    return await call_next(request)
                elif auth_data.get("status") == "NO_SESSION":
                    logger.info(f"No active session reported by auth service for {request.url.path}")
                    return JSONResponse(status_code=401, content={"detail": "No active session"})
                else:
                    logger.error(f"Auth service returned 200 but unexpected payload: {auth_data}")
                    return JSONResponse(status_code=500, content={"detail": "Invalid auth response"})
            
            elif response.status_code == 401:
                 logger.warning(f"Auth service returned 401 (Unauthorized) for {request.url.path}")
                 # Try parsing error detail from auth service
                 detail = "Unauthorized"
                 try:
                     error_data = response.json()
                     detail = error_data.get("message", detail)
                 except json.JSONDecodeError:
                     pass # Use default detail
                 return JSONResponse(status_code=401, content={"detail": detail})

            else:
                # Handle other potential errors from auth service
                logger.error(f"Auth service call failed with status {response.status_code} for {request.url.path}. Response: {response.text[:500]}")
                return JSONResponse(status_code=503, content={"detail": "Auth service unavailable or failed"})

        except httpx.RequestError as e:
            logger.error(f"HTTP error contacting auth service at {session_verify_url}: {e}", exc_info=True)
            return JSONResponse(status_code=503, content={"detail": "Failed to contact authentication service"})
        except Exception as e:
            # Ensure correct logging format and exception string conversion
            logger.error(f"AuthMiddleware: Unexpected error calling auth service: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during authentication check"}
            )

# --- User Model and Dependency (No change needed if it reads from request.state.user) ---

class User(BaseModel):
    id: str
    # Adjust fields based on what /auth/session actually returns and is stored in state
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True
        extra = "allow"

async def get_current_user(
    request: Request,
    # REMOVE SuperTokens dependency
) -> User:
    """Get the current authenticated user from the request state (set by middleware)."""
    if not hasattr(request.state, "user") or not request.state.user:
        logger.error("No user found in request state (AuthMiddleware should have set it)")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated (state missing)"
        )
    try:
        # Directly use the state set by the middleware
        user_data = request.state.user
        # Ensure keys match the User model
        return User(**user_data)
    except Exception as e:
        logger.error(f"Error creating user object from state: {e}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail="Invalid user data in state"
        )
