from typing import Dict, Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
from datetime import datetime
import platform as sys_platform
import psutil
from app.config import settings
from app.utils.minion import get_minion
from uuid import UUID, uuid4
import pytz
from app.config.prompts.base import get_location_from_ip
import logging

T = TypeVar('T')
DepsT = TypeVar('DepsT')

logger = logging.getLogger(__name__)

class AgentDeps(BaseModel):
    """Default agent dependencies"""
    deps: Dict[str, Any] = Field(default_factory=dict)

class SystemInfo(BaseModel):
    """System information context"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    timezone: str
    platform: str = Field(default_factory=sys_platform.system)
    platform_version: str = Field(default=sys_platform.version())
    python_version: str = Field(default=sys_platform.python_version())
    cpu_count: int = Field(default_factory=psutil.cpu_count)
    memory_available: int = Field(default_factory=lambda: psutil.virtual_memory().available)
    environment: str = Field(default=settings.ENVIRONMENT)
    version: str = Field(default=settings.SYSTEM_VERSION)
    session_id: UUID = Field(default_factory=uuid4)

class UserContext(BaseModel):
    """User-specific context"""
    user_id: str
    username: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    location: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "en"
    last_active: Optional[datetime] = None
    session_start: datetime = Field(default_factory=datetime.utcnow)

class MemoryContext(BaseModel):
    """Memory-related context"""
    recent_interactions: list = Field(default_factory=list)
    relevant_memories: list = Field(default_factory=list)
    conversation_history: list = Field(default_factory=list)
    last_topics: list = Field(default_factory=list)

class AgentContext(BaseModel):
    """Enhanced context for agent operations"""
    system: SystemInfo
    user: UserContext
    memory: MemoryContext
    request_id: str
    conversation_id: Optional[str] = None
    parent_request_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RunContext(BaseModel, Generic[DepsT]):
    """Context for agent runs"""
    context: Dict[str, Any] = Field(default_factory=dict)
    deps: DepsT
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Custom serialization method"""
        return {
            'context': self.context,
            'deps': self.deps if not hasattr(self.deps, 'model_dump') else self.deps.model_dump(),
            'metadata': self.metadata
        }

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Backwards compatibility for Pydantic v1"""
        return self.model_dump(**kwargs)

    class Config:
        arbitrary_types_allowed = True

async def create_agent_context(
    user_id: str,
    request_id: str,
    conversation_id: Optional[str] = None,
    parent_request_id: Optional[str] = None,
    **kwargs
) -> AgentContext:
    """Create a rich context object for agent operations"""
    
    # Get user info from database/cache
    user_info = await get_user_info(user_id)
    
    # Get relevant memories
    memory_minion = get_minion("memory")
    memories = await memory_minion.search_recent(
        user_id=user_id,
        limit=5,
        include_conversation=bool(conversation_id)
    )
    
    # Create context object
    context = AgentContext(
        system=SystemInfo(
            timezone=user_info.get("timezone", "UTC"),
        ),
        user=UserContext(
            user_id=user_id,
            username=user_info.get("username"),
            preferences=user_info.get("preferences", {}),
            location=user_info.get("location"),
            timezone=user_info.get("timezone"),
            language=user_info.get("language", "en"),
            last_active=user_info.get("last_active"),
        ),
        memory=MemoryContext(
            recent_interactions=[], # Leave empty for now
            relevant_memories=memories, # Use the list directly for relevant_memories
            conversation_history=[], # Leave empty for now
            last_topics=[] # Leave empty for now
        ),
        request_id=request_id,
        conversation_id=conversation_id,
        parent_request_id=parent_request_id,
        metadata=kwargs
    )
    
    return context

async def enhance_run_context(
    run_ctx: "RunContext[DepsT]",
    user_id: str,
    request_id: str,
    **kwargs
) -> "RunContext[DepsT]":
    """Enhance a RunContext with additional context"""
    
    # Create rich context
    agent_ctx = await create_agent_context(
        user_id=user_id,
        request_id=request_id,
        **kwargs
    )
    
    # Add to RunContext's context field
    run_ctx.context = {
        "system": agent_ctx.system.dict(),
        "user": agent_ctx.user.dict(),
        "memory": agent_ctx.memory.dict(),
        "request": {
            "id": agent_ctx.request_id,
            "conversation_id": agent_ctx.conversation_id,
            "parent_id": agent_ctx.parent_request_id
        },
        "metadata": agent_ctx.metadata
    }
    
    # Enhance context with additional helpful information
    current_time = datetime.utcnow()
    user_tz = run_ctx.context.get("user", {}).get("timezone", "UTC")
    
    # Add current time information directly to the top level for easy access
    try:
        local_time = current_time.astimezone(pytz.timezone(user_tz))
        run_ctx.context["timestamp"] = local_time.isoformat()
        run_ctx.context["timezone"] = user_tz
        run_ctx.context["formatted_time"] = local_time.strftime('%A, %B %d, %Y %I:%M:%S %p %Z')
        logger.debug(f"Added time information to context: {run_ctx.context['formatted_time']}")
    except Exception as e:
        logger.warning(f"Failed to add time information to context: {e}")
        run_ctx.context["timestamp"] = current_time.isoformat()
    
    # Ensure location information is accessible at the top level
    if "location" not in run_ctx.context:
        # Try to get from user context first
        user_location = run_ctx.context.get("user", {}).get("location")
        system_location = run_ctx.context.get("system", {}).get("location")
        
        if user_location:
            run_ctx.context["location"] = user_location
            logger.debug(f"Added user location to context: {user_location}")
        elif system_location:
            run_ctx.context["location"] = system_location
            logger.debug(f"Added system location to context: {system_location}")
        else:
            # Try to get location from IP as a fallback
            try:
                location = get_location_from_ip()
                if location:
                    run_ctx.context["location"] = location.dict()
                    logger.debug(f"Added IP-based location to context: {location}")
            except Exception as e:
                logger.warning(f"Failed to get location from IP: {e}")
    
    return run_ctx

# Helper function to get user info (implement based on your user storage)
async def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get user information from database/cache"""
    # TODO: Implement proper user info retrieval from database
    
    # For now, provide default information from settings.py
    # This ensures time requests don't default to UTC
    from app.config import settings
    
    return {
        "username": "User",
        "timezone": settings.DEFAULT_TIMEZONE,  # Use timezone from settings
        "language": settings.DEFAULT_LANGUAGE,
        "preferences": {},
        "location": f"Seattle, {settings.DEFAULT_STATE}"
    } 
