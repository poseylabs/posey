from enum import Enum
from typing import Dict, Any, List
from app.config import logger

class AgentAbility(Enum):
    """Enumeration of all available agent abilities"""
    CONTENT_ANALYSIS = "content_analysis"
    MEMORY = "memory"
    RESEARCH = "research"
    IMAGE_GENERATION = "image_generation"
    IMAGE_PROCESSING = "image_processing"
    VOYAGER = "voyager"
    # Add other abilities as we implement them

    @classmethod
    def get_minion_name(cls, ability: str) -> str:
        """Map ability names to minion names"""
        mapping = {
            cls.CONTENT_ANALYSIS.value: "content_analysis",
            cls.MEMORY.value: "memory",
            cls.RESEARCH.value: "research",
            cls.IMAGE_GENERATION.value: "image_generation",
            cls.IMAGE_PROCESSING.value: "image_processing",
            cls.VOYAGER.value: "voyager"
        }
        mapped_name = mapping.get(ability, ability)
        
        # Log the mapping for debugging
        if ability in mapping:
            logger.debug(f"Mapped ability '{ability}' to minion '{mapped_name}'")
        else:
            logger.warning(f"No explicit mapping for ability '{ability}', using name as is")
            
        return mapped_name

# Register available abilities
REGISTERED_ABILITIES = {
    ability.value: {
        "name": ability.value,
        "minion": AgentAbility.get_minion_name(ability.value)
    } for ability in AgentAbility
}

logger.info(f"Registered abilities: {list(REGISTERED_ABILITIES.keys())}")

__all__ = ['AgentAbility', 'REGISTERED_ABILITIES']

class AbilityRegistry:
    """Registry of available abilities and their configurations"""
    
    @staticmethod
    def get_available_abilities() -> List[Dict[str, Any]]:
        """Get list of all available abilities and their descriptions"""
        abilities = [
            {
                "name": AgentAbility.CONTENT_ANALYSIS.value,
                "description": "Analyzes user requests to determine intent and required abilities",
                "capabilities": ["intent_analysis", "task_decomposition"]
            },
            {
                "name": AgentAbility.MEMORY.value,
                "description": "Manages long-term memory storage and retrieval",
                "capabilities": ["store", "search", "update"]
            },
            {
                "name": AgentAbility.RESEARCH.value,
                "description": "Performs internet research and information gathering",
                "capabilities": ["search", "analyze", "synthesize"]
            },
            {
                "name": AgentAbility.IMAGE_GENERATION.value,
                "description": "Handles image generation",
                "capabilities": ["generate", "edit_generated", "optimize_prompt"]
            },
            {
                "name": AgentAbility.IMAGE_PROCESSING.value,
                "description": "Analyzes image processing requests and determines steps or delegates",
                "capabilities": ["analyze", "delegate", "coordinate"]
            },
            {
                "name": AgentAbility.VOYAGER.value,
                "description": "Navigates and interacts with web content",
                "capabilities": ["browse", "scrape", "interact"]
            }
        ]
        
        logger.debug(f"Returned {len(abilities)} available abilities")
        return abilities

    @staticmethod
    def validate_ability(ability_name: str) -> bool:
        """Validate if an ability exists"""
        is_valid = ability_name in [a.value for a in AgentAbility]
        
        if is_valid:
            logger.debug(f"Validated ability: {ability_name}")
        else:
            logger.warning(f"Invalid ability requested: {ability_name}")
            logger.warning(f"Available abilities are: {[a.value for a in AgentAbility]}")
            
        return is_valid

    @staticmethod
    def get_ability_config(ability_name: str) -> Dict[str, Any]:
        """Get configuration for a specific ability"""
        abilities = {a["name"]: a for a in AbilityRegistry.get_available_abilities()}
        config = abilities.get(ability_name, {})
        
        if ability_name in abilities:
            logger.debug(f"Retrieved config for ability: {ability_name}")
        else:
            logger.warning(f"No configuration found for ability: {ability_name}")
            
        return config

    @staticmethod
    def get_default_configs() -> Dict[str, Dict[str, Any]]:
        """Get default configurations for abilities"""
        return {
            AgentAbility.IMAGE_GENERATION.value: {
                "default_size": "1024x1024",
                "default_model": "dalle-3",
                "default_style": "realistic"
            },
            AgentAbility.MEMORY.value: {
                "max_results": 5,
                "relevance_threshold": 0.7
            },
            AgentAbility.RESEARCH.value: {
                "max_depth": 2,
                "max_sources": 3,
                "credibility_threshold": 0.8
            },
            AgentAbility.VOYAGER.value: {
                "max_pages": 5,
                "timeout": 30,
                "follow_links": True
            }
        } 
