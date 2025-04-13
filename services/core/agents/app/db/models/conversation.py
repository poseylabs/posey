from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func, Index, PrimaryKeyConstraint, ForeignKeyConstraint, CheckConstraint, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='conversations_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='conversations_user_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='conversations_project_id_fkey'),
        Index('idx_conversations_archived', 'is_archived'),
        Index('idx_conversations_project', 'project_id'),
        Index('idx_conversations_user_id', 'user_id'),
    )

    # Minimal definition required for Alembic FK resolution
    id = Column(PGUUID, primary_key=True, default=uuid4)

    # Define other columns based on your actual schema (e.g., 005_conversations.sql)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"), nullable=True)
    title = Column(String(255), nullable=True)
    status = Column(String(50), default='active')
    conv_metadata = Column(JSONB, name='metadata', default={}) # Renamed attribute
    is_archived = Column(Boolean, default=False)
    archive_reason = Column(Text, nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User") # Simplified, assumes User model exists
    project = relationship("Project", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    # background_tasks relationship might be defined in BackgroundTask model

    # Note: This is a basic definition. You should flesh it out to match your
    # actual 'conversations' table schema defined in your .sql migration file. 

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='conversation_messages_pkey'),
        ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='conversation_messages_conversation_id_fkey'),
        Index('idx_conversation_messages_conversation_id', 'conversation_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    conversation_id = Column(PGUUID, ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=True)
    sender_type = Column(String(50), nullable=True)
    msg_metadata = Column(JSONB, name='metadata', default={}) # Renamed attribute
    sender = Column(PGUUID, nullable=True)
    type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Note: This is a basic definition. You should flesh it out to match your
    # actual 'conversation_messages' table schema defined in your .sql migration file. 