import importlib.metadata
from typing import Dict, Any, Type, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import logger
from app.config.database import Database
from app.db.models.managed_minion import ManagedMinion
from app.minions.base import BaseMinion
from app.db.utils import get_minion_llm_config_by_key
from app.db.models import MinionLLMConfig
from app.minions.synthesis import SynthesisResponse

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
            
            # --- REVERTED: Fetch DB config AND LLM config within a session --- 
            minion_config: Optional[ManagedMinion] = None
            llm_config: Optional[MinionLLMConfig] = None # Variable for LLM config
            async with db_manager.get_session() as session:
                # Fetch ManagedMinion config
                stmt = select(ManagedMinion).where(ManagedMinion.minion_key == minion_key)
                result = await session.execute(stmt)
                minion_config = result.scalars().first()
                
                if not minion_config:
                    # This shouldn't happen if _load_active_minions worked, but safety check
                    raise ValueError(f"Database configuration for active minion '{minion_key}' not found during instantiation.")

                # REVERTED: Fetch associated MinionLLMConfig using the utility
                try:
                    llm_config = await get_minion_llm_config_by_key(session, minion_key)
                    if not llm_config:
                         logger.warning(f"Could not find LLM configuration for minion '{minion_key}' during setup. Setup might proceed with defaults or fail if LLM is required.")
                    else:
                         logger.info(f"Found LLM config for '{minion_key}' to pass to setup.")
                except Exception as llm_fetch_err:
                     logger.error(f"Error fetching LLM config for '{minion_key}' during setup: {llm_fetch_err}", exc_info=True)
                     # llm_config remains None
                
                # --- Instantiate with details from DB --- 
                description = minion_config.description or f"Minion for {minion_config.display_name}"
                instance = MinionClass(
                    name=minion_config.minion_key, # Internal key
                    display_name=minion_config.display_name, # User-facing name
                    description=description, # Description from DB
                )

                # --- Call setup WITH required args --- 
                # Setup needs the ORM object for potential relationship access
                await instance.setup(db_session=session, llm_config_orm=llm_config)

                # --- Agent Creation --- 
                # Move the import inside the method to break the circular dependency
                from app.utils.agent import create_agent
                agent = None # Initialize agent variable
                if llm_config:
                    try:
                        # --- Corrected Agent Creation Argument Preparation ---

                        # 1. Get model_identifier from the relationship
                        model_identifier = None
                        if hasattr(llm_config, 'llm_model') and llm_config.llm_model:
                            if hasattr(llm_config.llm_model, 'model_id') and llm_config.llm_model.model_id:
                                model_identifier = llm_config.llm_model.model_id
                                logger.debug(f"Retrieved model_identifier '{model_identifier}' from llm_model relationship for minion '{minion_key}'.")
                            else:
                                logger.error(f"Related llm_model found for minion '{minion_key}', but it has no 'model_id' attribute or it's empty.")
                                raise ValueError(f"Related LLMModel object for minion '{minion_key}' is missing the 'model_id' attribute.")
                        else:
                            logger.error(f"MinionLLMConfig for minion '{minion_key}' does not have a related 'llm_model' or it's None.")
                            raise ValueError(f"Could not find related LLMModel for minion '{minion_key}'. Cannot determine model identifier.")

                        # 2. Get OTHER config details (temperature, etc.) from the config JSON column
                        llm_config_details = {} # Default to empty dict
                        if hasattr(llm_config, 'config') and llm_config.config:
                            if isinstance(llm_config.config, dict):
                                llm_config_details = llm_config.config.copy() # Use copy to avoid modifying original
                                logger.debug(f"Retrieved base config details dictionary for minion '{minion_key}': {llm_config_details}")
                            else:
                                logger.warning(f"Minion '{minion_key}' llm_config.config is not a dictionary (type: {type(llm_config.config)}). Using empty config details.")
                        else:
                             logger.debug(f"Minion '{minion_key}' has no additional config details in llm_config.config.")

                        # *** ADD the model_identifier retrieved from relationship TO the config dict ***
                        if model_identifier:
                            llm_config_details['model_identifier'] = model_identifier
                            logger.debug(f"Added/Updated 'model_identifier' in config details for '{minion_key}'")
                        else:
                             # This case should have been caught by the checks above, but safety first
                             raise ValueError(f"Model identifier was None when trying to add to config for '{minion_key}'")

                        # 3. Get expected result type and settings override from ManagedMinion config
                        agent_result_type_str = getattr(minion_config, 'expected_output_type', None)
                        agent_result_type = agent_result_type_str # Pass str or None for now
                        model_settings_override = getattr(minion_config, 'default_model_settings', None)

                        # --- ADDED: Explicitly set result_type for synthesis minion --- 
                        if minion_key == 'synthesis':
                            logger.info(f"Setting result_type to SynthesisResponse for minion '{minion_key}'")
                            agent_result_type = SynthesisResponse
                        # --- END ADDED ---

                        # --- Use the create_agent utility ---
                        # Pass the ORM config object via db_llm_config_orm.
                        # create_agent will internally extract details from it.
                        # Do NOT pass the derived llm_config_details to the 'config' parameter.
                        agent = await create_agent(
                            agent_type=minion_key, 
                            abilities=[], # Placeholder
                            db=session, 
                            config=None, # Explicitly pass None for config override
                            result_type=agent_result_type,
                            user_preferences=None, # Not available at registry level
                            db_llm_config_orm=llm_config, # Pass the fetched ORM object
                            available_abilities_list=None # Placeholder
                        )
                        instance.agent = agent # Assign the created agent to the instance
                        logger.info(f"Successfully created and assigned agent to minion '{minion_key}'. Agent type: {type(instance.agent)}")

                    except (ValueError, TypeError, KeyError) as config_err:
                         logger.error(f"Configuration error during agent creation for minion '{minion_key}': {config_err}", exc_info=True)
                         raise RuntimeError(f"Agent configuration error for minion '{minion_key}'") from config_err
                    except Exception as agent_create_e:
                        # Catch potential DetachedInstanceError if session was closed before lazy load, etc.
                        logger.error(f"Failed to create agent for minion '{minion_key}': {agent_create_e}", exc_info=True)
                        raise RuntimeError(f"Agent creation failed for minion '{minion_key}'") from agent_create_e
                else:
                     logger.warning(f"Cannot create agent for minion '{minion_key}' because LLM configuration (MinionLLMConfig) was not found.")
                     # Consider if an agent MUST be present. If so, raise an error.
                     # raise RuntimeError(f"LLM config not found, cannot create agent for minion '{minion_key}'")

            self._instances[minion_key] = instance # Store after successful setup & agent creation (if applicable)
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
