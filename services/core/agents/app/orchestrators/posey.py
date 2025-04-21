from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from pydantic_ai import Agent, Tool, RunContext
from pydantic_ai.agent import AgentRunResult
import json
import time
import pprint
import traceback
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from sqlalchemy import text

from app.utils.agent import create_agent, AgentExecutionResult
from app.utils.context import RunContext
from app.utils.message_handler import extract_messages_from_context, get_last_user_message
from app.config import logger
from app.utils.minion_registry import MinionRegistry
from app.utils.ability_registry import AbilityRegistry, AbilityRequest, AbilityResponse
from app.config.prompts import PromptLoader
from app.db.models import MinionLLMConfig
from app.db.utils import get_minion_llm_config_by_key
from app.minions.base import BaseMinion
from app.minions.voyager import WebResponse
from app.minions.memory import MemoryMinion, MemoryResponse
from app.models.analysis import ContentAnalysis, ContentIntent, DelegationConfig, DelegationTarget, Param
from app.utils.result_types import AgentExecutionResult
from pydantic_ai import RunContext

class MinionDelegationRequest(BaseModel):
    """Schema for requesting delegation to a specific minion."""
    minion_key: str = Field(..., description="The unique key of the minion to delegate to (e.g., 'content_analysis', 'research').")
    task_description: str = Field(..., description="A detailed description of the task for the target minion.")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional dictionary of parameters specific to the task for the minion.")
    context_override: Optional[Dict[str, Any]] = Field(default=None, description="Specific context values (like 'location' or 'user_profile') needed by the minion for this task, overriding default context if keys conflict.")

