from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.utils.embeddings import get_embeddings
from app.middleware.response import standardize_response
from app.config import logger

router = APIRouter(
    prefix="/embeddings",
    tags=["embeddings"]
)

class EmbeddingDownloadRequest(BaseModel):
    models: Optional[List[str]] = None

class EmbeddingResponse(BaseModel):
    available_models: List[str]
    download_results: Optional[dict] = None

@router.get("/download/defaults", response_model=EmbeddingResponse)
@standardize_response
async def download_embeddings():
    """
    Download default embedding models to cache directory
    """
    try:
        # Download requested models
        results = await get_embeddings(["all-MiniLM-L6-v2"])  # Use a sensible default
        
        # Get updated list of available models
        available = ["all-MiniLM-L6-v2"]  # List available models
        
        return EmbeddingResponse(
            available_models=available,
            download_results=results
        )
        
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download/", response_model=EmbeddingResponse)
@standardize_response
async def download_embeddings(request: EmbeddingDownloadRequest):
    """
    Download specified embedding models to cache directory
    """
    try:
        # Download requested models
        results = await get_embeddings(request.models)
        
        # Get updated list of available models
        available = get_embeddings(request.models)
        
        return EmbeddingResponse(
            available_models=available,
            download_results=results
        )
        
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=EmbeddingResponse)
@standardize_response
async def list_available_embeddings():
    """
    List all available embedding models in cache directory
    """
    try:
        available = get_embeddings(DEFAULT_EMBEDDING_MODELS)
        return EmbeddingResponse(available_models=available)
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
