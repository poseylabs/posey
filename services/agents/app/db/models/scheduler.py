from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, JSON, Interval, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class UserTask(Base):
    __tablename__ = "user_tasks"
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"))
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, default="todo")
    priority = Column(String, nullable=False, default="medium")
    due_date = Column(DateTime)
    reminder_at = Column(DateTime)
    assigned_to = Column(PGUUID, ForeignKey("users.id"))
    parent_task_id = Column(PGUUID, ForeignKey("user_tasks.id"))
    estimated_duration = Column(Interval)
    completion_time = Column(Interval)
    tags = Column(ARRAY(String), default=[])
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
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
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    task_id = Column(PGUUID, ForeignKey("user_tasks.id"), nullable=False)
    depends_on_task_id = Column(PGUUID, ForeignKey("user_tasks.id"), nullable=False)
    dependency_type = Column(String, nullable=False)
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
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
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    project_id = Column(PGUUID, ForeignKey("projects.id"))
    title = Column(Text, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(Text)
    is_all_day = Column(Boolean, default=False)
    recurrence = Column(String, default="none")
    recurrence_config = Column(JSONB, default={})
    reminder_before = Column(Interval)
    attendees = Column(JSONB, default=[])
    conference_link = Column(Text)
    tags = Column(ARRAY(String), default=[])
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
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
    
    id = Column(PGUUID, primary_key=True, default=uuid4)
    event_id = Column(PGUUID, ForeignKey("calendar_events.id"), nullable=False)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    response_status = Column(String, default="pending")
    meta = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
