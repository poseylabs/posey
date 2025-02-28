from typing import List, Dict, Any
from pydantic import BaseModel

class AgentExecutionResult(BaseModel):
    """Result format for agent execution operations"""
    answer: str
    confidence: float = 0.0
    abilities_used: List[str] = []
    metadata: Dict[str, Any] = {}

__all__ = ['AgentExecutionResult'] 
