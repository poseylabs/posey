from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, Integer, JSON, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class ResearchSession(Base):
    __tablename__ = "research_sessions"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    task_id = Column(PGUUID, ForeignKey("background_tasks.id"))
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"))
    title = Column(Text, nullable=False)
    description = Column(Text)
    query = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="new")
    auto_tag = Column(Boolean, default=False)
    search_parameters = Column(JSONB, default={})
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    task = relationship("BackgroundTask", back_populates="research_sessions")
    user = relationship("User", back_populates="research_sessions")
    project = relationship("Project", back_populates="research_sessions")
    findings = relationship("ResearchFinding", back_populates="session", cascade="all, delete-orphan")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id) if self.task_id else None,
            "user_id": str(self.user_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "title": self.title,
            "description": self.description,
            "query": self.query,
            "status": self.status,
            "auto_tag": self.auto_tag,
            "search_parameters": self.search_parameters,
            "meta": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

class ResearchFinding(Base):
    __tablename__ = "research_findings"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    session_id = Column(PGUUID, ForeignKey("research_sessions.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"))
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)
    content = Column(JSONB, nullable=False)
    source_url = Column(Text)
    file_storage_key = Column(Text)
    original_filename = Column(Text)
    mime_type = Column(Text)
    categories = Column(ARRAY(String), default=[])
    tags = Column(ARRAY(String), default=[])
    confidence_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    importance_score = Column(Integer, default=5)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="findings")
    project = relationship("Project", back_populates="research_findings")
    interactions = relationship("ResearchInteraction", back_populates="finding", cascade="all, delete-orphan")
    references = relationship("ResearchReference", back_populates="finding", cascade="all, delete-orphan")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "title": self.title,
            "summary": self.summary,
            "content_type": self.content_type,
            "content": self.content,
            "source_url": self.source_url,
            "file_storage_key": self.file_storage_key,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "categories": self.categories,
            "tags": self.tags,
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score,
            "importance_score": self.importance_score,
            "meta": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class ResearchInteraction(Base):
    __tablename__ = "research_interactions"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    finding_id = Column(PGUUID, ForeignKey("research_findings.id"), nullable=False)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    interaction_type = Column(String, nullable=False)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    finding = relationship("ResearchFinding", back_populates="interactions")
    user = relationship("User", back_populates="research_interactions")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "finding_id": str(self.finding_id),
            "user_id": str(self.user_id),
            "interaction_type": self.interaction_type,
            "meta": self.meta,
            "created_at": self.created_at.isoformat()
        }

class ResearchReference(Base):
    __tablename__ = "research_references"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    finding_id = Column(PGUUID, ForeignKey("research_findings.id"), nullable=False)
    type = Column(String, nullable=False)
    title = Column(Text)
    url = Column(Text)
    content = Column(JSONB)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    finding = relationship("ResearchFinding", back_populates="references")
    
    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "finding_id": str(self.finding_id),
            "type": self.type,
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "meta": self.meta,
            "created_at": self.created_at.isoformat()
        } 
