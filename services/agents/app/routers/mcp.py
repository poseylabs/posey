from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.abilities import get_ability, REGISTERED_ABILITIES
from app.config import logger

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Map tool names to abilities
TOOL_ABILITY_MAP = {
    # Core tools
    "delegate_task": "task_delegation",
    "store_memory": "memory",
    "generate_image": "image",
    
    # Allow direct ability access
    **{name: name for name in REGISTERED_ABILITIES.keys()}
}

@router.post("/tool/{tool_name}")
async def handle_tool_call(tool_name: str, params: Dict[str, Any]):
    """Handle tool calls from MCP server"""
    try:
        # Get the corresponding ability name
        ability_name = TOOL_ABILITY_MAP.get(tool_name)
        if not ability_name:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown tool: {tool_name}. Available tools: {list(TOOL_ABILITY_MAP.keys())}"
            )
            
        # Get and execute the ability
        ability = get_ability(ability_name)
        result = await ability.execute(params)
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error handling tool call: {e}")
        return {
            "status": "error",
            "error": str(e)
        } 
