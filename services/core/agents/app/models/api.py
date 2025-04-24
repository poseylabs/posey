from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any, Union
from .enums import TaskPriority, TaskStatus, ProjectStatus, AgentType, AgentStatus, MessageType
from pydantic import ConfigDict

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    name: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.NEW

class ProjectResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: AgentType
    capabilities: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('capabilities')
    def validate_capabilities(cls, v):
        if not isinstance(v, list):
            raise ValueError('Capabilities must be a list')
        return v

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[AgentStatus] = None
    capabilities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    id: UUID
    name: str
    type: str
    status: str
    capabilities: List[str]
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = Field(default="user")
    sender_type: str = Field(default="human")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v

class MessageResponse(BaseModel):
    id: UUID
    content: str
    role: str
    sender_type: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = Field(None, alias='metadata')

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    meta: Optional[Dict] = None
    project_id: Optional[UUID] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    status: str
    meta: Optional[Dict] = None
    project_id: Optional[UUID] = None
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

__all__ = [
    'UserCreate', 'UserResponse',
    'ProjectCreate', 'ProjectResponse', 'ProjectUpdate',
    'AgentCreate', 'AgentUpdate', 'AgentResponse',
    'ConversationCreate', 'ConversationResponse',
    'MessageCreate', 'MessageResponse'
] 
