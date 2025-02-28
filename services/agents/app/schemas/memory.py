from pydantic import BaseModel, Field, UUID4
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

class MemoryResponse(BaseModel):
    id: UUID
    content: str
    metadata: Dict[str, Any]
    agent_id: UUID
    user_id: str
    context_type: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    memory_recurrence: int = Field(default=1, ge=1)
    total_importance: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    tags: List[str] = []
    source_type: str
    privacy_level: str = "shared"
    retention_period: int = 30
    importance_score: float = Field(ge=0.0, le=1.0)
    categories: List[str] = ["general"]
    is_shared: bool = True
    sharing_reason: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID4: lambda v: str(v)
        }