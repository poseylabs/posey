from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Text, func, Index, PrimaryKeyConstraint, ForeignKeyConstraint, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key'),
        UniqueConstraint('username', name='users_username_key'),
        Index('users_email_idx', 'email'),
        Index('users_username_idx', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username'),
        Index('idx_users_status', 'status'),
        Index('idx_users_role', 'role'),
    )
    
    id = Column(PGUUID, primary_key=True)
    username = Column(String(255), unique=False, nullable=False)
    email = Column(String(255), unique=False, nullable=True)
    name = Column(String(255), name='name', nullable=True)
    status = Column(String(50), default='active')
    role = Column(String(50), default='user')
    preferences = Column(JSONB, default={})
    meta = Column(JSONB, name='metadata', default={})
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Added from SQL files
    last_active = Column(DateTime(timezone=True), nullable=True)
    reset_token = Column(Text, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    two_factor_secret = Column(Text, nullable=True)
    two_factor_enabled = Column(Boolean, default=False)

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
            "name": self.name,
            "status": self.status,
            "role": self.role,
            "preferences": self.preferences,
            "metadata": self.meta,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        } 
