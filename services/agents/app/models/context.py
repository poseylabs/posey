from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from uuid import UUID
import json

@dataclass
class RunContext:
    """Context for a single run/conversation"""
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'RunContext':
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
