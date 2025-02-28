from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAbility(ABC):
    """Base class for all abilities"""
    
    def __init__(self):
        """Initialize the ability"""
        pass
        
    def extract_prompt(self, params: Dict[str, Any]) -> Optional[str]:
        """Helper method to extract prompt from parameters"""
        return params.get("prompt") or params.get("description")
        
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the ability with given parameters"""
        pass
        
    async def cleanup(self):
        """Cleanup any resources used by the ability"""
        pass
        
    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate the parameters for this ability"""
        return True 
