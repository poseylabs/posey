from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime

from app.db import get_db
from app.db.models import LLMProvider, LLMModel
from pydantic import BaseModel

# Pydantic Schemas
class LLMProviderBase(BaseModel):
    name: str
    slug: str
    api_base_url: Optional[str] = None
    api_key_secret_name: Optional[str] = None

class LLMProviderCreate(LLMProviderBase):
    pass

class LLMProviderUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    api_base_url: Optional[str] = None
    api_key_secret_name: Optional[str] = None
    is_active: Optional[bool] = None

class LLMProviderResponse(LLMProviderBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

class LLMProviderListResponse(BaseModel):
    providers: List[LLMProviderResponse]

router = APIRouter(
    prefix="/llm-providers",
    tags=["Admin - LLM Providers"],
    # TODO: Add dependencies=[Depends(require_admin_user)] for security
)

@router.get("", response_model=LLMProviderListResponse)
async def list_llm_providers(db: AsyncSession = Depends(get_db)) -> LLMProviderListResponse:
    # Endpoint path is now relative to the router prefix
    result = await db.execute(select(LLMProvider).order_by(LLMProvider.name))
    providers = result.scalars().all()
    return LLMProviderListResponse(providers=providers)

@router.post("", response_model=LLMProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_provider(provider_data: LLMProviderCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(LLMProvider).where(LLMProvider.slug == provider_data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider with slug '{provider_data.slug}' already exists."
        )
    new_provider = LLMProvider(
        id=uuid.uuid4(),
        **provider_data.model_dump()
    )
    db.add(new_provider)
    await db.commit()
    await db.refresh(new_provider)
    return new_provider

@router.get("/{provider_id}", response_model=LLMProviderResponse)
async def get_llm_provider(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return provider

@router.put("/{provider_id}", response_model=LLMProviderResponse)
async def update_llm_provider(provider_id: UUID, provider_update: LLMProviderUpdate, db: AsyncSession = Depends(get_db)):
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    update_data = provider_update.model_dump(exclude_unset=True)
    if "slug" in update_data and update_data["slug"] != provider.slug:
        existing = await db.execute(select(LLMProvider).where(LLMProvider.slug == update_data["slug"]))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Provider with slug '{update_data['slug']}' already exists."
            )
    for key, value in update_data.items():
        setattr(provider, key, value)
    await db.commit()
    await db.refresh(provider)
    return provider

@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_provider(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    model_dependency = await db.execute(select(LLMModel.id).where(LLMModel.provider_id == provider_id).limit(1))
    if model_dependency.scalar_one_or_none():
       raise HTTPException(
           status_code=status.HTTP_409_CONFLICT,
           detail="Cannot delete provider as it is being used by existing LLM models."
       )
    await db.delete(provider)
    await db.commit()
    return None 