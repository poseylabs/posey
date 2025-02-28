from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ToolDefinition(BaseModel):
    """Defines the structure and parameters of a tool"""
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {},
            "required": []
        }
    )

class ToolCall(BaseModel):
    """Represents a tool call request"""
    name: str
    arguments: Dict[str, Any] 
