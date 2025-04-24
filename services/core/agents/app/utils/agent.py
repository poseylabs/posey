from typing import TypedDict, List, Dict, Any, TypeVar, Optional, Type
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from langgraph.graph import Graph
import json
from dataclasses import asdict, replace
import logging
import pprint

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.utils.minion_registry import MinionRegistry

from app.utils.prompt_helpers import getSystemPrompt
from app.utils.ability_utils import execute_ability
from app.config import logger
from app.config.defaults import LLM_CONFIG, OLLAMA_URL
from app.config.llm_loader import get_llm_config_from_db, LLMDatabaseConfig
from app.config.prompts import PromptLoader
from app.minions.base import BaseMinion
import httpx
from app.utils.result_types import AgentExecutionResult
from pydantic_ai.models import ModelRequestParameters
from app.db.models import MinionLLMConfig
from app.models.analysis import ContentAnalysis
from pydantic_ai.models.gemini import GeminiModel

__all__ = ['create_agent', 'run_agent_with_messages']

T = TypeVar('T')

async def rally_minions(minion_names: List[str], registry: MinionRegistry, db: AsyncSession) -> List[BaseMinion]:
    """Gets instantiated minion objects based on a list of names."""
    
    # Get all *currently available* minion instances from the registry
    # This ensures they are loaded and set up
    available_minion_instances = await registry.get_minions(db)
    selected_minions = []

    for name in minion_names:
        if name in available_minion_instances:
            selected_minions.append(available_minion_instances[name])
        else:
            logger.warning(f"Minion '{name}' requested for rallying was not found in active instances.")
            # Optionally raise error or just skip

    return selected_minions

class AgentFactory(TypedDict):
    agent: Agent
    Response: type[BaseModel]
    graph: Graph

# Note: This factory seems less relevant now create_agent handles DB config loading.
# Consider refactoring or removing if agent creation logic is centralized in create_agent.
async def agentFactory(agent_name: str, minion_names: List[str], registry: MinionRegistry, db: AsyncSession) -> AgentFactory:
    """Creates and configures an agent with specified minions."""
    graph = Graph()

    class Response(BaseModel):
        answer: str
        confidence: float = 0.0

    system_prompt = getSystemPrompt(agent_name) # Assuming getSystemPrompt is still valid

    # Rally minions using the async function
    tools = await rally_minions(minion_names, registry, db)

    # Create agent with tools - This might conflict with create_agent's config logic
    # Using hardcoded fallback here as an example, but needs alignment
    boss = Agent(
        f"{LLM_CONFIG['fallback']['provider']}:{LLM_CONFIG['fallback']['model']}",
        system_prompt=system_prompt,
        tools=tools
    )

    return {
        "agent": boss,
        "Response": Response,
        "graph": graph
    }

