from typing import Dict, Any, Optional, List, Tuple
from pydantic_ai import RunContext, Agent
from pydantic import BaseModel, Field
import pprint
import json
import time
import traceback
from datetime import datetime
import uuid

from app.minions.base import BaseMinion
from app.config import logger
from pydantic_ai.agent import AgentRunResult
from app.config.prompts.base import (
    generate_base_prompt,
    get_default_context, # May be needed if context creation requires defaults
    BasePromptContext,
    UserContext,
    MemoryContext,
    SystemContext
)
from app.models.analysis import ContentAnalysis # Needed for type hinting
from app.db.models.minion_llm_config import MinionLLMConfig


# Define a basic response structure, although the primary output is a string
class SynthesisResponse(BaseModel):
    synthesized_response: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SynthesisMinion(BaseMinion):
    """
    Minion responsible for synthesizing a final user-facing response 
    based on the initial query, analysis, and execution results.
    """
    # Agent is initialized via registry/orchestrator
    llm_config_orm: Optional[MinionLLMConfig] = None

    def __init__(self, name: str, display_name: str, description: str, prompt_category: str = "minions", **kwargs):
        """Initialize the Synthesis Minion, accepting config from registry."""
        super().__init__(
            name=name,
            display_name=display_name,
            description=description,
            prompt_category=prompt_category
        )
        logger.info(f"SynthesisMinion '{self.name}' initialized with config from registry.")
        # kwargs can be ignored or used if BaseMinion needs more args in the future

    async def setup(self, db_session: Any, llm_config_orm: MinionLLMConfig, *args, **kwargs) -> None:
        """Set up the Synthesis Minion, storing LLM config."""
        logger.info(f"Performing setup for '{self.name}' minion...")
        self.llm_config_orm = llm_config_orm
        # Agent initialization happens externally and is set on the instance
        if self.agent:
             logger.info(f"'{self.name}' minion setup complete with agent: {self.agent}")
        else:
             logger.warning(f"'{self.name}' minion setup complete BUT agent is not set yet.")

    def create_prompt_context(self, context_deps: Dict[str, Any], analysis: ContentAnalysis, execution_results: List[Dict[str, Any]]) -> BasePromptContext:
        """
        Create a prompt context for the synthesis task, incorporating the 
        original context, analysis, and execution results.
        """
        # --- User Context ---
        user_id = context_deps.get("user_id", context_deps.get("id", "anonymous"))
        user_name = context_deps.get("user_name", "User")
        user_prefs = context_deps.get("preferences", {})
        
        # Extract location from context_deps if available
        location_obj = None
        loc_data = context_deps.get("location")
        if isinstance(loc_data, dict):
             # Assuming LocationInfo model exists and can handle this dict
             try:
                 # Replace with actual LocationInfo import and instantiation if needed
                 location_obj = loc_data # Placeholder
             except Exception as e:
                 logger.warning(f"Failed to process location data {loc_data}: {e}")
        
        user_context = UserContext(
            user_id=user_id,
            username=user_name, # Map to username
            name=user_name, # Keep name for now
            preferences=user_prefs,
            location=location_obj, # Pass location object/dict
            # Add other relevant fields if present in context_deps
            # email=context_deps.get("email"),
            # timezone=context_deps.get("timezone"),
            # language=context_deps.get("language"),
        )

        # --- Memory Context ---
        # Include relevant memories from original context and potentially analysis/results
        relevant_memories_combined = context_deps.get("relevant_memories", [])
        # TODO: Potentially add key info from execution_results as memories?
        
        memory_context = MemoryContext(
            recent_memories=context_deps.get("recent_memories", []),
            relevant_memories=relevant_memories_combined
        )

        # --- System Context ---
        # Start with base system context from original request
        system_context_data = context_deps.get("system", {}).copy()

        # Add analysis results (carefully selecting what's useful)
        system_context_data["analysis_intent"] = analysis.intent.model_dump() if analysis and analysis.intent else {}
        system_context_data["analysis_delegation"] = analysis.delegation.model_dump() if analysis and analysis.delegation else {}
        system_context_data["analysis_reasoning"] = analysis.reasoning if analysis else "N/A"

        # Add execution results (summarized or key info)
        # Ensure execution_results is a list of dicts
        if not isinstance(execution_results, list):
             logger.warning(f"execution_results is not a list: {type(execution_results)}. Setting to empty list.")
             execution_results_for_context = []
        else:
             # Convert results to JSON strings for safer inclusion if they contain complex objects
             try:
                  execution_results_for_context = [json.dumps(res, default=str) for res in execution_results]
             except Exception as json_err:
                  logger.error(f"Failed to serialize execution results for context: {json_err}")
                  execution_results_for_context = ["Error: Could not serialize results"]

        system_context_data["execution_results_summary"] = execution_results_for_context # List of JSON strings or error message

        # Set current operation and timestamp
        system_context_data["current_operation"] = "synthesize_response"
        system_context_data["timestamp"] = datetime.now().isoformat()
        system_context_data["agent_capabilities"] = ["information_synthesis", "natural_language_generation"]
        
        # Instantiate SystemContext, handling potential extra fields gracefully
        try:
            system_context = SystemContext(**system_context_data)
        except Exception as e:
            logger.error(f"Error creating SystemContext for synthesis: {e}. Data keys: {list(system_context_data.keys())}", exc_info=True)
            # Fallback to minimal context
            system_context = SystemContext(
                timestamp=system_context_data.get("timestamp", datetime.now().isoformat()),
                current_operation="synthesize_response",
                agent_capabilities=["information_synthesis", "natural_language_generation"]
            )
            logger.warning("Fell back to minimal SystemContext for synthesis.")


        # Return complete BasePromptContext
        return BasePromptContext(
            user=user_context,
            memory=memory_context,
            system=system_context
        )

    def _prepare_system_user_messages(
        self,
        original_query: Optional[str],
        content_analysis: Optional[Dict[str, Any]],
        execution_results: Optional[List[Dict[str, Any]]],
        context: RunContext
    ) -> Tuple[str, str]:
        """Prepares the system prompt and user message content for the synthesis agent."""
        
        # System Prompt (Load from config OR use enhanced default)
        # system_prompt = self.prompts.get('system', "You are a helpful synthesis agent.") # Original
        system_prompt = self.get_system_prompt()
        
        # User Message Construction
        user_message_parts = []
        if original_query:
            user_message_parts.append(f"Original User Query:\n```\n{original_query}\n```")
        else:
            logger.warning("Original query missing during synthesis prompt preparation.")

        if content_analysis:
            analysis_str = pprint.pformat(content_analysis, indent=2, width=100)
            user_message_parts.append(f"\n\nContent Analysis Summary:\n```json\n{analysis_str}\n```")
        else:
            logger.warning("Content analysis missing during synthesis prompt preparation.")
            
        if execution_results:
            # --- Improved Formatting for Execution Results --- 
            formatted_results = []
            for idx, res in enumerate(execution_results):
                 target_info = f"{res.get('target_type', 'unknown').capitalize()} '{res.get('target_key', 'unknown')}'"
                 status = res.get('status', 'unknown').upper()
                 result_data_str = "No data returned."
                 if res.get('result_data'):
                     # Pretty print if dict/list, otherwise just use str
                     if isinstance(res.get('result_data'), (dict, list)):
                         result_data_str = pprint.pformat(res.get('result_data'), indent=2, width=100, depth=3) # Limit depth
                     else:
                         result_data_str = str(res.get('result_data'))
                 elif res.get('error'):
                     result_data_str = f"ERROR: {res.get('error')}"
                     
                 formatted_results.append(
                     f"Step {idx + 1}: {target_info} - Status: {status}\n---\n{result_data_str}\n---"
                 )
            results_summary = "\n\n".join(formatted_results)
            user_message_parts.append(f"\n\nExecution Results Summary:\n{results_summary}")
            # --- End Improved Formatting ---
        else:
            logger.warning("Execution results missing during synthesis prompt preparation.")
            user_message_parts.append("\n\nExecution Results Summary:\nNo execution steps were performed or results are unavailable.")

        user_message_content = "\n".join(user_message_parts)
        
        # Log the prepared user message for debugging
        logger.debug(f"[SYNTHESIS_PREPARE] Prepared User Message Content:\n{user_message_content}")
        
        return system_prompt, user_message_content

    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        request_id = context.deps.get("run_id", str(uuid.uuid4()))
        logger.info(f"Executing SynthesisMinion for request_id: {request_id}")

        # Extract data from context.deps (passed from PoseyAgent)
        original_query = context.deps.get("original_query")
        content_analysis = context.deps.get("content_analysis")
        # Execution results are passed via params in the current PoseyAgent logic
        execution_results = params.get("execution_results")

        # --- Logging Extracted Inputs --- 
        logger.debug(f"[SYNTHESIS_EXEC] Context Deps Keys: {list(context.deps.keys())}")
        logger.debug(f"[SYNTHESIS_EXEC] Params Keys: {list(params.keys())}")
        logger.debug(f"[SYNTHESIS_EXEC] Extracted original_query (type: {type(original_query)}): {'Present' if original_query else 'MISSING!'}")
        logger.debug(f"[SYNTHESIS_EXEC] Extracted content_analysis (type: {type(content_analysis)}): {'Present' if content_analysis else 'MISSING!'}")
        logger.debug(f"[SYNTHESIS_EXEC] Extracted execution_results (type: {type(execution_results)}): {'Present' if execution_results else 'MISSING!'}")
        # --- End Logging --- 

        if not original_query:
            logger.warning("Original query is missing in context.deps.")
            # Potential fallback: try getting from params? context.prompt?

        if not content_analysis:
            logger.warning("Content analysis is missing in context.deps.")
            
        if not execution_results:
             logger.warning("Execution results are missing in params.")

        # Prepare messages for the internal synthesis agent
        system_prompt_content, user_message_content = self._prepare_system_user_messages(
            original_query=original_query,
            content_analysis=content_analysis,
            execution_results=execution_results,
            context=context # Pass RunContext for potential future use
        )
        
        messages_for_agent = [
            {"role": "system", "content": system_prompt_content},
            {"role": "user", "content": user_message_content}
        ]
        
        logger.info("Calling synthesis agent...")
        logger.debug(f"[SYNTHESIS_EXEC] Messages passed to agent.run_with_messages:\n{pprint.pformat(messages_for_agent)}")

        synthesis_run_result = None
        final_response = ""
        error_message = None
        
        try:
            # Use run_with_messages as it aligns with message structure
            synthesis_run_result = await self.agent.run_with_messages(messages=messages_for_agent, deps=context.deps) # Pass deps if agent needs them
            logger.info("Synthesis agent call completed.")
            
            # --- DETAILED LOGGING OF RESULT --- 
            logger.debug(f"[SYNTHESIS_RESULT] Raw result object type: {type(synthesis_run_result)}")
            logger.debug(f"[SYNTHESIS_RESULT] Raw result repr():\n{repr(synthesis_run_result)}")
            
            # Log attributes if it's an AgentRunResult
            if isinstance(synthesis_run_result, AgentRunResult):
                data_attr = getattr(synthesis_run_result, 'data', '<MISSING>')
                output_attr = getattr(synthesis_run_result, 'output', '<MISSING>')
                logger.debug(f"[SYNTHESIS_RESULT] AgentRunResult.data (type: {type(data_attr)}): {repr(data_attr)}")
                logger.debug(f"[SYNTHESIS_RESULT] AgentRunResult.output (type: {type(output_attr)}): {repr(output_attr)}")
                # --- Attempt to find source of the logging error --- 
                try:
                    # Log the structure that might be causing issues
                    # Check if raw_input exists and what it contains
                    if hasattr(synthesis_run_result, 'raw_input'):
                         logger.debug(f"[SYNTHESIS_RESULT_DEBUG] raw_input type: {type(synthesis_run_result.raw_input)}")
                         logger.debug(f"[SYNTHESIS_RESULT_DEBUG] raw_input repr: {repr(synthesis_run_result.raw_input)}")
                         # If raw_input is a list, check elements
                         if isinstance(synthesis_run_result.raw_input, list) and synthesis_run_result.raw_input:
                              logger.debug(f"[SYNTHESIS_RESULT_DEBUG] First element of raw_input type: {type(synthesis_run_result.raw_input[0])}")
                              logger.debug(f"[SYNTHESIS_RESULT_DEBUG] First element of raw_input repr: {repr(synthesis_run_result.raw_input[0])}")
                    else:
                         logger.debug("[SYNTHESIS_RESULT_DEBUG] AgentRunResult has no 'raw_input' attribute.")

                    # Check if raw_output exists
                    if hasattr(synthesis_run_result, 'raw_output'):
                         logger.debug(f"[SYNTHESIS_RESULT_DEBUG] raw_output type: {type(synthesis_run_result.raw_output)}")
                         logger.debug(f"[SYNTHESIS_RESULT_DEBUG] raw_output repr: {repr(synthesis_run_result.raw_output)}")
                    else:
                        logger.debug("[SYNTHESIS_RESULT_DEBUG] AgentRunResult has no 'raw_output' attribute.")
                except Exception as log_debug_err:
                    logger.error(f"[SYNTHESIS_RESULT_DEBUG] Error during extra debug logging: {log_debug_err}")
                # --- End attempt to find source --- 
            # --- END DETAILED LOGGING --- 

            # Extract the string response
            if isinstance(synthesis_run_result, AgentRunResult):
                # --- MODIFIED: Prioritize .data as SynthesisResponse --- 
                data_val = getattr(synthesis_run_result, 'data', None)
                output_val = getattr(synthesis_run_result, 'output', None)

                if isinstance(data_val, SynthesisResponse):
                    logger.info("Extracted response from AgentRunResult.data (SynthesisResponse)")
                    final_response = data_val.synthesized_response
                    if data_val.error:
                        logger.error(f"SynthesisResponse model reported an internal error: {data_val.error}")
                        # Override or append error? Let's prioritize the model's error
                        error_message = f"Synthesis model error: {data_val.error}"
                    elif not final_response:
                         logger.warning("SynthesisResponse model returned successfully but synthesized_response was empty.")
                         # Keep existing error logic below for this case

                # Fallback to checking .output or .data as string (as before)
                elif isinstance(output_val, str) and output_val.strip():
                    final_response = output_val.strip()
                    logger.info("Extracted response from AgentRunResult.output (String Fallback)")
                elif isinstance(data_val, str) and data_val.strip():
                    final_response = data_val.strip()
                    logger.info("Extracted response from AgentRunResult.data (String Fallback)")
                else:
                    logger.error(f"Synthesis agent returned AgentRunResult, but could not extract SynthesisResponse from .data or string from .output/.data. Output: {output_val!r}, Data: {data_val!r}")
                    error_message = "Synthesis structure error: Could not extract expected response."
                # --- END MODIFIED --- 

            elif isinstance(synthesis_run_result, str):
                # If the agent directly returns a string (less likely now, but keep fallback)
                final_response = synthesis_run_result.strip()
                logger.info("Extracted response directly (string result)")
            else:
                # Handle unexpected result types
                logger.error(f"Synthesis agent returned unexpected type: {type(synthesis_run_result)}")
                error_message = f"Synthesis type error: Expected string, got {type(synthesis_run_result).__name__}."

        except Exception as e:
            logger.error(f"Error during synthesis agent execution: {e}", exc_info=True)
            error_message = f"Synthesis execution error: {e}"

        # Check if we actually got a response string
        if not final_response and not error_message:
            logger.error("Synthesis agent did not return a valid string response.")
            error_message = "Synthesis failed to produce text output."
        elif final_response:
             logger.info(f"Successfully synthesized response: '{final_response[:100]}...'" )

        # Return dictionary matching _delegate_task_to_minion expectation
        return {
            "synthesized_response": final_response if final_response else None,
            "error": error_message
        }