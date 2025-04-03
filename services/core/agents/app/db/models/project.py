from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default="new")
    focus = Column(String, nullable=False, default="DEFAULT")
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime)
    budget = Column(Float)
    project_colors = Column(ARRAY(String), default=[])
    logo_url = Column(String)
    ai_overview = Column(String)
    last_overview_update = Column(DateTime)
    meta = Column(JSON, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    agent = relationship("Agent", back_populates="projects")
    tags = relationship("ProjectTag", back_populates="project", cascade="all, delete-orphan")
    collaborators = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project")
    research_sessions = relationship("ResearchSession", back_populates="project")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "focus": self.focus,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "budget": self.budget,
            "project_colors": self.project_colors,
            "logo_url": self.logo_url,
            "ai_overview": self.ai_overview,
            "last_overview_update": self.last_overview_update.isoformat() if self.last_overview_update else None,
            "meta": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }

class SystemTag(Base):
    __tablename__ = "system_tags"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    category = Column(String)
    color = Column(String)
    icon = Column(String)
    meta = Column(JSON, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    project_tags = relationship("ProjectTag", back_populates="system_tag")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "color": self.color,
            "icon": self.icon,
            "meta": self.meta,
            "created_at": self.created_at.isoformat()
        }

class UserTag(Base):
    __tablename__ = "user_tags"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    color = Column(String)
    icon = Column(String)
    meta = Column(JSON, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tags")
    project_tags = relationship("ProjectTag", back_populates="user_tag")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "meta": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class ProjectTag(Base):
    __tablename__ = "project_tags"
    
    project_id = Column(PGUUID, ForeignKey("projects.id"), primary_key=True)
    tag_id = Column(PGUUID, primary_key=True)
    is_system_tag = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="tags")
    system_tag = relationship("SystemTag", back_populates="project_tags", 
                            foreign_keys=[tag_id],
                            primaryjoin="and_(ProjectTag.tag_id==SystemTag.id, ProjectTag.is_system_tag==True)")
    user_tag = relationship("UserTag", back_populates="project_tags",
                          foreign_keys=[tag_id],
                          primaryjoin="and_(ProjectTag.tag_id==UserTag.id, ProjectTag.is_system_tag==False)")

class ProjectCollaborator(Base):
    __tablename__ = "project_collaborators"
    
    project_id = Column(PGUUID, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), primary_key=True)
    role = Column(String, nullable=False)
    permissions = Column(JSON, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="collaborators")
    user = relationship("User", back_populates="project_collaborations")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "project_id": str(self.project_id),
            "user_id": str(self.user_id),
            "role": self.role,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 
