import enum
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean, Float, Text, func,
    UniqueConstraint, PrimaryKeyConstraint, ForeignKeyConstraint, Index, CheckConstraint, Numeric
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY, JSONB, ENUM
from sqlalchemy.orm import relationship
from app.db.base import Base

# Define Enums matching PostgreSQL types
class ProjectStatusEnum(enum.Enum):
    new = 'new'
    planning = 'planning'
    in_progress = 'in_progress'
    active = 'active'
    paused = 'paused'
    stale = 'stale'
    postponed = 'postponed'
    completed = 'completed'
    abandoned = 'abandoned'
    archived = 'archived'

class ProjectFocusEnum(enum.Enum):
    DEFAULT = 'DEFAULT'
    VISUAL_MEDIA = 'VISUAL_MEDIA'
    AUDIO_MEDIA = 'AUDIO_MEDIA'
    CODE = 'CODE'
    RESEARCH = 'RESEARCH'
    PLANNING = 'PLANNING'
    WRITING = 'WRITING'
    EDUCATION = 'EDUCATION'
    DATA_ANALYSIS = 'DATA_ANALYSIS'

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='projects_pkey'),
        UniqueConstraint('user_id', 'title', name='projects_user_id_title_key'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='projects_user_id_fkey'),
        ForeignKeyConstraint(['agent_id'], ['agents.id'], name='projects_agent_id_fkey', use_alter=True),
        Index('idx_projects_focus', 'focus'),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_user', 'user_id'),
        Index('idx_projects_agent', 'agent_id'),
    )

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    agent_id = Column(PGUUID, nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(ENUM(ProjectStatusEnum, name='project_status', create_type=False), nullable=False, default=ProjectStatusEnum.active)
    focus = Column(ENUM(ProjectFocusEnum, name='project_focus', create_type=False), nullable=False, default=ProjectFocusEnum.DEFAULT)
    start_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    budget = Column(Numeric(15, 2), nullable=True)
    project_colors = Column(ARRAY(Text), default=[])
    logo_url = Column(Text, nullable=True)
    ai_overview = Column(Text, nullable=True)
    last_overview_update = Column(DateTime(timezone=True), nullable=True)
    project_metadata = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    agent = relationship("Agent", back_populates="projects", foreign_keys=[agent_id])
    tags = relationship("ProjectTag", back_populates="project", cascade="all, delete-orphan")
    collaborators = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project")
    research_sessions = relationship("ResearchSession", back_populates="project")
    calendar_events = relationship("CalendarEvent", back_populates="project")
    research_findings = relationship("ResearchFinding", back_populates="project")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "agent_id": str(self.agent_id),
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
            "meta": self.project_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }

class SystemTag(Base):
    __tablename__ = "system_tags"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='system_tags_pkey'),
        UniqueConstraint('name', name='system_tags_name_key'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    color = Column(Text, nullable=True)
    icon = Column(Text, nullable=True)
    system_tag_metadata = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
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
            "meta": self.system_tag_metadata,
            "created_at": self.created_at.isoformat()
        }

class UserTag(Base):
    __tablename__ = "user_tags"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='user_tags_pkey'),
        UniqueConstraint('user_id', 'name', name='user_tags_user_id_name_key'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='user_tags_user_id_fkey'),
        Index('idx_user_tags_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(Text, nullable=True)
    icon = Column(Text, nullable=True)
    user_tag_metadata = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
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
            "meta": self.user_tag_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class ProjectTag(Base):
    __tablename__ = "project_tags"
    __table_args__ = (
        PrimaryKeyConstraint('project_id', 'tag_id', name='project_tags_pkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='project_tags_project_id_fkey'),
        ForeignKeyConstraint(['tag_id'], ['system_tags.id'], name='fk_system_tag', deferrable=True, initially='DEFERRED'),
        ForeignKeyConstraint(['tag_id'], ['user_tags.id'], name='fk_user_tag', deferrable=True, initially='DEFERRED'),
        Index('idx_project_tags_project', 'project_id'),
        Index('idx_project_tags_tag', 'tag_id'),
    )

    project_id = Column(PGUUID, ForeignKey("projects.id"), primary_key=True)
    tag_id = Column(PGUUID, primary_key=True)
    is_system_tag = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
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
    __table_args__ = (
        PrimaryKeyConstraint('project_id', 'user_id', name='project_collaborators_pkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='project_collaborators_project_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='project_collaborators_user_id_fkey'),
        Index('idx_project_collaborators_project', 'project_id'),
        Index('idx_project_collaborators_user', 'user_id'),
    )

    project_id = Column(PGUUID, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), primary_key=True)
    role = Column(Text, nullable=False)
    permissions = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
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