async def test_ollama_connection(url: str) -> bool:
    """Test Ollama connection"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/api/health")
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {str(e)}")
        return False

async def create_agent(
    agent_type: str,
    abilities: List[Dict[str, Any]],
    db: AsyncSession,
    config: Optional[Dict[str, Any]] = None,
    result_type: Optional[Type[BaseModel]] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
    db_llm_config_orm: Optional[MinionLLMConfig] = None,
    available_abilities_list: Optional[List[Dict[str, Any]]] = None
) -> Agent:
    """Create a PydanticAI agent. 
    
    Uses user preferences for orchestrator types, 
    DB config for minions (falling back to defaults).
    Accepts pre-fetched available abilities list.
    """

    # Define orchestrator types that use user preferences
    orchestrator_types = ["orchestrator", "synthesis"]

    # Use agent_type as default config_key if not provided
    resolved_config_key = config or agent_type
    logger.info(f"Attempting to create agent of type '{agent_type}' using config key '{resolved_config_key}'")

    db_llm_config: Optional[LLMDatabaseConfig] = None
    final_config: Dict[str, Any] = None
    config_source: str = "unknown"

    # 1. Determine configuration source based on agent type
    if db_llm_config_orm:
        logger.info(f"Using provided ORM LLM configuration for '{agent_type}' (Key: {db_llm_config_orm.config_key}).")
        # Validation: Ensure relationships are loaded (should be guaranteed by PoseyAgent.create)
        if not db_llm_config_orm.llm_model or not db_llm_config_orm.llm_model.provider:
            logger.error(f"Provided ORM config for '{db_llm_config_orm.config_key}' is missing loaded relationships! This is unexpected.")
            raise ValueError(f"Provided ORM config for {db_llm_config_orm.config_key} lacks relationships.")

        final_config = {
            'provider': db_llm_config_orm.llm_model.provider.slug,
            'model': db_llm_config_orm.llm_model.model_id,
            'base_url': getattr(db_llm_config_orm.llm_model.provider, 'api_base_url', None),
            'model_params': {
                "temperature": getattr(db_llm_config_orm, 'temperature', 0.7),
                "max_tokens": getattr(db_llm_config_orm, 'max_tokens', 1000),
                "top_p": getattr(db_llm_config_orm, 'top_p', 0.95),
                "frequency_penalty": getattr(db_llm_config_orm, 'frequency_penalty', 0.0),
                "presence_penalty": getattr(db_llm_config_orm, 'presence_penalty', 0.0),
                **(db_llm_config_orm.additional_settings or {}),
            }
        }
        config_source = f"provided_orm (key: {db_llm_config_orm.config_key})"
    elif agent_type in orchestrator_types:
        logger.info(f"Agent type '{agent_type}' identified as orchestrator. Checking user preferences...")
        preferred_provider = user_preferences.get("preferred_provider") if user_preferences else None
        preferred_model = user_preferences.get("preferred_model") if user_preferences else None

        if preferred_provider and preferred_model:
            logger.info(f"Found provider '{preferred_provider}' and model '{preferred_model}' in user preferences.")
            # Use hardcoded defaults for other parameters for now
            default_params = LLM_CONFIG.get('default', {})
            final_config = {
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
                 # Base URL might be needed for Ollama, etc. - check provider?
                 # For now, assume standard providers or check hardcoded defaults later
                 'base_url': LLM_CONFIG.get(preferred_provider, {}).get('base_url') or default_params.get('base_url')
            }
            config_source = "user_preferences"
        else:
            logger.warning(f"Provider/Model not found or incomplete in user preferences for '{agent_type}'. Falling back to hardcoded defaults.")
            # Fallback handled below

    else: # Assume it's a minion if not an orchestrator type and no ORM config provided
        logger.info(f"Agent type '{agent_type}' identified as minion. No ORM config provided, checking database...")
        # Try loading config from DB (with fallback to 'default' key within the function)
        db_llm_config = await get_llm_config_from_db(db, resolved_config_key)
        if db_llm_config:
            logger.info(f"Using LLM configuration from database for key '{db_llm_config.config_key}'")
            final_config = db_llm_config.model_dump()
            final_config['provider'] = db_llm_config.provider_slug
            final_config['model'] = db_llm_config.model_id
            final_config['base_url'] = getattr(db_llm_config.llm_model.provider, 'api_base_url', None)
            final_config['model_params'] = {
                "temperature": getattr(db_llm_config, 'temperature', 0.7),
                "max_tokens": getattr(db_llm_config, 'max_tokens', 1000),
                "top_p": getattr(db_llm_config, 'top_p', 0.95),
                "frequency_penalty": getattr(db_llm_config, 'frequency_penalty', 0.0),
                "presence_penalty": getattr(db_llm_config, 'presence_penalty', 0.0),
                **(db_llm_config.additional_settings or {}),
            }
            config_source = f"database (key: {db_llm_config.config_key})"
        else:
            logger.warning(f"Could not load config for minion '{agent_type}' (key '{resolved_config_key}') from DB. Falling back to hardcoded defaults.")
            # Fallback handled below

    # 2. Handle Fallback if config wasn't determined yet
    if not final_config:
        logger.warning(f"Using hardcoded default LLM configuration for '{agent_type}'.")
        hardcoded_fallback_config = LLM_CONFIG.get('fallback', LLM_CONFIG['default'])
        final_config = hardcoded_fallback_config.copy()
        # Ensure 'model_params' exists for consistency
        final_config['model_params'] = {
            k: v for k, v in final_config.items()
            if k not in ['provider', 'model', 'capabilities', 'base_url'] # Added base_url exclusion
        }
        # If base_url was in the hardcoded config, keep it
        if 'base_url' in hardcoded_fallback_config:
            final_config['base_url'] = hardcoded_fallback_config['base_url']
        config_source = "hardcoded_default"


    logger.info(f"Final config resolved (Source: {config_source}): Provider='{final_config['provider']}', Model='{final_config['model']}'")
    logger.debug(f"Final model params: {final_config['model_params']}")

    # --- Prepare System Prompt using PromptLoader --- 
    try:
        prompt_loader = PromptLoader()
        # Load the full prompt config using the resolved_config_key (e.g., 'posey')
        logger.debug(f"Loading prompt config using resolved key: {resolved_config_key}")
        agent_prompts = prompt_loader.get_prompt_with_shared_config(resolved_config_key)
        
        # --- Construct full system prompt --- 
        system_sections = agent_prompts.get('system', {})
        base = system_sections.get('base', f'Default prompt for {agent_type}')
        capabilities = "\n".join(system_sections.get('capabilities', []))
        guidelines = "\n".join(system_sections.get('guidelines', []))
        abilities_template = system_sections.get('abilities_template', "Available Abilities:\n{abilities_json}")
        critical_instructions = "\n".join(system_sections.get('critical_instructions', []))
        response_instruction = system_sections.get('response_instruction', 'Provide a structured response.')

        # --- USE PRE-FETCHED ABILITIES LIST --- 
        # Use the passed-in list if available, otherwise fetch as a fallback (though ideally it should always be passed)
        if available_abilities_list is None:
            logger.warning(f"available_abilities_list not provided to create_agent for '{agent_type}'. Fetching fallback.")
            # Call the static method via BaseMinion class (synchronously)
            _abilities_list_internal = BaseMinion.fetch_available_abilities()
        else:
             _abilities_list_internal = available_abilities_list

        abilities_json = json.dumps(_abilities_list_internal, indent=2)
        abilities_section = abilities_template.format(abilities_json=abilities_json)
        # --- END USE PRE-FETCHED --- 

        # Assemble the full prompt (simplified version, adjust as needed)
        # IMPORTANT: We are OMITTING the context_template here because create_agent doesn't have dynamic request context
        system_prompt = f"""{base}