class PoseyResponse(BaseModel):
    """Model for final orchestrated response"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    memory_updates: List[Dict[str, Any]] = []
    
    @classmethod
    def from_str(cls, text: str) -> "PoseyResponse":
        """Create a PoseyResponse from a string, parsing JSON if possible"""
        # If it's already a PoseyResponse, return it
        if isinstance(text, PoseyResponse):
            return text

        # If it's a string that looks like JSON, try to parse it
        if isinstance(text, str) and text.strip().startswith('{') and text.strip().endswith('}'):
            try:
                data = json.loads(text.strip())
                # If the parsed JSON has the expected fields, create a PoseyResponse
                if isinstance(data, dict) and 'answer' in data:
                    return cls(
                        answer=data.get('answer', ''),
                        confidence=data.get('confidence', 0.5),
                        sources=data.get('sources', []),
                        metadata=data.get('metadata', {}),
                        memory_updates=data.get('memory_updates', [])
                    )
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse string as JSON: {text[:100]}...")
                
        # Default case: treat as plain text answer
        return cls(
            answer=text,
            confidence=0.5,
            sources=[],
            metadata={},
            memory_updates=[]
        )

class PoseyAgentState(BaseModel):
    """Represents the state of the Posey agent graph."""
    user_query: str = Field(..., description="The initial query from the user.")
    conversation_id: str = Field(..., description="The ID of the current conversation.")
    user_id: str = Field(..., description="The ID of the user.")
    project_id: Optional[str] = Field(None, description="The ID of the associated project, if any.")
    session_id: str = Field(..., description="The session ID for this interaction.")
    
    # Contextual information
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences.")
    system_capabilities: List[str] = Field(default_factory=list, description="System capabilities.")
    
    # Planning and Execution
    task_plan: Optional[List[Dict[str, Any]]] = Field(None, description="The generated plan of tasks.")
    current_task_index: int = Field(0, description="Index of the current task being executed.")
    task_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from executed tasks.")
    intermediate_steps: List[Tuple[Any, Any]] = Field(default_factory=list, description="Intermediate agent steps (action, observation).")
    
    # Agent Outputs
    final_response: Optional[str] = Field(None, description="The final synthesized response for the user.")
    error_message: Optional[str] = Field(None, description="Any error message encountered during execution.")
    
    # Minion Tracking
    active_minions: List[str] = Field(default_factory=list, description="List of active minion keys used in this run.")
    
    # Agent Instances (optional, depending on approach)
    # orchestrator: Optional[Agent] = None
    # synthesis_agent: Optional[Agent] = None
    
    # Add fields for necessary objects
    db_session: Optional[AsyncSession] = Field(None, exclude=True)
    minion_registry: Optional[MinionRegistry] = Field(None, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True # Allow complex types like AsyncSession

class PoseyAgent:
    """Main orchestrator agent using PydanticAI and LangGraph

    Use the async factory method `create` to instantiate.
    """
    orchestrator: Agent
    synthesis_agent: Agent
    orchestrator_model_id: str
    content_analysis_minion: BaseMinion
    db: AsyncSession
    registry: MinionRegistry
    ability_registry: AbilityRegistry
    minion_tools: Dict[str, Tool]
    initialized_minions: Dict[str, BaseMinion]
    minion_llm_configs: Dict[str, MinionLLMConfig]
    available_abilities_list: List[Dict[str, Any]]

    def __init__(
        self,
        orchestrator_agent: Agent,
        synthesis_agent: Agent,
        orchestrator_model_id: str,
        content_analysis_minion: BaseMinion,
        db_session: AsyncSession,
        registry: MinionRegistry,
        ability_registry: AbilityRegistry,
        initialized_minions: Dict[str, BaseMinion],
        minion_llm_configs: Dict[str, MinionLLMConfig]
    ):
        """Initialize PoseyAgent with necessary components."""
        self.orchestrator = orchestrator_agent
        self.synthesis_agent = synthesis_agent
        self.orchestrator_model_id = orchestrator_model_id
        self.content_analysis_minion = content_analysis_minion
        self.db = db_session
        self.registry = registry
        self.ability_registry = ability_registry
        self.minion_tools = {}
        self.initialized_minions = initialized_minions
        self.minion_llm_configs = minion_llm_configs
        self.available_abilities_list = []
        logger.info("PoseyAgent synchronous initialization complete.")

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        registry: MinionRegistry,
        initialized_minions: Dict[str, BaseMinion],
        user_preferences: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> "PoseyAgent":
        """Asynchronous factory method to create and initialize PoseyAgent."""
        logger.info("Starting async creation of PoseyAgent...")

        # First, get the available minions from the database for logging (using registry)
        try:
            if not registry._initialized: # Ensure registry classes are loaded if not already
                await registry._load_active_minions(db)
                
            logger.info("=" * 80)
            logger.info("AVAILABLE MINIONS REGISTERED:")
            if registry._loaded_classes:
                # Fetch DB details for logging active status if needed
                stmt = text("SELECT minion_key, display_name, is_active FROM managed_minions")
                result = await db.execute(stmt)
                db_minion_status = {row[0]: {"name": row[1], "active": row[2]} for row in result.fetchall()}
                
                for key, klass in registry._loaded_classes.items():
                    status_info = db_minion_status.get(key, {"name": f"{key} (DB status unknown)", "active": "Unknown"})
                    status = "ACTIVE" if status_info["active"] else "INACTIVE"
                    logger.info(f"  - {key} ({status_info['name']}) - {status}")
            else:
                logger.warning("No minion classes loaded in the registry.")
            logger.info("=" * 80)
            
            # Also pre-initialize the AbilityRegistry
            ability_registry = AbilityRegistry() # Initialize BEFORE try block
            try: # Inner try for ability initialization
                logger.info("Initializing AbilityRegistry cache...")
                ability_registry._initialize_cache() 
                logger.info("Ability registry cache initialized.")
                
                # Fetch abilities list once for logging and later use
                available_abilities_list = ability_registry.get_available_abilities()
                
                # Log abilities immediately after fetching inside the try block
                logger.info("AVAILABLE ABILITIES (within try):")
                if available_abilities_list:
                    for ability in available_abilities_list:
                        display_name = ability.get('display_name', ability.get('name', 'Unknown Ability'))
                        description = ability.get('description', 'No description')
                        logger.info(f"  - {ability.get('name', 'Unknown')}: {description} (Provided by: {display_name})")
                else:
                    logger.info("  (No abilities found in registry)")
            
            # Correctly indented except block for the inner try
            except Exception as inner_e: 
                logger.error(f"Failed during initial ability registry processing: {inner_e}", exc_info=True)
                # Logged the error, now ensure variables are initialized for the outer block
                if 'ability_registry' not in locals():
                    ability_registry = AbilityRegistry() # Basic init if first try failed
                if 'available_abilities_list' not in locals():
                    available_abilities_list = [] # Use empty list on error
                    logger.warning("Ability list set to empty due to initialization error.")
            
        except Exception as e:
            logger.error(f"Failed during initial minion OR ability logging/initialization: {e}", exc_info=True)
            # Ensure ability_registry is initialized even on error for later steps
            if 'ability_registry' not in locals():
                ability_registry = AbilityRegistry() # Basic init
            # Fetch abilities even if initial logging failed
            if 'available_abilities_list' not in locals():
                try:
                    available_abilities_list = ability_registry.get_available_abilities()
                    logger.warning("Fetched abilities after initial logging failure.")
                except Exception as fetch_err:
                    logger.error(f"Failed to fetch abilities after logging error: {fetch_err}")
                    available_abilities_list = [] # Use empty list on error

        # --- Pre-fetch LLM Configs for Initialized Minions ---
        fetched_minion_llm_configs: Dict[str, MinionLLMConfig] = {}
        logger.info("Pre-fetching LLM configurations for initialized minions...")
        if initialized_minions:
            for minion_key in initialized_minions.keys():
                try:
                    # Use the utility function to fetch the config ORM object
                    # Pass db session directly
                    llm_config = await get_minion_llm_config_by_key(db, minion_key) 
                    if llm_config:
                        fetched_minion_llm_configs[minion_key] = llm_config
                        # -- Enhanced Logging --
                        provider_info = f"{llm_config.llm_model.provider.name}/{llm_config.llm_model.name}" if llm_config.llm_model and llm_config.llm_model.provider else "(Provider/Model info missing)"
                        logger.info(f"Successfully fetched & stored LLM config for minion \t'{minion_key}\t'. Key: {llm_config.config_key}, Model: {provider_info}")
                        # -- End Enhanced Logging --
                    else:
                        # This might happen if a minion is active but has no LLM config entry (or default)
                        logger.warning(f"Could not find LLM configuration for active minion \t'{minion_key}\t'. Agent creation might fail later.")
                except Exception as fetch_exc:
                    logger.error(f"Error fetching LLM config for minion '{minion_key}': {fetch_exc}", exc_info=True)
        else:
            logger.warning("No minions were initialized, skipping LLM config pre-fetching.")
        logger.info(f"Finished pre-fetching LLM configs. Found {len(fetched_minion_llm_configs)} configs.")
        # --- End Pre-fetching ---

        # --- Determine Orchestrator Config & Create Agent ---
        logger.info("Determining orchestrator configuration...")
        orchestrator_final_config: Dict[str, Any] = None
        orchestrator_config_source: str = "unknown"
        preferred_provider = user_preferences.get("preferred_provider") if user_preferences else None
        preferred_model = user_preferences.get("preferred_model") if user_preferences else None

        # --- ADD LOGGING --- 
        logger.debug(f"[PoseyAgent.create] Checking User Preferences for Orchestrator. Raw prefs received: {user_preferences}")
        logger.debug(f"[PoseyAgent.create] Extracted preferred_provider: {preferred_provider}")
        logger.debug(f"[PoseyAgent.create] Extracted preferred_model: {preferred_model}")
        # --- END LOGGING ---

        if preferred_provider and preferred_model:
            logger.info(f"Using orchestrator provider '{preferred_provider}' and model '{preferred_model}' from user preferences.")
            # Reconstruct config similar to create_agent logic
            from app.config.defaults import LLM_CONFIG # Need import here
            default_params = LLM_CONFIG.get('default', {})
            orchestrator_final_config = {
                'provider': preferred_provider,
                'model': preferred_model,
                'model_params': {
                    'temperature': default_params.get('temperature', 0.7),
                    'max_tokens': default_params.get('max_tokens', 1000),
                    'top_p': default_params.get('top_p', 0.95),
                    'frequency_penalty': default_params.get('frequency_penalty', 0.0),
                    'presence_penalty': default_params.get('presence_penalty', 0.0),
                    **(default_params.get('additional_settings') or {})
                 },
                 'base_url': LLM_CONFIG.get(preferred_provider, {}).get('base_url') or default_params.get('base_url')
            }
            orchestrator_config_source = "user_preferences"
        else:
            logger.warning("Orchestrator provider/model not found in user preferences. Using hardcoded default.")
            from app.config.defaults import LLM_CONFIG # Need import here
            hardcoded_fallback_config = LLM_CONFIG.get('fallback', LLM_CONFIG['default'])
            orchestrator_final_config = hardcoded_fallback_config.copy()
            orchestrator_final_config['model_params'] = { k: v for k, v in orchestrator_final_config.items() if k not in ['provider', 'model', 'capabilities', 'base_url'] }
            if 'base_url' not in orchestrator_final_config and 'base_url' in hardcoded_fallback_config:
                 orchestrator_final_config['base_url'] = hardcoded_fallback_config['base_url']
            orchestrator_config_source = "hardcoded_default"
        
        # Get the actual model identifier string
        orchestrator_model_id_str = f"{orchestrator_final_config['provider']}:{orchestrator_final_config['model']}"
        logger.info(f"Resolved orchestrator model identifier: '{orchestrator_model_id_str}' (Source: {orchestrator_config_source})")

        # Create the main orchestrator agent using the determined config
        logger.info("Creating orchestrator agent...")
        orchestrator_agent = await create_agent(
            agent_type="orchestrator",
            config="posey", # Explicitly use the 'posey' prompt config
            abilities=[], # Orchestrator uses delegation tool, not direct abilities
            db=db,
            user_preferences=user_preferences, # Pass prefs for create_agent to re-evaluate source
            available_abilities_list=available_abilities_list # Pass fetched list
        )
        logger.info("Orchestrator agent created.")
        # --- End Orchestrator Config & Creation ---

        # Create the synthesis agent using DB config OR user preferences
        logger.info("Creating synthesis agent...")
        synthesis_agent = await create_agent(
            agent_type="synthesis",
            abilities=[],
            db=db,
            user_preferences=user_preferences,
            available_abilities_list=available_abilities_list # Pass fetched list
        )
        logger.info("Synthesis agent created.")

        # Get the Content Analysis minion (assuming it was pre-initialized)
        logger.info("Verifying ContentAnalysisMinion instance...") 
        content_analysis_minion = initialized_minions.get("content_analysis")
        if not content_analysis_minion:
             logger.error("Content Analysis minion was not found in pre-initialized minions!")
             raise RuntimeError("Critical Content Analysis minion failed to initialize during startup.")
        logger.info("ContentAnalysisMinion instance verified.") 

        # Create the PoseyAgent instance, passing the determined model ID
        instance = cls(
            orchestrator_agent=orchestrator_agent,
            synthesis_agent=synthesis_agent,
            orchestrator_model_id=orchestrator_model_id_str, # Pass the string ID
            content_analysis_minion=content_analysis_minion,
            db_session=db,
            registry=registry,
            ability_registry=ability_registry,
            initialized_minions=initialized_minions, # Pass the dictionary
            minion_llm_configs=fetched_minion_llm_configs # <-- Pass fetched configs
        )
        
        # Store the fetched abilities list on the instance
        instance.available_abilities_list = available_abilities_list
        
        # Load prompts for Posey (orchestrator) and Synthesis agents
        try:
            prompt_loader = PromptLoader()
            # Corrected method call
            instance.orchestrator_prompts = prompt_loader.get_prompt_with_shared_config("posey") 
            instance.synthesis_prompts = prompt_loader.get_prompt_with_shared_config("synthesis")
            logger.info("Loaded prompts for posey orchestrator and synthesis agents with shared configurations")
        except Exception as e:
            logger.error(f"Failed to load prompts for Posey/Synthesis agents: {e}")
            instance.orchestrator_prompts = {}
            instance.synthesis_prompts = {}

        # Register tools AFTER instance is created
        await instance.register_minion_tools()
        
        logger.info("PoseyAgent instance created successfully.")
        return instance

    # --- Updated Delegation Logic --- 
    async def _delegate_task_to_minion(
        self,
        context: RunContext,
        request: MinionDelegationRequest # Use the new model here
    ) -> Dict[str, Any]:
        """(Internal Logic) Delegate a task based on a MinionDelegationRequest."""
        minion_key = request.minion_key
        # Use task_description as a fallback label for logging
        task_label = request.task_description 
        params = request.params or {}
        
        # --- Get the actual query/task for the minion from params --- 
        minion_prompt = params.get("query", task_label) # Use param['query'] if available, else fallback
        if minion_prompt == task_label:
             logger.warning(f"[ORCHESTRATOR TOOL / {minion_key}] Using fallback task label '{task_label}' as minion prompt. Was 'query' param missing from ContentAnalysis?")
        # --- End get query --- 
        
        logger.info(f"[ORCHESTRATOR TOOL] Attempting task '{task_label[:50]}...' on Minion '{minion_key}' using prompt: '{minion_prompt[:100]}...'")
        
        minion_instance = self.initialized_minions.get(minion_key)
        if not minion_instance:
            logger.error(f"[ORCHESTRATOR TOOL] Invalid minion_key '{minion_key}'. Available: {list(self.initialized_minions.keys())}")
            return {"error": f"Invalid minion key: '{minion_key}'. Choose from: {list(self.initialized_minions.keys())}"}

        llm_config = self.minion_llm_configs.get(minion_key)
        if not llm_config:
            logger.error(f"[ORCHESTRATOR TOOL] LLM config for minion '{minion_key}' was not pre-fetched. Cannot execute task.")
            return {"error": f"LLM configuration missing for minion '{minion_key}'."}
            
        try:
            # --- Instantiate Agent Just-in-Time --- 
            agent_instance: Optional[Agent] = None
            try:
                logger.info(f"[ORCHESTRATOR TOOL] Instantiating agent for '{minion_key}'...")
                # Validate config relationships before use
                if not llm_config.llm_model or not llm_config.llm_model.provider:
                     raise ValueError(f"LLM config for '{minion_key}' is missing model/provider relationship.")
                     
                # Construct model ID and settings from config
                provider_slug = llm_config.llm_model.provider.slug
                model_id = llm_config.llm_model.model_id
                agent_model_id = f"{provider_slug}:{model_id}"
                
                agent_kwargs = {
                    "temperature": llm_config.temperature,
                    "max_tokens": llm_config.max_tokens,
                    "top_p": llm_config.top_p,
                    "frequency_penalty": llm_config.frequency_penalty,
                    "presence_penalty": llm_config.presence_penalty,
                    **(llm_config.additional_settings or {})
                }
                model_settings = {k: v for k, v in agent_kwargs.items() if v is not None}
                system_prompt = minion_instance.get_system_prompt()
                
                # --- Determine result_type --- 
                expected_result_type = None
                if minion_key == 'voyager':
                    expected_result_type = WebResponse
                    logger.info(f"[ORCHESTRATOR TOOL] Setting expected result_type to WebResponse for voyager.")
                # TODO: Add logic here later to get result_type from other minions
                # --- End determine result_type ---
                
                # Instantiate the pydantic_ai.Agent
                agent_instance = Agent(
                    agent_model_id,
                    system_prompt=system_prompt,
                    # Use the determined result type
                    result_type=expected_result_type, 
                    model_settings=model_settings
                )
                logger.info(f"[ORCHESTRATOR TOOL] Successfully instantiated agent for '{minion_key}'.")

            except Exception as agent_creation_exc:
                logger.error(f"[ORCHESTRATOR TOOL] Failed to instantiate agent for '{minion_key}': {agent_creation_exc}", exc_info=True)
                return {"error": f"Failed to create agent for minion '{minion_key}': {agent_creation_exc}"}
            # --- End Agent Instantiation ---
            
            # --- Prepare Dependencies for Minion Run --- 
            # Start with base deps available to the tool
            merged_deps = context.deps.copy() if context.deps else {}
            
            # Merge/override with context provided explicitly in the request
            if request.context_override:
                logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] Merging context_override into deps: {list(request.context_override.keys())}")
                merged_deps.update(request.context_override)
            else:
                logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] No context_override provided in request.")
            
            # --- Add specific context fetching logic IF NOT overridden ---
            # Example: Fetch memories if not already provided in override
            if minion_key == 'voyager' and 'relevant_memories' not in merged_deps: 
                logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] Fetching relevant_memories (not in context_override).")
                try:
                    memory_minion = self.initialized_minions.get("memory")
                    if memory_minion and isinstance(memory_minion, MemoryMinion):
                        memory_params = {"query": minion_prompt, "k": 3}
                        memory_run_context = RunContext(model="memory_retrieval", usage={}, prompt=minion_prompt, deps=merged_deps) # Use merged deps for memory context
                        memory_response_dict = await memory_minion.execute(memory_params, memory_run_context)
                        retrieved_memories = memory_response_dict.get('memories', [])
                        if retrieved_memories:
                            logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] Retrieved {len(retrieved_memories)} memories.")
                            merged_deps['relevant_memories'] = retrieved_memories
                        else:
                            logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] No relevant memories found.")
                    else:
                        logger.warning(f"[ORCHESTRATOR TOOL / {minion_key}] Memory minion instance not found/invalid. Cannot fetch memories.")
                except Exception as ctx_fetch_err:
                    logger.error(f"[ORCHESTRATOR TOOL / {minion_key}] Error fetching memories: {ctx_fetch_err}", exc_info=True)

            # Example: Add user profile if not already provided in override
            if 'user_profile' not in merged_deps: 
                logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] Adding user_profile data (not in context_override).")
                if merged_deps: # Check if base deps exist
                    user_profile_data = {
                        'user_id': merged_deps.get('user_id'),
                        'username': merged_deps.get('user_name'), 
                        'location': merged_deps.get('location'), # Location might be here now if passed via override or base deps
                        'preferences': merged_deps.get('preferences')
                    }
                    user_profile_data = {k: v for k, v in user_profile_data.items() if v is not None}
                    if user_profile_data:
                        merged_deps['user_profile'] = user_profile_data
                        logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] Added user profile data: {list(user_profile_data.keys())}")
                    else:
                        logger.info(f"[ORCHESTRATOR TOOL / {minion_key}] No user profile components found in base deps.")
                else:
                    logger.warning(f"[ORCHESTRATOR TOOL / {minion_key}] Base context deps are empty, cannot add user profile.")

            # --- Determine Location ---
            user_prefs = context.get("user_preferences", {})
            final_location = user_prefs.get("location")

            browser_location_data = context.get("metadata", {}).get("browser", {}).get("location") # Safely get browser location
            logger.debug(f"[{request_id}] Browser location data from context: {browser_location_data}")

            logger.info(f"[MINION_PROMPT_INPUT / {minion_key}] System Prompt Used:")
            logger.info(f"-------------------- SYSTEM PROMPT START ({minion_key}) --------------------")
            logger.info(system_prompt)
            logger.info(f"-------------------- SYSTEM PROMPT END ({minion_key}) ----------------------")
            logger.info(f"[MINION_PROMPT_INPUT / {minion_key}] Task Description (User Prompt) Passed to run():")

            logger.info(f"-------------------- TASK DESC START ({minion_key}) -----------------------")
            logger.info(minion_prompt) 
            logger.info(f"-------------------- TASK DESC END ({minion_key}) -------------------------")

            logger.info(f"[ORCHESTRATOR TOOL] Executing task on '{minion_key}' agent.")
            
            # --- ADDED DEBUG LOG --- 
            logger.debug(f"[ORCHESTRATOR TOOL / {minion_key}] Final merged_deps being passed to agent.run():\n{pprint.pformat(merged_deps)}")
            # --- END DEBUG LOG --- 

            agent_result = await agent_instance.run(minion_prompt, deps=merged_deps) 
            
            logger.info(f"[RAW_MINION_RESULT / {minion_key}] Raw agent result received. Type: {type(agent_result)}")
            logger.debug(f"[RAW_MINION_RESULT / {minion_key}] Raw Result repr():\n{repr(agent_result)}")
            logger.info(f"[ORCHESTRATOR TOOL] Minion '{minion_key}' finished. Result type: {type(agent_result)}")
            
            return self._serialize_result(agent_result, minion_key)

        except Exception as e:
            logger.error(f"[ORCHESTRATOR TOOL] Error executing task on '{minion_key}': {e}", exc_info=True)
            return {"error": f"Failed task execution on '{minion_key}': {str(e)}"}
            
    # --- End Updated Delegation Logic --- 

    def _serialize_result(self, result: Any, source_key: str) -> Dict[str, Any]:
        """Helper function to serialize results consistently."""
        # --- MODIFICATION START ---
        # Specifically handle AgentRunResult from minions
        if isinstance(result, AgentRunResult):
            logger.debug(f"[SERIALIZE] Handling AgentRunResult from {source_key}.")
            # Try to extract data, prioritize .data, then .output, then fallback
            data = getattr(result, 'data', None)
            output = getattr(result, 'output', None)
            if data is not None:
                 logger.debug(f"[SERIALIZE] Extracting from AgentRunResult.data (type: {type(data)})")
                 # Recursively serialize the inner data
                 return self._serialize_result(data, f"{source_key}.data")
            elif isinstance(output, str) and output.strip():
                 logger.debug("[SERIALIZE] Extracting from AgentRunResult.output (string)")
                 # If output is just a string, return it directly in a dict
                 return {"result": output}
            else:
                 logger.warning(f"[SERIALIZE] AgentRunResult from {source_key} had neither .data nor useful .output. Falling back to str.")
                 return {"result": str(result)} # Fallback if data/output are None/empty
        # --- MODIFICATION END ---
        
        # Existing serialization logic for other types
        if hasattr(result, 'model_dump'): 
            return result.model_dump()
        if hasattr(result, 'dict') and callable(result.dict): 
            return result.dict()
        if isinstance(result, (dict, list, str, int, float, bool)) or result is None:
            # Ensure top-level is always a dict for consistency
            return {"result": result} if not isinstance(result, dict) else result
        
        logger.warning(f"[ORCHESTRATOR TOOL] Non-serializable result type {type(result)} from {source_key}. Converting to str.")
        return {"result": str(result)}

    async def register_minion_tools(self):
        """Register a single minion delegation tool using a simplified signature."""
        logger.info("=" * 80)
        logger.info("REGISTERING SINGLE MINION DELEGATION TOOL (Simplified Signature)")
        logger.info("=" * 80)
        
        self.minion_tools = {} 
        tool_name = "delegate_task_to_minion"

        # List available minions for the tool description
        available_minion_keys = list(self.initialized_minions.keys())
        available_minions_str = ", ".join(available_minion_keys)
        logger.info(f"Minions available for delegation: {available_minions_str}")

        async def _delegate_wrapper_simplified(
            context: RunContext[Dict[str, Any]],
            request: MinionDelegationRequest
        ) -> Dict[str, Any]:
            return await self._delegate_task_to_minion(context, request)

        # Construct the docstring for the wrapper function
        # Base docstring now comes from the MinionDelegationRequest model itself
        wrapper_docstring = f"""
        Delegates a task to a specified minion using a structured request. 
        Available minion_key values: [{available_minions_str}]
        """
        _delegate_wrapper_simplified.__doc__ = wrapper_docstring.strip()
        _delegate_wrapper_simplified.__name__ = tool_name 
        # --- End Simplified Wrapper --- 

        try:
            # Register the SIMPLIFIED WRAPPER function
            registered_tool = self.orchestrator.tool()(_delegate_wrapper_simplified) 
            
            self.minion_tools[tool_name] = registered_tool
            logger.info(f"Successfully registered delegation tool '{tool_name}' (Simplified Signature) with the orchestrator.")
        except Exception as registration_e:
             logger.error(f"CRITICAL ERROR registering delegation tool '{tool_name}' (Simplified Signature): {registration_e}", exc_info=True)

        logger.info("=" * 80)
        logger.info("ORCHESTRATOR DELEGATION TOOL REGISTRATION SUMMARY:")
        reg_status = "(Registered)" if tool_name in self.minion_tools else "(Registration FAILED)"
        logger.info(f"  - Tool '{tool_name}' {reg_status}")
        logger.info("=" * 80)

    async def run(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """Execute the orchestration pipeline using the orchestrator agent with delegation tools"""
        total_start = time.time()
        request_id = str(uuid.uuid4())
        logger.info(f"[POSEY_RUN] Starting Posey execution for request {request_id}")
        
        execution_steps = [] # Initialize list to store execution steps
        try:
            context = context or {}
            # Ensure messages are present in context, potentially passed from run_with_messages
            messages = context.get("messages")
            if not messages:
                 # Fallback: If messages aren't in context, create a minimal list from prompt
                 logger.warning(f"[{request_id}] 'messages' not found in context. Creating minimal history from prompt.")
                 messages = [{'role': 'user', 'content': prompt}]
                 context["messages"] = messages # Add it to context for downstream use
            else:
                 logger.info(f"[{request_id}] Using message history provided in context (count: {len(messages)}).")
            
            user_id = context.get("user_id", "default_user")
            conversation_id = context.get("conversation_id", str(uuid.uuid4()))
            project_id = context.get("project_id")
            
            # --- Format Message History for LLM Prompt --- 
            def format_history_for_prompt(history: List[Dict[str, str]]) -> str:
                formatted = []
                for msg in history:
                    role = msg.get('role', 'unknown').capitalize()
                    content = msg.get('content', '')
                    formatted.append(f"{role}: {content}")
                return "\n\n".join(formatted) # Separate messages clearly
            
            analysis_prompt_input = format_history_for_prompt(messages)
            # --- End Format History --- 
            
            # Add the helper function definition inside the run method scope
            def params_to_dict(params: List[Param]) -> Dict[str, Any]:
                return {p.key: p.value for p in params}
            
            # 1. Content Analysis (Just-in-Time Agent Creation)
            logger.info("STEP 1: CONTENT ANALYSIS")
            logger.info("================================================================================")

            # --- Enhanced Logging --- 
            logger.info("[POSEY_RUN / STEP 1] Requesting ContentAnalysis agent instance...")
            analysis_result_type = ContentAnalysis # Explicitly reference the expected type
            logger.info(f"[POSEY_RUN / STEP 1] Expected result_type: {analysis_result_type.__name__}")
            # ------------------------

            try:
                # -- Fetch pre-loaded config --
                content_analysis_config_orm = self.minion_llm_configs.get("content_analysis")
                if content_analysis_config_orm:
                    provider_info = f"{content_analysis_config_orm.llm_model.provider.slug}:{content_analysis_config_orm.llm_model.model_id}" if content_analysis_config_orm.llm_model and content_analysis_config_orm.llm_model.provider else "(Provider/Model info missing)"
                    logger.info(f"[POSEY_RUN / STEP 1] Found pre-fetched config for \t'content_analysis\t\t: Key=	'{content_analysis_config_orm.config_key}\t\t, Model=	'{provider_info}\t\t")
                else:
                    logger.warning("[POSEY_RUN / STEP 1] Pre-fetched config for \t'content_analysis\t\t not found in self.minion_llm_configs. \t\tcreate_agent\t\t will attempt DB lookup.")
                # -- End Fetch pre-loaded config --
                
                # --- MODIFIED LOGGING: Log the formatted history --- 
                logger.info(f"[POSEY_RUN / STEP 1] Content Analysis Input (Formatted History):\n---\n{analysis_prompt_input}\n---")
                # --- END MODIFIED LOGGING --- 
                
                analysis_agent_instance = await create_agent(
                    agent_type="content_analysis",
                    abilities=[], # Content analysis doesn't use abilities directly
                    db=self.db, 
                    result_type=analysis_result_type, # Pass the specific result type
                    user_preferences=context.get("user_preferences", {}),
                    db_llm_config_orm=content_analysis_config_orm, # Pass the fetched ORM object
                    available_abilities_list=self.available_abilities_list # Pass the stored list
                )
                # --- Enhanced Logging --- 
                if analysis_agent_instance:
                    logger.info(f"[POSEY_RUN / STEP 1] Successfully obtained analysis_agent_instance: Type={type(analysis_agent_instance).__name__}")
                    # Log the model instance if possible (check if it's our debug model)
                    if hasattr(analysis_agent_instance, 'model') and analysis_agent_instance.model:
                        logger.info(f"[POSEY_RUN / STEP 1] Agent's internal model: {type(analysis_agent_instance.model).__name__}")
                    else:
                        logger.warning("[POSEY_RUN / STEP 1] Agent instance does not have a 'model' attribute or it is None.")
                else:
                    logger.error("[POSEY_RUN / STEP 1] Failed to obtain analysis_agent_instance!")
                    raise ValueError("Failed to get or create content analysis agent instance")
                # ------------------------

            except Exception as agent_init_error:
                logger.error(f"[POSEY_RUN / STEP 1] CRITICAL ERROR during agent instantiation: {agent_init_error}", exc_info=True)
                # Handle critical failure to get agent
                final_response = "I encountered a critical error setting up my analysis components. Please try again later."
                # ... (rest of error handling)
                # ...
                return AgentExecutionResult(answer=final_response, confidence=0.0, error_message=str(agent_init_error))

            # Prepare context for the analysis run
            # --- MODIFIED: Pass formatted history and full context --- 
            analysis_run_deps = {
                # Start with the full incoming context dictionary
                **context, 
                # Ensure core IDs are present
                "user_id": user_id,
                "conversation_id": conversation_id,
                "run_id": request_id,
                "timestamp": datetime.now().isoformat(),
                # Include the formatted prompt history string
                "formatted_history": analysis_prompt_input, 
                # Pass the full, original metadata from the request (already in context)
                # "request_metadata": context.get('metadata', {}) # Redundant now
                # Add constructed user_profile with backend-derived location if needed
                # (Assuming location logic happens before this or is part of context)
                "user_profile": {
                    "user_id": user_id,
                    "preferences": context.get("user_preferences", {}),
                    "ip_derived_location": final_location, # Renamed for clarity
                    "browser_reported_location": browser_location_data # Add browser location
                }
            }
            logger.debug(f"[{request_id}] Initial dependencies prepared for Content Analysis: {list(analysis_run_deps.keys())}")
            # --- END MODIFIED --- 

            try:
                content_analysis_schema = ContentAnalysis.model_json_schema()
                logger.info(">>> MANUALLY GENERATED ContentAnalysis SCHEMA <<< 	")
                pretty_schema = pprint.pformat(content_analysis_schema, indent=2)
                logger.info(pretty_schema)
                logger.info(">>> END MANUALLY GENERATED SCHEMA <<< 	")
            except Exception as schema_e:
                logger.error(f"Failed to generate/log ContentAnalysis schema: {schema_e}")

            # --- Enhanced Logging --- 
            logger.info(f"[POSEY_RUN / STEP 1] Preparing to run analysis_agent_instance.run()")
            # logger.debug(f"[POSEY_RUN / STEP 1] Prompt being passed: \n---\n{prompt}\n---\") # Old log
            # Use pprint for deps for better readability
            pretty_deps = pprint.pformat(analysis_run_deps, indent=2, width=120)
            logger.debug(f"[POSEY_RUN / STEP 1] Deps being passed:\n{pretty_deps}")
            # ------------------------

            # Run content analysis
            try:
                # --- MODIFIED CALL: Pass formatted history as prompt and updated deps --- 
                raw_analysis_result = await analysis_agent_instance.run(analysis_prompt_input, deps=analysis_run_deps)
                # --- END MODIFIED CALL --- 
                logger.info(f"[POSEY_RUN / STEP 1] Raw analysis result received. Type: {type(raw_analysis_result)}")

                analysis: Optional[ContentAnalysis] = None # Initialize analysis variable

                # --- Extract ContentAnalysis object --- 
                if isinstance(raw_analysis_result, ContentAnalysis):
                    analysis = raw_analysis_result
                    analysis_repr = pprint.pformat(analysis.model_dump(), indent=2, width=120)
                    logger.debug(f"[POSEY_RUN / STEP 1] Analysis Result (ContentAnalysis):\n{analysis_repr}")
                elif isinstance(raw_analysis_result, AgentRunResult):
                    logger.warning(f"[POSEY_RUN / STEP 1] Analysis returned AgentRunResult instead of ContentAnalysis direct.")
                    # Check if the data attribute holds the ContentAnalysis object
                    if hasattr(raw_analysis_result, 'data') and isinstance(raw_analysis_result.data, ContentAnalysis):
                        analysis = raw_analysis_result.data
                        logger.info("[POSEY_RUN / STEP 1] Extracted ContentAnalysis object from AgentRunResult.data")
                        analysis_repr = pprint.pformat(analysis.model_dump(), indent=2, width=120)
                        logger.debug(f"[POSEY_RUN / STEP 1] Extracted Analysis Result (ContentAnalysis):\n{analysis_repr}")
                    else:
                        # Log the full repr if data doesn't contain the expected type
                        analysis_repr = repr(raw_analysis_result)
                        logger.warning(f"[POSEY_RUN / STEP 1] AgentRunResult.data did not contain ContentAnalysis. Full object:\n{analysis_repr}")
                else:
                    # Fallback for unexpected types
                    analysis_repr = pprint.pformat(raw_analysis_result, indent=2, width=120)
                    logger.warning(f"[POSEY_RUN / STEP 1] Unexpected Analysis Result Type. Full Object:\n{analysis_repr}")
                
                # Check if we successfully extracted or received a ContentAnalysis object
                if analysis is None:
                    logger.error("[POSEY_RUN / STEP 1] Failed to obtain a valid ContentAnalysis object.")
                    # Fallback to error state if extraction failed
                    analysis = ContentAnalysis(
                        intent=ContentIntent(primary_intent="error", requires_memory=False, needs_clarification=True, clarification_questions=["Analysis failed to produce expected structure."]),
                        delegation=DelegationConfig(should_delegate=False),
                        reasoning="Analysis failed internally after LLM call.",
                        confidence=0.0
                    )
            except Exception as analysis_error:
                # Log the specific error during the run
                logger.error(f"[POSEY_RUN / STEP 1] Error during analysis_agent_instance.run() or result processing: {analysis_error}", exc_info=True)
                
                # --- ADDED: Return error result immediately --- 
                return AgentExecutionResult(
                    success=False,
                    answer=f"I encountered an error during the analysis phase: {str(analysis_error)}",
                    error="ContentAnalysisError",
                    run_id=request_id,
                    start_time=total_start, 
                    metadata={
                        "status": "error",
                        "error_message": str(analysis_error),
                        "traceback": traceback.format_exc().splitlines()
                    },
                    confidence=0.0
                )
                # --- END ADDED --- 
            
            # Extract intent and reasoning for orchestrator context
            intent = "unknown"
            analysis_summary = "Analysis unavailable"
            if hasattr(analysis, "intent") and analysis.intent:
                intent = analysis.intent.primary_intent if hasattr(analysis.intent, "primary_intent") else str(analysis.intent)
            if hasattr(analysis, "reasoning"):
                analysis_summary = analysis.reasoning
            
            # --- REFACTOR START: Execute based on Content Analysis --- 
            logger.info("=" * 80)
            logger.info(f"[{request_id}] STEP 2: EXECUTE PLAN FROM ANALYSIS")
            logger.info("=" * 80)
            
            all_results = [] # Store results from minions and abilities
            execution_error: Optional[str] = None
            final_metadata = {} # Initialize metadata dictionary

            # A. Handle Clarification Needed
            if hasattr(analysis, 'intent') and analysis.intent.needs_clarification:
                logger.info(f"[{request_id}] Analysis indicates clarification needed.")
                questions = "\n - ".join(analysis.intent.clarification_questions)
                clarification_msg = f"To help me understand better, could you please clarify:\n - {questions}"
                # Return immediately for clarification
                return AgentExecutionResult(
                    success=True, # Technically successful in identifying clarification need
                    answer=clarification_msg,
                    result_type="clarification_needed",
                    run_id=request_id,
                    start_time=total_start,
                    metadata={
                        "analysis": analysis.model_dump(), 
                        "processing_time": time.time() - total_start,
                        "intent": analysis.intent.primary_intent
                    },
                    confidence=analysis.confidence # Carry over confidence from analysis
                )

            # B. Handle Delegation/Execution
            elif hasattr(analysis, 'delegation') and analysis.delegation.should_delegate and analysis.delegation.delegation_targets:
                logger.info(f"[{request_id}] Executing delegation targets...") 

                # Determine execution order: use priority list if available, else order in targets
                target_keys_in_order = analysis.delegation.priority
                if not target_keys_in_order:
                    target_keys_in_order = [t.target_key for t in analysis.delegation.delegation_targets]
                    logger.warning(f"[{request_id}] No priority list found in analysis result. Executing targets in default order: {target_keys_in_order}")

                # Create a map for easy lookup - Ensure correct indentation
                targets_map = {t.target_key: t for t in analysis.delegation.delegation_targets}

                # Corrected indentation for loop and contents
                for target_key in target_keys_in_order:
                    target: Optional[DelegationTarget] = targets_map.get(target_key) # Add type hint
                    if not target:
                        logger.warning(f"[{request_id}] Target '{target_key}' from priority list not found in delegation_targets. Skipping.")
                        continue # Correctly indented continue

                    # Convert List[Param] to Dict for easier use
                    target_params_dict = params_to_dict(target.config_params)
                    logger.info(f"[{request_id}] Processing target ({target.target_type}): '{target.target_key}' with params: {target_params_dict}")

                    # Inner try/except for individual target execution
                    try:
                        if target.target_type == 'minion':
                            # Construct MinionDelegationRequest
                            minion_request = MinionDelegationRequest(
                                minion_key=target.target_key,
                                # Get task description from params if provided, else use intent
                                task_description=target_params_dict.get("task_description", analysis.intent.primary_intent),
                                # Pass all other params extracted by analysis
                                params=target_params_dict 
                            )
                            
                            # Delegate to Minion
                            minion_run_context = RunContext(
                                model="delegation_context", # Placeholder model name
                                usage={}, # Placeholder usage stats
                                prompt=prompt, # The original user prompt
                                deps=context # Pass the original run context dictionary as deps
                            )
                            
                            minion_result_dict = await self._delegate_task_to_minion(
                                context=minion_run_context, 
                                request=minion_request
                            )
                            
                            # Store result
                            all_results.append({
                                "target_key": target.target_key,
                                "target_type": "minion",
                                "status": "success" if "error" not in minion_result_dict else "error", # Infer status
                                "result_data": minion_result_dict.get("result"), 
                                "error": minion_result_dict.get("error")
                            })
                            if "error" in minion_result_dict:
                                logger.error(f"[{request_id}] Minion '{target.target_key}' execution failed: {minion_result_dict.get('error')}")
                                # Optional: Decide if we should stop execution 
                                # execution_error = f"Minion {target.target_key} failed."
                                # break 

                        elif target.target_type == 'ability':
                            # Construct AbilityRequest
                            ability_request = AbilityRequest(
                                ability_name=target.target_key,
                                parameters=target_params_dict, # Pass extracted params
                                # Add essential context metadata for the ability
                                metadata={'user_id': user_id, 'conversation_id': conversation_id, 'run_id': request_id} 
                            )
                            
                            # Execute Ability using AbilityRegistry
                            ability_response: AbilityResponse = await self.ability_registry.execute(ability_request)
                            
                            # Store result
                            all_results.append({
                                "target_key": target.target_key,
                                "target_type": "ability",
                                "status": ability_response.status,
                                "result_data": ability_response.data,
                                "error": ability_response.error
                            })
                            if ability_response.status == "error":
                                logger.error(f"[{request_id}] Ability '{target.target_key}' execution failed: {ability_response.error}")
                                # Optional: Decide if we should stop execution
                                # execution_error = f"Ability {target.target_key} failed."
                                # break 
                        else: # Moved inside the try block
                            logger.warning(f"[{request_id}] Unknown target_type '{target.target_type}' for target '{target.target_key}'. Skipping.")
                    except Exception as exec_err: # Correct indentation for the except block
                        err_msg = f"Error executing target '{target.target_key}' ({target.target_type}): {exec_err}"
                        logger.error(f"[{request_id}] {err_msg}", exc_info=True)
                        all_results.append({
                            "target_key": target.target_key,
                            "target_type": target.target_type,
                            "status": "error",
                            "result_data": None,
                            "error": err_msg
                        })
                        # Optional: Decide if we should stop execution
                        # execution_error = f"Execution failed for {target.target_key}."
                        # break 
                
                # Check for overall execution error after the loop
                if execution_error:
                    # Ensure analysis object exists before dumping
                    analysis_dump = analysis.model_dump() if analysis else {}
                    intent_str = analysis.intent.primary_intent if hasattr(analysis, 'intent') else 'unknown'
                    # Correct indentation for the return statement
                    return AgentExecutionResult(
                         success=False,
                         answer=f"Execution failed during delegation: {execution_error}",
                         error="ExecutionError",
                         run_id=request_id,
                         start_time=total_start,
                metadata={
                              "analysis": analysis_dump,
                              "execution_results": all_results,
                    "processing_time": time.time() - total_start,
                              "intent": intent_str
                          },
                          confidence=0.1 # Low confidence on execution failure
                    )
                # If loop completes without critical error, proceed to synthesis
            
            # C. Handle No Delegation Needed (Simple Response)
            else:
                # No delegation needed, and no clarification needed.
                logger.info(f"[{request_id}] No delegation required. Generating simple response (placeholder)...")
                # TODO: Implement simple response generation using synthesis agent?
                primary_intent = analysis.intent.primary_intent if hasattr(analysis, 'intent') else 'unknown'
                simple_response = f"Okay, I understand your intent seems to be '{primary_intent}'. How can I help further?" # Placeholder
                all_results.append({
                    "target_key": "simple_response",
                    "target_type": "internal",
                    "status": "success",
                    "result_data": simple_response,
                    "error": None
                })
                # Set confidence based on analysis confidence
                final_confidence = analysis.confidence if hasattr(analysis, 'confidence') else 0.6 
                final_answer = simple_response # Ensure final_answer is set here

            # --- REFACTOR END --- 

            # Step 3: Synthesize Final Response
            # Check if we should proceed with synthesis (no clarification, no simple response already generated)
            synthesis_needed = not execution_error and not (hasattr(analysis, 'intent') and analysis.intent.needs_clarification) and 'final_answer' not in locals()
            
            if synthesis_needed:
                 logger.info(f"[{request_id}] Step 3: Synthesizing final response...")
                 try:
                    # Prepare synthesis prompt input (Simplified construction)
                    intent_str = analysis.intent.primary_intent if hasattr(analysis, 'intent') else 'Unknown'
                    results_json = json.dumps(all_results, indent=2, default=str)
                    synthesis_prompt_parts = [
                        f"Original User Query: {prompt}",
                        f"Analysis Intent: {intent_str}",
                        f"Execution Results:\n{results_json}",
                        "\nSynthesize a final, helpful response to the user based on the query and the execution results.",
                        "If the results indicate an error or failure, acknowledge it appropriately."
                    ]
                    synthesis_prompt_input = "\n\n".join(synthesis_prompt_parts)

                    # Prepare dependencies for synthesis agent run
                    synthesis_deps = {
                    "request_id": request_id,
                        "db": self.db, 
                        "conversation_id": conversation_id, 
                        "user_id": user_id,
                        # Pass results and analysis if the agent needs them structured
                        "execution_results": all_results,
                        "analysis": analysis.model_dump() if analysis else None,
                        **context # Pass original context
                    }
                    
                    logger.debug(f"[{request_id}] Synthesis Agent Input Prompt:\n{synthesis_prompt_input}")
                    
                    # Ensure synthesis agent is available
                    if not self.synthesis_agent:
                        raise ValueError("Synthesis agent is not initialized.")
                        
                    # Run synthesis agent - Pass prompt as positional arg
                    synthesis_run_result = await self.synthesis_agent.run(
                        synthesis_prompt_input, 
                        deps=synthesis_deps
                    )
                    
                    raw_synthesis_output = None
                    if isinstance(synthesis_run_result, AgentRunResult):
                        # Prioritize .data if it exists and is meaningful (e.g., a structured object)
                        if hasattr(synthesis_run_result, 'data') and synthesis_run_result.data:
                            logger.info(f"[{request_id}] Using synthesis output from AgentRunResult.data (Type: {type(synthesis_run_result.data)})")
                            raw_synthesis_output = synthesis_run_result.data # Could be a string or a Pydantic model
                        # Fallback to .output if it's a non-empty string
                        elif hasattr(synthesis_run_result, 'output') and isinstance(synthesis_run_result.output, str) and synthesis_run_result.output.strip():
                            logger.info(f"[{request_id}] Using synthesis output from AgentRunResult.output")
                            raw_synthesis_output = synthesis_run_result.output
                        else:
                            logger.warning(f"[{request_id}] Synthesis AgentRunResult had neither useful .data nor .output. Result: {synthesis_run_result!r}")
                            raw_synthesis_output = str(synthesis_run_result) # Fallback to string representation
                    elif isinstance(synthesis_run_result, str):
                        # If the agent somehow returned a raw string directly
                         logger.info(f"[{request_id}] Synthesis agent returned a raw string.")
                         raw_synthesis_output = synthesis_run_result
                    else:
                        # Handle unexpected types
                         logger.warning(f"[{request_id}] Unexpected synthesis result type: {type(synthesis_run_result)}. Converting to string.")
                         raw_synthesis_output = str(synthesis_run_result)
                         
                    logger.info(f"[{request_id}] Raw Synthesis Output to be parsed: {str(raw_synthesis_output)[:200]}...")
                    # --- MODIFICATION END ---
                    
                    # Parse the synthesis output using PoseyResponse helper
                    posey_response = PoseyResponse.from_str(raw_synthesis_output)
                    final_answer = posey_response.answer
                    final_confidence = posey_response.confidence
                    # Merge metadata from synthesis response if any
                    final_metadata.update(posey_response.metadata) 
                    # TODO: Handle posey_response.sources and posey_response.memory_updates if needed
                    
                 except Exception as synth_err:
                      logger.error(f"[{request_id}] Error during synthesis: {synth_err}", exc_info=True)
                      final_answer = f"I processed the request regarding '{analysis.intent.primary_intent if hasattr(analysis, 'intent') else 'unknown'}' but encountered an issue synthesizing the final response." 
                      final_confidence = 0.3 # Lower confidence due to synthesis error
            
            elif 'final_answer' not in locals():
                 # Handle cases where synthesis wasn't needed but answer wasn't set (e.g., execution error handled earlier)
                 logger.warning(f"[{request_id}] Skipping synthesis, but final_answer not set. Using fallback error message.")
                 final_answer = "I encountered an issue while processing the results."
                 final_confidence = 0.2
            # If final_answer was set in Step 2 (e.g., simple response), we use that directly.

            # --- Final Result Construction --- 
            logger.info(f"[POSEY_RUN] Final answer: {final_answer[:150]}... (Confidence: {final_confidence:.2f})")
            total_time = time.time() - total_start
            logger.info(f"Posey execution completed in {total_time:.2f}s for request {request_id}")

            # Ensure analysis dump is safe even if analysis is None
            analysis_dump = analysis.model_dump() if analysis else None

            return AgentExecutionResult(
                success=True, 
                answer=final_answer,
                result_type="success",
                run_id=request_id,
                start_time=total_start,
                end_time=time.time(),
                duration=total_time,
                metadata={
                    "analysis": analysis_dump,
                    "execution_results": all_results,
                    "processing_time": total_time,
                    "intent": analysis.intent.primary_intent if hasattr(analysis, 'intent') else 'unknown',
                     **final_metadata # Merge any other relevant metadata collected
                },
                confidence=final_confidence
            )

        # Add main exception handler for the entire run method
        except Exception as e:
            total_time = time.time() - total_start
            logger.error(f"[POSEY_RUN] Unhandled error in Posey execution after {total_time:.2f}s: {e}", exc_info=True)
            
            # Return error result
            return AgentExecutionResult(
                success=False,
                answer=f"I encountered an unexpected error while processing your request: {str(e)}",
                error="UnhandledException",
                run_id=request_id,
                start_time=total_start,
                end_time=time.time(),
                duration=total_time,
                metadata={
                    "status": "error",
                    "error_message": str(e),
                    "traceback": traceback.format_exc().splitlines() # Include traceback
                },
                confidence=0.0
            )
        
    # --- End of run method ---

    async def run_with_messages(self, messages: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """Execute the orchestration pipeline with message-based input"""
        # Get the latest user message as the prompt
        prompt = get_last_user_message(messages)
        if not prompt:
            raise ValueError("No user messages found in the provided messages list")
        
        # Update context with messages
        context = context or {}
        context["messages"] = messages
        
        # Call the main run method
        return await self.run(prompt, context)
