from fastapi import Request, Depends, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from jose import jwt, JWTError
from app.config.settings import settings
from app.config import logger
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from pydantic import BaseModel

# Import SuperTokens session verification
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.session.interfaces import SessionClaimValidator
from supertokens_python.recipe.session.exceptions import TryRefreshTokenError, UnauthorisedError
from supertokens_python.interfaces import SuperTokensError

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for OPTIONS requests and certain paths
        # Keep health/docs open, but admin routes should be protected
        excluded_paths = ["/health", "/docs", "/openapi.json", "/openapi.json/"]
        if request.method == "OPTIONS" or request.url.path in excluded_paths:
            logger.debug(f"Skipping auth for path: {request.url.path}")
            return await call_next(request)

        logger.debug(f"AuthMiddleware running for: {request.url.path}")
        session: Optional[SessionContainer] = None
        try:
            # Use SuperTokens verify_session
            # session_required=False means it won't raise if no session exists,
            # allowing further checks or public routes if needed later.
            # For admin routes, we actually *want* it to fail if no session.
            # Let's make it required for now, can adjust later if needed.
            session = await verify_session()(request) # Call the decorator result
            logger.debug("SuperTokens session verified successfully.")

            if session is None:
                 # This case might not be reachable if session_required=True (default)
                 logger.error("AuthMiddleware: Session is None after verify_session (unexpected)")
                 return JSONResponse(status_code=401, content={"detail": "Session not found"})

            # Extract user info from the verified session
            user_id = session.get_user_id()
            payload = session.get_access_token_payload()
            user_state = {
                "id": user_id,
                "session": session.get_handle(),
                "tId": payload.get("tId"),
                "rsub": payload.get("rsub"),
                "email": payload.get("email"),
                "username": payload.get("username") or (payload.get("email", "").split("@")[0] if payload.get("email") else None)
                # Add any other relevant claims from payload
            }
            request.state.user = user_state
            logger.debug(f"User state set for user_id: {user_id}")
            response = await call_next(request)
            return response

        # Handle SuperTokens specific errors (like refresh needed or unauthorized)
        except (TryRefreshTokenError, UnauthorisedError) as e:
             # These are typically handled by the SuperTokensMiddleware + frontend SDK
             # Logging them here might be redundant but can be useful for debugging
             logger.warning(f"AuthMiddleware: SuperTokens session error ({type(e).__name__}): {e}")
             # Reraise or let SuperTokensMiddleware handle it?
             # For now, let the default ST handler manage the response
             # Return a generic 401 might interfere with ST refresh mechanism
             # return JSONResponse(status_code=401, content={"detail": "Session expired or invalid"})
             raise e # Re-raise for SuperTokensMiddleware to handle

        except SuperTokensError as e:
            # Catch other potential SuperTokens errors
            logger.error(f"AuthMiddleware: SuperTokens general error: {str(e)}", exc_info=True)
            # Let the ST exception handler deal with this
            raise e

        except Exception as e:
            logger.error(f"AuthMiddleware: Unexpected error during authentication: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"Internal server error during authentication"}
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
    session: SessionContainer = Depends(verify_session()) # Use verify_session dependency
) -> User:
    """Get the current authenticated user via SuperTokens session."""
    if not session:
        # Should not happen if verify_session() is used without optional=True
        logger.error("get_current_user: No session found (unexpected)")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = session.get_user_id()
        payload = session.get_access_token_payload()
        
        # Reconstruct user from session info
        user = User(
            id=user_id,
            session=session.get_handle(),
            tId=payload.get("tId"),
            rsub=payload.get("rsub"),
            email=payload.get("email"),
            username=payload.get("username") or (payload.get("email", "").split("@")[0] if payload.get("email") else None)
            # Add other fields from payload if needed
        )
        return user
    except Exception as e:
        logger.error(f"Error creating user object from session: {e}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail="Invalid user session data"
        )
