from functools import wraps
from typing import Any, Dict, Optional
from fastapi import HTTPException

def standardize_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            result = await func(*args, **kwargs)
            if isinstance(result, dict) and "success" in result:
                return result
            return {
                "success": True,
                "data": result
            }
        except HTTPException as e:
            return {
                "success": False,
                "error": {
                    "code": e.status_code,
                    "message": str(e.detail)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": 500,
                    "message": str(e)
                }
            }
    return wrapper 
