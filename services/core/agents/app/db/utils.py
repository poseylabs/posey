from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional

from app.db.models import MinionLLMConfig, LLMModel, LLMProvider
from app.config import logger

async def get_minion_llm_config_by_key(
    db: AsyncSession,
    config_key: str,
    fallback_to_default: bool = True
) -> Optional[MinionLLMConfig]:
    """
    Fetches a MinionLLMConfig by its config_key, with full relationships.

    Args:
        db: The async database session.
        config_key: The primary config key to fetch.
        fallback_to_default: If True and the primary key is not found,
                             attempts to fetch the 'default' config key.

    Returns:
        The fetched MinionLLMConfig object with llm_model and provider loaded,
        or None if not found (after potentially trying the fallback).
    """
    fetched_config: Optional[MinionLLMConfig] = None
    attempted_key = config_key

    query = (
        select(MinionLLMConfig)
        .options(
            joinedload(MinionLLMConfig.llm_model)
            .joinedload(LLMModel.provider)
        )
        .where(MinionLLMConfig.config_key == attempted_key)
    )

    try:
        result = await db.execute(query)
        fetched_config = result.unique().scalar_one_or_none()

        if fetched_config:
            logger.info(f"Successfully fetched DB config for key: '{attempted_key}'")
            return fetched_config
        elif fallback_to_default and config_key != "default":
            logger.warning(f"No DB config found for key: '{config_key}'. Trying 'default'.")
            attempted_key = "default"
            # Fall through to try fetching default below
        elif config_key == "default":
             logger.warning(f"Primary key '{config_key}' not found, and it was the default key.")
             return None # Don't try default again if it was the primary key
        else:
            logger.warning(f"DB config not found for key: '{config_key}' and fallback disabled.")
            return None

    except Exception as e:
        logger.error(f"Error fetching DB config for key '{attempted_key}': {e}")
        if fallback_to_default and config_key != "default" and attempted_key == config_key:
             logger.warning("Falling back to 'default' due to error.")
             attempted_key = "default"
             # Fall through to try fetching default below
        else:
            return None # Error occurred, no fallback or fallback already attempted

    # --- Attempt Fallback to 'default' if needed ---
    if attempted_key == "default":
        default_query = (
             select(MinionLLMConfig)
            .options(
                joinedload(MinionLLMConfig.llm_model)
                .joinedload(LLMModel.provider)
            )
            .where(MinionLLMConfig.config_key == "default")
        )
        try:
            result = await db.execute(default_query)
            fetched_config = result.unique().scalar_one_or_none()
            if fetched_config:
                logger.info("Successfully fetched 'default' DB config as fallback.")
                return fetched_config
            else:
                logger.error("Critical: Fallback 'default' DB configuration not found.")
                return None
        except Exception as e:
            logger.error(f"Critical: Error fetching fallback 'default' DB configuration: {e}")
            return None

    # Should not be reached if logic is correct, but ensures None is returned
    return None 