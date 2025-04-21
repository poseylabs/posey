from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime
import os # For environment variables
import httpx # For making external API calls

from app.db import get_db
from app.db.models import LLMProvider, LLMModel, MinionLLMConfig
from pydantic import BaseModel, Field

# Import needed schemas from providers router if necessary, or redefine
# For simplicity here, let's assume needed types are available or redefine minimally
class LLMProviderResponse(BaseModel): # Minimal definition for linking
    id: UUID
    name: str
    slug: str # Added slug for sync logic
    api_base_url: Optional[str] = None
    api_key_secret_name: Optional[str] = None
    model_config = { "from_attributes": True }

# Schemas
class LLMModelBase(BaseModel):
    name: str
    model_id: str
    provider_id: UUID
    context_window: int = 0 # Default to 0 for newly synced
    max_tokens: Optional[int] = None
    cost_per_token: Optional[float] = None
    is_active: bool = False # Default to False for newly synced
    capabilities: List[str] = []
    supports_embeddings: bool = False
    embedding_dimensions: Optional[int] = None
    supports_thinking: bool = False # Added
    supports_tool_use: bool = False # Added
    supports_computer_use: bool = False # Added
    config: Dict[str, Any] = {}

class LLMModelCreate(LLMModelBase):
    id: Optional[UUID] = None

class LLMModelUpdate(BaseModel):
    name: Optional[str] = None
    model_id: Optional[str] = None # Generally shouldn't be updated post-creation
    provider_id: Optional[UUID] = None # Generally shouldn't be updated post-creation
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    cost_per_token: Optional[float] = None
    is_active: Optional[bool] = None
    capabilities: Optional[List[str]] = None
    supports_embeddings: Optional[bool] = None
    embedding_dimensions: Optional[int] = None
    supports_thinking: Optional[bool] = None # Added
    supports_tool_use: Optional[bool] = None # Added
    supports_computer_use: Optional[bool] = None # Added
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

class SyncResponse(BaseModel):
    provider_name: str
    status: str
    new_models_added: int
    message: Optional[str] = None

