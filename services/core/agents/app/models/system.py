from typing import Optional
from pydantic import BaseModel

class LocationInfo(BaseModel):
    """Location information"""
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None 