from typing import Dict, List, Any, Optional, Tuple
from langgraph.store.memory import InMemoryStore
from app.config import settings, logger
from app.utils.embeddings import get_embeddings
import time

class MemoryStore:
    """Manages long-term memory storage using LangGraph"""
    
    def __init__(self):
        # Initialize store with embedding function
        self.store = InMemoryStore(
            index={
                "embed": get_embeddings,
                "dims": settings.EMBEDDING_DIMENSIONS
            }
        )
    
    async def store_memory(
        self,
        user_id: str,
        content: Dict[str, Any],
        memory_type: str = "semantic",
        context: str = "general"
    ) -> str:
        """Store a new memory"""
        try:
            timestamp = int(time.time())
            namespace_prefix = f"{user_id}_{memory_type}_{context}"
            memory_id = f"mem_{timestamp}"
            
            await self.store.put(
                namespace_prefix,  # Required positional argument
                key=memory_id,
                value={
                    "content": content,
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "context": context,
                    "timestamp": timestamp
                }
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        context: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search memories by similarity"""
        try:
            # Build key pattern for filtering
            memory_types = [memory_type] if memory_type else ["semantic", "episodic", "procedural"]
            contexts = [context] if context else ["general", "personal"]
            
            # Search using namespace prefixes
            results = []
            for mt in memory_types:
                for ctx in contexts:
                    namespace_prefix = f"{user_id}_{mt}_{ctx}"
                    
                    memories = self.store.search(
                        namespace_prefix,  # Required positional argument
                        query=query,
                        limit=limit
                    )
                    
                    results.extend([
                        memory.value
                        for memory in memories
                    ])
            
            # Sort by relevance and return top results
            results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise
            
    async def search_recent(
        self,
        user_id: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
        context: Optional[str] = None,
        include_conversation: bool = False
    ) -> List[Dict[str, Any]]:
        """Get recent memories ordered by timestamp"""
        try:
            # Build key pattern for filtering
            memory_types = [memory_type] if memory_type else ["semantic", "episodic", "procedural"]
            contexts = [context] if context else ["general", "personal"]
            
            # Add conversation context if requested
            if include_conversation:
                contexts.append("conversation")
            
            # Search using namespace prefixes
            results = []
            current_memories = []  # Initialize current_memories before using in debug
            logger.debug(f"Type of memories before await: {type(current_memories)}")
            
            for mt in memory_types:
                for ctx in contexts:
                    namespace_prefix = f"{user_id}_{mt}_{ctx}"
                    
                    current_memories = self.store.search(
                        namespace_prefix,  # Required positional argument
                        query="",  # Empty query to get all memories
                        limit=100  # High limit to get most memories
                    )
                    logger.debug(f"Type of memories after await: {type(current_memories)}")
                    
                    results.extend([
                        memory.value
                        for memory in current_memories
                    ])
            
            # Sort by timestamp (most recent first) and return top results
            results.sort(key=lambda x: x["timestamp"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent memories: {e}")
            raise
