from typing import Dict, Type, Any, List, Optional
from pydantic import BaseModel, Field
from app.abilities.base import BaseAbility
from app.abilities.image_ability import ImageAbility
from app.abilities.memory import MemoryAbility
from app.abilities.file_processing import FileProcessingAbility
from app.config import logger
import asyncio

class AbilityRequest(BaseModel):
    """Model for ability execution requests"""
    ability_name: str = Field(..., description="Name of the ability to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the ability")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class AbilityResponse(BaseModel):
    """Model for ability execution responses"""
    status: str = Field(..., description="Status of the execution")
    data: Dict[str, Any] = Field(default_factory=dict, description="Result data")
    error: str | None = Field(default=None, description="Error message if any")

class AbilityRegistry:
    """Registry for standalone abilities (tools)."""

    # Dictionary to register ability implementations
    _abilities: Dict[str, Type[BaseAbility]] = {
        "image_generation": ImageAbility,
        "memory": MemoryAbility,
        "file_processing": FileProcessingAbility
    }

    # Cache for available abilities generated from _abilities
    _available_abilities_cache: List[Dict[str, Any]] = []
    _cache_initialized = False

    @classmethod
    def register(cls, name: str, ability_class: Type[BaseAbility]) -> None:
        """Register a new ability"""
        if name in cls._abilities:
             logger.warning(f"Overwriting existing ability registration: {name}")
        cls._abilities[name] = ability_class
        cls._cache_initialized = False # Invalidate cache on registration
        logger.info(f"Registered ability: {name}")

    @classmethod
    def _initialize_cache(cls) -> None: # Removed db parameter
        """Initialize cache from registered abilities.""" # Updated docstring
        if cls._cache_initialized:
            return

        logger.info("Initializing AbilityRegistry cache...")
        cls._available_abilities_cache = []
        for name, ability_class in cls._abilities.items():
            description = getattr(ability_class, "description", f"Ability for {name}")
            capabilities = getattr(ability_class, "capabilities", [])

            cls._available_abilities_cache.append({
                "name": name,
                "description": description,
                "capabilities": capabilities
            })

        cls._cache_initialized = True
        logger.info(f"Ability registry cache initialized with {len(cls._available_abilities_cache)} abilities.")
        logger.debug(f"Available abilities: {[a['name'] for a in cls._available_abilities_cache]}")

    @classmethod
    def get_available_abilities_names(cls) -> List[str]: # Removed db parameter
        """Return list of available ability names"""
        cls._initialize_cache() # Ensure cache is initialized
        return list(cls._abilities.keys())

    @classmethod
    def get_available_abilities(cls) -> List[Dict[str, Any]]: # Removed db parameter
        """Return list of available abilities with descriptions"""
        cls._initialize_cache() # Ensure cache is initialized
        return cls._available_abilities_cache

    @classmethod
    def validate_ability(cls, ability_name: str) -> bool: # Removed db parameter
        """Check if an ability exists in the registry"""
        cls._initialize_cache() # Ensure cache is initialized
        return ability_name in cls._abilities

    @classmethod
    async def execute(cls, request: AbilityRequest) -> AbilityResponse: # Removed db parameter
        """Execute an ability"""
        cls._initialize_cache() # Ensure cache is initialized
        try:
            ability_class = cls._abilities.get(request.ability_name)
            if not ability_class:
                logger.error(f"Attempted to execute unknown ability: {request.ability_name}")
                return AbilityResponse(
                    status="error",
                    error=f"Unknown ability: {request.ability_name}"
                )

            # Instantiate the ability class
            # Consider if abilities need specific initialization parameters later
            ability_instance = ability_class()
            logger.info(f"Executing ability '{request.ability_name}' with params: {request.parameters}")

            # Execute the ability's main method (assuming 'execute')
            # Ensure the execute method is async
            if hasattr(ability_instance, 'execute') and asyncio.iscoroutinefunction(ability_instance.execute):
                 result = await ability_instance.execute(request.parameters) # Pass parameters directly
            else:
                 # Handle synchronous execute or raise error if 'execute' is missing/not async
                 logger.error(f"Ability '{request.ability_name}' does not have a valid async execute method.")
                 return AbilityResponse(
                      status="error",
                      error=f"Ability '{request.ability_name}' is not executable asynchronously."
                 )

            # Assuming the ability's execute method returns a dict suitable for AbilityResponse.data
            return AbilityResponse(
                status="success",
                data=result # The result from the ability's execute method
            )

        except Exception as e:
            logger.exception(f"Error executing ability {request.ability_name}: {e}") # Log traceback
            return AbilityResponse(
                status="error",
                error=f"Execution failed: {str(e)}"
            ) 
