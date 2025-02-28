from typing import Dict, Any
from app.utils.serializers import serialize_response

async def format_response(data: Any) -> Dict[str, Any]:
    """Format and serialize response data"""
    try:
        # Perform any necessary response formatting
        formatted_data = {
            "status": "success",
            "data": data
        }
        
        # Serialize the response
        return serialize_response(formatted_data)
    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        return {
            "status": "error",
            "message": "Error formatting response",
            "error": str(e)
        } 
