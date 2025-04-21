from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.db.models.minion_llm_config import MinionLLMConfig
from app.db.models.llm_model import LLMModel
from app.db.models.llm_provider import LLMProvider
from app.config import logger
from app.config.defaults import LLM_CONFIG

class LLMDatabaseConfig(BaseModel):
    """
    Pydantic model representing LLM configuration from database
    """
    config_key: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    additional_settings: Optional[Dict[str, Any]] = None
    # New properties for accessing provider/model info correctly
    provider_slug: str  # Will be set from llm_model.provider.slug
    provider_name: str  # Will be set from llm_model.provider.name
    model_id: str       # Will be set from llm_model.model_id
    api_base_url: Optional[str] = None  # Will be set from llm_model.provider.base_url

async def get_llm_config_from_db(db: AsyncSession, config_key: str) -> Optional[LLMDatabaseConfig]:
    """
    Fetch LLM configuration from database by key
    Falls back to 'default' key if specified key not found
    
    Args:
        db: Database session
        config_key: Configuration key to look up
        
    Returns:
        LLM config if found, None otherwise
    """
    
    try:
        # Try to fetch specified key, with joins for provider/model relationships
        stmt = (
            select(MinionLLMConfig)
            .options(
                joinedload(MinionLLMConfig.llm_model).joinedload(LLMModel.provider)
            )
            .where(MinionLLMConfig.config_key == config_key)
        )
        
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        # If not found and key wasn't already 'default', try the 'default' key
        if not config and config_key != 'default':
            logger.warning(f"LLM config key '{config_key}' not found. Falling back to 'default'.")
            
            # Re-query with 'default' key
            stmt = (
                select(MinionLLMConfig)
                .options(
                    joinedload(MinionLLMConfig.llm_model).joinedload(LLMModel.provider)
                )
                .where(MinionLLMConfig.config_key == 'default')
            )
            
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            
        # If config is found, convert to pydantic model
        if config:
            # --- Add validation checks --- 
            if not config.llm_model:
                 logger.error(f"LLM config '{config.config_key}' found but is missing the required LLMModel relationship.")
                 return None
            if not config.llm_model.provider:
                 logger.error(f"LLM model '{config.llm_model.model_id}' linked to config '{config.config_key}' is missing the required LLMProvider relationship.")
                 return None
            if not config.llm_model.provider.slug:
                 logger.error(f"Provider for LLM model '{config.llm_model.model_id}' is missing the required 'slug'.")
                 return None
            if not config.llm_model.model_id:
                 logger.error(f"LLMModel linked to config '{config.config_key}' is missing the required 'model_id'.")
                 return None
            # --- End validation checks ---
            
            logger.info(f"Loaded LLM config for key: '{config.config_key}' -> Model: {config.llm_model.provider.name}/{config.llm_model.model_id}")
            
            # Create and return Pydantic model, ensuring provider/model info is properly included
            return LLMDatabaseConfig(
                config_key=config.config_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                additional_settings=config.additional_settings,
                # Important: Set provider and model fields correctly
                provider_slug=config.llm_model.provider.slug,
                provider_name=config.llm_model.provider.name,
                model_id=config.llm_model.model_id,
                api_base_url=config.llm_model.provider.base_url
            )
            
        # No config found for this key or 'default'
        logger.warning(f"No LLM config found for key '{config_key}' (or 'default').")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching LLM config for key '{config_key}': {e}")
        return None