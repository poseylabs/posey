from typing import Any, Dict
import json
from datetime import datetime
from uuid import UUID

class PoseyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Posey objects"""
    
    def default(self, obj: Any) -> Any:
        # Handle RunContext serialization
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'RunContext':
            return {
                'type': 'RunContext',
                'data': {
                    k: v for k, v in obj.__dict__.items() 
                    if not k.startswith('_')
                }
            }
            
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
            
        # Handle UUID objects
        if isinstance(obj, UUID):
            return str(obj)
            
        # Handle other custom objects that have a to_dict method
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
            
        return super().default(obj)

def serialize_response(data: Any) -> Dict[str, Any]:
    """Serialize response data to JSON-compatible format"""
    try:
        return json.loads(json.dumps(data, cls=PoseyJSONEncoder))
    except Exception as e:
        # If serialization fails, return a simplified error response
        return {
            "error": "Serialization error",
            "details": str(e),
            "data_type": str(type(data))
        } 
