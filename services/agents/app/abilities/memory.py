from typing import Dict, Any, Optional
from app.abilities.base import BaseAbility
from app.config import logger
from app.utils.memory_utils import flatten_dict
from app.utils.analysis_utils import (
    handle_memory_operations,
    perform_memory_search
)
from hashlib import md5
import time
from app.utils.task_status_update import send_task_status_update

class MemoryAbility(BaseAbility):
    """Ability to store and retrieve memories from the vector database"""
    
    name = "memory"
    description = "Store and retrieve memories from the vector database"
    agent_type = "memory"
    
    def __init__(self):
        super().__init__()
        self._current_operation_id = None

    def _generate_operation_id(self, action: str, content: Optional[str] = None) -> str:
        """Generate a meaningful operation ID for memory operations"""
        if content:
            content_hash = md5(content.encode()).hexdigest()[:8]
            return f"memory_{action}_{content_hash}"
        return f"memory_{action}_{md5(str(time.time()).encode()).hexdigest()[:8]}"

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the memory operation"""
        try:
            action = parameters.get('action')
            content = parameters.get('content')
            metadata = parameters.get('metadata', {})
            conversation_id = parameters.get('conversation_id')
            user_id = parameters.get('user_id')
            agent_id = parameters.get('agent_id')

            if not user_id or not agent_id:
                raise ValueError("user_id and agent_id are required")

            # Ensure IDs are in metadata
            metadata = {
                **metadata,
                "user_id": user_id,
                "agent_id": agent_id
            }

            if action == 'store':
                # Convert nested content into atomic memories
                if isinstance(content, dict):
                    flattened_memories = flatten_dict(content)
                    stored_ids = []
                    
                    for memory in flattened_memories:
                        memory_metadata = {
                            **metadata,
                            "categories": memory.get("categories", ["personal"]),
                            "tags": memory.get("tags", []),
                            "importance": memory.get("importance", 7),
                            "entities": memory.get("entities", []),
                            "user_id": user_id,
                            "agent_id": agent_id
                        }
                        
                        result = await handle_memory_operations(
                            operation_type=action,
                            content=memory["content"],
                            metadata=memory_metadata,
                            user_id=user_id
                        )
                        stored_ids.append(result)
                    
                    return {
                        "status": "success", 
                        "message": f"Stored {len(stored_ids)} atomic memories",
                        "memory_ids": stored_ids
                    }

            if action == 'search':
                await send_task_status_update(
                    task_id=conversation_id if conversation_id else f"memory_search_{user_id}",
                    status="executing",
                    message=f"Trying to remember {content}",
                    progress=0
                )

            if action == 'store':
                await send_task_status_update(
                    task_id=conversation_id if conversation_id else f"memory_store_{user_id}",
                    status="executing",
                    message=f"Remembering {content}",
                    progress=0
                )
            
            if action == 'delete':
                await send_task_status_update(
                    task_id=parameters.get('conversation_id', f"memory_delete_{user_id}"),
                    status="executing",
                    message=f"Forgetting I ever knew about {content}",
                    progress=0
                )
            
            if not action or not content:
                raise ValueError("Missing required parameters: action and content")
            
            if action in ['store', 'update', 'delete']:
                result = await handle_memory_operations(
                    operation_type=action,
                    content=content,
                    metadata=metadata,
                    user_id=user_id
                )
                return {
                    "status": "success",
                    "message": f"Memory {action} operation completed",
                    "memory_id": result
                }
            elif action in ['search', 'retrieve']:
                memories = await perform_memory_search(
                    query=content,
                    user_id=user_id,
                    agent_id=agent_id,
                    metadata=metadata,
                    limit=parameters.get('limit', 5),
                    min_relevance=parameters.get('min_relevance', 0.5),
                    search_config=parameters.get('search_config')
                )
                return {
                    "status": "success",
                    "message": "Memory search completed",
                    "memories": memories
                }
            
            else:
                raise ValueError(f"Unknown action: {action}")
            
        except Exception as e:
            logger.error(f"Error in memory ability: {e}")
            return {
                "status": "error",
                "message": f"Failed to execute memory operation: {str(e)}"
            }
