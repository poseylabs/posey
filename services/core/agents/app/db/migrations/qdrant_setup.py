from qdrant_client import AsyncQdrantClient
from app.config import logger
from app.config.settings import settings
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
async def setup_qdrant(embedding_size: int = 1024):
    """Setup Qdrant collections and indexes"""
    
    url = settings.QDRANT_FULL_URL
    logger.info(f"Setting up Qdrant with URL: {url}")

    client = AsyncQdrantClient(url=url)
    logger.info(f"Qdrant client created")
    
    try:
        # First check if collection exists
        collections = await client.get_collections()
        collection_exists = any(c.name == "agent_memories" for c in collections.collections)
        
        if not collection_exists:
            # Create collection if it doesn't exist
            await client.create_collection(
                collection_name="agent_memories",
                vectors_config=models.VectorParams(
                    size=embedding_size,  # Voyage AI embedding size
                    distance=models.Distance.COSINE
                ),
                on_disk_payload=True  # Store payload on disk for larger datasets
            )
            logger.info("Created agent_memories collection")
        else:
            logger.info("agent_memories collection already exists")

        # Create payload indexes
        index_fields = [
            ("timestamp", models.PayloadSchemaType.DATETIME),
            ("categories", models.PayloadSchemaType.KEYWORD),
            ("user_id", models.PayloadSchemaType.KEYWORD),
            ("memory_type", models.PayloadSchemaType.KEYWORD),
            ("temporal_context", models.PayloadSchemaType.DATETIME),
            ("related_memories", models.PayloadSchemaType.KEYWORD)
        ]

        for field_name, field_type in index_fields:
            try:
                await client.create_payload_index(
                    collection_name="agent_memories",
                    field_name=field_name,
                    field_schema=field_type
                )
                logger.info(f"Created/verified index for {field_name}")
            except UnexpectedResponse as e:
                if "already exists" in str(e):
                    logger.info(f"Index for {field_name} already exists")
                else:
                    raise

        logger.info("Qdrant setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up Qdrant: {e}")
        raise

async def reset_qdrant(embedding_size: int = 1024):
    """Delete and recreate Qdrant collections with new dimensions"""
    client = AsyncQdrantClient(url=settings.QDRANT_FULL_URL)

    try:
        # Delete existing collection if it exists
        try:
            await client.delete_collection(
                collection_name="agent_memories"
            )
            logger.info("Deleted existing agent_memories collection")
        except Exception as e:
            logger.info(f"Collection might not exist, continuing: {e}")
        
        # Create collection with new dimensions
        await client.create_collection(
            collection_name="agent_memories",
            vectors_config={
                "size": embedding_size,  # Voyage AI embedding size
                "distance": "Cosine"
            }
        )
        
        # Create payload indexes
        await client.create_payload_index(
            collection_name="agent_memories",
            field_name="timestamp",
            field_schema="datetime"
        )
        
        await client.create_payload_index(
            collection_name="agent_memories",
            field_name="category",
            field_schema="keyword"
        )
        
        logger.info(f"Successfully recreated agent_memories collection with {embedding_size} dimensions")
        
    except Exception as e:
        logger.error(f"Error resetting Qdrant collection: {e}")
        raise

async def setup_memory_collection(client: AsyncQdrantClient):
    """Setup or update the memory collection with proper configuration for atomic memories"""
    try:
        # Create collection with updated schema
        await client.create_collection(
            collection_name="agent_memories",
            vectors_config=models.VectorParams(
                size=1024,  # Assuming BAAI/bge-large-en-v1.5 embedding size
                distance=models.Distance.COSINE
            ),
            on_disk_payload=True  # Store payload on disk for larger datasets
        )

        # Configure payload indexes for efficient filtering
        await client.create_payload_index(
            collection_name="agent_memories",
            field_name="related_memories",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        # Add temporal context index
        await client.create_payload_index(
            collection_name="agent_memories",
            field_name="temporal_context",
            field_schema=models.PayloadSchemaType.DATETIME,
        )

        # Add category index
        await client.create_payload_index(
            collection_name="agent_memories",
            field_name="categories",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        # Add memory type index
        await client.create_payload_index(
            collection_name="agent_memories",
            field_name="memory_type",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    except Exception as e:
        if "already exists" not in str(e):
            logger.error(f"Error setting up memory collection: {e}")
            raise e
