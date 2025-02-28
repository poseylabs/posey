from typing import List, Union
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import logger, settings
import asyncio

async def get_embeddings(texts: Union[str, List[str]], model_name: str = None) -> List[List[float]]:
    """Get embeddings for text using specified model"""
    try:
        model_name = model_name or settings.EMBEDDING_MODEL
        # Initialize LangChain's HuggingFaceEmbeddings instance using the provided model name.
        embedding_instance = HuggingFaceEmbeddings(model_name=model_name)
        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]
        # Wrap the synchronous call to embed_documents in asyncio.to_thread for async compatibility.
        embeddings = await asyncio.to_thread(embedding_instance.embed_documents, texts)
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise
