import enum
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, DateTime, ForeignKey, Boolean, Float, Integer, JSON, Text, func, Numeric,
    PrimaryKeyConstraint, ForeignKeyConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY, ENUM
from sqlalchemy.orm import relationship
from app.db.base import Base

# Define Enums matching PostgreSQL types
class ResearchStatusEnum(enum.Enum):
    new = 'new'
    in_progress = 'in_progress'
    completed = 'completed'
    needs_review = 'needs_review'
    archived = 'archived'

class ContentTypeEnum(enum.Enum):
    text = 'text'
    link = 'link'
    image = 'image'
    audio = 'audio'
    video = 'video'
    document = 'document'
    spreadsheet = 'spreadsheet'
    dataset = 'dataset'
    code = 'code'
    spreadsheet_data = 'spreadsheet_data'
    document_text = 'document_text'
    extracted_table = 'extracted_table'
    converted_file = 'converted_file'
    other = 'other'

class ResearchSession(Base):
    __tablename__ = "research_sessions"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='research_sessions_pkey'),
        ForeignKeyConstraint(['task_id'], ['background_tasks.id'], name='research_sessions_task_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='research_sessions_user_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='research_sessions_project_id_fkey'),
        Index('idx_research_sessions_project', 'project_id'),
        Index('idx_research_sessions_status', 'status'),
        Index('idx_research_sessions_task', 'task_id'),
        Index('idx_research_sessions_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    task_id = Column(PGUUID, ForeignKey("background_tasks.id"), nullable=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    query = Column(Text, nullable=False)
    status = Column(ENUM(ResearchStatusEnum, name='research_status', create_type=False), nullable=False, default=ResearchStatusEnum.new)
    auto_tag = Column(Boolean, default=False)
    search_parameters = Column(JSONB, default={})
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
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
    __table_args__ = (
        PrimaryKeyConstraint('id', name='research_findings_pkey'),
        ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name='research_findings_session_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='research_findings_project_id_fkey'),
        Index('idx_research_findings_categories', 'categories', postgresql_using='gin'),
        Index('idx_research_findings_project', 'project_id'),
        Index('idx_research_findings_session', 'session_id'),
        Index('idx_research_findings_tags', 'tags', postgresql_using='gin'),
        Index('idx_research_findings_type', 'content_type'),
    )
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    session_id = Column(PGUUID, ForeignKey("research_sessions.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"), nullable=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    content_type = Column(ENUM(ContentTypeEnum, name='content_type', create_type=False), nullable=False)
    content = Column(JSONB, nullable=False)
    source_url = Column(Text, nullable=True)
    file_storage_key = Column(Text, nullable=True)
    original_filename = Column(Text, nullable=True)
    mime_type = Column(Text, nullable=True)
    categories = Column(ARRAY(Text), default=[])
    tags = Column(ARRAY(Text), default=[])
    confidence_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    importance_score = Column(Integer, default=5)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
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
    __table_args__ = (
        PrimaryKeyConstraint('id', name='research_interactions_pkey'),
        ForeignKeyConstraint(['finding_id'], ['research_findings.id'], name='research_interactions_finding_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='research_interactions_user_id_fkey'),
        Index('idx_research_interactions_finding', 'finding_id'),
        Index('idx_research_interactions_type', 'interaction_type'),
        Index('idx_research_interactions_user', 'user_id'),
    )
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    finding_id = Column(PGUUID, ForeignKey("research_findings.id"), nullable=False)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    interaction_type = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
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
            "notes": self.notes,
            "meta": self.meta,
            "created_at": self.created_at.isoformat()
        }

class ResearchReference(Base):
    __tablename__ = "research_references"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='research_references_pkey'),
        ForeignKeyConstraint(['finding_id'], ['research_findings.id'], name='research_references_finding_id_fkey'),
        Index('idx_research_references_finding', 'finding_id'),
        Index('idx_research_references_type', 'type'),
    )
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    finding_id = Column(PGUUID, ForeignKey("research_findings.id"), nullable=False)
    type = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
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
            "summary": self.summary,
            "meta": self.meta,
            "created_at": self.created_at.isoformat()
        }

# New model based on 008_research.sql
class ProductIdea(Base):
    __tablename__ = "product_ideas"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='product_ideas_pkey'),
        ForeignKeyConstraint(['task_id'], ['background_tasks.id'], name='product_ideas_task_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='product_ideas_user_id_fkey'),
        Index('idx_product_ideas_category', 'category'),
        Index('idx_product_ideas_status', 'status'),
        Index('idx_product_ideas_task', 'task_id'),
        Index('idx_product_ideas_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    task_id = Column(PGUUID, ForeignKey("background_tasks.id"), nullable=True)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    product_name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    affiliate_links = Column(JSONB, default=[])
    category = Column(Text, nullable=False)
    subcategories = Column(ARRAY(Text), default=[])
    status = Column(ENUM(ResearchStatusEnum, name='research_status', create_type=False), nullable=False, default=ResearchStatusEnum.new)
    estimated_commission = Column(Numeric(10, 2), nullable=True)
    price_range = Column(JSONB, default=lambda: {"min": 0, "max": 0, "currency": "USD"})
    relevance_score = Column(Float, default=0.0)
    prod_idea_metadata = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    # task = relationship("BackgroundTask")
    # user = relationship("User")

    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id) if self.task_id else None,
            "user_id": str(self.user_id),
            "product_name": self.product_name,
            "description": self.description,
            "source_url": self.source_url,
            "affiliate_links": self.affiliate_links,
            "category": self.category,
            "subcategories": self.subcategories,
            "status": self.status,
            "estimated_commission": self.estimated_commission,
            "price_range": self.price_range,
            "relevance_score": self.relevance_score,
            "prod_idea_metadata": self.prod_idea_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 
