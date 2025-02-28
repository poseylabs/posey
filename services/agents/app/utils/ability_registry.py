from typing import Dict, Type, Any
from pydantic import BaseModel, Field
from app.abilities.base import BaseAbility
from app.abilities.image_ability import ImageAbility
from app.abilities.memory import MemoryAbility
from app.config import logger

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
    """Registry for agent abilities"""
    
    _abilities: Dict[str, Type[BaseAbility]] = {
        "image_generation": ImageAbility,
        "memory": MemoryAbility
    }
    
    @classmethod
    def register(cls, name: str, ability_class: Type[BaseAbility]) -> None:
        """Register a new ability"""
        cls._abilities[name] = ability_class
        logger.info(f"Registered ability: {name}")
    
    @classmethod
    async def execute(cls, request: AbilityRequest) -> AbilityResponse:
        """Execute an ability"""
        try:
            ability_class = cls._abilities.get(request.ability_name)
            if not ability_class:
                return AbilityResponse(
                    status="error",
                    error=f"Unknown ability: {request.ability_name}"
                )
            
            ability = ability_class()
            result = await ability.execute(**request.parameters)
            
            return AbilityResponse(
                status="success",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error executing ability {request.ability_name}: {e}")
            return AbilityResponse(
                status="error",
                error=str(e)
            ) 
