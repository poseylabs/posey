from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.db.models.minion_llm_config import MinionLLMConfig
from app.db.models.llm_model import LLMModel
from app.db.models.llm_provider import LLMProvider
from app.config import logger

class LLMDatabaseConfig(BaseModel):
    """Structure for LLM configuration loaded from the database."""
    config_key: str
    provider_name: str
    model_slug: str # e.g., claude-3-7-sonnet-latest
    api_base_url: Optional[str] = None
    supports_tools: bool = False
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    additional_settings: Dict[str, Any] = Field(default_factory=dict)

async def get_llm_config_from_db(
    db: AsyncSession,
    config_key: str,
    fallback_to_default: bool = True
) -> Optional[LLMDatabaseConfig]:
    """Fetches LLM configuration for a given key from the database."""

    logger.debug(f"Attempting to load LLM config for key: '{config_key}'")
    stmt = (
        select(MinionLLMConfig)
        .options(
            joinedload(MinionLLMConfig.model).joinedload(LLMModel.provider)
        )
        .where(MinionLLMConfig.config_key == config_key)
    )
    result = await db.execute(stmt)
    db_config = result.scalars().first()

    if not db_config and fallback_to_default and config_key != 'default':
        logger.warning(f"LLM config key '{config_key}' not found. Falling back to 'default'.")
        return await get_llm_config_from_db(db, 'default', fallback_to_default=False)
    elif not db_config:
        logger.error(f"LLM config key '{config_key}' not found in database.")
        return None

    if not db_config.model or not db_config.model.provider:
        logger.error(f"Incomplete config for key '{config_key}': Missing model or provider link.")
        return None

    if not db_config.model.is_enabled or not db_config.model.provider.is_active:
        logger.warning(f"LLM model '{db_config.model.slug}' or provider '{db_config.model.provider.name}' is disabled for config key '{config_key}'.")
        # Optionally, could fallback to default here too, but returning None indicates an issue.
        return None

    logger.info(f"Loaded LLM config for key: '{config_key}' -> Model: {db_config.model.provider.name}/{db_config.model.slug}")
    return LLMDatabaseConfig(
        config_key=db_config.config_key,
        provider_name=db_config.model.provider.name,
        model_slug=db_config.model.slug,
        api_base_url=db_config.model.provider.base_url,
        supports_tools=db_config.model.supports_tools,
        temperature=db_config.temperature,
        max_tokens=db_config.max_tokens,
        top_p=db_config.top_p,
        frequency_penalty=db_config.frequency_penalty,
        presence_penalty=db_config.presence_penalty,
        additional_settings=db_config.additional_settings or {},
    ) 