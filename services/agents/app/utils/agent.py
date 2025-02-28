from typing import TypedDict, List, Dict, Any, TypeVar, Optional
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from langgraph.graph import Graph
import json
from dataclasses import asdict

from app.utils.prompt_helpers import getSystemPrompt
from app.utils.ability_utils import execute_ability
from app.config import logger
from app.config.defaults import LLM_CONFIG, OLLAMA_URL
import httpx
from app.utils.result_types import AgentExecutionResult  # Import from the new module

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

def create_agent(
    agent_type: str, 
    abilities: List[str],
    provider: str = LLM_CONFIG['default']['provider'],
    model: str = LLM_CONFIG['default']['model']
) -> Agent:
    """Create a PydanticAI agent with specified abilities"""
    
    logger.info(f"Creating agent of type '{agent_type}' with provider '{provider}' and model '{model}'")
    logger.info(f"Abilities to register: {abilities}")
    
    system_prompt = f"""You are a specialized {agent_type} agent with the following abilities: {', '.join(abilities)}.
    Use these abilities when appropriate to accomplish tasks.
    Always think through your actions carefully and explain your reasoning.
    
    When responding to users, provide clear, helpful answers in natural language.
    If you're not using any specific format, just respond conversationally.
    Only use JSON or other special formats when specifically instructed to do so."""
    
    try:
        if provider == "ollama":
            from pydantic_ai.models.openai import OpenAIModel
            
            # Log Ollama connection details
            logger.info(f"Configuring Ollama connection to {OLLAMA_URL}")
            # Create OpenAI-compatible model for Ollama
            ollama_model_name = model
            model = OpenAIModel(
                model_name=ollama_model_name, # Use explicit Ollama model name
                base_url=OLLAMA_URL
            )
            logger.info(f"Created Ollama model configuration with model name: {ollama_model_name}")
            logger.info(f"Created Ollama model configuration: {model}")
            
            agent = Agent(
                model,
                system_prompt=system_prompt,
                deps_type=dict,
                result_type=AgentExecutionResult
            )
        else:
            # Standard provider:model format for other providers
            model_string = f"{provider}:{model}"
            logger.info(f"Creating agent with model string: {model_string}")
            
            agent = Agent(
                model_string,
                system_prompt=system_prompt,
                deps_type=dict,
                result_type=AgentExecutionResult
            )

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
            
        logger.info("Successfully created agent with all abilities registered")
        return agent
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        logger.info(f"Falling back to default {LLM_CONFIG['default']['provider']} model")
        return Agent(
            f"{LLM_CONFIG['default']['provider']}:{LLM_CONFIG['default']['model']}",
            system_prompt=system_prompt,
            deps_type=dict,
            result_type=AgentExecutionResult
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
