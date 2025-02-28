from mcp.tools import Tool
from typing import Dict, Any
import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger(__name__)

class AgentTool(Tool):
    def __init__(self):
        super().__init__(
            name="agent",
            description="Delegate tasks to specialized Posey agents",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["delegate", "status"],
                        "description": "The action to perform"
                    },
                    "task": {
                        "type": "string",
                        "description": "Task description for delegation"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "ID of the target agent"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task to check status"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata for the task"
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent operations"""
        try:
            action = args.get("action")
            if not action:
                raise ValueError("Action is required")
                
            async with httpx.AsyncClient(timeout=settings.DEFAULT_TIMEOUT) as client:
                if action == "delegate":
                    result = await self._delegate_task(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Task delegated successfully: {result.get('task_id')}"
                            }
                        ]
                    }
                elif action == "status":
                    result = await self._check_status(client, args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Task status: {result.get('status')}"
                            }
                        ]
                    }
                else:
                    raise ValueError(f"Unknown action: {action}")
                    
        except Exception as e:
            logger.error(f"Error in agent tool: {str(e)}")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }

    async def _delegate_task(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a task to an agent"""
        task = args.get("task")
        agent_id = args.get("agent_id")
        
        if not task or not agent_id:
            raise ValueError("Task and agent_id are required for delegation")
            
        response = await client.post(
            f"{settings.AGENTS_SERVICE_URL}/tasks",
            json={
                "task": task,
                "agent_id": agent_id,
                "metadata": args.get("metadata", {})
            }
        )
        response.raise_for_status()
        return response.json()

    async def _check_status(self, client: httpx.AsyncClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check task status"""
        task_id = args.get("task_id")
        if not task_id:
            raise ValueError("task_id is required for status check")
            
        response = await client.get(
            f"{settings.AGENTS_SERVICE_URL}/tasks/{task_id}"
        )
        response.raise_for_status()
        return response.json() 
