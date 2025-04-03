from fastapi import Request, Depends, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from jose import jwt, JWTError
from app.config.settings import settings
from app.config import logger
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for OPTIONS requests and certain paths
        if request.method == "OPTIONS" or request.url.path in ["/health", "/docs", "/openapi.json", "/openapi.json/"]:
            return await call_next(request)
        
        token = request.cookies.get("sAccessToken")  # SuperTokens default cookie name
        
        if not token:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.error("Missing or invalid authorization token")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid authorization token"}
                )
            token = auth_header.split(" ")[1]

        try:
            # First decode without verification to check claims
            unverified_payload = jwt.decode(
                token,
                None,
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_iss": False
                }
            )
            
            if not unverified_payload.get("st-jwt"):
                logger.error("Invalid token format - missing st-jwt claim")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token format"}
                )

            # Set the user state before calling next
            user_state = {
                "id": unverified_payload.get("sub"),
                "session": unverified_payload.get("sessionHandle"),
                "tId": unverified_payload.get("tId"),
                "rsub": unverified_payload.get("rsub"),
                "email": unverified_payload.get("email"),
                "username": unverified_payload.get("email", "").split("@")[0] if unverified_payload.get("email") else None
            }

            request.state.user = user_state
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Auth Middleware - Error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=401,
                content={"detail": f"Authentication error: {str(e)}"}
            )

class User(BaseModel):
    id: str
    session: str | None = None
    tId: str | None = None
    rsub: str | None = None
    email: str | None = None
    username: str | None = None

    class Config:
        from_attributes = True
        extra = "allow"

async def get_current_user(
    request: Request,
) -> User:
    """Get the current authenticated user from the request state"""
    
    if not hasattr(request.state, "user") or not request.state.user:
        logger.error("No user found in request state")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    try:
        user_data = request.state.user

        user = User(
            id=user_data["id"],
            session=user_data.get("session"),
            tId=user_data.get("tId"),
            rsub=user_data.get("rsub"),
            email=user_data.get("email"),
            username=user_data.get("username")
        )

        return user
    except Exception as e:
        logger.error(f"Error creating user object: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid user data"
        )
