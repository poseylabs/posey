"""Shared base prompt module for all agent interactions"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
import pytz
import json
from string import Template
import requests
from . import PromptLoader
from ..posey import get_posey_config
from app.config import logger

class LocationInfo(BaseModel):
    """Location information"""
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserContext(BaseModel):
    """User context information"""
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = "en-US"
    preferences: Dict[str, Any] = {}
    location: Optional[LocationInfo] = None

class SystemContext(BaseModel):
    """System context information"""
    timestamp: str
    timezone: str = "UTC"
    location: Optional[LocationInfo] = None

class MemoryContext(BaseModel):
    """Memory context information"""
    recent_topics: list[str] = []
    relevant_memories: list[Dict[str, Any]] = []

class BasePromptContext(BaseModel):
    """Combined context for base prompt generation"""
    user: Optional[UserContext] = None
    system: SystemContext
    memory: Optional[MemoryContext] = None

def get_location_from_ip() -> Optional[LocationInfo]:
    """Get location information from IP address using ipapi.co"""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return LocationInfo(
                city=data.get('city'),
                region=data.get('region'),
                country=data.get('country_name'),
                timezone=data.get('timezone'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )
    except Exception as e:
        logger.warning(f"Failed to get location from IP: {e}")
    return None

def generate_base_prompt(context: BasePromptContext) -> str:
    """Generate the base system prompt used across all LLM interactions
    
    Args:
        context: Combined context information including user, system and memory data
        
    Returns:
        Formatted base prompt string incorporating all context
    """
    # Load base prompt template
    base_template = PromptLoader.get_shared_prompt("base")
    
    # Get Posey's config
    config = get_posey_config()
    
    # Parse timestamp
    timestamp = datetime.fromisoformat(context.system.timestamp)
    formatted_time = timestamp.strftime('%B %d, %Y %I:%M:%S %p %Z')
    
    # Get location info (prefer user location over system location)
    location = None
    if context.user and context.user.location:
        location = context.user.location
    elif context.system.location:
        location = context.system.location
    
    # Prepare template variables
    template_vars = {
        # Identity from Posey's config
        "name": config.vitals.name,
        "full_name": config.vitals.full_name,
        "age": config.vitals.age,
        "email": config.contact.email,
        "city": config.location.city,
        "state": config.location.state,
        
        # System/Temporal
        "timestamp": formatted_time,
        "timezone": context.system.timezone,
        
        # User Info (with defaults)
        "user_id": context.user.id if context.user else "Unknown",
        "user_name": context.user.name if context.user else "Unknown",
        "user_email": context.user.email if context.user else "Unknown",
        "user_timezone": context.user.timezone if context.user else context.system.timezone,
        "user_language": context.user.language if context.user else "en-US",
        "user_preferences": json.dumps(context.user.preferences if context.user else {}, indent=2),
        
        # Location Info
        "user_location": (
            f"{location.city}, {location.region}, {location.country}" if location
            else "Unknown Location"
        ),
        
        # Memory Info
        "recent_topics": ", ".join(context.memory.recent_topics) if context.memory else "None",
        "relevant_memories": json.dumps(context.memory.relevant_memories if context.memory else [], indent=2)
    }
    
    # Build sections using templates
    sections = []
    
    # Add identity section
    identity_template = Template(base_template["system"]["identity"])
    sections.append(identity_template.substitute(template_vars))
    
    # Add temporal section
    temporal_template = Template(base_template["system"]["temporal"])
    sections.append(temporal_template.substitute(template_vars))
    
    # Add user section if user context exists
    if context.user:
        user_template = Template(base_template["system"]["user_info"])
        sections.append(user_template.substitute(template_vars))
    
    # Add memory section if memory context exists
    if context.memory:
        memory_template = Template(base_template["system"]["memory_info"])
        sections.append(memory_template.substitute(template_vars))
    
    # Add response format requirements
    sections.append(base_template["system"]["response_format"])
    
    # Combine all sections with double newlines for readability
    return "\n\n".join(sections) + "\n\nYou should use this contextual information to provide more personalized and temporally-aware responses while strictly adhering to the required JSON response format."

def get_default_context() -> BasePromptContext:
    """Get a default context with current time in UTC and approximate location"""
    now = datetime.now(pytz.UTC)
    
    # Try to get location from IP
    location = get_location_from_ip()
    
    # If we got location info, use its timezone
    timezone = location.timezone if location and location.timezone else "UTC"
    
    return BasePromptContext(
        system=SystemContext(
            timestamp=now.isoformat(),
            timezone=timezone,
            location=location
        )
    )
