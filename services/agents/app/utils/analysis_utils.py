import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS
from app.config import db, logger
from qdrant_client.http import models
from app.utils.embeddings import get_embeddings
from app.config import logger
from app.config.models import DEFAULT_MODEL

from app.schemas.memory import MemoryResponse
import math

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Add at top of file
CATEGORY_MAPPINGS = {
    'person': ['spouse', 'family', 'personal', 'relationship'],
    'relationship': ['spouse', 'family', 'personal'],
    'interaction': ['personal', 'experience', 'family'],
    'personal': ['spouse', 'family', 'experience'],
    'family': ['spouse', 'personal', 'relationship'],
}

logger = logging.getLogger(__name__)


class MemoryEntry(BaseModel):
    content: str
    score: float
    timestamp: datetime
    categories: List[str] = ["general"]
    context_type: Optional[str] = "content_analysis"
    user_id: str
    is_shared: bool = True
    importance_score: Optional[float] = None
    relevance_score: Optional[float] = None
    memory_id: UUID = Field(default_factory=uuid4)
    memory_type: Optional[str] = "general"
    id: Optional[str] = None

    def __init__(self, **data):
        if 'memory_id' not in data:
            data['memory_id'] = uuid4()
        if 'id' not in data and 'memory_id' in data:
            data['id'] = str(data['memory_id'])
        super().__init__(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "content": self.content,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "categories": self.categories,
            "context_type": self.context_type,
            "user_id": self.user_id,
            "is_shared": self.is_shared,
            "importance_score": self.importance_score or self.score,
            "relevance_score": self.relevance_score or self.score,
            "memory_id": str(self.memory_id),
            "memory_type": self.memory_type,
            "id": self.id or str(self.memory_id)
        }

    @classmethod
    def from_search_result(cls, result: Any) -> "MemoryEntry":
        """Create MemoryEntry from a search result"""
        try:
            return cls(
                content=result.payload.get("content", ""),
                score=float(result.score),
                timestamp=datetime.fromisoformat(result.payload.get("timestamp")),
                categories=result.payload.get("categories", ["general"]),
                user_id=result.payload.get("user_id"),
                context_type=result.payload.get("context_type", "content_analysis"),
                memory_type=result.payload.get("memory_type", "general"),
                is_shared=result.payload.get("is_shared", True),
                importance_score=result.payload.get("importance_score"),
                relevance_score=float(result.score),
                id=result.payload.get("id"),
                memory_id=UUID(result.payload.get("id")) if result.payload.get("id") else uuid4()
            )
        except Exception as e:
            logger.error(f"Error creating MemoryEntry from search result: {e}")
            logger.error(f"Result payload: {result.payload}")
            raise

async def embed_text(text: str, model_name: str = None) -> List[float]:
    """
    Helper function that returns an embedding for a single text.
    Uses the LangChain get_embeddings function.
    """
    embeddings = await get_embeddings(text, model_name)
    return embeddings[0]

async def get_enhanced_context(
    query: str,
    user_id: str,
    limit: int = 5,
    min_relevance: float = 0.5,
    include_shared: bool = True,
    context_type: Optional[str] = "general",
    time_range: Optional[Dict[str, datetime]] = None
) -> List[MemoryEntry]:
    """Get enhanced context with relevance scoring."""
    logger.info(f"Getting enhanced context for query: {query}")
    try:
        # Build search filter conditions
        filter_conditions = [
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id)
            )
        ]

        # Add sharing filter if not including shared memories
        if not include_shared:
            filter_conditions.append(
                models.FieldCondition(
                    key="is_shared",
                    match=models.MatchValue(value=False)
                )
            )

        # Add context type filter if specified
        if context_type and context_type != "general":
            filter_conditions.append(
                models.FieldCondition(
                    key="context_type",
                    match=models.MatchValue(value=context_type)
                )
            )

        # Add time range filter if specified
        if time_range:
            start = time_range.get('start')
            end = time_range.get('end', datetime.now())
            if start:
                filter_conditions.append(
                    models.FieldCondition(
                        key="timestamp",
                        range=models.Range(
                            gte=start.isoformat(),
                            lte=end.isoformat()
                        )
                    )
                )

        # Get vector embedding for query
        query_vector = await embed_text(query)
        
        if not query_vector:
            logger.error("Failed to generate query embedding")
            return []

        search_filter = models.Filter(must=filter_conditions)
        
        # Perform search
        results = await db.qdrant_client.search(
            collection_name="agent_memories",
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit,
            score_threshold=min_relevance,
            with_payload=True
        )
        
        entries = []
        for result in results:
            try:
                entry = MemoryEntry(
                    content=result.payload.get("content", ""),
                    score=float(result.score),
                    timestamp=datetime.fromisoformat(result.payload.get("timestamp")),
                    categories=result.payload.get("categories", ["general"]),
                    user_id=result.payload.get("user_id"),
                    context_type=result.payload.get("memory_type", "general"),
                    is_shared=result.payload.get("is_shared", True),
                    importance_score=result.payload.get("importance_score"),
                    relevance_score=float(result.score)  # Use the search score as relevance
                )
                entries.append(entry)
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                logger.error(f"Result payload: {result.payload}")
                continue

        return entries

    except Exception as e:
        logger.error(f"Error in memory search (get_enhanced_context): {e}")
        logger.error("Stack trace:", exc_info=True)
        return []

