from typing import TypeVar, Generic, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def success_response(cls, data: T, message: Optional[str] = None) -> "StandardResponse[T]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(cls, message: str, error: Optional[Dict[str, Any]] = None) -> "StandardResponse":
        return cls(success=False, message=message, error=error)
