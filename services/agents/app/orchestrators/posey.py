from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.utils.result import AgentResult
from app.utils.agent import create_agent, AgentExecutionResult, run_agent_with_messages
from app.utils.context import RunContext
from app.utils.json_encoder import CustomJSONEncoder
from app.utils.message_handler import prepare_system_user_messages, extract_messages_from_context, get_last_user_message, log_messages
from app.config import logger
from app.utils.context import enhance_run_context
from app.utils.minion import get_minion
from app.config.defaults import LLM_CONFIG
from app.minions.content_analysis import ContentAnalysisMinion, ContentAnalysis
from app.config.abilities import AbilityRegistry, AgentAbility
from app.config.prompts import PromptLoader
import json
import time
import traceback
from mcp.server.fastmcp import FastMCP
from app.models.analysis import ContentAnalysis  # Update import

from app.config.abilities import REGISTERED_ABILITIES
import re
from datetime import datetime

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

class PoseyAgent:
    """Main orchestrator agent using PydanticAI and LangGraph"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Posey orchestrator"""
        self.config = config or {}
        self.started = False
        self.agent_name = "posey"
        
        # Load prompts with shared configurations
        try:
            self.prompts = {
                "posey": PromptLoader.get_prompt_with_shared_config("posey"),
                "synthesis": PromptLoader.get_prompt_with_shared_config("synthesis")
            }
            logger.info(f"Loaded prompts for {self.agent_name} orchestrator with shared configurations")
        except Exception as e:
            logger.error(f"Failed to load prompts for {self.agent_name} orchestrator: {e}")
            self.prompts = {"posey": {}, "synthesis": {}}
        
        self.minions = {}
        self.abilities = {}
        self.user_context = {}
        
        # Create the content analysis agent using the reasoning model to avoid tool usage issues
        self.content_analyzer = ContentAnalysisMinion()
        self.ability_registry = AbilityRegistry()
        logger.info("Content analyzer created")

        # Create the main orchestrator agent
        self.agent = create_agent(
            "orchestrator",
            ["synthesis", "task_management"],
            provider=LLM_CONFIG["default"]["provider"],
            model=LLM_CONFIG["default"]["model"]
        )
        logger.info("Main orchestrator agent created")
        
        # Create a synthesis agent that will be used with explicit message handling
        synthesis_system_prompt = self.prompts["synthesis"]["system_prompt"]
        self.synthesis_agent = create_agent(
            "synthesis",
            [], # No abilities needed for synthesis
            provider=LLM_CONFIG["default"]["provider"],
            model=LLM_CONFIG["default"]["model"],
        )
        # Override the system prompt with the one from the prompts file
        self.synthesis_agent._system_prompt = synthesis_system_prompt
        logger.info("Synthesis agent created for message-based handling")

        # Define minion mapping
        self.minion_map = {
            "image_generation": "image",
            "internet_research": "voyager",
            "memory_management": "memory",
            "research": "research"
        }
        logger.debug(f"Minion mapping configured: {json.dumps(self.minion_map, indent=2, cls=CustomJSONEncoder)}")

        # Add MCP server for inter-agent communication
        self.mcp = FastMCP("posey-orchestrator")
        self.register_minion_tools()

    def register_minion_tools(self):
        """Register minion abilities as MCP tools"""
        self.minion_tools = {}
        for ability_name in REGISTERED_ABILITIES.keys():
            @self.mcp.tool(name=ability_name)
            async def minion_tool(ability: str = ability_name, context: Dict[str, Any] = None, **params) -> Dict[str, Any]:
                """Dynamic tool handler for minion abilities"""
                try:
                    minion = get_minion(AgentAbility.get_minion_name(ability))
                    if not minion:
                        raise ValueError(f"No minion found for ability: {ability}")
                    
                    result = await minion.execute(params, context or {})
                    return {
                        "status": "success",
                        "result": result,
                        "metadata": {
                            "ability": ability,
                            "minion": minion.__class__.__name__
                        }
                    }
                except Exception as e:
                    logger.error(f"Error in minion tool {ability}: {e}")
                    return {
                        "status": "error",
                        "error": str(e)
                    }
            self.minion_tools[ability_name] = minion_tool

    async def execute_agent_chain(
        self,
        prompt: str,
        analysis: ContentAnalysis,
        context: RunContext
    ) -> Dict[str, Any]:
        """Execute chain of agents based on content analysis"""
        chain_start = time.time()
        results = {"results": {}, "context": context.context, "executed_abilities": []}
        executed = []

        try:
            if not analysis.delegation or not analysis.delegation.abilities:
                logger.info("No abilities required for this request")
                return results

            logger.info(f"Content analysis determined these abilities are needed: {analysis.delegation.abilities}")
            logger.info(f"Delegation config: {json.dumps(analysis.delegation.model_dump(), cls=CustomJSONEncoder)}")
            logger.info(f"Content analysis reasoning: {analysis.reasoning}")

            # Execute required abilities in priority order
            for ability in analysis.delegation.abilities:
                if not self.ability_registry.validate_ability(ability):
                    logger.warning(f"Skipping invalid ability: {ability}")
                    # Log available abilities for comparison
                    available = [a["name"] for a in self.ability_registry.get_available_abilities()]
                    logger.warning(f"Available abilities are: {available}")
                    continue

                config = analysis.delegation.configs.get(ability, {})
                logger.info(f"Executing ability: {ability} with config: {json.dumps(config, cls=CustomJSONEncoder)}")
                
                # Execute ability (implement ability execution logic)
                results["results"][ability] = await self.execute_ability(ability, config, context)
                executed.append(ability)

            # Log time information from context being passed to synthesis
            logger.info("Time information in context:")
            logger.info(f"Context timestamp: {context.context.get('timestamp', 'NOT_FOUND')}")
            logger.info(f"Context formatted_time: {context.context.get('formatted_time', 'NOT_FOUND')}")
            
            # Store executed abilities in results
            results["executed_abilities"] = executed
            
            chain_time = time.time() - chain_start
            logger.info(f"Agent chain execution completed in {chain_time:.2f}s")
            logger.info(f"Executed {len(executed)} agents successfully: {executed}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during agent chain execution: {str(e)}")
            
            # Add error info to results
            results["error"] = str(e)
            results["executed_abilities"] = executed
            
            logger.error(f"Agent chain execution failed after {time.time() - chain_start:.2f}s")
            return results

    async def execute_ability(
        self, 
        ability: str, 
        config: Dict[str, Any], 
        context: RunContext
    ) -> Dict[str, Any]:
        """Execute ability using MCP tool calling"""
        ability_start = time.time()
        logger.info(f"Starting execution of ability: {ability}")
        
        try:
            # Check if ability is registered with MCP
            if ability not in self.minion_tools:
                registered_tools = list(self.minion_tools.keys())
                logger.error(f"Ability '{ability}' is not registered as an MCP tool. Available tools: {registered_tools}")
                return {
                    "status": "error",
                    "error": f"Ability '{ability}' is not registered",
                    "error_type": "missing_ability",
                    "attempted_operation": ability,
                    "metadata": {
                        "ability": ability,
                        "available_tools": registered_tools,
                        "execution_time": time.time() - ability_start
                    }
                }
            
            # Log minion mapping
            minion_name = AgentAbility.get_minion_name(ability)
            logger.info(f"Ability '{ability}' maps to minion: {minion_name}")
            
            # Use MCP tool calling for standardized execution
            logger.info(f"Calling MCP tool '{ability}' with config: {json.dumps(config, cls=CustomJSONEncoder)}")
            result = await self.mcp.run_tool(ability, **config)
            
            # Log the result status
            status = result.get("status") if isinstance(result, dict) else "unknown"
            logger.info(f"MCP tool '{ability}' execution completed with status: {status}")
            
            # Enhanced error handling - ensure consistent error format
            if isinstance(result, dict) and result.get("status") == "error":
                error_msg = result.get("error", "Unknown error occurred")
                logger.error(f"Error in ability '{ability}': {error_msg}")
                
                # Ensure error has standardized format with additional context
                return {
                    "status": "error",
                    "error": error_msg,
                    "error_type": result.get("error_type", "minion_execution_error"),
                    "attempted_operation": ability,
                    "operation_config": config,
                    "minion": minion_name,
                    "metadata": {
                        **result.get("metadata", {}),
                        "execution_time": time.time() - ability_start
                    }
                }
            
            # Extract the response data
            if isinstance(result, (AgentExecutionResult, AgentResult)):
                if hasattr(result, 'data'):
                    return result.data
                return result.model_dump()
            
            ability_time = time.time() - ability_start
            logger.info(f"Ability '{ability}' execution completed in {ability_time:.2f}s")
            
            # Add execution metadata to successful results
            if isinstance(result, dict):
                if not result.get("metadata"):
                    result["metadata"] = {}
                result["metadata"]["execution_time"] = ability_time
                result["metadata"]["ability"] = ability
                result["metadata"]["minion"] = minion_name
            
            return result
            
        except Exception as e:
            ability_time = time.time() - ability_start
            logger.error(f"Failed to execute ability '{ability}' after {ability_time:.2f}s: {str(e)}")
            
            # Create detailed error report
            error_traceback = traceback.format_exc()
            logger.error(f"Error traceback:\n{error_traceback}")
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": "exception",
                "attempted_operation": ability,
                "error_traceback": error_traceback.split("\n")[-3:],  # Include last few lines of traceback
                "metadata": {
                    "ability": ability,
                    "minion": AgentAbility.get_minion_name(ability),
                    "config": config,
                    "execution_time": ability_time
                }
            }

    async def synthesize_response(
        self,
        prompt: str,
        chain_results: Dict[str, Any]
    ) -> AgentExecutionResult:
        """Synthesize final response from all agent results"""
        logger.info("Starting response synthesis")
        logger.debug(f"Chain results type: {type(chain_results)}")
        logger.debug(f"Chain results content: {json.dumps(chain_results, indent=2, cls=CustomJSONEncoder)}")
        synthesis_start = time.time()

        try:
            # Prepare messages array with separate system and user messages
            messages = self._prepare_synthesis_messages(prompt, chain_results)
            
            # Log the messages being sent
            logger.info("Sending messages to synthesis agent:")
            log_messages(messages)

            # Use our utility function to run the agent with messages
            logger.info("=" * 80)
            logger.info("CALLING LLM FOR SYNTHESIS RESPONSE")
            result = await run_agent_with_messages(self.synthesis_agent, messages)
            
            # Enhanced logging of raw result
            logger.info("=" * 80)
            logger.info("RAW SYNTHESIS RESULT FROM LLM:")
            logger.info(str(result))
            logger.info("=" * 80)
            
            # Detailed result structure debugging
            logger.info(f"Result type: {type(result).__name__}")
            
            if hasattr(result, 'data'):
                logger.info(f"Result has data attribute of type: {type(result.data).__name__}")
                logger.info(f"Result data content: {str(result.data)[:1000]}")
            
            if hasattr(result, 'answer'):
                logger.info(f"Result has answer: {result.answer[:500]}")
            
            if hasattr(result, 'model_dump'):
                try:
                    logger.info(f"Result model_dump: {json.dumps(result.model_dump(), indent=2, cls=CustomJSONEncoder)[:1000]}")
                except Exception as e:
                    logger.info(f"Could not dump result model: {e}")
            
            # Log for specific time-related output patterns
            raw_response = str(result)
            if "time" in prompt.lower():
                logger.info("TIME-RELATED QUERY DETECTED - ANALYZING RESPONSE")
                time_patterns = ["current time", "time is", "right now", "currently"]
                for pattern in time_patterns:
                    if pattern in raw_response.lower():
                        logger.info(f"Found time pattern '{pattern}' in response")
                        start_idx = max(0, raw_response.lower().find(pattern) - 30)
                        end_idx = min(len(raw_response), raw_response.lower().find(pattern) + 50)
                        context = raw_response[start_idx:end_idx]
                        logger.info(f"Context around pattern: '...{context}...'")
            
            # Process the result as before
            if hasattr(result, 'data'):
                result_data = result.data
                # If the data attribute is already an AgentExecutionResult, return it
                if isinstance(result_data, AgentExecutionResult):
                    logger.info("Found AgentExecutionResult in result.data, returning directly")
                    logger.info(f"Final answer: {result_data.answer[:200]}")
                    return result_data
                
                # If the data is a string, try to parse it as JSON
                if isinstance(result_data, str):
                    try:
                        # If it starts with { and ends with }, try to parse as JSON
                        if result_data.strip().startswith('{') and result_data.strip().endswith('}'):
                            parsed_json = json.loads(result_data.strip())
                            logger.info(f"Successfully parsed result.data as JSON: {parsed_json}")
                            
                            # Create AgentExecutionResult from parsed JSON
                            if 'answer' in parsed_json:
                                result = AgentExecutionResult(
                                    answer=parsed_json.get('answer', ''),
                                    confidence=parsed_json.get('confidence', 0.95),
                                    abilities_used=chain_results.get("executed_abilities", []),
                                    metadata={
                                        "processing_time": time.time() - synthesis_start,
                                        "agent_count": len(chain_results.get("executed_abilities", [])),
                                        "sources": parsed_json.get('metadata', {}).get('sources', []) 
                                            if 'metadata' in parsed_json else [],
                                        "memory_updates": parsed_json.get('metadata', {}).get('memory_updates', [])
                                            if 'metadata' in parsed_json else []
                                    }
                                )
                                logger.info(f"Created AgentExecutionResult from JSON with answer: {result.answer[:200]}")
                                return result
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse result.data as JSON: {e}")
                
                # Use as plain text if not JSON
                result = AgentExecutionResult(
                    answer=str(result_data),
                    confidence=0.9,
                    abilities_used=chain_results.get("executed_abilities", []),
                    metadata={
                        "processing_time": time.time() - synthesis_start,
                        "agent_count": len(chain_results.get("executed_abilities", [])),
                        "extraction_method": "plain_text"
                    }
                )
                logger.info(f"Created AgentExecutionResult from plain text with answer: {result.answer[:200]}")
                return result
            
            # Same fallback logic as before
            raw_response = str(result)
            try:
                json_match = re.search(r'({[\s\S]*?})', raw_response)
                if json_match:
                    json_str = json_match.group(1)
                    parsed_json = json.loads(json_str)
                    
                    if 'answer' in parsed_json:
                        result = AgentExecutionResult(
                            answer=parsed_json.get('answer', ''),
                            confidence=parsed_json.get('confidence', 0.95),
                            abilities_used=chain_results.get("executed_abilities", []),
                            metadata={
                                "processing_time": time.time() - synthesis_start,
                                "agent_count": len(chain_results.get("executed_abilities", [])),
                                "sources": parsed_json.get('metadata', {}).get('sources', [])
                                    if 'metadata' in parsed_json else [],
                                "memory_updates": parsed_json.get('metadata', {}).get('memory_updates', [])
                                    if 'metadata' in parsed_json else []
                            }
                        )
                        logger.info(f"Created AgentExecutionResult from regex-parsed JSON with answer: {result.answer[:200]}")
                        return result
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.warning(f"Failed to extract and parse JSON from result string: {e}")
            
            result = AgentExecutionResult(
                answer=raw_response,
                confidence=0.8,
                abilities_used=chain_results.get("executed_abilities", []),
                metadata={
                    "processing_time": time.time() - synthesis_start,
                    "agent_count": len(chain_results.get("executed_abilities", [])),
                    "extraction_method": "raw_response"
                }
            )
            logger.info(f"Created fallback AgentExecutionResult with raw answer: {result.answer[:200]}")
            return result

        except Exception as e:
            logger.error(f"Response synthesis failed after {time.time() - synthesis_start:.2f}s: {str(e)}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            raise
            
    def _prepare_synthesis_messages(self, prompt: str, chain_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Prepare messages for synthesis with explicit roles"""
        logger.info("=" * 80)
        logger.info("PREPARING SYNTHESIS MESSAGES - DETAILED DEBUG")
        
        # Use the prompts loaded at initialization
        synthesis_prompts = self.prompts["synthesis"]
        logger.debug(f"Synthesis prompts keys: {list(synthesis_prompts.keys())}")
        
        # Get system prompt from synthesis prompts
        system_content = synthesis_prompts["system"]["format_instructions"]
        logger.debug(f"System content length: {len(system_content)}")
        logger.debug(f"System content first 100 chars: {system_content[:100]}...")
        
        # Enhanced error highlighting - create summary of errors for synthesis prompt
        error_summary = {}
        if "error" in chain_results:
            # Error in the overall chain
            error_summary["chain_error"] = chain_results["error"]
        
        # Check for errors in individual ability results
        if "results" in chain_results:
            ability_errors = {}
            for ability, result in chain_results["results"].items():
                if isinstance(result, dict) and result.get("status") == "error":
                    ability_errors[ability] = {
                        "error": result.get("error"),
                        "error_type": result.get("error_type", "unknown_error"),
                        "attempted_operation": result.get("attempted_operation", ability)
                    }
            
            if ability_errors:
                error_summary["ability_errors"] = ability_errors
        
        # If errors found, add highlighted error section to chain results
        if error_summary:
            chain_results["_error_summary"] = error_summary
            logger.info("Found errors in chain results, adding error summary for synthesis agent")
            logger.info(f"Error summary: {json.dumps(error_summary, indent=2, cls=CustomJSONEncoder)}")
        
        # Shared response guidelines should already be loaded in initialization
        # Just add them to chain_results if they exist
        if "response_guidelines" in self.prompts["synthesis"]:
            chain_results["response_guidelines"] = self.prompts["synthesis"]["response_guidelines"]
            logger.debug("Added shared response guidelines to chain results")
            logger.debug(f"Response guidelines: {json.dumps(self.prompts['synthesis']['response_guidelines'], indent=2, cls=CustomJSONEncoder)}")
        
        # Add debug logging for time context in chain results
        logger.debug("========== SYNTHESIS TIME CONTEXT DEBUG ==========")
        if 'context' in chain_results:
            logger.debug(f"Chain results context keys: {list(chain_results.get('context', {}).keys())}")
            if 'system_info' in chain_results.get('context', {}):
                system_info = chain_results.get('context', {}).get('system_info', {})
                logger.debug(f"System info timestamp: {system_info.get('timestamp')}")
                logger.debug(f"System info formatted time: {system_info.get('formatted_time')}")
                logger.debug(f"System info user timezone: {system_info.get('user_timezone')}")
        else:
            logger.debug("No 'context' found in chain_results")
        
        logger.debug(f"Chain results top-level keys: {list(chain_results.keys())}")
        
        # Ensure we add time context to the synthesis message if not present
        if 'context' not in chain_results:
            current_time = datetime.utcnow()
            synthesis_context = {}
            synthesis_context["system_info"] = {
                "timestamp": current_time.isoformat(),
                "formatted_time": current_time.strftime('%A, %B %d, %Y %I:%M:%S %p %Z')
            }
            logger.debug(f"Added synthesis timestamp context: {synthesis_context['system_info']['formatted_time']}")
            
            # Add to chain results
            chain_results["context"] = synthesis_context
        
        logger.debug("=================================================")
        
        # Get user prompt template and format it
        user_template = synthesis_prompts["tasks"]["synthesize"]["prompt"]
        logger.debug(f"User template length: {len(user_template)}")
        logger.debug(f"User template first 100 chars: {user_template[:100]}...")
        
        user_content = user_template.replace("{prompt}", prompt).replace(
            "{chain_results}", json.dumps(chain_results, indent=2, cls=CustomJSONEncoder)
        )
        logger.debug(f"Formatted user content length: {len(user_content)}")
        
        # Log specific sections that might be related to time formatting
        if "examples" in synthesis_prompts:
            logger.info("SYNTHESIS EXAMPLES SECTION:")
            logger.info(json.dumps(synthesis_prompts["examples"], indent=2, cls=CustomJSONEncoder))
            
            # Log time-specific examples if they exist
            time_examples = [ex for ex in synthesis_prompts["examples"] 
                            if isinstance(ex, dict) and "time" in ex.get("query", "").lower()]
            if time_examples:
                logger.info("TIME-SPECIFIC EXAMPLES:")
                logger.info(json.dumps(time_examples, indent=2, cls=CustomJSONEncoder))
        
        if "response_contrasts" in synthesis_prompts:
            logger.info("RESPONSE CONTRASTS SECTION:")
            logger.info(json.dumps(synthesis_prompts["response_contrasts"], indent=2, cls=CustomJSONEncoder))
            
            # Log time-specific contrasts if they exist
            time_contrasts = [ex for ex in synthesis_prompts["response_contrasts"] 
                             if isinstance(ex, dict) and "time" in ex.get("scenario", "").lower()]
            if time_contrasts:
                logger.info("TIME-SPECIFIC RESPONSE CONTRASTS:")
                logger.info(json.dumps(time_contrasts, indent=2, cls=CustomJSONEncoder))
        
        messages = prepare_system_user_messages(system_content, user_content)
        logger.info(f"Prepared {len(messages)} messages for synthesis")
        logger.info("=" * 80)
        
        # Create and return messages array
        return messages

    async def run_with_messages(self, messages: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """Execute the full orchestration pipeline with message-based input"""
        total_start = time.time()
        request_id = context.get("request_id", "unknown") if context else "unknown"
        logger.info(f"Starting Posey execution with messages for request {request_id}")
        
        try:
            # Get the latest user message as the prompt
            prompt = get_last_user_message(messages)
            if not prompt:
                raise ValueError("No user messages found in the provided messages list")
            
            # Initialize or enhance context with the full message history
            initial_context = context or {}
            initial_context["messages"] = messages
            
            run_context = RunContext[Dict[str, Any]](deps=initial_context)
            run_context = await enhance_run_context(
                run_context,
                user_id=initial_context.get("user_id"),
                request_id=request_id,
                conversation_id=initial_context.get("conversation_id")
            )

            # Add prompt and abilities to context
            run_context.deps["prompt"] = prompt
            run_context.deps["available_abilities"] = self.ability_registry.get_available_abilities()

            # Step 1: Analyze content directly with minion
            analysis = await self.content_analyzer.run(run_context)
            logger.info(f"Content analysis completed for request {request_id}")

            # Step 2: Execute agent chain
            chain_results = await self.execute_agent_chain(
                prompt,
                analysis,
                run_context
            )
            logger.info(f"Chain execution completed with {len(chain_results['results'])} agents")

            # Step 3: Synthesize final response
            response = await self.synthesize_response(prompt, chain_results)
            
            total_time = time.time() - total_start
            logger.info(f"Posey execution completed in {total_time:.2f}s for request {request_id}")
            logger.info(f"Final response confidence: {response.confidence}")

            return response

        except Exception as e:
            total_time = time.time() - total_start
            logger.error(f"Error in Posey execution with messages after {total_time:.2f}s: {e}")
            logger.error(f"Request {request_id} failed")
            raise

    async def run(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """Execute the full orchestration pipeline"""
        # Extract messages from context or create basic message array
        context = context or {}
        messages = extract_messages_from_context(context, prompt)
        
        # Ensure the current prompt is included as the latest user message if not already present
        if prompt and not any(m["role"] == "user" and m["content"] == prompt for m in messages):
            messages.append({"role": "user", "content": prompt})
            
        return await self.run_with_messages(messages, context)
