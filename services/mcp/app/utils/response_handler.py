from typing import Dict, Any, Union
import logging
from pydantic_ai.result import RunResult
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MCPResponse(BaseModel):
    """Standardized MCP response format"""
    status: str = "success"
    output: Any = None
    metadata: Dict[str, Any] = {}
    run_id: str = None
    error: str = None
    type: str = None

def parse_run_result(result: Union[RunResult, Dict[str, Any], Any]) -> Dict[str, Any]:
    """Parse RunResult into a dictionary format"""
    try:
        # Handle pydantic_ai RunResult
        if isinstance(result, RunResult):
            return MCPResponse(
                status="success",
                output=result.content if hasattr(result, 'content') else None,
                metadata={
                    "model": result.model if hasattr(result, 'model') else None,
                    "created_at": result.created_at if hasattr(result, 'created_at') else None,
                    "usage": result.usage if hasattr(result, 'usage') else None
                },
                run_id=result.id if hasattr(result, 'id') else None
            ).model_dump()
            
        # Handle dictionary results
        elif isinstance(result, dict):
            return MCPResponse(**result).model_dump()
            
        # Handle other result types
        else:
            logger.warning(f"Converting unexpected result type to string: {type(result)}")
            return MCPResponse(
                status="success",
                output=str(result),
                type=str(type(result))
            ).model_dump()
            
    except Exception as e:
        logger.error(f"Error parsing run result: {str(e)}")
        return MCPResponse(
            status="error",
            error=str(e),
            type=str(type(result)) if result else None
        ).model_dump() 