Capabilities:
{capabilities}

Guidelines:
{guidelines}

{abilities_section}

CRITICAL INSTRUCTIONS:
{critical_instructions}

{response_instruction}"""
        # --- End construction ---
        logger.info(f"Successfully loaded and constructed system prompt for config key '{resolved_config_key}' (agent type '{agent_type}')")
        logger.debug(f"System prompt being used for '{agent_type}':\n---\n{system_prompt}\n---")
    except Exception as e:
        # Use resolved_config_key in the error message as well
        logger.error(f"Failed to load or construct system prompt for config key '{resolved_config_key}' (agent type '{agent_type}'): {e}. Falling back to simple prompt.")
        system_prompt = f"You are a helpful AI assistant functioning as a {agent_type}." 
    # --- End System Prompt Preparation ---
    
    # 3. Instantiate Agent based on final_config
    try:
        # Use provider and model from final_config
        provider_slug = final_config['provider']
        model_id = final_config['model']
        model_params = final_config['model_params'].copy()

        # Construct the model identifier string using slug
        model_identifier = f"{provider_slug}:{model_id}"
        logger.info(f"Using model identifier: {model_identifier}")

        # Special handling for Ollama base_url
        if provider_slug == "ollama":
            # Prioritize final_config base_url (from DB or hardcoded default)
            ollama_base_url = final_config.get('base_url', OLLAMA_URL)
            if ollama_base_url:
                logger.info(f"Adding Ollama base_url to model params: {ollama_base_url}")
                model_params['base_url'] = ollama_base_url
            else:
                logger.warning("Ollama provider specified but no base_url found in config or defaults.")

        # Instantiate Agent (Single block, handles all providers initially)
        logger.info(f"Instantiating Agent with identifier '{model_identifier}' and model settings: {model_params}")
        agent = Agent(
            model_identifier,
            system_prompt=system_prompt,
            deps_type=Dict[str, Any],
            result_type=result_type,
            model_settings=model_params
        )
        logger.info(f"Initial Agent instance created for type '{agent_type}' with model identifier '{model_identifier}'")

        # Add helper method for message-based communication
        async def run_with_messages(self, messages: List[Dict[str, str]], **kwargs):
            """Run the agent with a list of messages instead of a single prompt
            
            Args:
                messages: List of message objects with 'role' and 'content' keys
                
            Returns:
                The result from the model
            """
            # Use the model's native message support if available
            if hasattr(self.model, 'run_messages'):
                return await self.model.run_messages(messages, **kwargs)
            else:
                # Otherwise, build context with messages and use the standard run
                from pydantic_ai import RunContext

                # Extract the last user message as the prompt
                last_user_message = next((msg["content"] for msg in reversed(messages) 
                                         if msg["role"] == "user"), "")
                
                # Ensure all messages have content (Anthropic API requires this)
                sanitized_messages = []
                for msg in messages:
                    if not msg.get("content"):
                        # Skip empty content messages or add placeholder content
                        msg_copy = msg.copy()
                        msg_copy["content"] = " " # Minimal placeholder content
                        sanitized_messages.append(msg_copy)
                    else:
                        sanitized_messages.append(msg)

                # Create a context with the messages and required parameters
                context = RunContext[Dict[str, Any]](
                    model=getattr(self, "_model_identifier", model_identifier),
                    usage={},         # Empty usage stats
                    prompt=last_user_message,
                    deps={"messages": sanitized_messages}
                )

                # Use the run method with the context - passing context.deps through kwargs instead of as positional arg
                return await self.run(last_user_message, **{"deps": context.deps, **kwargs})

        # Attach the helper method to the agent instance
        agent.run_with_messages = run_with_messages.__get__(agent, agent.__class__)

        # Register abilities
        logger.info("Registering abilities as tools...")
        for ability in abilities:
            tool_name = ability.lower().replace(' ', '_').replace('-', '_')
            logger.debug(f"Registering ability '{ability}' as tool '{tool_name}'")
            
            def create_ability_function(ability_name: str):
                async def execute_specific_ability(ctx: RunContext[dict], **parameters) -> Dict[str, Any]:
                    try:
                        logger.debug(f"Executing ability '{ability_name}' with parameters: {parameters}")
                        result = await execute_ability(ability_name, **parameters)
                        
                        logger.debug(f"Ability '{ability_name}' execution result: {result}")
                        serialized_result = json.loads(json.dumps(result, default=serialize_context))
                        return serialized_result
                        
                    except Exception as e:
                        logger.error(f"Error executing ability {ability_name}: {e}", exc_info=True)
                        return {
                            "status": "error",
                            "error": str(e)
                        }
                
                execute_specific_ability.__name__ = tool_name
                execute_specific_ability.__doc__ = f"Executes the {ability_name} ability with provided parameters."
                return execute_specific_ability

            # Register the dynamically created function
            # Use the actual function object, pydantic-ai uses __name__ and __doc__
            agent.tool()(create_ability_function(ability))

        logger.info(f"Successfully created and configured agent for type '{agent_type}'")
        return agent

    except Exception as e:
        logger.critical(f"Failed to instantiate pydantic_ai.Agent for type '{agent_type}' with identifier '{model_identifier if 'model_identifier' in locals() else 'unknown'}': {e}", exc_info=True)
        raise ValueError(f"Could not create agent for {agent_type}. Error: {e}") from e

def serialize_context(obj):
    """Custom serializer for context objects that might not be JSON serializable"""
    if isinstance(obj, RunContext):
        # Assuming RunContext has a dict() or model_dump() method
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            return obj.dict()
    elif hasattr(obj, '__dict__'):
        # Fallback for other objects
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    try:
        # Default JSON encoder will handle basic types
        # Let it raise TypeError for unserializable types
        return json.JSONEncoder().default(obj)
    except TypeError:
        return f"<<unserializable: {type(obj).__name__}>>"

async def handle_tool_response(self, tool_name: str, tool_result: Dict[str, Any]) -> str:
    """Format tool result for Claude's expected format"""
    # Serialize the tool result properly
    serialized_result = json.dumps(tool_result, default=serialize_context)
    return f"""<tool_result>{serialized_result}</tool_result>
    
Based on the {tool_name} results above, I'll continue with my response:
"""

