from functools import wraps
from typing import Any, Dict, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from app.config import logger # Import logger

def standardize_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Response:
        try:
            result = await func(*args, **kwargs)
            # --- Add Logging --- 
            logger.debug(f"[Decorator] Result from function '{func.__name__}': {result!r}") 
            # --- End Logging --- 
            response_data = {}
            status_code = 200

            if isinstance(result, dict) and "success" in result:
                response_data = result
                if not result["success"] and "error" in result and "code" in result["error"]:
                    error_code = result["error"]["code"]
                    if isinstance(error_code, int) and 100 <= error_code <= 599:
                        status_code = error_code
                    else:
                        status_code = 500
            else:
                response_data = {
                    "success": True,
                    "data": result
                }
            # --- Add Logging --- 
            logger.debug(f"[Decorator] Response data being sent: {response_data!r}")
            # --- End Logging ---
            return JSONResponse(content=response_data, status_code=status_code)

        except HTTPException as e:
            # --- Add Logging ---
            logger.error(f"[Decorator] Caught HTTPException: Status={e.status_code}, Detail={e.detail!r}")
            # --- End Logging ---
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": e.status_code,
                        "message": str(e.detail)
                    }
                }
            )
        except Exception as e:
            # --- Add Logging ---
            logger.error(f"[Decorator] Caught generic Exception: {type(e).__name__}: {e}", exc_info=True)
            # --- End Logging ---
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": 500,
                        "message": f"Internal server error"
                    }
                }
            )
    return wrapper 
