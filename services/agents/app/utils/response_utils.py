from fastapi import HTTPException
from typing import Callable
from functools import wraps
from app.models.responses import StandardResponse

def standardize_response(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> StandardResponse:
        try:
            result = await func(*args, **kwargs)
            return StandardResponse.success_response(result)
        except HTTPException as he:
            return StandardResponse.error_response(str(he.detail))
        except Exception as e:
            return StandardResponse.error_response(str(e))
    return wrapper
