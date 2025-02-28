from typing import Dict, Any, Optional
from pydantic import BaseModel

class AgentResult(BaseModel):
    """Generic result type for agent operations"""
    data: Dict[str, Any]
    answer: Optional[str] = None
    metadata: Dict[str, Any] = {}
    confidence: float = 0.8 
