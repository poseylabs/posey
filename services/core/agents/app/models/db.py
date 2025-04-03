"""Database models and enums for SQLAlchemy."""

from sqlalchemy import Column, String, UUID, ForeignKey, JSON, Boolean, TIMESTAMP, Enum, Integer, ARRAY, Text, Interval
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql import func
import uuid
from typing import Dict

from app.models.enums import EventRecurrence, FileSource, FileRelationshipType, ProjectFocus, ProjectStatus, TaskPriority, UserTaskStatus
from app.db.base import Base

# Models
class DBUser(Base):
    """Database model for users table."""
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True)
    name = Column(String)
    status = Column(String, default="active")
    role = Column(String, default="user")
    preferences = Column(JSONB, default={})
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(TIMESTAMP(timezone=True))
    last_active = Column(TIMESTAMP(timezone=True))

class DBConversation(Base):
    """Database model for conversations table."""
    __tablename__ = "conversations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String)
    status = Column(String, default="active")
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class DBConversationMessage(Base):
    """Database model for conversation_messages table."""
    __tablename__ = "conversation_messages"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String, default="text")
    sender = Column(UUID)
    sender_type = Column(String)
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class DBProject(Base):
    """Database model for projects table."""
    __tablename__ = "projects"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    focus = Column(Enum(ProjectFocus), default=ProjectFocus.DEFAULT)
    description = Column(Text)
    start_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    due_date = Column(TIMESTAMP(timezone=True))
    budget = Column(Integer)
    project_colors = Column(ARRAY(String), default=[])
    logo_url = Column(String)
    ai_overview = Column(Text)
    last_overview_update = Column(TIMESTAMP(timezone=True))
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class DBCalendarEvent(Base):
    """Database model for calendar_events table."""
    __tablename__ = "calendar_events"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    location = Column(String)
    is_all_day = Column(Boolean, default=False)
    recurrence = Column(Enum(EventRecurrence), default=EventRecurrence.NONE)
    recurrence_config = Column(JSONB, default={})
    reminder_before = Column(Interval)
    attendees = Column(JSONB, default=[])
    conference_link = Column(String)
    tags = Column(ARRAY(String), default=[])
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True))

class DBUserFile(Base):
    """Database model for user_files table."""
    __tablename__ = "user_files"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    source = Column(Enum(FileSource), nullable=False, default=FileSource.USER_UPLOAD)
    source_task_id = Column(UUID, ForeignKey("tasks.id"))
    source_agent_id = Column(UUID)
    favorite = Column(Boolean, default=False)
    tags = Column(ARRAY(String), default=[])
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed_at = Column(TIMESTAMP(timezone=True))
    deleted_at = Column(TIMESTAMP(timezone=True))

class DBFileVersion(Base):
    """Database model for file_versions table."""
    __tablename__ = "file_versions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    original_file_id = Column(UUID, ForeignKey("user_files.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    storage_key = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_by = Column(String, nullable=False)
    changes_description = Column(Text)
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class DBFileRelationship(Base):
    """Database model for file_relationships table."""
    __tablename__ = "file_relationships"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID, ForeignKey("user_files.id"), nullable=False)
    related_type = Column(Enum(FileRelationshipType), nullable=False)
    related_id = Column(UUID, nullable=False)
    relationship_context = Column(String)
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class DBUserTask(Base):
    """Database model for user_tasks table."""
    __tablename__ = "user_tasks"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(UserTaskStatus), default=UserTaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = Column(TIMESTAMP(timezone=True))
    reminder_at = Column(TIMESTAMP(timezone=True))
    assigned_to = Column(UUID, ForeignKey("users.id"))
    parent_task_id = Column(UUID, ForeignKey("user_tasks.id"))
    estimated_duration = Column(Interval)
    completion_time = Column(Interval)
    tags = Column(ARRAY(String), default=[])
    meta: Dict = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    deleted_at = Column(TIMESTAMP(timezone=True))
