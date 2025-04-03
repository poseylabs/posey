from fastapi import HTTPException
from typing import Optional, Dict, Any

class BaseAgentError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(BaseAgentError):
    pass

class MemoryError(BaseAgentError):
    pass

class AgentError(Exception):
    """Base class for agent-related errors"""
    pass

class TrainingError(AgentError):
    """Error during agent training"""
    pass

class CapabilityError(AgentError):
    """Error related to agent capabilities"""
    pass

class AnalysisError(AgentError):
    """Error during conversation analysis"""
    pass

class ValidationError(AgentError):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=422)

class NotFoundError(AgentError):
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            detail=f"{resource} with id {resource_id} not found",
            status_code=404
        )

class AuthorizationError(AgentError):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(detail=detail, status_code=403)

def handle_training_error(e: Exception) -> Dict[str, Any]:
    """Handle training-related errors"""
    if isinstance(e, TrainingError):
        return {
            "status": "failed",
            "error": str(e),
            "type": "training"
        }
    elif isinstance(e, CapabilityError):
        return {
            "status": "failed",
            "error": str(e),
            "type": "capability"
        }
    else:
        return {
            "status": "failed",
            "error": "Unknown error during training",
            "type": "unknown"
        } 
