import importlib.metadata
from typing import Dict, Any, Type, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import logger
from app.config.database import Database
from app.db.models.managed_minion import ManagedMinion
from app.minions.base import BaseMinion

MINION_ENTRY_POINT_GROUP = "posey.minions"

class MinionRegistry:
    """Registry for discovering, loading, and managing minion instances dynamically."""

    def __init__(self):
        # Stores loaded *classes* of active minions, keyed by minion_key
        self._loaded_classes: Dict[str, Type[BaseMinion]] = {}
        # Stores instantiated and set up *instances*, keyed by minion_key
        self._instances: Dict[str, BaseMinion] = {}
        self._initialized: bool = False

    async def _load_active_minions(self,
            db_manager: Database,
            minion_type: Optional[str] = None,
            tags: Optional[List[str]] = None
    ) -> None:
        """Load active minion *classes* from the database and entry points (async). Populates self._loaded_classes."""
        logger.info(f"Loading active minions (type: {minion_type}, tags: {tags})")
        self._loaded_classes = {}
        active_minions_from_db: Dict[str, ManagedMinion] = {}

        try:
            # 1. Fetch active minions from the database using a session
            async with db_manager.get_session() as session:
                stmt = select(ManagedMinion).where(ManagedMinion.is_active == True)
                result = await session.execute(stmt)
                active_minions_from_db = {m.minion_key: m for m in result.scalars().all()}
            logger.info(f"Found {len(active_minions_from_db)} active minions configured in the database.")

            # 2. Discover entry points
            try:
                discovered_entry_points = {ep.name: ep for ep in importlib.metadata.entry_points(group=MINION_ENTRY_POINT_GROUP)}
                logger.info(f"Discovered {len(discovered_entry_points)} entry points in group '{MINION_ENTRY_POINT_GROUP}'.")
            except Exception as e:
                logger.error(f"Failed to discover entry points for group '{MINION_ENTRY_POINT_GROUP}': {e}", exc_info=True)
                discovered_entry_points = {}

            # 3. Load classes for active, discoverable minions
            for key, minion_config in active_minions_from_db.items():
                if key not in discovered_entry_points:
                    logger.warning(f"Active minion '{key}' from DB has no corresponding entry point registered. Skipping.")
                    continue
                
                entry_point = discovered_entry_points[key]
                try:
                    MinionClass = entry_point.load()
                    if not issubclass(MinionClass, BaseMinion):
                        logger.error(f"Entry point '{key}' ({entry_point.value}) loaded class {MinionClass.__name__} which is not a subclass of BaseMinion. Skipping.")
                        continue
                        
                    self._loaded_classes[key] = MinionClass
                    logger.debug(f"Successfully loaded class for active minion: '{key}' -> {MinionClass.__name__}")
                except Exception as e:
                    logger.error(f"Failed to load class for entry point '{key}' ({entry_point.value}): {e}", exc_info=True)
            
            self._initialized = True
            logger.info(f"Minion registry initialized. Loaded {len(self._loaded_classes)} active minion classes.")

        except Exception as e:
            logger.critical(f"Failed to load active minions from database: {e}", exc_info=True)
            self._initialized = False # Ensure we retry if loading fails

    async def get_minion(self,
            db_manager: Database,
            minion_key: str
    ) -> Optional[BaseMinion]:
        """Get a specific minion instance by its key (async). Initializes if needed."""
        
        # Ensure classes are loaded
        if not self._initialized:
            await self._load_active_minions(db_manager)
        
        if minion_key not in self._loaded_classes:
            available = list(self._loaded_classes.keys())
            logger.error(f"Requested minion '{minion_key}' is not loaded or not active. Available active minions: {available}")
            # Consider raising an error or returning None based on desired behavior
            # raise ValueError(f"Minion '{minion_key}' not found or not active. Available: {available}")
            return None # Return None if not found/active
            
        # Return existing instance if already created and set up
        if minion_key in self._instances:
            return self._instances[minion_key]

        # Create and setup new instance
        logger.info(f"Creating and setting up new '{minion_key}' minion instance")
        instance = None
        try:
            MinionClass = self._loaded_classes[minion_key]
            
            # --- Fetch DB config FIRST using a session ---
            async with db_manager.get_session() as session:
                stmt = select(ManagedMinion).where(ManagedMinion.minion_key == minion_key)
                result = await session.execute(stmt)
                minion_config: Optional[ManagedMinion] = result.scalars().first()
            
            if not minion_config:
                # This shouldn't happen if _load_active_minions worked, but safety check
                raise ValueError(f"Database configuration for active minion '{minion_key}' not found during instantiation.")
            
            # --- Instantiate with details from DB --- 
            # Ensure description is not None, provide default if it is
            description = minion_config.description or f"Minion for {minion_config.display_name}"
            instance = MinionClass(
                name=minion_config.minion_key, # Internal key
                display_name=minion_config.display_name, # User-facing name
                description=description, # Description from DB
                # prompt_category can remain default ('agents') or be configured in DB later
            )

            await instance.setup()

            self._instances[minion_key] = instance # Store after successful setup
            logger.info(f"Successfully initialized and set up '{minion_key}' minion")
            return instance

        except Exception as e:
            logger.error(f"Failed to initialize or set up '{minion_key}' minion: {e}", exc_info=True)
            # Don't store the instance if setup failed
            # Re-raise or return None? Re-raising might be better to signal failure upstream
            raise ValueError(f"Minion initialization or setup failed: {minion_key} - {e}")

    async def get_minions(self,
            db_manager: Database,
            minion_type: Optional[str] = None,
            tags: Optional[List[str]] = None,
            active: bool = True
    ) -> Dict[str, BaseMinion]:
        """Get all available active minion instances, initializing if necessary."""
        if not self._initialized:
            await self._load_active_minions(db_manager)
            
        logger.info(f"Getting all active minion instances: {list(self._loaded_classes.keys())}")
        
        initialization_errors = []
        for name in self._loaded_classes:
            if name not in self._instances:
                try:
                    # Pass manager to get_minion
                    await self.get_minion(db_manager, name)
                except Exception as e:
                    # Log error but continue trying to get other minions
                    logger.error(f"Failed to get/initialize {name} minion during get_all: {e}")
                    initialization_errors.append(name)
        
        if initialization_errors:
            logger.warning(f"Some minions failed to initialize during get_minions: {initialization_errors}")
                
        return self._instances.copy()

    async def sync_with_db(self, db_manager: Database):
        """Force a reload of active minions from the database."""
        logger.info("Forcing synchronization of minion registry with database.")
        self._initialized = False # Mark as uninitialized
        self._instances = {} # Clear existing instances
        await self._load_active_minions(db_manager)

    async def cleanup(self):
        """Cleanup all minion instances"""
        logger.info("Cleaning up minion instances...")
        for name, instance in self._instances.items():
            try:
                if hasattr(instance, 'cleanup') and callable(instance.cleanup):
                    # Check if cleanup is async or sync
                    if asyncio.iscoroutinefunction(instance.cleanup):
                        await instance.cleanup()
                    else:
                        instance.cleanup() # Call synchronously if needed
                    logger.debug(f"Cleaned up {name} minion.")
            except Exception as e:
                logger.error(f"Error cleaning up {name} minion: {e}")
        self._instances = {}
        self._loaded_classes = {}
        self._initialized = False
        logger.info("Minion cleanup complete.")

# For now, let's export the class itself and handle instantiation/dependency injection
# in the application code where the db session is available.
__all__ = ['MinionRegistry']
