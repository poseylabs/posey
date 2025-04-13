import enum
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean, Integer, JSON, Interval, Text, func,
    UniqueConstraint, PrimaryKeyConstraint, ForeignKeyConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY, ENUM
from sqlalchemy.orm import relationship
from app.db.base import Base

# Define Enums matching PostgreSQL types
class TaskPriorityEnum(enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    urgent = 'urgent'

class UserTaskStatusEnum(enum.Enum):
    todo = 'todo'
    in_progress = 'in_progress'
    blocked = 'blocked'
    completed = 'completed'
    cancelled = 'cancelled'
    deferred = 'deferred'

class EventRecurrenceEnum(enum.Enum):
    none = 'none'
    daily = 'daily'
    weekly = 'weekly'
    biweekly = 'biweekly'
    monthly = 'monthly'
    yearly = 'yearly'
    custom = 'custom'

class UserTask(Base):
    __tablename__ = "calendar_tasks"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='calendar_tasks_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='calendar_tasks_user_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='calendar_tasks_project_id_fkey'),
        ForeignKeyConstraint(['assigned_to'], ['users.id'], name='calendar_tasks_assigned_to_fkey'),
        ForeignKeyConstraint(['parent_task_id'], ['calendar_tasks.id'], name='calendar_tasks_parent_task_id_fkey'),
        CheckConstraint("status IN ('todo', 'in_progress', 'blocked', 'completed', 'cancelled', 'deferred')", name='user_task_status_check'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='task_priority_check'),
        Index('idx_calendar_tasks_assigned', 'assigned_to'),
        Index('idx_calendar_tasks_due_date', 'due_date'),
        Index('idx_calendar_tasks_parent', 'parent_task_id'),
        Index('idx_calendar_tasks_priority', 'priority'),
        Index('idx_calendar_tasks_project', 'project_id'),
        Index('idx_calendar_tasks_status', 'status'),
        Index('idx_calendar_tasks_tags', 'tags', postgresql_using='gin'),
        Index('idx_calendar_tasks_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(ENUM(UserTaskStatusEnum, name='user_task_status', create_type=False), nullable=False, default=UserTaskStatusEnum.todo)
    priority = Column(ENUM(TaskPriorityEnum, name='task_priority', create_type=False), nullable=False, default=TaskPriorityEnum.medium)
    due_date = Column(DateTime(timezone=True), nullable=True)
    reminder_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(PGUUID, ForeignKey("users.id"), nullable=True)
    parent_task_id = Column(PGUUID, ForeignKey("calendar_tasks.id"), nullable=True)
    estimated_duration = Column(Interval, nullable=True)
    completion_time = Column(Interval, nullable=True)
    tags = Column(ARRAY(Text), default=[])
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    project = relationship("Project")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    parent_task = relationship("UserTask", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("UserTask", back_populates="parent_task")
    dependencies = relationship("TaskDependency", foreign_keys="[TaskDependency.task_id]", back_populates="task")
    dependent_tasks = relationship("TaskDependency", foreign_keys="[TaskDependency.depends_on_task_id]", back_populates="depends_on_task")

    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "reminder_at": self.reminder_at.isoformat() if self.reminder_at else None,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "parent_task_id": str(self.parent_task_id) if self.parent_task_id else None,
            "estimated_duration": str(self.estimated_duration) if self.estimated_duration else None,
            "completion_time": str(self.completion_time) if self.completion_time else None,
            "tags": self.tags,
            "metadata": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='task_dependencies_pkey'),
        UniqueConstraint('task_id', 'depends_on_task_id', name='task_dependencies_task_id_depends_on_task_id_key'),
        ForeignKeyConstraint(['task_id'], ['calendar_tasks.id'], name='task_dependencies_task_id_fkey'),
        ForeignKeyConstraint(['depends_on_task_id'], ['calendar_tasks.id'], name='task_dependencies_depends_on_task_id_fkey'),
        Index('idx_task_dependencies_depends', 'depends_on_task_id'),
        Index('idx_task_dependencies_task', 'task_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    task_id = Column(PGUUID, ForeignKey("calendar_tasks.id"), nullable=False)
    depends_on_task_id = Column(PGUUID, ForeignKey("calendar_tasks.id"), nullable=False)
    dependency_type = Column(Text, nullable=False)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    task = relationship("UserTask", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("UserTask", foreign_keys=[depends_on_task_id], back_populates="dependent_tasks")

    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "depends_on_task_id": str(self.depends_on_task_id),
            "dependency_type": self.dependency_type,
            "metadata": self.meta,
            "created_at": self.created_at.isoformat()
        }

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='calendar_events_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='calendar_events_user_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.id'], name='calendar_events_project_id_fkey'),
        CheckConstraint("recurrence IN ('none', 'daily', 'weekly', 'biweekly', 'monthly', 'yearly', 'custom')", name='calendar_events_recurrence_check'),
        Index('idx_calendar_events_end', 'end_time'),
        Index('idx_calendar_events_project', 'project_id'),
        Index('idx_calendar_events_recurrence', 'recurrence'),
        Index('idx_calendar_events_start', 'start_time'),
        Index('idx_calendar_events_tags', 'tags', postgresql_using='gin'),
        Index('idx_calendar_events_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    project_id = Column(PGUUID, nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(Text, nullable=True)
    is_all_day = Column(Boolean, default=False)
    recurrence = Column(ENUM(EventRecurrenceEnum, name='event_recurrence', create_type=False), default=EventRecurrenceEnum.none)
    recurrence_config = Column(JSONB, default={})
    reminder_before = Column(Interval, nullable=True)
    attendees = Column(JSONB, default=[])
    conference_link = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), default=[])
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="calendar_events")
    project = relationship("Project", back_populates="calendar_events")
    event_attendees = relationship("EventAttendee", back_populates="event", cascade="all, delete-orphan")

    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "location": self.location,
            "is_all_day": self.is_all_day,
            "recurrence": self.recurrence,
            "recurrence_config": self.recurrence_config,
            "reminder_before": str(self.reminder_before) if self.reminder_before else None,
            "attendees": self.attendees,
            "conference_link": self.conference_link,
            "tags": self.tags,
            "metadata": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }

class EventAttendee(Base):
    __tablename__ = "event_attendees"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='event_attendees_pkey'),
        UniqueConstraint('event_id', 'user_id', name='event_attendees_event_id_user_id_key'),
        ForeignKeyConstraint(['event_id'], ['calendar_events.id'], name='event_attendees_event_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='event_attendees_user_id_fkey'),
        Index('idx_event_attendees_event', 'event_id'),
        Index('idx_event_attendees_status', 'response_status'),
        Index('idx_event_attendees_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    event_id = Column(PGUUID, ForeignKey("calendar_events.id"), nullable=False)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    response_status = Column(Text, default='pending', nullable=False)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    event = relationship("CalendarEvent", back_populates="event_attendees")
    user = relationship("User", back_populates="event_attendances")

    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "user_id": str(self.user_id),
            "response_status": self.response_status,
            "metadata": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 
