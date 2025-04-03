"""Configuration for Posey's identity and settings"""

from typing import Dict, Any
from pydantic import BaseModel

class ContactConfig(BaseModel):
    """Contact information configuration"""
    email: str
    phone: Dict[str, Any]

class LocationConfig(BaseModel):
    """Location information configuration"""
    city: str
    state: str
    zip: str

class VitalsConfig(BaseModel):
    """Vital information configuration"""
    name: str
    full_name: str
    age: int

class PoseyConfig(BaseModel):
    """Complete Posey configuration"""
    vitals: VitalsConfig
    contact: ContactConfig
    location: LocationConfig

# Default configuration
DEFAULT_CONFIG = PoseyConfig(
    vitals=VitalsConfig(
        name="Posey",
        full_name="Posey Wilder",
        age=25
    ),
    contact=ContactConfig(
        email="posey@posey.ai",
        phone={
            "number": "",
            "country-code": 1
        }
    ),
    location=LocationConfig(
        city="Auburn",
        state="WA",
        zip="98092"
    )
)

def get_posey_config() -> PoseyConfig:
    """Get Posey's configuration
    
    In the future, this could load from environment variables,
    a database, or other sources.
    
    Returns:
        PoseyConfig: The current Posey configuration
    """
    return DEFAULT_CONFIG
