from typing import Dict, Any
from app.utils.ability_registry import AbilityRegistry, AbilityRequest

async def execute_ability(ability_name: str, **parameters) -> Dict[str, Any]:
    """Tool function for executing abilities"""
    request = AbilityRequest(
        ability_name=ability_name,
        parameters=parameters
    )
    response = await AbilityRegistry.execute(request)
    return response.model_dump()

async def use_ability(ability_name: str, **parameters) -> Dict[str, Any]:
    """Execute an ability directly"""
    return await execute_ability(ability_name, **parameters) 