async def handle_memory_operations(
    operation_type: str,
    content: str,
    metadata: Dict[str, Any],
    user_id: str
) -> Union[str, List[Dict[str, Any]]]:
    """Handle memory operations with proper access control"""
    try:
        if not user_id:
            raise ValueError("user_id is required for memory operations")
        if not metadata.get("agent_id"):
            raise ValueError("agent_id is required in metadata for memory operations")

        if operation_type == "store":
            # Convert single category to array if needed
            if "category" in metadata:
                metadata["categories"] = [metadata.pop("category")]
            elif "categories" not in metadata:
                metadata["categories"] = ["personal"]  # Default category

            # Generate embedding
            embedding = await embed_text(content)
            
            # Generate memory ID
            memory_id = str(uuid4())
            
            # Prepare payload with required IDs
            payload = {
                "id": memory_id,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "agent_id": metadata["agent_id"],
                **{k: v for k, v in metadata.items() if k not in ["user_id", "agent_id"]}
            }

            # Store in Qdrant
            await db.qdrant_client.upsert(
                collection_name="agent_memories",
                points=[
                    models.PointStruct(
                        id=memory_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            return memory_id

        elif operation_type in ['search', 'retrieve']:
            results = await perform_memory_search(content, metadata)
            return results
        
        else:
            raise ValueError(f"Unknown action: {operation_type}")
            
    except Exception as e:
        logger.error(f"Error in memory operations: {e}")
        logger.error("Stack trace:", exc_info=True)
        raise

def format_memory_response(result) -> MemoryResponse:
    """Format search result into MemoryResponse"""
    try:
        # Extract base importance score
        importance_score = result.payload.get('importance_score', 0.5)
        
        # Normalize the relevance score to ensure it's between 0 and 1
        relevance_score = min(1.0, result.score / 2)  # Divide by 2 since we're applying 1.5x boost
        
        # Calculate total importance (weighted average)
        total_importance = min(1.0, (importance_score * 0.6) + (relevance_score * 0.4))
        
        return MemoryResponse(
            id=UUID(result.id),
            content=result.payload.get('content', ''),
            metadata=result.payload.get('metadata', {}),
            agent_id=UUID(result.payload.get('agent_id')),
            user_id=result.payload.get('user_id', ''),
            context_type=result.payload.get('context_type', 'content_analysis'),
            relevance_score=relevance_score,  # Use normalized relevance score
            memory_recurrence=result.payload.get('memory_recurrence', 1),
            total_importance=total_importance,
            timestamp=datetime.fromisoformat(result.payload.get('timestamp')),
            tags=result.payload.get('tags', []),
            source_type=result.payload.get('source_type', 'system_event'),
            privacy_level=result.payload.get('privacy_level', 'shared'),
            retention_period=result.payload.get('retention_period', 30),
            importance_score=importance_score,
            categories=result.payload.get('categories', ['general']),
            is_shared=result.payload.get('is_shared', True),
            sharing_reason=result.payload.get('sharing_reason')
        )
    except Exception as e:
        logger.error(f"Error formatting memory response: {str(e)}")
        logger.error(f"Raw result: {result}")
        raise ValueError(f"Invalid memory result format: {str(e)}")


async def perform_memory_search(
    query: str,
    user_id: str,
    agent_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    limit: int = 5,
    min_relevance: float = 0.5,
    search_config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Search for memories with proper access control"""
    try:
        logger.info(f"Performing memory search for user_id={user_id}, agent_id={agent_id}")
        logger.info(f"Search parameters: query='{query}', limit={limit}, min_relevance={min_relevance}")
        logger.debug(f"Metadata for search: {metadata}")
        
        # Create filter for user_id and agent_id
        must_conditions = [
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id)
            ),
            models.FieldCondition(
                key="agent_id",
                match=models.MatchValue(value=agent_id)
            )
        ]

        # Add any additional filters from metadata
        if metadata and metadata.get("categories"):
            logger.info(f"Adding category filter: {metadata['categories']}")
            must_conditions.append(
                models.FieldCondition(
                    key="categories",
                    match=models.MatchAny(any=metadata["categories"])
                )
            )
            
        # Add memory type filter if specified
        if metadata and metadata.get("memory_type"):
            logger.info(f"Adding memory_type filter: {metadata['memory_type']}")
            must_conditions.append(
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchValue(value=metadata["memory_type"])
                )
            )
            
        # Add context type filter if specified
        if metadata and metadata.get("context_type"):
            logger.info(f"Adding context_type filter: {metadata['context_type']}")
            must_conditions.append(
                models.FieldCondition(
                    key="context_type",
                    match=models.MatchValue(value=metadata["context_type"])
                )
            )

        logger.info(f"Constructed {len(must_conditions)} filter conditions for memory search")
        
        # Check if collection exists before searching
        try:
            collections = await db.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            logger.info(f"Available Qdrant collections: {collection_names}")
            
            if "agent_memories" not in collection_names:
                logger.warning("The 'agent_memories' collection does not exist in Qdrant")
                return []
                
            # Get collection info to check if it has any points
            collection_info = await db.qdrant_client.get_collection("agent_memories")
            logger.info(f"Collection 'agent_memories' has {collection_info.vectors_count} vectors/points")
            
            if collection_info.vectors_count == 0:
                logger.warning("The 'agent_memories' collection exists but is empty")
                return []
        except Exception as e:
            logger.error(f"Error checking Qdrant collections: {e}")
            # Continue with search regardless of error checking collections

        # Perform search with filters
        logger.info(f"Executing Qdrant search on 'agent_memories' collection with {len(must_conditions)} filters")
        search_result = await db.qdrant_client.search(
            collection_name="agent_memories",
            query_vector=await embed_text(query),
            query_filter=models.Filter(
                must=must_conditions
            ),
            limit=limit,
            score_threshold=min_relevance
        )
        
        logger.info(f"Qdrant search returned {len(search_result)} results")
        if search_result:
            # Log a sample of the first result
            logger.debug(f"First result score: {search_result[0].score}, payload keys: {list(search_result[0].payload.keys())}")

        results = [
            {
                "content": point.payload.get("content"),
                "score": point.score,
                "metadata": {
                    "category": point.payload.get("category"),
                    "tags": point.payload.get("tags", []),
                    "timestamp": point.payload.get("timestamp"),
                    "importance": point.payload.get("importance")
                }
            }
            for point in search_result
        ]
        
        logger.info(f"Processed {len(results)} memory search results")
        return results

    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        logger.exception("Full traceback for memory search error:")
        raise

async def get_similar_memories(
    query_text: str,
    limit: int = 5,
    score_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Get similar memories using vector similarity search"""
    try:
        # Generate query embedding
        query_embedding = await embed_text(
            text=query_text,
            model=DEFAULT_MODEL,
            input_type="query"
        )
        
        # Search parameters
        search_params = models.SearchParams(
            hnsw_ef=128,
            exact=False
        )
        
        # Perform search
        results = await db.qdrant_client.search(
            collection_name="agent_memories",
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            search_params=search_params
        )
        
        return [
            {
                "id": UUID(point.id),
                "content": point.payload["content"],
                "metadata": point.payload["metadata"],
                "score": point.score,
                "timestamp": datetime.fromisoformat(point.payload["timestamp"])
            }
            for point in results
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving similar memories: {e}")
        return []

async def log_user_action(
    user_id: str,
    event_type: str,
    content: str,
    metadata: dict = None
) -> bool:
    """Store user-related events in the vector memory system."""
    try:
        # Verify Qdrant connection
        if not db.qdrant_client:
            logger.error("Qdrant client not initialized")
            return False

        # Generate a proper UUID for the log entry
        memory_id = str(uuid5(NAMESPACE_DNS, f"{user_id}_{int(datetime.utcnow().timestamp())}"))

        # Create the memory point
        memory_point = {
            "user_id": user_id,
            "event_type": event_type,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Generate vector embedding
        vector = await embed_text(content)
        if not vector:
            logger.error("Failed to generate embedding for memory storage")
            return False

        # Store in Qdrant
        point = models.PointStruct(
            id=memory_id,
            vector=vector,
            payload=memory_point
        )

        await db.qdrant_client.upsert(
            collection_name="user_actions",
            points=[point]
        )

        return True

    except Exception as e:
        logger.error(f"Failed to store user memory: {e}")
        return False

async def store_memory_vector(
    content: str,
    metadata: Dict[str, Any],
    collection_name: str = "agent_memories"
) -> str:
    """Store memory vector in Qdrant"""
    try:
        # Calculate expiry if applicable
        expiry_date = get_retention_expiry(
            retention_period=metadata.get("retention_period", 0),
            expiration_policy=metadata.get("expiration_policy", "never")
        )
        
        # Add expiry to metadata if set
        if expiry_date:
            metadata["expires_at"] = expiry_date.isoformat()
        
        # Generate embedding
        vector = await embed_text(content)
        
        # Normalize vector before storage
        vector_norm = np.linalg.norm(vector)
        if vector_norm > 0:
            vector = vector / vector_norm
        
        # Generate ID
        point_id = str(uuid4())
        
        # Store in Qdrant
        await db.qdrant_client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload={
                    "id": point_id,
                    **metadata,
                }
            )]
        )
        
        return point_id
        
    except Exception as e:
        logger.error(f"Error storing memory vector: {e}")
        raise

async def rebuild_vector_database():
    """Rebuild vector database with normalized vectors"""
    try:
        # Get all existing memories
        all_memories = await db.qdrant_client.scroll(
            collection_name="agent_memories",
            limit=10000  # Adjust based on your data size
        )
        
        # Delete collection
        await db.qdrant_client.delete_collection("agent_memories")
        
        # Recreate collection
        await db.qdrant_client.create_collection(
            collection_name="agent_memories",
            vectors_config=models.VectorParams(
                size=1536,  # Adjust based on your embedding size
                distance=models.Distance.COSINE
            )
        )
        
        # Reinsert memories with normalized vectors
        for memory in all_memories[0]:  # [0] contains points
            await store_memory_vector(
                content=memory.payload["content"],
                metadata=memory.payload
            )
            
        logger.info("Vector database rebuilt successfully")
        
    except Exception as e:
        logger.error(f"Error rebuilding vector database: {e}")
        raise

async def calculate_total_importance(
    base_score: float,
    recurrence_count: int,
    relevance_score: float
) -> float:
    """Calculate total importance score based on multiple factors"""
    # Base importance from LLM analysis (0-1)
    normalized_base = min(1.0, max(0.0, base_score))
    
    # Recurrence factor (starts at 1, increases with diminishing returns)
    recurrence_factor = 1 + (math.log(recurrence_count + 1) / math.log(10))
    
    # Relevance factor from vector similarity
    relevance_factor = min(1.0, max(0.0, relevance_score))
    
    # Combined score with weights
    total_score = (
        normalized_base * 0.4 +  # Base importance
        (recurrence_factor * 0.3) +  # Recurrence impact
        (relevance_factor * 0.3)  # Similarity impact
    )
    
    return min(1.0, total_score)  # Ensure final score is 0-1

async def check_memory_recurrence(
    content: str,
    user_id: str,
    threshold: float = 0.92
) -> Tuple[int, Optional[Dict[str, Any]]]:
    """Check how many times similar content has been stored"""
    try:
        query_vector = await embed_text(content)
        
        # Search for similar memories
        results = await db.qdrant_client.search(
            collection_name="agent_memories",
            query_vector=query_vector,
            limit=5,  # Get a few to check for variations
            score_threshold=threshold,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            )
        )
        
        if not results:
            return 0, None
            
        # Return count of similar memories and most similar one
        return len(results), results[0].payload
        
    except Exception as e:
        logger.error(f"Error checking memory recurrence: {e}")
        return 0, None

def calculate_final_importance(
    base_importance: float,
    recurrence_count: int,
    max_boost: float = 0.3
) -> float:
    """Calculate final importance score including recurrence"""
    # Log scale boost from recurrence (diminishing returns)
    recurrence_boost = min(max_boost, math.log(recurrence_count + 1) / math.log(10))
    
    # Combine base importance with recurrence boost
    final_score = min(1.0, base_importance + recurrence_boost)
    
    return final_score

def get_retention_expiry(retention_period: int, expiration_policy: str) -> Optional[datetime]:
    """
    Calculate expiry date based on retention period and policy
    Returns None for permanent retention
    """
    if retention_period <= 0 or expiration_policy == "never":
        return None
        
    if expiration_policy == "conditional":
        # Conditional expiry handled separately through periodic review
        return None

    # Calculate expiry date for finite retention periods
    return datetime.utcnow() + timedelta(days=retention_period)
