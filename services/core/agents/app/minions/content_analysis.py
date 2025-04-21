from typing import Dict, Any, List, Optional
from pydantic_ai import RunContext, Agent
from app.config import logger
from app.config.prompts.base import ( generate_base_prompt, BasePromptContext, UserContext, MemoryContext, SystemContext )
import json
import time
from datetime import datetime
import pytz
from app.models.analysis import ContentAnalysis
from app.minions.base import BaseMinion
import traceback
from app.utils.ability_registry import AbilityRegistry
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system import LocationInfo
from app.config.database import Database

class ContentAnalysisMinion(BaseMinion):
    """Content Analysis Minion - analyzes content, determines intent and required abilities"""

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
        
        # Extract location info - Assign None if not properly found
        location_obj: Optional[LocationInfo] = None # Initialize as None
        if context.get('system', {}).get('location'):
            loc_data = context['system']['location']
            # Ensure loc_data is a dict before creating LocationInfo
            if isinstance(loc_data, dict):
                try:
                    # Create LocationInfo object if possible
                    location_obj = LocationInfo(**loc_data)
                except Exception as loc_e:
                    logger.warning(f"Failed to create LocationInfo from context data: {loc_data}, Error: {loc_e}")
            else:
                logger.warning(f"Location data in context is not a dict: {loc_data}")
        
        # Create user context using the consolidated model from app.models.context
        user_context = UserContext(
            user_id=user_id, # Correct field name
            username=user_name, # Map user_name to username
            name=user_name, # Also set name for now, consider consolidating later
            email=context.get("email"), # Add email if available
            preferences=context.get("preferences", {}),
            location=location_obj, # Use the LocationInfo object or None
            timezone=user_tz, # Use extracted timezone
            language=context.get("language", "en-US") # Add language
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
            # Add query-related info to user context - THIS IS NO LONGER NEEDED
            # if "query" in analysis_data:
            #     user_context.query = analysis_data["query"]
                
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
        
        # --- Log the Base Prompt --- 
        logger.debug(f"[CON_ANA_PREP] Base Prompt Content:\n---\n{base_prompt}\n---")
        # --- End Log --- 
        
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
        

        location_info = "Unknown"
        if context.get('system', {}).get('location'):
            loc = context['system']['location']
            if loc.get('city') and loc.get('country'):
                location_info = f"{loc.get('city', '')}, {loc.get('region', '')}, {loc.get('country', '')}"

        conversation_id = context.get('conversation_id', 'N/A')
        uploaded_files = context.get('uploaded_files', [])
        uploaded_files_json = json.dumps(uploaded_files, indent=2)

        context_section = context_template.format(
            formatted_time=formatted_time,
            user_tz=user_tz,
            location_info=location_info,
            conversation_id=conversation_id,
            uploaded_files_json=uploaded_files_json 
            # context=context # Remove the raw context dictionary from format args
        )

        # Format ability information
        abilities_json = json.dumps(available_abilities, indent=2) # Pre-format the JSON string
        abilities_section = abilities_template.format(abilities_json=abilities_json)
        
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
        # Access request_id from context.deps
        request_id = context.deps.get("request_id", "unknown") # Use context.deps
        logger.info(f"[CON_ANA_RUN / {request_id}] Starting content analysis")
        
        # --- DEBUG: Log incoming context and deps ---
        # logger.debug(f"[CON_ANA_RUN] Incoming RunContext.context keys: {list(context.context.keys())}") # This was the error source
        logger.debug(f"[CON_ANA_RUN] Incoming RunContext.deps keys: {list(context.deps.keys())}")
        # --- END DEBUG ---

        try:
            # Extract user query from context.deps
            query = context.deps.get("query", "")
            logger.info(f"[CON_ANA_RUN / {request_id}] Extracted query: '{query if query else '[EMPTY]'}'")
            if not query:
                logger.warning(f"[CON_ANA_RUN / {request_id}] No query found in context.deps. Returning default analysis.")
                return ContentAnalysis(
                    intent={"primary_intent": "unknown", "secondary_intents": []},
                    delegation={"should_delegate": False, "delegated_abilities": []},
                    reasoning="No query provided for analysis",
                    confidence=0.0
                )
            
            # Get the database session from context.deps
            db_session = context.deps.get("db", None)
            logger.debug(f"[CON_ANA_RUN / {request_id}] Database session present: {db_session is not None}")
            
            # Get available abilities
            available_abilities = await fetch_available_abilities()
            logger.debug(f"[CON_ANA_RUN / {request_id}] Fetched {len(available_abilities)} available abilities: {list(available_abilities.keys())}")
            
            # Enhanced logging for available abilities
            logger.info(f"[CONTENT_ANALYSIS] Found {len(available_abilities)} abilities for consideration:")
            for ability_name, ability_info in available_abilities.items():
                capabilities = ability_info.get("capabilities", [])
                logger.info(f"[CONTENT_ANALYSIS] - {ability_name}: {ability_info.get('description', 'No description')} | Capabilities: {capabilities}")
            
            # Create analysis-specific context data
            analysis_data = {
                # DEBUG: Log the data being added
                # "query": query, # Query is already in context.deps
                "operation": "content_analysis",
                "available_abilities": available_abilities
            }
            logger.debug(f"[CON_ANA_RUN / {request_id}] Created analysis_data for prompt context: {analysis_data}")
            
            # Create proper prompt context using context.deps
            prompt_context = self.create_prompt_context(context.deps, analysis_data) # Pass context.deps here
            logger.debug(f"[CON_ANA_RUN / {request_id}] Created BasePromptContext.")
            
            # Get task prompt from configuration with the structured context
            user_prompt = self.get_task_prompt(
                "analysis",
                context=prompt_context,
                prompt=query,
                abilities=json.dumps(available_abilities, indent=2)
            )
            logger.debug(f"[CON_ANA_RUN] Generated user_prompt for analysis task (length: {len(user_prompt)} chars)") # DEBUG
            
            # Create message array for the agent - Pass context.deps to helper
            messages = self._prepare_system_user_messages(
                generate_base_prompt(prompt_context), 
                user_prompt, 
                context.deps, # Pass context.deps here
                available_abilities
            )
            logger.debug(f"[CON_ANA_RUN / {request_id}] Prepared {len(messages)} messages for agent.")
            
            # Run the content analysis agent
            logger.info(f"[CON_ANA_RUN / {request_id}] Calling content analysis agent...")
            if not self.agent:
                logger.error(f"[CON_ANA_RUN / {request_id}] Content analysis agent is None! Cannot run.")
                raise RuntimeError("ContentAnalysisMinion agent not initialized.")
            logger.debug(f"[CON_ANA_RUN / {request_id}] Agent instance: {self.agent}")
            result = await self.agent.run_with_messages(messages)
            
            # Add enhanced logging for delegation decisions
            if hasattr(result, 'delegation') and result.delegation:
                if result.delegation.should_delegate:
                    # Extract ability names for initial logging
                    requested_ability_names = [req.ability_name for req in result.delegation.delegated_abilities]
                    logger.info(f"[CONTENT_ANALYSIS] Analysis determined to delegate to abilities: {requested_ability_names}")

                    # Validate requested abilities against available abilities
                    registry = AbilityRegistry()
                    valid_delegation_requests = []
                    invalid_ability_names = []

                    for delegation_request in result.delegation.delegated_abilities:
                        ability_name = delegation_request.ability_name
                        is_valid = await registry.validate_ability(ability_name, db=db_session)
                        if is_valid:
                            valid_delegation_requests.append(delegation_request)
                            # Log the minion that handles this ability
                            minion_name = await registry.get_minion_name_for_ability(ability_name, db=db_session)
                            logger.info(f"[CONTENT_ANALYSIS] Ability '{ability_name}' will be handled by minion '{minion_name}'")
                        else:
                            invalid_ability_names.append(ability_name)

                    if invalid_ability_names:
                        logger.warning(f"[CONTENT_ANALYSIS] These requested abilities were not found in registry: {invalid_ability_names}")
                        # Update the delegation with only valid requests
                        result.delegation.delegated_abilities = valid_delegation_requests
                        # Note: No need to separately clean up configs anymore, as they are part of the request object

                    # Log final validated abilities and their configs
                    final_validated_abilities = [req.ability_name for req in valid_delegation_requests]
                    logger.info(f"[CONTENT_ANALYSIS] Final validated abilities for delegation: {final_validated_abilities}")
                    logger.info(f"[CONTENT_ANALYSIS] Delegation priority: {result.delegation.priority}")
                    # Log configs for each validated ability
                    for req in valid_delegation_requests:
                        # Convert List[Param] to a simple dict for logging readability
                        config_dict_for_log = {param.key: param.value for param in req.config_params}
                        logger.debug(f"[CONTENT_ANALYSIS] Config for '{req.ability_name}': {json.dumps(config_dict_for_log, indent=2, default=str)}")
                else:
                    logger.info(f"[CONTENT_ANALYSIS] Analysis decided NOT to delegate to any abilities. Intent: {result.intent.primary_intent if hasattr(result.intent, 'primary_intent') else 'unknown'}")
                    logger.info(f"[CONTENT_ANALYSIS] Reasoning: {result.reasoning}")
            else:
                logger.warning("[CONTENT_ANALYSIS] Analysis result is missing delegation information")
            
            execution_time = time.time() - start_time
            logger.info(f"[CON_ANA_RUN / {request_id}] Content analysis completed in {execution_time:.2f}s")
            
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
                    "delegated_abilities": [],
                    "priority": [],
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
                        "delegated_abilities": []
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
                    "delegated_abilities": []
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
    abilities_list = await registry.get_available_abilities()
    
    # Convert to the expected format
    abilities_dict = {}
    for ability in abilities_list:
        abilities_dict[ability["name"]] = {
            "description": ability.get("description", ""),
            "capabilities": ability.get("capabilities", [])
        }
    
    logger.debug(f"Fetched {len(abilities_dict)} available abilities: {list(abilities_dict.keys())}")
    return abilities_dict

