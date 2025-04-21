from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, List, Optional
import logging

from app.db import get_db
from app.db.models.managed_minion import ManagedMinion
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Pydantic schemas
class ManagedMinionUpdate(BaseModel):
    is_active: bool

class ManagedMinionResponse(BaseModel):
    minion_key: str
    display_name: str
    description: Optional[str] = None
    entry_point_ref: str
    is_active: bool
    source: str
    configuration: Optional[Dict] = None
    associated_abilities: Optional[List[str]] = None

    class Config:
        from_attributes = True

class ManagedMinionListResponse(BaseModel):
    minions: List[ManagedMinionResponse]

router = APIRouter(
    prefix="/minions",
    tags=["Admin - Managed Minions"],
    # TODO: Add dependencies=[Depends(require_admin_user)] for security
)

@router.get("", response_model=ManagedMinionListResponse)
async def list_minions(db: AsyncSession = Depends(get_db)):
    """
    List all managed minions
    """
    query = select(ManagedMinion).order_by(ManagedMinion.minion_key)
    result = await db.execute(query)
    minions = result.scalars().all()
    
    return ManagedMinionListResponse(minions=minions)

@router.get("/{minion_key}", response_model=ManagedMinionResponse)
async def get_minion(minion_key: str, db: AsyncSession = Depends(get_db)):
    """
    Get a specific minion by key
    """
    minion = await db.get(ManagedMinion, minion_key)
    if not minion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minion not found")
    
    return minion

@router.put("/{minion_key}/status", response_model=ManagedMinionResponse)
async def update_minion_status(
    minion_key: str, 
    status_update: ManagedMinionUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Update the activation status of a minion
    """
    minion = await db.get(ManagedMinion, minion_key)
    if not minion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minion not found")
    
    # Update the status
    minion.is_active = status_update.is_active
    
    await db.commit()
    await db.refresh(minion)
    
    # Log the change
    logger.info(f"Updated minion {minion_key} activation status to {status_update.is_active}")
    
    return minion 