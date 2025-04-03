# Built-in imports 
from enum import Enum
from typing import Dict, Any, List

# External imports
from pydantic import BaseModel, Field


class LocaleConfig(BaseModel):
  default: str = "en-US"
  supported: List[str] = ["en-US", "vi-VN"]

class AbilityConfig(BaseModel):
    id: str
    name: str
    description: str
    type: str

class AgentConfig(BaseModel):
    id: str
    name: str
    description: str
    type: str

class ServiceType(str, Enum):
    """Service types"""
    AGENT = "agent"
    ABILITY = "ability"
    MINION = "minion"
    ORCHESTRATOR = "orchestrator"

class ServiceConfig(BaseModel):
    """Configuration for a service"""
    type: ServiceType
    name: str
    description: str
    version: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceRegistry(BaseModel):
    """Registry of available services"""
    services: Dict[str, ServiceConfig] = Field(default_factory=dict)

# Export service-specific constants
DEFAULT_SERVICE_CONFIG = {
    "type": ServiceType.AGENT,
    "name": "default",
    "description": "Default service configuration",
    "version": "1.0.0-alpha.3",
    "enabled": True,
    "config": {},
    "dependencies": [],
    "metadata": {}
}

# Initialize service registry
service_registry = ServiceRegistry()
