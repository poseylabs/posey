from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ANALYZING = "analyzing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProjectStatus(str, Enum):
    NEW = "new"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ACTIVE = "active"
    PAUSED = "paused"
    STALE = "stale"
    POSTPONED = "postponed"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"

class AgentType(str, Enum):
    ASSISTANT = "assistant"
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    PLANNER = "planner"
    CREATIVE = "creative"

class AgentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    TRAINING = "training"
    OFFLINE = "offline"
    ERROR = "error"

class MessageType(str, Enum):
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"



class UserTaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"

class ProjectStatus(str, Enum):
    NEW = "new"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ACTIVE = "active"
    PAUSED = "paused"
    STALE = "stale"
    POSTPONED = "postponed"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"

class ProjectFocus(str, Enum):
    DEFAULT = "DEFAULT"
    VISUAL_MEDIA = "VISUAL_MEDIA"
    AUDIO_MEDIA = "AUDIO_MEDIA"
    CODE = "CODE"
    RESEARCH = "RESEARCH"
    PLANNING = "PLANNING"
    WRITING = "WRITING"
    EDUCATION = "EDUCATION"
    DATA_ANALYSIS = "DATA_ANALYSIS"

class FileSource(str, Enum):
    USER_UPLOAD = "user_upload"
    AGENT_GENERATED = "agent_generated"
    CONVERSION_RESULT = "conversion_result"
    RESEARCH_ARTIFACT = "research_artifact"
    OTHER = "other"

class FileRelationshipType(str, Enum):
    PROJECT = "project"
    CONVERSATION = "conversation"
    RESEARCH_SESSION = "research_session"

class EventRecurrence(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


# Add other enums...

__all__ = [
    'TaskStatus', 'TaskPriority', 'ProjectStatus',
    'AgentType', 'AgentStatus', 'MessageType'
]
