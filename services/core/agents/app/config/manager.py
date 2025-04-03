import os
import logging
from typing import Optional
from functools import lru_cache

# Internal imports
from .service import ServiceConfig
from .defaults import DEFAULT_CONFIG
from .models import ModelConfig, AbilityConfig

logger = logging.getLogger(__name__)

@lru_cache()
class ConfigManager:
    def __init__(self):
        self._config: ServiceConfig = DEFAULT_CONFIG
        self._load_config()

    def _load_config(self):
        # Load config from environment/files
        pass

    @property
    def config(self) -> ServiceConfig:
        return self._config

    def get_llm_model(self, type: str = "standard", size: str = "medium"):
        return self.config.llm_models.__getattribute__(type).__getattribute__(size)

    def get_agent_config(self, agent_id: str):
        return self.config.agents.get(agent_id)

    @classmethod
    def get_image_model(cls, type: str = "standard", size: str = "medium") -> ModelConfig:
        return cls._config.image_models[type].__getattribute__(size)

    @classmethod
    def get_ability_config(cls, ability_id: str) -> Optional[AbilityConfig]:
        return next(
            (ability for ability in cls._config.abilities if ability.id == ability_id),
            None
        )

# Single instance
config_manager = ConfigManager()
config = config_manager.config 
