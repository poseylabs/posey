from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from uuid import UUID
import json
from pydantic import BaseModel, Field
from datetime import datetime
from .system import LocationInfo

@dataclass
class RunMetadata:
    """Metadata for a single run/conversation"""
    
    conversation_id: UUID
    user_id: str
    agent_id: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            'conversation_id': str(self.conversation_id),
            'user_id': self.user_id,
            'agent_id': self.agent_id,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RunMetadata':
        """Create context from dictionary"""
        return cls(
            conversation_id=UUID(data['conversation_id']),
            user_id=data['user_id'],
            agent_id=data['agent_id'],
            metadata=data.get('metadata', {})
        )
    
    def __str__(self) -> str:
        """String representation"""
        return json.dumps(self.to_dict())

class UserContext(BaseModel):
    """Consolidated User context information"""
    # From utils/context.py
    user_id: str # Changed from Optional in prompts/base.py to required as in utils/context.py
    username: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    language: str = "en-US" # Default from prompts/base.py
    last_active: Optional[datetime] = None
    session_start: Optional[datetime] = Field(default=None) # Allow None initially

    # From prompts/base.py
    name: Optional[str] = None # Note: Overlaps with username, decide if needed
    email: Optional[str] = None
    timezone: Optional[str] = None
    location: Optional[LocationInfo] = None # Using LocationInfo object

    class Config:
        # If overlap like name/username exists, can add alias or validation
        pass 
