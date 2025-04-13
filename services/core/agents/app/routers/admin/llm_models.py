from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime

from app.db import get_db
from app.db.models import LLMProvider, LLMModel, MinionLLMConfig
from pydantic import BaseModel, Field

# Import needed schemas from providers router if necessary, or redefine
# For simplicity here, let's assume needed types are available or redefine minimally
class LLMProviderResponse(BaseModel): # Minimal definition for linking
    id: UUID
    name: str
    model_config = { "from_attributes": True }

# Schemas
class LLMModelBase(BaseModel):
    name: str
    model_id: str
    provider_id: UUID
    context_window: int
    max_tokens: Optional[int] = None
    supports_embeddings: bool = False
    embedding_dimensions: Optional[int] = None
    cost_per_token: Optional[float] = None
    is_active: bool = True
    capabilities: List[str] = []
    config: Dict[str, Any] = {}

class LLMModelCreate(LLMModelBase):
    id: Optional[UUID] = None

class LLMModelUpdate(BaseModel):
    name: Optional[str] = None
    model_id: Optional[str] = None
    provider_id: Optional[UUID] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    supports_embeddings: Optional[bool] = None
    embedding_dimensions: Optional[int] = None
    cost_per_token: Optional[float] = None
    is_active: Optional[bool] = None
    capabilities: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

class LLMModelResponse(LLMModelBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    provider: Optional[LLMProviderResponse] = None # Include provider details

    model_config = {
        "from_attributes": True,
    }

class LLMModelListResponse(BaseModel):
    models: List[LLMModelResponse]


router = APIRouter(
    prefix="/llm-models",
    tags=["Admin - LLM Models"],
    # TODO: Add dependencies=[Depends(require_admin_user)] for security
)

@router.get("", response_model=LLMModelListResponse)
async def list_llm_models(db: AsyncSession = Depends(get_db)) -> LLMModelListResponse:
    result = await db.execute(
        select(LLMModel)
        .options(selectinload(LLMModel.provider))
        .order_by(LLMModel.provider_id, LLMModel.name)
    )
    models = result.scalars().all()
    return LLMModelListResponse(models=models)

@router.post("", response_model=LLMModelResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_model(model_data: LLMModelCreate, db: AsyncSession = Depends(get_db)):
    provider = await db.get(LLMProvider, model_data.provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider with ID {model_data.provider_id} not found")
    existing = await db.execute(
        select(LLMModel).where(
            LLMModel.provider_id == model_data.provider_id,
            LLMModel.model_id == model_data.model_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Model with model_id \"{model_data.model_id}\" already exists for provider {provider.name}.'
        )
    new_model = LLMModel(
        id=model_data.id or uuid.uuid4(),
        **model_data.model_dump(exclude={'id'} if not model_data.id else {})
    )
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    await db.refresh(new_model, attribute_names=['provider'])
    return new_model

@router.get("/{model_id}", response_model=LLMModelResponse)
async def get_llm_model(model_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LLMModel)
        .options(selectinload(LLMModel.provider))
        .where(LLMModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model

@router.put("/{model_id}", response_model=LLMModelResponse)
async def update_llm_model(model_id: UUID, model_update: LLMModelUpdate, db: AsyncSession = Depends(get_db)):
    model = await db.get(LLMModel, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    update_data = model_update.model_dump(exclude_unset=True)
    if "provider_id" in update_data and update_data["provider_id"] != model.provider_id:
        new_provider = await db.get(LLMProvider, update_data["provider_id"])
        if not new_provider:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider with ID {update_data['provider_id']} not found")
    check_conflict = False
    current_provider_id = model.provider_id
    current_model_id_api = model.model_id
    if "provider_id" in update_data and update_data["provider_id"] != current_provider_id:
        check_conflict = True
        current_provider_id = update_data["provider_id"]
    if "model_id" in update_data and update_data["model_id"] != current_model_id_api:
        check_conflict = True
        current_model_id_api = update_data["model_id"]
    if check_conflict:
        existing = await db.execute(
            select(LLMModel).where(
                LLMModel.provider_id == current_provider_id,
                LLMModel.model_id == current_model_id_api,
                LLMModel.id != model_id
            )
        )
        if existing.scalar_one_or_none():
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Another model with model_id \"{current_model_id_api}\" already exists for the target provider.'
            )
    for key, value in update_data.items():
        setattr(model, key, value)
    await db.commit()
    await db.refresh(model)
    await db.refresh(model, attribute_names=['provider'])
    return model

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_model(model_id: UUID, db: AsyncSession = Depends(get_db)):
    model = await db.get(LLMModel, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    config_dependency = await db.execute(
        select(MinionLLMConfig.id).where(MinionLLMConfig.llm_model_id == model_id).limit(1)
    )
    if config_dependency.scalar_one_or_none():
       raise HTTPException(
           status_code=status.HTTP_409_CONFLICT,
           detail="Cannot delete model as it is being used by existing Minion LLM configurations."
       )
    await db.delete(model)
    await db.commit()
    return None 