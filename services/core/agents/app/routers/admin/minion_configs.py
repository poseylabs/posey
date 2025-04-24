from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
import uuid
from datetime import datetime
import json
import logging

from app.db import get_db
from app.db.models import MinionLLMConfig, LLMModel, LLMProvider
from app.db.models.managed_minion import ManagedMinion
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Pydantic Schemas
class MinionLLMConfigBase(BaseModel):
    config_key: str
    llm_model_id: UUID
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 0.95
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    additional_settings: Optional[Dict[str, Any]] = None

class MinionLLMConfigCreate(MinionLLMConfigBase):
    pass

class MinionLLMConfigUpdate(BaseModel):
    config_key: Optional[str] = None
    llm_model_id: Optional[UUID] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    additional_settings: Optional[Dict[str, Any]] = None
    # Add minion activation field
    is_active: Optional[bool] = None

class MinionLLMConfigModelResponse(BaseModel):
    id: UUID
    name: str
    provider: Optional[dict] = None
    
    model_config = {
        "from_attributes": True,
    }

class MinionInfoResponse(BaseModel):
    is_active: bool
    display_name: Optional[str] = None
    description: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
    }

class MinionLLMConfigResponse(MinionLLMConfigBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    model: Optional[MinionLLMConfigModelResponse] = None
    minion_info: Optional[MinionInfoResponse] = None

    model_config = {
        "from_attributes": True,
    }

class MinionLLMConfigListResponse(BaseModel):
    configs: List[MinionLLMConfigResponse]

class MinionStatusToggleRequest(BaseModel):
    is_active: bool

router = APIRouter(
    prefix="/minion-configs",
    tags=["Admin - Minion LLM Configurations"],
    # TODO: Add dependencies=[Depends(require_admin_user)] for security
)

@router.get("", response_model=MinionLLMConfigListResponse)
async def list_minion_configs(
    include_model: bool = Query(True, description="Include model data"),
    include_provider: bool = Query(True, description="Include provider data"),
    include_minion_info: bool = Query(False, description="Include minion activation status"),
    db: AsyncSession = Depends(get_db)
) -> MinionLLMConfigListResponse:
    """
    List all minion LLM configurations with optional relationships
    """
    query = select(MinionLLMConfig)
    
    if include_model:
        query = query.options(joinedload(MinionLLMConfig.llm_model))
        
        if include_provider:
            query = query.options(joinedload(MinionLLMConfig.llm_model).joinedload(LLMModel.provider))
    
    result = await db.execute(query.order_by(MinionLLMConfig.config_key))
    configs = result.unique().scalars().all()
    
    # If requested, fetch minion info for each config
    minion_data = {}
    if include_minion_info:
        # Get all minion keys
        config_keys = [config.config_key for config in configs]
        if config_keys:
            # Fetch all minions in one query
            minion_query = select(ManagedMinion).where(ManagedMinion.minion_key.in_(config_keys))
            minion_result = await db.execute(minion_query)
            minions = minion_result.scalars().all()
            
            # Create a lookup dict for quick access
            minion_data = {minion.minion_key: minion for minion in minions}
    
    # Process provider data for response
    for config in configs:
        # Add model data if requested
        if include_model and hasattr(config, 'llm_model') and config.llm_model:
            provider_data = None
            if include_provider and hasattr(config.llm_model, 'provider') and config.llm_model.provider:
                provider_data = {
                    "id": config.llm_model.provider.id,
                    "name": config.llm_model.provider.name,
                    "slug": config.llm_model.provider.slug
                }
            
            # Create model data structure
            config.model = {
                "id": config.llm_model.id,
                "name": config.llm_model.name,
                "provider": provider_data
            }
        
        # Add minion info if requested
        if include_minion_info:
            minion = minion_data.get(config.config_key)
            if minion:
                config.minion_info = {
                    "is_active": minion.is_active,
                    "display_name": minion.display_name,
                    "description": minion.description
                }
            else:
                # If no matching minion found, still include with default values
                config.minion_info = {
                    "is_active": False,
                    "display_name": None,
                    "description": None
                }
    
    return MinionLLMConfigListResponse(configs=configs)

@router.post("", response_model=MinionLLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_minion_config(config_data: MinionLLMConfigCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new minion LLM configuration
    """
    # Check if the LLM model exists
    model = await db.get(LLMModel, config_data.llm_model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM model with id '{config_data.llm_model_id}' not found."
        )
    
    # Check if the config_key already exists
    existing = await db.execute(select(MinionLLMConfig).where(MinionLLMConfig.config_key == config_data.config_key))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Minion config with key '{config_data.config_key}' already exists."
        )
    
    new_config = MinionLLMConfig(
        id=uuid.uuid4(),
        **config_data.model_dump()
    )
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    # Load relationships for response
    await db.refresh(new_config, ["llm_model"])
    if new_config.llm_model:
        await db.refresh(new_config.llm_model, ["provider"])
        
        # Create model data structure for response
        new_config.model = {
            "id": new_config.llm_model.id,
            "name": new_config.llm_model.name,
            "provider": {
                "id": new_config.llm_model.provider.id,
                "name": new_config.llm_model.provider.name,
                "slug": new_config.llm_model.provider.slug
            } if new_config.llm_model.provider else None
        }
    
    # Check if there's a corresponding minion and add info to response
    minion = await db.get(ManagedMinion, new_config.config_key)
    if minion:
        new_config.minion_info = {
            "is_active": minion.is_active,
            "display_name": minion.display_name,
            "description": minion.description
        }
    
    return new_config

@router.get("/{config_id}", response_model=MinionLLMConfigResponse)
async def get_minion_config(
    config_id: UUID, 
    include_model: bool = Query(True, description="Include model data"),
    include_provider: bool = Query(True, description="Include provider data"),
    include_minion_info: bool = Query(False, description="Include minion activation status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific minion LLM configuration by ID
    """
    query = select(MinionLLMConfig).where(MinionLLMConfig.id == config_id)
    
    if include_model:
        query = query.options(joinedload(MinionLLMConfig.llm_model))
        
        if include_provider:
            query = query.options(joinedload(MinionLLMConfig.llm_model).joinedload(LLMModel.provider))
    
    result = await db.execute(query)
    config = result.unique().scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minion config not found")
    
    # Process model and provider data for response
    if include_model and hasattr(config, 'llm_model') and config.llm_model:
        provider_data = None
        if include_provider and hasattr(config.llm_model, 'provider') and config.llm_model.provider:
            provider_data = {
                "id": config.llm_model.provider.id,
                "name": config.llm_model.provider.name,
                "slug": config.llm_model.provider.slug
            }
        
        # Create model data structure
        config.model = {
            "id": config.llm_model.id,
            "name": config.llm_model.name,
            "provider": provider_data
        }
    
    # Add minion info if requested
    if include_minion_info:
        minion = await db.get(ManagedMinion, config.config_key)
        if minion:
            config.minion_info = {
                "is_active": minion.is_active,
                "display_name": minion.display_name,
                "description": minion.description
            }
        else:
            config.minion_info = {
                "is_active": False,
                "display_name": None,
                "description": None
            }
    
    return config

@router.put("/{config_id}", response_model=MinionLLMConfigResponse)
async def update_minion_config(
    config_id: UUID, 
    config_update: MinionLLMConfigUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing minion LLM configuration and optionally its minion status
    """
    config = await db.get(MinionLLMConfig, config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minion config not found")
    
    update_data = config_update.model_dump(exclude_unset=True)
    
    # Extract is_active if present (for managed_minions table)
    is_active = None
    if "is_active" in update_data:
        is_active = update_data.pop("is_active")
    
    # Check if config_key is being updated and if it already exists
    if "config_key" in update_data and update_data["config_key"] != config.config_key:
        existing = await db.execute(
            select(MinionLLMConfig)
            .where(MinionLLMConfig.config_key == update_data["config_key"])
            .where(MinionLLMConfig.id != config_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Minion config with key '{update_data['config_key']}' already exists."
            )
    
    # Check if LLM model exists if being updated
    if "llm_model_id" in update_data:
        model = await db.get(LLMModel, update_data["llm_model_id"])
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM model with id '{update_data['llm_model_id']}' not found."
            )
    
    # Store the old config_key in case it's being changed
    old_config_key = config.config_key
    
    # Apply updates to the config
    for key, value in update_data.items():
        setattr(config, key, value)
    
    # Handle minion activation status update if needed
    minion = None
    if is_active is not None:
        # Get the minion using current config_key
        minion = await db.get(ManagedMinion, old_config_key)
        
        if minion:
            # If config_key changed, we need to handle the minion key change too
            if "config_key" in update_data and old_config_key != config.config_key:
                # This is a complex operation with potential cascading effects
                # For now, we'll raise an error suggesting this needs to be handled separately
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Changing config_key and minion status in the same request is not supported. Please update them separately."
                )
            
            # Update minion activation
            minion.is_active = is_active
            logger.info(f"Updated minion {minion.minion_key} activation status to {is_active}")
    
    await db.commit()
    await db.refresh(config)
    
    # Load relationships for response
    await db.refresh(config, ["llm_model"])
    if config.llm_model:
        await db.refresh(config.llm_model, ["provider"])
        
        # Create model data structure for response
        config.model = {
            "id": config.llm_model.id,
            "name": config.llm_model.name,
            "provider": {
                "id": config.llm_model.provider.id,
                "name": config.llm_model.provider.name,
                "slug": config.llm_model.provider.slug
            } if config.llm_model.provider else None
        }
    
    # Add minion info to response
    if minion is None:
        minion = await db.get(ManagedMinion, config.config_key)
    
    if minion:
        config.minion_info = {
            "is_active": minion.is_active,
            "display_name": minion.display_name,
            "description": minion.description
        }
    else:
        config.minion_info = {
            "is_active": False,
            "display_name": None,
            "description": None
        }
    
    return config

@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_minion_config(config_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Delete a minion LLM configuration
    """
    config = await db.get(MinionLLMConfig, config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minion config not found")
    
    # TODO: Check if this config is being used by any active minions before deleting
    # This would require adding a check against any tables that reference this config
    
    await db.delete(config)
    await db.commit()
    return None

# Add a dedicated endpoint just for toggling minion status
@router.put("/{config_id}/toggle-status", response_model=MinionLLMConfigResponse)
async def toggle_minion_status(
    config_id: UUID,
    status_update: MinionStatusToggleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle the activation status of a minion associated with this configuration
    """
    config = await db.get(MinionLLMConfig, config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minion config not found")
    
    # Find the corresponding minion
    minion = await db.get(ManagedMinion, config.config_key)
    if not minion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No managed minion found with key '{config.config_key}'"
        )
    
    # Update the minion's active status from the request body
    minion.is_active = status_update.is_active
    
    await db.commit()
    
    # Refresh data for response
    await db.refresh(config, ["llm_model"])
    if config.llm_model:
        await db.refresh(config.llm_model, ["provider"])
        
        # Create model data structure for response
        config.model = {
            "id": config.llm_model.id,
            "name": config.llm_model.name,
            "provider": {
                "id": config.llm_model.provider.id,
                "name": config.llm_model.provider.name,
                "slug": config.llm_model.provider.slug
            } if config.llm_model.provider else None
        }
    
    # Add minion info to response
    config.minion_info = {
        "is_active": minion.is_active,
        "display_name": minion.display_name,
        "description": minion.description
    }
    
    logger.info(f"Toggled minion {minion.minion_key} activation status to {status_update.is_active}")
    
    return config
