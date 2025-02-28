"""Database models using SQLAlchemy."""

from sqlalchemy.orm import relationship, declarative_base
from app.db.base import sync_engine
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from typing import List, Optional, Dict
from uuid import uuid4
from pydantic import BaseModel, ConfigDict

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String)
    status = Column(String, default="new")
    meta = Column(JSONB, name='metadata', default={})
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages = relationship("ConversationMessage", back_populates="conversation")
    user = relationship("User", back_populates="conversations")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(50))
    sender_type = Column(String(50))
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    status = Column(String, default="active")
    preferences = Column(JSONB, default={})
    meta = Column(JSON, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    conversations = relationship("Conversation", back_populates="user")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversations = relationship("Conversation", backref="project")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

# Pydantic models for API
class ConversationCreate(BaseModel):
    title: str | None = None
    meta: dict | None = None
    project_id: UUID | None = None
    
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
    'Base', 'User', 'Project', 'Conversation', 
    'ConversationMessage', 'Agent',
    'ConversationCreate', 'ConversationResponse'
]