# Helper Functions
async def _add_anthropic_model_if_not_exists(db: AsyncSession, provider_id: UUID, anthropic_model_data: dict):
    # Renamed original helper to be specific
    anthropic_model_id = anthropic_model_data.get('id')
    anthropic_display_name = anthropic_model_data.get('display_name')

    if not anthropic_model_id or not anthropic_display_name:
        print(f"Skipping Anthropic model due to missing data: {anthropic_model_data}") # Added print
        return False # Skip if essential data is missing

    # Check if model already exists for this provider
    existing = await db.execute(
        select(LLMModel.id).where(
            LLMModel.provider_id == provider_id,
            LLMModel.model_id == anthropic_model_id
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        return False # Already exists

    # Create new model (inactive by default)
    print(f"Adding new Anthropic model: {anthropic_display_name} ({anthropic_model_id})") # Added print
    new_model_data = LLMModelCreate(
        provider_id=provider_id,
        name=anthropic_display_name,
        model_id=anthropic_model_id,
        # Set other fields to defaults or None as appropriate
        context_window=0, # Placeholder - Anthropic API doesn't provide this here
        max_tokens=None, # Placeholder - Anthropic API doesn't provide this here
        cost_per_token=None,
        is_active=False,
        capabilities=[], # Placeholder
        supports_embeddings=False,
        embedding_dimensions=None,
        supports_thinking=False,
        supports_tool_use=False,
        supports_computer_use=False,
        config={}
    )
    new_model = LLMModel(
        id=uuid.uuid4(),
        **new_model_data.model_dump(exclude={'id'})
    )
    db.add(new_model)
    return True # Indicates a new model was added

async def _add_google_model_if_not_exists(db: AsyncSession, provider_id: UUID, google_model_data: dict):
    # Helper specific to Google Gemini API response structure
    google_model_path = google_model_data.get('name') # e.g., "models/gemini-1.5-pro-latest"
    google_display_name = google_model_data.get('displayName')
    google_context_window = google_model_data.get('inputTokenLimit')
    google_max_tokens = google_model_data.get('outputTokenLimit')
    google_supported_methods = google_model_data.get('supportedGenerationMethods', [])

    if not google_model_path or not google_display_name:
        print(f"Skipping Google model due to missing data: {google_model_data}")
        return False
    
    # Extract model_id from the path name
    google_model_id = google_model_path.split('/')[-1] if '/' in google_model_path else google_model_path

    # Check if model already exists for this provider
    existing = await db.execute(
        select(LLMModel.id).where(
            LLMModel.provider_id == provider_id,
            LLMModel.model_id == google_model_id
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        return False # Already exists

    # Basic capability check (can refine)
    capabilities = []
    if "generateContent" in google_supported_methods:
        capabilities.append("text_generation")
    if "embedContent" in google_supported_methods:
        capabilities.append("embeddings")
        # Attempt to get embedding dimension if available (may not be standard)
        embedding_dimensions = google_model_data.get('embeddingDimensions') 
    else:
        embedding_dimensions = None
        
    # Placeholder for specific Gemini feature flags
    supports_thinking = "thinking" in google_model_id # Crude check, needs better logic
    supports_tool_use = "functionCalling" in google_supported_methods or "tool" in google_model_id # Crude check

    print(f"Adding new Google model: {google_display_name} ({google_model_id})")
    new_model_data = LLMModelCreate(
        provider_id=provider_id,
        name=google_display_name,
        model_id=google_model_id,
        context_window=google_context_window or 0,
        max_tokens=google_max_tokens,
        cost_per_token=None, # Google API doesn't provide cost here
        is_active=False,
        capabilities=capabilities,
        supports_embeddings="embeddings" in capabilities,
        embedding_dimensions=embedding_dimensions,
        supports_thinking=supports_thinking,
        supports_tool_use=supports_tool_use,
        supports_computer_use=False, # Assume false unless API indicates otherwise
        config={}
    )
    new_model = LLMModel(
        id=uuid.uuid4(),
        **new_model_data.model_dump(exclude={'id'})
    )
    db.add(new_model)
    return True

async def _add_openai_model_if_not_exists(db: AsyncSession, provider_id: UUID, openai_model_data: dict):
    # Helper specific to OpenAI API response structure
    openai_model_id = openai_model_data.get('id') # e.g., "gpt-4o"
    # OpenAI list endpoint doesn't provide a separate display name, use the id
    openai_display_name = openai_model_id 

    if not openai_model_id:
        print(f"Skipping OpenAI model due to missing id: {openai_model_data}")
        return False

    # Check if model already exists for this provider
    existing = await db.execute(
        select(LLMModel.id).where(
            LLMModel.provider_id == provider_id,
            LLMModel.model_id == openai_model_id
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        return False # Already exists

    # Basic capability check (can refine - OpenAI list doesn't give capabilities easily)
    capabilities = ["text_generation"] # Assume basic text gen
    supports_embeddings = "embedding" in openai_model_id.lower()
    supports_tool_use = "tool" in openai_model_id.lower() or "function" in openai_model_id.lower()

    print(f"Adding new OpenAI model: {openai_display_name} ({openai_model_id})")
    new_model_data = LLMModelCreate(
        provider_id=provider_id,
        name=openai_display_name, # Use model_id as name
        model_id=openai_model_id,
        context_window=0, # Placeholder
        max_tokens=None, # Placeholder
        cost_per_token=None, # Placeholder
        is_active=False,
        capabilities=capabilities,
        supports_embeddings=supports_embeddings,
        embedding_dimensions=None, # Placeholder
        supports_thinking=False, # Assume false unless known otherwise
        supports_tool_use=supports_tool_use,
        supports_computer_use=False, # Assume false
        config={}
    )
    new_model = LLMModel(
        id=uuid.uuid4(),
        **new_model_data.model_dump(exclude={'id'})
    )
    db.add(new_model)
    return True

router = APIRouter(
    prefix="/llm-models",
    tags=["Admin - LLM Models"],
    # TODO: Add dependencies=[Depends(require_admin_user)] for security
)

@router.get("", response_model=LLMModelListResponse)
async def list_llm_models(
    provider_id: Optional[UUID] = None, # Add optional provider_id query parameter
    db: AsyncSession = Depends(get_db)
) -> LLMModelListResponse:
    stmt = (
        select(LLMModel)
        .options(selectinload(LLMModel.provider))
        .order_by(LLMModel.provider_id, LLMModel.name)
    )
    # Apply filter if provider_id is provided
    if provider_id:
        stmt = stmt.where(LLMModel.provider_id == provider_id)

    result = await db.execute(stmt)
    models = result.scalars().all()
    return LLMModelListResponse(models=models)

@router.post("/sync", response_model=SyncResponse)
async def sync_models_from_provider(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    # 1. Get Provider Info and required attributes early
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    
    # Access needed attributes before potential session closure
    provider_name_val = provider.name
    provider_slug_val = provider.slug
    api_key_name_val = provider.api_key_secret_name
    api_base_url_val = provider.api_base_url

    new_models_added = 0
    error_message = None
    status_code = "success"

    # 2. Provider-Specific Logic
    if provider_slug_val == "anthropic": # Use the fetched value
        # 3. Get API Key
        if not api_key_name_val:
            error_message = "Provider requires an API key secret name configured."
            status_code = "error"
        else:
            api_key = os.environ.get(api_key_name_val)
            if not api_key:
                error_message = f"API key environment variable '{api_key_name_val}' not set."
                status_code = "error"
            else:
                # 4. Call Anthropic API
                anthropic_api_url = api_base_url_val or "https://api.anthropic.com"
                # Ensure the URL doesn't already contain /v1/models
                if not anthropic_api_url.endswith("/v1/models"):
                    if anthropic_api_url.endswith("/"):
                         anthropic_api_url = f"{anthropic_api_url[:-1]}v1/models"
                    else:
                         anthropic_api_url = f"{anthropic_api_url}/v1/models"

                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01", # Or a more recent version if needed
                    "Content-Type": "application/json"
                }
                try:
                    async with httpx.AsyncClient() as client:
                        print(f"Requesting Anthropic models from: {anthropic_api_url}") # Debug print
                        response = await client.get(anthropic_api_url, headers=headers)
                        response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
                        anthropic_models_data = response.json()

                    # 5. Process Response
                    if isinstance(anthropic_models_data.get('data'), list):
                        for model_data in anthropic_models_data['data']:
                            if await _add_anthropic_model_if_not_exists(db, provider.id, model_data):
                                new_models_added += 1
                        await db.commit() # Commit after processing all models for this provider
                    else:
                        error_message = "Unexpected response format from Anthropic API."
                        status_code = "error"
                        await db.rollback()
                except httpx.RequestError as exc:
                    error_message = f"Error requesting Anthropic API: {exc}"
                    status_code = "error"
                    await db.rollback()
                except httpx.HTTPStatusError as exc:
                    error_message = f"Anthropic API error: {exc.response.status_code} - {exc.response.text}"
                    status_code = "error"
                    await db.rollback()
                except Exception as exc:
                    error_message = f"Sync error (Anthropic): {exc}"
                    status_code = "error"
                    await db.rollback()

    elif provider_slug_val == "google": # Check for Google slug
        if not api_key_name_val:
            error_message = "Provider requires an API key secret name configured."
            status_code = "error"
        else:
            api_key = os.environ.get(api_key_name_val)
            if not api_key:
                error_message = f"API key environment variable '{api_key_name_val}' not set."
                status_code = "error"
            else:
                 # Use default Gemini API endpoint if base_url not set
                google_api_url = api_base_url_val or "https://generativelanguage.googleapis.com/v1beta/models"
                
                try:
                    async with httpx.AsyncClient() as client:
                        print(f"Requesting Google models from: {google_api_url}") # Debug print
                        response = await client.get(google_api_url, params={"key": api_key})
                        response.raise_for_status()
                        google_models_data = response.json()

                    if isinstance(google_models_data.get('models'), list):
                        for model_data in google_models_data['models']:
                             if await _add_google_model_if_not_exists(db, provider.id, model_data):
                                new_models_added += 1
                        await db.commit() 
                    else:
                        error_message = "Unexpected response format from Google API."
                        status_code = "error"
                        await db.rollback()
                except httpx.RequestError as exc:
                    error_message = f"Error requesting Google API: {exc}"
                    status_code = "error"
                    await db.rollback()
                except httpx.HTTPStatusError as exc:
                    error_message = f"Google API error: {exc.response.status_code} - {exc.response.text}"
                    status_code = "error"
                    await db.rollback()
                except Exception as exc:
                    error_message = f"Sync error (Google): {exc}"
                    status_code = "error"
                    await db.rollback()

    elif provider_slug_val == "openai": # Handle OpenAI
        if not api_key_name_val:
            error_message = "Provider requires an API key secret name configured."
            status_code = "error"
        else:
            api_key = os.environ.get(api_key_name_val)
            if not api_key:
                error_message = f"API key environment variable '{api_key_name_val}' not set."
                status_code = "error"
            else:
                openai_api_url = api_base_url_val or "https://api.openai.com/v1/models"
                # Ensure base URL ends correctly if custom
                if api_base_url_val and not openai_api_url.endswith("/v1/models"):
                     if openai_api_url.endswith("/"):
                         openai_api_url = f"{openai_api_url[:-1]}/v1/models"
                     else:
                         openai_api_url = f"{openai_api_url}/v1/models"
                
                headers = {
                    "Authorization": f"Bearer {api_key}"
                }
                try:
                    async with httpx.AsyncClient() as client:
                        print(f"Requesting OpenAI models from: {openai_api_url}")
                        response = await client.get(openai_api_url, headers=headers)
                        response.raise_for_status()
                        openai_models_data = response.json()

                    if isinstance(openai_models_data.get('data'), list):
                        for model_data in openai_models_data['data']:
                            if await _add_openai_model_if_not_exists(db, provider.id, model_data):
                                new_models_added += 1
                        await db.commit()
                    else:
                        error_message = "Unexpected response format from OpenAI API."
                        status_code = "error"
                        await db.rollback()
                except httpx.RequestError as exc:
                    error_message = f"Error requesting OpenAI API: {exc}"
                    status_code = "error"
                    await db.rollback()
                except httpx.HTTPStatusError as exc:
                    error_message = f"OpenAI API error: {exc.response.status_code} - {exc.response.text}"
                    status_code = "error"
                    await db.rollback()
                except Exception as exc:
                    error_message = f"Sync error (OpenAI): {exc}"
                    status_code = "error"
                    await db.rollback()

    else:
        status_code = "skipped"
        error_message = f"Sync not implemented for provider type '{provider_slug_val}'."

    # 6. Return Result
    return SyncResponse(
        provider_name=provider_name_val,
        status=status_code,
        new_models_added=new_models_added,
        message=error_message or f"Successfully synced models. {new_models_added} new models added."
    )

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
            detail=f'Model with model_id "{model_data.model_id}" already exists for provider {provider.name}.'
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
    model = await db.get(LLMModel, model_id, options=[selectinload(LLMModel.provider)]) # Eager load provider
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    update_data = model_update.model_dump(exclude_unset=True)

    # Check for potential provider change and related conflicts
    new_provider_id = update_data.get("provider_id", model.provider_id)
    new_model_id_api = update_data.get("model_id", model.model_id)

    if new_provider_id != model.provider_id or new_model_id_api != model.model_id:
        if new_provider_id != model.provider_id:
             new_provider = await db.get(LLMProvider, new_provider_id)
             if not new_provider:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider with ID {new_provider_id} not found")

        # Check if the target combination already exists (excluding the current model)
        existing = await db.execute(
            select(LLMModel.id).where(
                LLMModel.provider_id == new_provider_id,
                LLMModel.model_id == new_model_id_api,
                LLMModel.id != model_id
            ).limit(1)
        )
        if existing.scalar_one_or_none():
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Another model with model_id "{new_model_id_api}" already exists for the target provider.'
            )

    # Apply updates
    for key, value in update_data.items():
        setattr(model, key, value)

    await db.commit()
    await db.refresh(model)
     # Ensure provider is loaded after refresh if it was changed
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