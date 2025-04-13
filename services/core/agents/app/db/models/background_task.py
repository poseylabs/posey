from datetime import datetime
from uuid import uuid4
import enum
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Integer, Text, func,
    Index, PrimaryKeyConstraint, ForeignKeyConstraint, CheckConstraint,
    text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from app.db.base import Base

# Define Enums matching PostgreSQL types from 000_init_schema.sql
class TaskStatusEnum(enum.Enum):
    pending = 'pending'
    in_progress = 'in_progress'
    analyzing = 'analyzing'
    paused = 'paused'
    completed = 'completed'
    failed = 'failed'
    cancelled = 'cancelled'

class TaskPriorityEnum(enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    urgent = 'urgent'

class BackgroundTask(Base):
    __tablename__ = "background_tasks"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='background_tasks_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='background_tasks_user_id_fkey'),
        ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='background_tasks_conversation_id_fkey'),
        CheckConstraint('progress >= 0 AND progress <= 100', name='valid_progress'),
        Index('idx_tasks_user', 'user_id'),
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_next_run', 'next_run_at', postgresql_where=text("status = 'pending'")),
    )

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    conversation_id = Column(PGUUID, nullable=True)
    task_type = Column(String(50), nullable=False)
    status = Column(ENUM(TaskStatusEnum, name='task_status', create_type=False), default=TaskStatusEnum.pending)
    priority = Column(ENUM(TaskPriorityEnum, name='task_priority', create_type=False), default=TaskPriorityEnum.medium)
    progress = Column(Integer, default=0)
    parameters = Column(JSONB, default={})
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    task_metadata = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships (add relationships based on ForeignKeys if needed)
    # user = relationship("User", back_populates="background_tasks") # Needs back_populates in User model
    # conversation = relationship("Conversation", back_populates="background_tasks") # Needs Conversation model & back_populates
    research_sessions = relationship("ResearchSession", back_populates="task") # Already defined in ResearchSession

    # Note: Consider defining SQLAlchemy Enums if task_status/priority have fixed values
    # from sqlalchemy import Enum
    # status = Column(Enum('pending', 'running', 'completed', 'failed', name='task_status_enum'), default='pending') 