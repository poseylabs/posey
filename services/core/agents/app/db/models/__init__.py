# Import all models here so Alembic can find them
from .user import User
from .llm_provider import LLMProvider
from .llm_model import LLMModel
from .minion_llm_config import MinionLLMConfig

# Import models from scheduler.py
from .scheduler import (
    UserTask,
    TaskDependency,
    CalendarEvent,
    EventAttendee
)

# Import models from project.py
from .project import (
    Project,
    SystemTag,
    UserTag,
    ProjectTag,
    ProjectCollaborator
)

# Import models from research.py
from .research import (
    ResearchSession,
    ResearchFinding,
    ResearchInteraction,
    ResearchReference,
    ProductIdea
)

# Import other models
from .background_task import BackgroundTask
from .conversation import Conversation, ConversationMessage
from .agent import Agent
from .file import UserFile, FileRelationship, FileVersion
from .memory import MemoryVector
from .feedback import AgentFeedback
from .integration import IntegrationLog, IntegrationConfig
from .media_history import MediaGenerationHistory
from .invite_code import InviteCode
from .session import Session
from .favorite import SavedMessage, SavedImage, SavedVideo, SavedSong
from .llm_api_key import LLMApiKey
from .seed_version import SeedVersion
from .agent_training_history import AgentTrainingHistory
from .migration import Migration

# Import other models (add any missing ones here)
# Example: from .conversation import ConversationMessage

__all__ = [
    # Core User/Auth/Config
    "User",
    "LLMProvider",
    "LLMModel",
    "MinionLLMConfig",

    # Scheduler Models
    "UserTask",
    "TaskDependency",
    "CalendarEvent",
    "EventAttendee",

    # Project Models
    "Project",
    "SystemTag",
    "UserTag",
    "ProjectTag",
    "ProjectCollaborator",

    # Research Models
    "ResearchSession",
    "ResearchFinding",
    "ResearchInteraction",
    "ResearchReference",
    "ProductIdea",

    # Add other model names here as they are imported
    "BackgroundTask",
    "Conversation",
    "ConversationMessage",
    "Agent",
    # "ConversationMessage",

    # File Models (Add these)
    "UserFile",
    "FileRelationship",
    "FileVersion",

    # Memory Models
    "MemoryVector",

    # Feedback Models
    "AgentFeedback",

    # Integration Models
    "IntegrationLog",
    "IntegrationConfig",

    # Media History Models
    "MediaGenerationHistory",

    # Invite Code Models
    "InviteCode",

    # Session Models
    "Session",

    # Favorite Models
    "SavedMessage",
    "SavedImage",
    "SavedVideo",
    "SavedSong",

    # LLM Models (Add LLMApiKey)
    "LLMApiKey",

    # Migration/Seed Models
    "SeedVersion",
    "Migration",
    "AgentTrainingHistory",
] 