from typing import Any, Dict, TypeVar, Generic
from json import dumps, loads
from pathlib import Path
from pydantic import BaseModel
from app.config.models import PoseyJSONEncoder
from app.utils.context import RunContext

def serialize_context(obj: Any) -> str:
    """Safely serialize objects including RunContext instances"""
    try:
        if isinstance(obj, RunContext):
            return dumps(obj.model_dump())
        return dumps(obj, cls=PoseyJSONEncoder)
    except Exception as e:
        # Fallback to safe_dict if direct serialization fails
        return dumps(safe_dict(obj))

def safe_dict(obj: Any) -> Dict:
    """Convert an object to a safely serializable dictionary"""
    if isinstance(obj, RunContext):
        return obj.model_dump()
    if hasattr(obj, 'model_dump'):  # Pydantic v2
        return obj.model_dump()
    elif hasattr(obj, 'dict'):      # Pydantic v1
        return obj.dict()
    elif hasattr(obj, '__dict__'):
        return {k: safe_dict(v) for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    elif isinstance(obj, dict):
        return {k: safe_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_dict(x) for x in obj]
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)

def deserialize_context(data: str) -> Dict:
    """Deserialize context data back into a dictionary"""
    return loads(data) 
