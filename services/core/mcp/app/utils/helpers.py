from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def format_error_response(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format error response with context"""
    return {
        "status": "error",
        "error": str(error),
        "error_type": type(error).__name__,
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {}
    }

def validate_tool_args(args: Dict[str, Any], required_fields: list) -> bool:
    """Validate required fields in tool arguments"""
    missing = [field for field in required_fields if field not in args]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    return True

def sanitize_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize response data"""
    try:
        # Convert to JSON and back to ensure serializable
        return json.loads(json.dumps(response))
    except Exception as e:
        logger.error(f"Error sanitizing response: {e}")
        return {"error": "Invalid response format"} 
