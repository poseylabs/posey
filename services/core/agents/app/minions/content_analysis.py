from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import RunContext, Agent
from app.utils.result import AgentResult
from app.utils.agent import run_agent_with_messages
from app.utils.message_handler import prepare_system_user_messages, extract_messages_from_context, get_last_user_message
from app.config import logger
from app.config.prompts.base import ( generate_base_prompt, get_default_context, BasePromptContext, UserContext, MemoryContext, SystemContext )
from app.config.defaults import LLM_CONFIG
import json
import time
from datetime import datetime
import pytz
from app.models.analysis import ContentAnalysis, ContentIntent, DelegationConfig
from app.minions.base import BaseMinion
import traceback
from app.config.abilities import AbilityRegistry

class ContentAnalysisMinion(BaseMinion):
    """Content Analysis Minion - analyzes content, determines intent and required abilities"""

    def __init__(self):
        super().__init__(
            name="content_analysis",
            description="Analyze user requests to determine intent and required abilities"
        )

    def setup(self):
        """Initialize minion-specific components"""
        # Create agent with content analysis result type
        self.agent = self.create_agent(result_type=ContentAnalysis, model_key="reasoning")
        logger.info(f"Content analysis agent initialized with model: {LLM_CONFIG['reasoning']['model']}")

    def create_prompt_context(self, context: Dict[str, Any], analysis_data: Dict[str, Any] = None) -> BasePromptContext:
        """Create a properly structured prompt context for content analysis operations
        
        Args:
            context: The raw context dictionary
            analysis_data: Additional analysis-specific data to include in the context
            
        Returns:
            A BasePromptContext object with user, memory, and system contexts
        """
        # Extract user information from context
        user_id = context.get("user_id", "anonymous")
        user_name = context.get("user_name", "User")
        
        # Get current time in user's timezone or UTC
        user_tz = context.get('timezone', 'UTC')
        try:
            now = datetime.now(pytz.timezone(user_tz))
        except:
            now = datetime.now()
        
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Extract location info
        location_info = "Unknown"
        if context.get('system', {}).get('location'):
            loc = context['system']['location']
            if loc.get('city') and loc.get('country'):
                location_info = f"{loc.get('city', '')}, {loc.get('region', '')}, {loc.get('country', '')}"
        
        # Create user context
        user_context = UserContext(
            id=user_id,
            name=user_name,
            preferences=context.get("preferences", {}),
            location=location_info,
            timezone=user_tz
        )
        
        # Create memory context
        memory_context = MemoryContext(
            recent_memories=context.get("recent_memories", []),
            relevant_memories=context.get("relevant_memories", [])
        )
        
        # Create system context
        system_context = SystemContext(
            current_time=formatted_time,
            timestamp=now.isoformat(),
            agent_capabilities=["content_analysis", "intent_detection", "ability_delegation"],
            uploaded_files=context.get("uploaded_files", []),
            **context.get("system", {})
        )
        
        # Add analysis-specific data to the appropriate context
        if analysis_data:
            # Add query-related info to user context
            if "query" in analysis_data:
                user_context.query = analysis_data["query"]
                
            # Add analysis-specific fields to system context
            if "operation" in analysis_data:
                system_context.current_operation = analysis_data["operation"]
            if "available_abilities" in analysis_data:
                system_context.available_abilities = analysis_data["available_abilities"]
        
        # Return complete context
        return BasePromptContext(
            user=user_context,
            memory=memory_context,
            system=system_context
        )

    def _prepare_system_user_messages(self, base_prompt: str, user_prompt: str, context: Dict[str, Any], available_abilities: Dict[str, Any]) -> List[Dict[str, str]]:
        """Prepare system and user messages for content analysis"""
        # Get all prompt components from the loaded JSON
        system_prompt = self.get_system_prompt()
        context_template = self.prompts["system"]["context_template"]
        abilities_template = self.prompts["system"]["abilities_template"]
        critical_instructions = "\n".join(self.prompts["system"]["critical_instructions"])
        determination_tasks = "\n".join(self.prompts["system"]["determination_tasks"])
        response_instruction = self.prompts["system"]["response_instruction"]
        
        # Get current time in user's timezone or UTC
        user_tz = context.get('timezone', 'UTC')
        try:
            now = datetime.now(pytz.timezone(user_tz))
        except:
            now = datetime.now()
        
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Add debug logging for time-related context
        logger.info("========== TIME CONTEXT DEBUG ==========")
        logger.info(f"Context timestamp: {context.get('timestamp', 'NOT_FOUND')}")
        logger.info(f"Context formatted_time: {context.get('formatted_time', 'NOT_FOUND')}")
        logger.info(f"Context timezone: {user_tz}")
        logger.info(f"Local formatted_time: {formatted_time}")
        logger.info(f"Full context keys: {list(context.keys())}")
        
        if 'system' in context:
            logger.info(f"System context timestamp: {context['system'].get('timestamp', 'NOT_FOUND')}")
        
        logger.info("========================================")
        
        # Extract location info for context
        location_info = "Unknown"
        if context.get('system', {}).get('location'):
            loc = context['system']['location']
            if loc.get('city') and loc.get('country'):
                location_info = f"{loc.get('city', '')}, {loc.get('region', '')}, {loc.get('country', '')}"

        # Format the system context template
        context_section = context_template.format(
            formatted_time=formatted_time,
            now=now,
            user_tz=user_tz,
            location_info=location_info,
            context=context
        )
        
        # Format ability information
        abilities_section = abilities_template.format(json=json, available_abilities=available_abilities)
        
        # Combine all components into a complete system prompt
        complete_system_prompt = f"""{base_prompt}

{context_section}

{abilities_section}

CRITICAL INSTRUCTIONS:
{critical_instructions}

Determine:
{determination_tasks}

{response_instruction}"""

        # Create message array
        messages = [
            {"role": "system", "content": complete_system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.debug(f"Generated analysis messages with {len(messages)} messages")
        return messages

    async def run(self, context: RunContext) -> ContentAnalysis:
        """Execute content analysis"""
        start_time = time.time()
        request_id = context.context.get("request_id", "unknown")
        logger.info(f"Starting content analysis for request ID: {request_id}")
        
        try:
            # Extract user query from context
            query = context.deps.get("query", "")
            if not query:
                return ContentAnalysis(
                    intent={"primary_intent": "unknown", "secondary_intents": []},
                    delegation={"should_delegate": False, "abilities": []},
                    reasoning="No query provided for analysis",
                    confidence=0.0
                )
            
            # Get available abilities
            available_abilities = await fetch_available_abilities()
            
            # Create analysis-specific context data
            analysis_data = {
                "query": query,
                "operation": "content_analysis",
                "available_abilities": available_abilities
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context.context, analysis_data)
            
            # Get task prompt from configuration with the structured context
            user_prompt = self.get_task_prompt(
                "analysis",
                context=prompt_context,
                prompt=query,
                abilities=json.dumps(available_abilities, indent=2)
            )
            
            # Create message array for the agent - still using the existing method for compatibility
            messages = self._prepare_system_user_messages(
                generate_base_prompt(prompt_context), 
                user_prompt, 
                context.context, 
                available_abilities
            )
            
            # Run the content analysis agent
            logger.debug(f"Running content analysis agent for: {query}")
            result = await self.agent.run_with_messages(messages)
            
            # Add enhanced logging for delegation decisions
            if hasattr(result, 'delegation') and result.delegation:
                if result.delegation.should_delegate:
                    logger.info(f"Content analysis decided to delegate to abilities: {result.delegation.abilities}")
                    
                    # Validate requested abilities against available abilities
                    registry = AbilityRegistry()
                    valid_abilities = []
                    invalid_abilities = []
                    
                    for ability in result.delegation.abilities:
                        if registry.validate_ability(ability):
                            valid_abilities.append(ability)
                        else:
                            invalid_abilities.append(ability)
                    
                    if invalid_abilities:
                        logger.warning(f"Requested abilities not found in registry: {invalid_abilities}")
                        # Update the delegation with only valid abilities
                        result.delegation.abilities = valid_abilities
                        
                        # Cleanup configs for invalid abilities
                        if hasattr(result.delegation, 'configs'):
                            for invalid_ability in invalid_abilities:
                                if invalid_ability in result.delegation.configs:
                                    del result.delegation.configs[invalid_ability]
                    
                    logger.info(f"Validated abilities for delegation: {valid_abilities}")
                    logger.info(f"Delegation priority: {result.delegation.priority}")
                    logger.debug(f"Delegation configs: {json.dumps(result.delegation.configs, indent=2, default=str)}")
                    logger.info(f"Delegation reasoning: {result.reasoning}")
                else:
                    logger.info("Content analysis decided NOT to delegate to any abilities")
                    logger.info(f"Reasoning: {result.reasoning}")
            else:
                logger.warning("Content analysis result is missing delegation information")
            
            execution_time = time.time() - start_time
            logger.info(f"Content analysis completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during content analysis: {str(e)}")
            traceback.print_exc()
            
            # Return a fallback analysis
            return ContentAnalysis(
                intent={
                    "primary_intent": "error_fallback",
                    "secondary_intents": [],
                    "requires_memory": False,
                    "memory_operations": {},
                    "metadata": {"error": str(e)},
                    "needs_clarification": False
                },
                delegation={
                    "should_delegate": False,
                    "abilities": [],
                    "priority": [],
                    "configs": {},
                    "fallback_strategies": []
                },
                reasoning=f"Error occurred during analysis: {str(e)}",
                confidence=0.0
            )

    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute content analysis"""
        start_time = time.time()
        
        try:
            # Extract context from RunContext
            run_context = context.deps if hasattr(context, "deps") else {}
            
            # Add context to params
            params["context"] = run_context
            
            # Get the result from the run method
            result = await self.run(context)
            
            # Convert the result to a dictionary
            if isinstance(result, ContentAnalysis):
                return result.model_dump()
            else:
                return {
                    "status": "error",
                    "error": "Failed to generate valid content analysis result",
                    "error_type": "invalid_analysis_result",
                    "attempted_operation": "content_analysis",
                    "intent": {
                        "primary_intent": "error",
                        "secondary_intents": []
                    },
                    "delegation": {
                        "should_delegate": False,
                        "abilities": []
                    },
                    "reasoning": "Error: Unable to process content analysis",
                    "confidence": 0.0,
                    "metadata": {
                        "execution_time": time.time() - start_time,
                        "minion": "content_analysis"
                    }
                }
        except Exception as e:
            logger.error(f"Error in content analysis execute: {str(e)}")
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Traceback: {error_traceback}")

            return {
                "status": "error",
                "error": str(e),
                "error_type": "content_analysis_exception",
                "attempted_operation": "content_analysis",
                "intent": {
                    "primary_intent": "error_fallback",
                    "secondary_intents": [],
                    "requires_memory": False
                },
                "delegation": {
                    "should_delegate": False,
                    "abilities": []
                },
                "reasoning": f"Error occurred during analysis: {str(e)}",
                "confidence": 0.0,
                "metadata": {
                    "error_traceback": error_traceback.split("\n")[-3:],
                    "execution_time": time.time() - start_time,
                    "minion": "content_analysis",
                    "parameters": {k: v for k, v in params.items() if k != "query"} # Exclude query to avoid leaking sensitive info
                }
            }

async def fetch_available_abilities() -> Dict[str, Dict[str, Any]]:
    """Fetch all available abilities and their configurations"""
    # Get abilities from the registry
    registry = AbilityRegistry()
    abilities_list = registry.get_available_abilities()
    
    # Convert to the expected format
    abilities_dict = {}
    for ability in abilities_list:
        abilities_dict[ability["name"]] = {
            "description": ability.get("description", ""),
            "capabilities": ability.get("capabilities", [])
        }
    
    logger.debug(f"Fetched {len(abilities_dict)} available abilities: {list(abilities_dict.keys())}")
    return abilities_dict

