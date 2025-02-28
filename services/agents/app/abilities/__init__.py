from typing import Dict, Any
from .base import BaseAbility
from .image_ability import ImageAbility
from .memory import MemoryAbility
import logging

__all__ = [
    'BaseAbility',
    'ImageAbility',
    'MemoryAbility'
]

# Register abilities
REGISTERED_ABILITIES = {
    'image_generation': ImageAbility,
    'image': ImageAbility,
    'image_generator': ImageAbility,
    'memory': MemoryAbility,  # Add unified memory ability
}

# Add debug logging
logger = logging.getLogger(__name__)


def get_ability(ability_name: str) -> BaseAbility:
    """Get an ability instance by name"""
    ability_class = REGISTERED_ABILITIES.get(ability_name)
    if not ability_class:
        logger.warning(f"Unknown ability requested: {ability_name}")  # Add warning logging
        raise ValueError(f"Unknown ability: {ability_name}")
    return ability_class()

class SpeechAbility(BaseAbility):
    async def execute(self, **parameters) -> Dict[str, Any]:
        """Execute speech synthesis"""
        # Implement speech synthesis logic
        pass

class TranslationAbility(BaseAbility):
    async def execute(self, **parameters) -> Dict[str, Any]:
        """Execute translation"""
        # Implement translation logic
        pass 
