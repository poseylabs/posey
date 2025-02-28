from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    permissions = Column(ARRAY(String), default=[])
    preferences = Column(JSON, default={})
    meta = Column(JSONB, name='metadata', nullable=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships
    tasks = relationship("UserTask", foreign_keys="[UserTask.user_id]", back_populates="user")
    assigned_tasks = relationship("UserTask", foreign_keys="[UserTask.assigned_to]", back_populates="assignee")
    calendar_events = relationship("CalendarEvent", back_populates="user")
    event_attendances = relationship("EventAttendee", back_populates="user")
    projects = relationship("Project", back_populates="user")
    project_collaborations = relationship("ProjectCollaborator", back_populates="user")
    research_sessions = relationship("ResearchSession", back_populates="user")
    research_interactions = relationship("ResearchInteraction", back_populates="user")
    tags = relationship("UserTag", back_populates="user")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "permissions": self.permissions,
            "preferences": self.preferences,
            "metadata": self.meta,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        } 
