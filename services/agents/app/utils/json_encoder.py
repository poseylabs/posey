from datetime import datetime
from json import JSONEncoder
from uuid import UUID
from pydantic import BaseModel

class CustomJSONEncoder(JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)
