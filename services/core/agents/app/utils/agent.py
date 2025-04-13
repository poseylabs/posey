from typing import TypedDict, List, Dict, Any, TypeVar, Optional
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from langgraph.graph import Graph
import json
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db

from app.utils.prompt_helpers import getSystemPrompt
from app.utils.ability_utils import execute_ability
from app.config import logger
from app.config.defaults import LLM_CONFIG, OLLAMA_URL
from app.config.llm_loader import get_llm_config_from_db, LLMDatabaseConfig
import httpx
from app.utils.result_types import AgentExecutionResult

__all__ = ['create_agent', 'run_agent_with_messages']

T = TypeVar('T')

def rally_minions(minions: List[str]) -> None:
    """Adds a list of minions (tools) to the given agent.

    Args:
        boss: The agent to add minions to.
        minions: A list of minion names to add.
    """
    # Import get_minions here to avoid circular imports
    from app.utils.minion import get_minions
    available_minions = get_minions()
    selected_minions = []

    for minion in available_minions:
        if minion in minions:
            selected_minions.append(available_minions[minion])

    return selected_minions

class AgentFactory(TypedDict):
    agent: Agent
    Response: type[BaseModel]
    graph: Graph

def agentFactory(agent_name: str, minion_names: List[str]) -> AgentFactory:
    """Creates and configures an agent with specified minions.

    Args:
        agent_name: The name of the agent.
        minion_names: A list of minion names to equip the agent with.

    Returns:
        AgentFactory: A dictionary containing the configured agent,
                      its response model, and the associated graph.
    """
    graph = Graph()

    class Response(BaseModel):
        answer: str
        confidence: float = 0.0

    system_prompt = getSystemPrompt(agent_name)

    tools = rally_minions(minion_names)

    # Create agent with tools
    boss = Agent(
        f"{LLM_CONFIG['default']['provider']}:{LLM_CONFIG['default']['model']}",
        system_prompt=system_prompt,
        tools=tools  # Pass tools during initialization
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
    abilities: List[str],
    db: AsyncSession,
    config_key: Optional[str] = None,
) -> Agent:
    """Create a PydanticAI agent with specified abilities, loading config from DB."""

    # Use agent_type as default config_key if not provided
    resolved_config_key = config_key or agent_type
    logger.info(f"Attempting to create agent of type '{agent_type}' using config key '{resolved_config_key}'")

    # 1. Try loading config from DB (with fallback to 'default' key within the function)
    db_llm_config: Optional[LLMDatabaseConfig] = await get_llm_config_from_db(db, resolved_config_key)

    # 2. Determine final config (DB or Hardcoded Fallback)
    final_config: Dict[str, Any]
    if db_llm_config:
        logger.info(f"Using LLM configuration from database for key '{db_llm_config.config_key}'")
        # Convert Pydantic model to dict for easier use
        final_config = db_llm_config.model_dump()
        # Add capabilities field expected by Agent instantiation?
        # This depends on how pydantic-ai Agent uses params.
        # For now, let's assume separate handling for tools/abilities
        final_config['provider'] = db_llm_config.provider_name
        final_config['model'] = db_llm_config.model_slug
        final_config['base_url'] = db_llm_config.api_base_url
        # Store model parameters separately
        final_config['model_params'] = {
            "temperature": db_llm_config.temperature,
            "max_tokens": db_llm_config.max_tokens,
            "top_p": db_llm_config.top_p,
            "frequency_penalty": db_llm_config.frequency_penalty,
            "presence_penalty": db_llm_config.presence_penalty,
            **(db_llm_config.additional_settings or {}),
        }
    else:
        logger.warning(
            f"Could not load config for key '{resolved_config_key}' (or default) from DB. "
            f"Falling back to hardcoded defaults."
        )
        # Use the 'fallback' or 'default' entry from the hardcoded config
        hardcoded_fallback_config = LLM_CONFIG.get('fallback', LLM_CONFIG['default'])
        final_config = hardcoded_fallback_config.copy()
        # Add model_params for consistency
        # Ensure all relevant params are included
        final_config['model_params'] = {
            k: v for k, v in final_config.items()
            if k not in ['provider', 'model', 'capabilities'] # Removed base_url here as well
        }

    logger.info(f"Final config resolved: Provider='{final_config['provider']}', Model='{final_config['model']}'")
    logger.debug(f"Final model params: {final_config['model_params']}")

    # Prepare System Prompt (no change needed)
    system_prompt = f"""You are a specialized {agent_type} agent with the following abilities: {', '.join(abilities)}.
    Use these abilities when appropriate to accomplish tasks.
    Always think through your actions carefully and explain your reasoning.
    
    When responding to users, provide clear, helpful answers in natural language.
    If you're not using any specific format, just respond conversationally.
    Only use JSON or other special formats when specifically instructed to do so."""
    
    # 3. Instantiate Agent based on final_config
    try:
        provider = final_config['provider']
        model_name = final_config['model']
        model_params = final_config['model_params'].copy() # Copy to avoid modifying original

        # Construct the model identifier string
        model_identifier = f"{provider}:{model_name}"
        logger.info(f"Using model identifier: {model_identifier}")

        # Special handling for Ollama base_url - add it to params if present
        if provider == "ollama":
            ollama_base_url = final_config.get('base_url', OLLAMA_URL)
            if ollama_base_url:
                logger.info(f"Adding Ollama base_url to model params: {ollama_base_url}")
                model_params['base_url'] = ollama_base_url

        # Instantiate Agent directly with the model identifier string and parameters
        logger.info(f"Instantiating Agent with identifier '{model_identifier}' and params: {model_params}")
        agent = Agent(
            model_identifier,
            system_prompt=system_prompt,
            deps_type=dict,
            result_type=AgentExecutionResult,
            **model_params # Pass parameters directly to the agent
        )
        logger.info(f"Successfully created agent instance for type '{agent_type}'")

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

                # Create a context with the messages and required parameters
                context = RunContext[Dict[str, Any]](
                    model="unknown",  # Placeholder value
                    usage={},         # Empty usage stats
                    prompt=last_user_message,
                    deps={"messages": messages}
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
                return execute_specific_ability
            
            try:
                agent.tool()(create_ability_function(ability))
                logger.debug(f"Successfully registered tool '{tool_name}'")
            except Exception as e:
                logger.error(f"Failed to register tool '{tool_name}': {e}", exc_info=True)
                raise
            
        logger.info("Successfully created and configured agent for type '{agent_type}'")
        return agent

    except Exception as e:
        logger.error(f"Error creating agent instance: {e}", exc_info=True)
        logger.error("Falling back to absolute hardcoded default agent due to instantiation error.")
        # Ultimate fallback if instantiation fails even with loaded config
        fallback_provider = LLM_CONFIG['fallback']['provider']
        fallback_model = LLM_CONFIG['fallback']['model']
        fallback_model_string = f"{fallback_provider}:{fallback_model}"
        # Extract fallback params
        fallback_params = {
            k: v for k, v in LLM_CONFIG['fallback'].items()
            if k not in ['provider', 'model', 'capabilities']
        }
        # Add ollama base_url if provider is ollama
        if fallback_provider == "ollama":
             fallback_params['base_url'] = LLM_CONFIG['fallback'].get('base_url', OLLAMA_URL)
            
        logger.info(f"Creating fallback agent with identifier: {fallback_model_string} and params: {fallback_params}")
        return Agent(
            fallback_model_string,
            system_prompt=system_prompt,
            deps_type=dict,
            result_type=AgentExecutionResult,
            **fallback_params # Pass fallback parameters
        )

def serialize_context(obj: Any) -> Any:
    """Helper function to serialize RunContext and other complex objects"""
    if isinstance(obj, RunContext):
        return asdict(obj.state)  # Convert RunContext to dict
    elif isinstance(obj, BaseModel):
        return obj.dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return obj

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
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Run an agent with a list of messages.
    
    This is a utility function that can be used by any component (orchestrator or minion)
    to run an agent with a message-based conversation rather than a single prompt.
    
    Args:
        agent: The agent to run
        messages: List of message objects with 'role' and 'content' keys
        context: Optional context to pass to the agent
        
    Returns:
        The result from the agent
    """
    logger.info(f"Running agent with {len(messages)} messages")
    
    # Log the messages (but limit to latest few to avoid excessive logging)
    from app.utils.message_handler import log_messages
    log_messages(messages[-3:] if len(messages) > 3 else messages)
    
    # Additional enhanced message logging - log all messages in full detail
    logger.info("=" * 80)
    logger.info("FULL MESSAGES BEING SENT TO LLM:")
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        logger.info(f"--- MESSAGE {i+1} ({role}) ---")
        logger.info(content)
        logger.info("-" * 40)
    logger.info("=" * 80)
    
    # Log system prompt specifically
    system_msgs = [msg for msg in messages if msg.get("role") == "system"]
    if system_msgs and hasattr(agent, "_system_prompt"):
        logger.info("AGENT SYSTEM PROMPT CHECK:")
        logger.info(f"From messages: {system_msgs[0].get('content', '')[:200]}...")
        logger.info(f"From agent._system_prompt: {agent._system_prompt[:200]}...")
        
    # Check if the agent has our helper method (should be added by create_agent)
    if hasattr(agent, 'run_with_messages'):
        # If context is None, use an empty dict
        context_dict = context or {}
        return await agent.run_with_messages(messages, **context_dict)
    else:
        # Fall back to creating a RunContext and running the agent with it
        from pydantic_ai import RunContext
        
        # Extract the last user message as the prompt
        from app.utils.message_handler import get_last_user_message
        prompt = get_last_user_message(messages) or ""
        
        # Create a context with the messages
        run_context = RunContext[Dict[str, Any]](deps={"messages": messages})
        
        # Add any additional context
        if context:
            for key, value in context.items():
                run_context.deps[key] = value
        
        # Use the run method with the context - passing deps as a keyword argument
        return await agent.run(prompt, **{"deps": run_context.deps})
