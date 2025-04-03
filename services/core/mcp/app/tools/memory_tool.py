from mcp.tools import Tool
from typing import Dict, Any
import httpx
import logging
from app.config import settings
from app.types import ToolDefinition

logger = logging.getLogger(__name__)

class MemoryTool(Tool):
    def __init__(self):
        self.definition = ToolDefinition(
            name="memory",
            description="Store and retrieve agent memories",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["store", "retrieve", "search"],
                        "description": "The memory operation to perform"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to store in memory"
                    },
                    "memory_id": {
                        "type": "string",
                        "description": "ID of memory to retrieve"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for finding memories"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata for the memory"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    },
                    "min_relevance": {
                        "type": "number",
                        "description": "Minimum relevance score for search results",
                        "default": 0.5
                    }
                },
                "required": ["action"]
            }
        )

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def description(self) -> str:
        return self.definition.description or ""

    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory operations"""
        try:
            action = args.get("action")
            if not action:
                raise ValueError("Action is required")
                
            async with httpx.AsyncClient() as client:
                if action == "store":
                    result = await self._store_memory(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Memory stored successfully: {result.get('memory_id')}"
                            }
                        ]
                    }
                elif action == "retrieve":
                    result = await self._retrieve_memory(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": result.get('content', 'Memory not found')
                            },
                            {
                                "type": "metadata",
                                "data": result.get('metadata', {})
                            }
                        ]
                    }
                elif action == "search":
                    result = await self._search_memories(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Search results:"
                            },
                            {
                                "type": "list",
                                "items": [
                                    {"text": memory.get('content')} 
                                    for memory in result.get('memories', [])
                                ]
                            }
                        ]
                    }
                else:
                    raise ValueError(f"Unknown action: {action}")
                    
        except Exception as e:
            logger.error(f"Error in memory tool: {str(e)}")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }

    async def _store_memory(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Store a new memory"""
        content = args.get("content")
        if not content:
            raise ValueError("Content is required for memory storage")
            
        response = await client.post(
            f"{settings.AGENTS_SERVICE_URL}/memory",
            json={
                "content": content,
                "metadata": args.get("metadata", {}),
                "user_id": args.get("user_id"),
                "agent_id": args.get("agent_id")
            }
        )
        response.raise_for_status()
        return response.json()

    async def _retrieve_memory(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve a specific memory"""
        memory_id = args.get("memory_id")
        if not memory_id:
            raise ValueError("memory_id is required for retrieval")
            
        response = await client.get(
            f"{settings.AGENTS_SERVICE_URL}/memory/{memory_id}"
        )
        response.raise_for_status()
        return response.json()

    async def _search_memories(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories by query"""
        query = args.get("query")
        if not query:
            raise ValueError("Query is required for memory search")
            
        response = await client.post(
            f"{settings.AGENTS_SERVICE_URL}/memory/search",
            json={
                "query": query,
                "metadata": args.get("metadata", {}),
                "limit": args.get("limit", 5),
                "min_relevance": args.get("min_relevance", 0.5)
            }
        )
        response.raise_for_status()
        return response.json() 
