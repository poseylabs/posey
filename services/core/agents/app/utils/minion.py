from typing import Dict, Any, Type
from app.minions.memory import MemoryMinion
from app.minions.voyager import VoyagerMinion
from app.minions.image_generation import ImageGenerationMinion
from app.minions.research import ResearchMinion
from app.minions.content_analysis import ContentAnalysisMinion
from app.minions.image_processing import ImageProcessingMinion
from app.config import logger
from app.db import db # Import the shared db object

class MinionRegistry:
    """Registry for managing minion instances"""
    
    def __init__(self):
        self._minion_classes: Dict[str, Type] = {
            "memory": MemoryMinion,
            "voyager": VoyagerMinion,
            "image_generation": ImageGenerationMinion,
            "research": ResearchMinion,
            "content_analysis": ContentAnalysisMinion,
            "image_processing": ImageProcessingMinion
        }
        self._instances: Dict[str, Any] = {}

    def get_minion(self, name: str) -> Any:
        """Get or create a minion instance by name.
        
        Args:
            name: The name of the minion to retrieve.
            
        Returns:
            The minion instance.
            
        Raises:
            ValueError: If the minion name is unknown.
        """
        if name not in self._minion_classes:
            available = list(self._minion_classes.keys())
            logger.error(f"Unknown minion type requested: '{name}'. Available minions: {available}")
            raise ValueError(f"Unknown minion type: {name}. Available minions: {available}")
            
        # Create instance if it doesn't exist
        if name not in self._instances:
            logger.info(f"Creating new {name} minion instance")
            try:
                # Pass the db object to the MemoryMinion constructor
                if name == "memory":
                    self._instances[name] = self._minion_classes[name](db)
                else:
                    self._instances[name] = self._minion_classes[name]()
                logger.info(f"Successfully initialized {name} minion")
            except Exception as e:
                logger.error(f"Failed to initialize {name} minion: {e}")
                raise ValueError(f"Minion initialization failed: {name} - {e}")
            
        return self._instances[name]

    def get_minions(self) -> Dict[str, Any]:
        """Get all available minion instances.
        
        Returns:
            Dict mapping minion names to their instances.
        """
        # Log all available minion types
        logger.info(f"Available minion types: {list(self._minion_classes.keys())}")
        
        # Initialize any uninitialized minions
        initialization_errors = []
        for name in self._minion_classes:
            if name not in self._instances:
                try:
                    logger.info(f"Initializing {name} minion")
                    # Pass the db object to the MemoryMinion constructor
                    if name == "memory":
                        self._instances[name] = self._minion_classes[name](db)
                    else:
                        self._instances[name] = self._minion_classes[name]()
                    logger.info(f"Successfully initialized {name} minion")
                except Exception as e:
                    logger.error(f"Failed to initialize {name} minion: {e}")
                    initialization_errors.append(f"{name}: {e}")
        
        if initialization_errors:
            logger.warning(f"Some minions failed to initialize: {initialization_errors}")
                
        return self._instances.copy()

    async def cleanup(self):
        """Cleanup all minion instances"""
        for name, instance in self._instances.items():
            try:
                if hasattr(instance, 'cleanup'):
                    await instance.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {name} minion: {e}")

# Create global registry instance
registry = MinionRegistry()

# Expose convenience functions
get_minion = registry.get_minion
get_minions = registry.get_minions
cleanup = registry.cleanup

__all__ = ['get_minion', 'get_minions', 'cleanup']