async def process_message(self, message: str, tool_results: List[Dict[str, Any]] = None) -> str:
    """Process message and include any tool results at the start"""
    if tool_results:
        # Add tool results at the beginning of the message
        tool_result_blocks = []
        for result in tool_results:
            # Serialize each result properly
            serialized_result = json.dumps(result, default=serialize_context)
            tool_result_blocks.append(f"<tool_result>{serialized_result}</tool_result>")
        
        message = f"""{''.join(tool_result_blocks)}

{message}"""
    
    return message

async def run_agent_with_messages(
    agent: Agent,
    messages: List[Dict[str, str]],
    deps: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AgentExecutionResult:
    """Run the agent with a list of messages, ensuring compatibility."""
    
    logger.debug(f"Running agent {type(agent).__name__} with {len(messages)} messages.")
    
    # Check if the agent instance has our custom run_with_messages method
    if hasattr(agent, 'run_with_messages') and callable(agent.run_with_messages):
        logger.debug("Using attached run_with_messages helper method.")
        result = await agent.run_with_messages(messages, deps=deps, **kwargs)
    else:
        # Fallback: Use the standard run method with the last user prompt
        logger.warning("run_with_messages method not found on agent. Using standard run with last user prompt.")
        last_user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
        if not last_user_message:
            logger.error("No user message found in history for standard run.")
            return AgentExecutionResult(answer="Error: No user message found.", confidence=0.0)
        
        # Construct RunContext manually if needed by the standard run method
        # This might vary depending on pydantic-ai version and agent setup
        run_context = RunContext[Dict[str, Any]](
            model=getattr(agent, "_model_identifier", "unknown"),
            usage={}, 
            prompt=last_user_message,
            deps=deps or {}
        )
        # Add message history to deps if not already present
        if 'messages' not in run_context.deps:
            run_context.deps['messages'] = messages
            
        result = await agent.run(last_user_message, deps=run_context.deps, **kwargs)

    # Ensure the result is in AgentExecutionResult format
    if isinstance(result, AgentExecutionResult):
        return result
    elif isinstance(result, str):
        # If we just get a string, wrap it
        logger.warning("Agent returned a raw string. Wrapping in AgentExecutionResult.")
        return AgentExecutionResult(answer=result, confidence=0.8) # Assign default confidence
    elif hasattr(result, 'answer'):
        # If it looks like it has the right field, try creating from it
        logger.warning("Agent returned an object with 'answer'. Wrapping in AgentExecutionResult.")
        return AgentExecutionResult(
            answer=result.answer,
            confidence=getattr(result, 'confidence', 0.8),
            metadata=getattr(result, 'metadata', {})
        )
    else:
        # Fallback for unknown result types
        logger.error(f"Agent returned unexpected result type: {type(result)}. Converting to string.")
        return AgentExecutionResult(answer=str(result), confidence=0.1)

# --- DEBUGGING SUBCLASS ---
class DebuggingGeminiModel(GeminiModel):
    """Subclass of GeminiModel to intercept and log the schema before simplification."""
    def customize_request_parameters(
        self, model_request_parameters: ModelRequestParameters
    ) -> ModelRequestParameters:
        """Override to log the schema before calling the original method."""
        logger.info(">>> DEBUGGING GEMINI SCHEMA <<<")
        # Log the schema for the result_tool (which causes the issue)
        if model_request_parameters.result_tools:
            for tool in model_request_parameters.result_tools:
                try:
                    schema_to_log = getattr(tool, 'parameters_json_schema', None)
                    if schema_to_log:
                        logger.info(f"Schema for tool '{getattr(tool, 'name', 'UNKNOWN')}':")
                        # Use pprint for better readability of complex dicts
                        pretty_schema = pprint.pformat(schema_to_log, indent=2)
                        logger.info(pretty_schema)
                    else:
                        logger.info(f"Tool '{getattr(tool, 'name', 'UNKNOWN')}' has no parameters_json_schema.")
                except Exception as log_e:
                    logger.error(f"Error logging schema for tool: {log_e}")
        else:
            logger.info("No result_tools found in request parameters.")
        logger.info(">>> END DEBUGGING GEMINI SCHEMA <<<")
        
        # Call the original method AFTER logging
        # Note: We still expect this to potentially raise the error,
        # but now we'll have the schema logged just before it does.
        return super().customize_request_parameters(model_request_parameters)

# --- END DEBUGGING SUBCLASS ---
