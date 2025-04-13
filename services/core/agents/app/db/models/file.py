import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    Boolean, BigInteger, UniqueConstraint, Integer,
    PrimaryKeyConstraint, ForeignKeyConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

# Define Enums matching PostgreSQL types
class FileSourceEnum(enum.Enum):
    user_upload = 'user_upload'
    agent_generated = 'agent_generated'
    conversion_result = 'conversion_result'
    research_artifact = 'research_artifact'
    other = 'other'

class FileRelationshipTypeEnum(enum.Enum):
    project = 'project'
    conversation = 'conversation'
    research_session = 'research_session'

class UserFile(Base):
    __tablename__ = "user_files"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='user_files_pkey'),
        UniqueConstraint('user_id', 'storage_key', name='user_files_user_id_storage_key_key'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='user_files_user_id_fkey'),
        ForeignKeyConstraint(['source_task_id'], ['background_tasks.id'], name='user_files_source_task_id_fkey'),
        Index('idx_user_files_agent', 'source_agent_id'),
        Index('idx_user_files_source', 'source'),
        Index('idx_user_files_tags', 'tags', postgresql_using='gin'),
        Index('idx_user_files_task', 'source_task_id'),
        Index('idx_user_files_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    filename = Column(Text, nullable=False)
    original_filename = Column(Text, nullable=False)
    storage_key = Column(Text, nullable=False)
    mime_type = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    source = Column(ENUM(FileSourceEnum, name='file_source', create_type=False), nullable=False, default=FileSourceEnum.user_upload)
    source_task_id = Column(PGUUID, ForeignKey("background_tasks.id"), nullable=True)
    source_agent_id = Column(PGUUID, nullable=True) # Assuming no FK to agents table? Check SQL if needed.
    favorite = Column(Boolean, default=False)
    tags = Column(ARRAY(Text), default=[])
    file_metadata = Column(JSONB, name='metadata', default={}) # Renamed attribute
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User") # Simplified
    source_task = relationship("BackgroundTask") # Simplified
    relationships = relationship("FileRelationship", back_populates="file", cascade="all, delete-orphan")
    versions = relationship("FileVersion", back_populates="original_file", cascade="all, delete-orphan")

class FileRelationship(Base):
    __tablename__ = "file_relationships"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='file_relationships_pkey'),
        UniqueConstraint('file_id', 'related_type', 'related_id', name='file_relationships_file_id_related_type_related_id_key'),
        ForeignKeyConstraint(['file_id'], ['user_files.id'], name='file_relationships_file_id_fkey'),
        Index('idx_file_relationships_context', 'relationship_context'),
        Index('idx_file_relationships_file', 'file_id'),
        Index('idx_file_relationships_related', 'related_type', 'related_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    file_id = Column(PGUUID, ForeignKey("user_files.id"), nullable=False)
    related_type = Column(ENUM(FileRelationshipTypeEnum, name='file_relationship_type', create_type=False), nullable=False)
    related_id = Column(PGUUID, nullable=False) # Cannot add specific FKs here easily due to dynamic related_type
    relationship_context = Column(Text, nullable=True)
    rel_metadata = Column(JSONB, name='metadata', default={}) # Renamed attribute
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    file = relationship("UserFile", back_populates="relationships")
    # Note: Cannot easily define polymorphic relationship to Project/Conversation/ResearchSession here
    # based *solely* on related_id and related_type without more advanced SQLAlchemy techniques.
    # Accessing the related object would typically require a query based on related_type.

class FileVersion(Base):
    __tablename__ = "file_versions"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='file_versions_pkey'),
        UniqueConstraint('original_file_id', 'version_number', name='file_versions_original_file_id_version_number_key'),
        ForeignKeyConstraint(['original_file_id'], ['user_files.id'], name='file_versions_original_file_id_fkey'),
        Index('idx_file_versions_original', 'original_file_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    original_file_id = Column(PGUUID, ForeignKey("user_files.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    storage_key = Column(Text, nullable=False)
    mime_type = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    created_by = Column(Text, nullable=False) # 'user' or agent_id (string)
    changes_description = Column(Text, nullable=True)
    ver_metadata = Column(JSONB, name='metadata', default={}) # Renamed attribute
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    original_file = relationship("UserFile", back_populates="versions") 