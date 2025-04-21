from typing import Dict, Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
from datetime import datetime
import platform as sys_platform
import psutil
from app.config import settings
from app.utils.minion_registry import MinionRegistry
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
import pytz
from app.models.context import UserContext
from app.models.system import LocationInfo
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
    registry: MinionRegistry,
    db: AsyncSession,
    conversation_id: Optional[str] = None,
    parent_request_id: Optional[str] = None,
    **kwargs
) -> AgentContext:
    """Create a rich context object for agent operations"""
    
    # Get user info from database/cache
    user_info = await get_user_info(user_id)
    
    # Get relevant memories using the registry instance
    memory_minion = await registry.get_minion("memory", db)
    if not memory_minion:
        logger.error("Memory minion not found or failed to initialize.")
        memories = []
    else:
        memories = await memory_minion.search_recent(
            user_id=user_id,
            limit=5,
            include_conversation=bool(conversation_id)
        )
    
    # --- Convert location string from get_user_info to LocationInfo if needed --- 
    user_location_str = user_info.get("location")
    user_location_obj: Optional[LocationInfo] = None
    if isinstance(user_location_str, str):
         # Attempt to parse the string (simple example, might need more robust parsing)
         try:
             parts = user_location_str.split(',')
             if len(parts) >= 1:
                 user_location_obj = LocationInfo(city=parts[0].strip()) 
             # Add more parsing logic if region/country are expected
         except Exception as parse_e:
             logger.warning(f"Could not parse location string '{user_location_str}' into LocationInfo: {parse_e}")
    elif isinstance(user_location_str, LocationInfo):
         user_location_obj = user_location_str # It's already the correct type
         
    # Create context object using consolidated UserContext
    context = AgentContext(
        system=SystemInfo(
            timezone=user_info.get("timezone", "UTC"),
        ),
        user=UserContext( # Use imported UserContext
            user_id=user_id,
            username=user_info.get("username"),
            name=user_info.get("username"), # Populate name with username for now
            preferences=user_info.get("preferences", {}),
            location=user_location_obj, # Use the LocationInfo object
            timezone=user_info.get("timezone"),
            language=user_info.get("language", "en-US"), # Match default in model
            last_active=user_info.get("last_active"),
            session_start=datetime.utcnow() # Assuming session starts now
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
    registry: MinionRegistry,
    db: AsyncSession,
    **kwargs
) -> "RunContext[DepsT]":
    """Enhance a RunContext with additional context"""
    
    # Create rich context
    agent_ctx = await create_agent_context(
        user_id=user_id,
        request_id=request_id,
        registry=registry,
        db=db,
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
        # Try to get from user context first (now an object)
        user_location = run_ctx.context.get("user", {}).get("location") # This is LocationInfo or None
        system_location = run_ctx.context.get("system", {}).get("location") # This is LocationInfo or None
        
        final_location_obj: Optional[LocationInfo] = None
        if user_location and isinstance(user_location, dict):
            final_location_obj = LocationInfo(**user_location)
        elif system_location and isinstance(system_location, dict):
            final_location_obj = LocationInfo(**system_location)
        
        if final_location_obj:
            run_ctx.context["location"] = final_location_obj.dict() # Store as dict
            logger.debug(f"Added user/system location object to context: {final_location_obj}")
        else:
            # Restore fallback call to get_location_from_ip here
            try:
                location_ip = get_location_from_ip()
                if location_ip:
                    run_ctx.context["location"] = location_ip.dict() # Store as dict
                    logger.debug(f"Added IP-based location to context: {location_ip}")
                else:
                    logger.warning("Location not found in user/system context and IP fallback returned None.")
            except Exception as e:
                logger.warning(f"Failed to get location from IP during fallback: {e}")
    
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
