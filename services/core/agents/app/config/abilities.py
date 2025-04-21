from enum import Enum
from typing import Dict, Any, List
from app.config import logger

class AgentAbility(Enum):
    """Enumeration of all available agent abilities"""
    # CONTENT_ANALYSIS = "content_analysis" # This is a Minion
    MEMORY = "memory"
    # RESEARCH = "research" # This is a Minion
    IMAGE_GENERATION = "image_generation"
    # IMAGE_PROCESSING = "image_processing" # This is a Minion
    # VOYAGER = "voyager" # This is a Minion
    FILE_PROCESSING = "file_processing" # Add the actual file processing ability
    # Add other TRUE abilities as we implement them

    @classmethod
    def get_minion_name(cls, ability: str) -> str:
        """Map ability names to minion names - Deprecated/Review Needed?"""
        # This mapping might need review/removal now that enum only contains true abilities
        # For now, returning the ability name itself might be safer
        logger.warning(f"AgentAbility.get_minion_name called for ability '{ability}'. This mapping might be outdated.")
        # mapping = {
        #     cls.MEMORY.value: "memory", # Memory might be handled by a minion OR ability
        #     cls.IMAGE_GENERATION.value: "image_generation", # Image Gen might be handled by minion OR ability
        # }
        # mapped_name = mapping.get(ability, ability)
        return ability # Return ability name directly for now

# Register available abilities - This also needs update after get_available_abilities is fixed
# REGISTERED_ABILITIES = {
#     ability.value: {
#         "name": ability.value,
#         "minion": AgentAbility.get_minion_name(ability.value)
#     } for ability in AgentAbility
# }
REGISTERED_ABILITIES = {}

logger.info(f"Registered abilities (Enum Updated - List needs fix): {list(AgentAbility.__members__.keys())}")

__all__ = ['AgentAbility', 'REGISTERED_ABILITIES']