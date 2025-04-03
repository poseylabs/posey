from typing import Dict, Optional, List, Any
from app.config import logger
import json

def create_atomic_memory(content: str, entity: Optional[Dict] = None, 
                        categories: List[str] = ["personal"], 
                        tags: List[str] = [], 
                        importance: int = 7) -> Dict:
    """Helper to create properly formatted atomic memories"""
    # For image-related memories, store both prompt and description
    if "image_generation" in tags:
        memory = {
            "content": content,
            "categories": categories,
            "tags": tags,
            "importance": importance,
            "prompt": content,  # Store as both for backward compatibility
            "description": content
        }
    else:
        memory = {
            "content": content,
            "categories": categories,
            "tags": tags,
            "importance": importance
        }
    if entity:
        memory["entities"] = [entity]
    return memory

def flatten_dict(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten a nested dictionary into atomic memory entries"""
    result = []
    
    def process_item(item, prefix=""):
        if isinstance(item, dict):
            for key, value in item.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                process_item(value, new_prefix)
        elif isinstance(item, list):
            for i, value in enumerate(item):
                new_prefix = f"{prefix}[{i}]"
                process_item(value, new_prefix)
        else:
            # Convert to string representation if not already a string
            if not isinstance(item, str):
                content = str(item)
            else:
                content = item
                
            # Only add non-empty content
            if content.strip():
                result.append({
                    "content": content,
                    "path": prefix,
                    "categories": ["personal"]  # Default category
                })
    
    process_item(data)
    return result

async def check_memory_database_status() -> Dict[str, Any]:
    """
    Check the status of the Qdrant memory database and return detailed information
    about collections, counts, and sample data.
    
    Returns:
        Dictionary with status information including:
        - collections: List of collection names
        - total_memories: Total number of memory points across all collections
        - collection_counts: Dictionary mapping collection names to vector counts
        - sample_memories: Sample memories from each collection (if available)
    """
    from app.config import db
    
    try:
        logger.info("Checking memory database status...")
        status_info = {
            "collections": [],
            "total_memories": 0,
            "collection_counts": {},
            "sample_memories": {},
            "status": "success"
        }
        
        # Get all collections
        collections = await db.qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        status_info["collections"] = collection_names
        logger.info(f"Found {len(collection_names)} collections: {collection_names}")
        
        # Check each collection
        for collection_name in collection_names:
            try:
                # Get collection info
                collection_info = await db.qdrant_client.get_collection(collection_name)
                vector_count = collection_info.vectors_count
                status_info["collection_counts"][collection_name] = vector_count
                status_info["total_memories"] += vector_count
                
                logger.info(f"Collection '{collection_name}' has {vector_count} vectors")
                
                # Try to get sample data if collection has points
                if vector_count > 0:
                    try:
                        # Get a sample of points (up to 5)
                        sample_points = await db.qdrant_client.scroll(
                            collection_name=collection_name,
                            limit=5,
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        # Extract relevant information from sample points
                        samples = []
                        for point in sample_points[0]:  # First element is list of points
                            sample = {
                                "id": str(point.id),
                                "payload_keys": list(point.payload.keys()) if point.payload else [],
                            }
                            
                            # Include content if available (but truncate if too long)
                            if point.payload and "content" in point.payload:
                                content = point.payload["content"]
                                if isinstance(content, str) and len(content) > 100:
                                    content = content[:100] + "..."
                                sample["content"] = content
                                
                            samples.append(sample)
                            
                        status_info["sample_memories"][collection_name] = samples
                        logger.info(f"Retrieved {len(samples)} sample memories from '{collection_name}'")
                    except Exception as e:
                        logger.error(f"Error getting sample memories from '{collection_name}': {e}")
                        status_info["sample_memories"][collection_name] = f"Error: {str(e)}"
            except Exception as e:
                logger.error(f"Error getting info for collection '{collection_name}': {e}")
                status_info["collection_counts"][collection_name] = f"Error: {str(e)}"
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error checking memory database status: {e}")
        logger.exception("Full traceback for memory database status check error:")
        return {
            "status": "error",
            "error": str(e),
            "collections": [],
            "total_memories": 0
        } 
