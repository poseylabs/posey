from typing import Dict, Any, Optional, List, Type
from app.utils.serialization import serialize_context, safe_dict
from app.llm.adapters import get_adapter
from app.config.defaults import LLM_CONFIG
from app.utils.validation import validate_response, ResponseValidation, ValidationResult
from app.config.prompts import PromptLoader
from app.config import logger
from pydantic import BaseModel
import json


class BaseAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config.get("llm", LLM_CONFIG["default"])
        self.adapter = get_adapter(self.llm_config)
        # Load validation requirements and prompts
        system_config = PromptLoader.get_shared_prompt("system")
        formatter_config = PromptLoader.get_shared_prompt("formatter")
        self.validation_type = system_config["response_requirements"]["validation"]
        self.max_retries = config.get("max_retries", 2)
        self.response_handling = config.get("response_handling", "hybrid")  # retry, formatter, or hybrid
        self.formatter_prompt = formatter_config["json_formatter"]["prompt"]
        self.formatter_format = formatter_config["json_formatter"]["formats"]["standard_response"]
        
    async def validate_and_parse(
        self,
        response: str,
        schema_model: Optional[Type[BaseModel]] = None
    ) -> ValidationResult:
        """Validate and parse response with schema if provided"""
        validation_type = (
            ResponseValidation.SCHEMA_VALIDATION.value if schema_model
            else self.validation_type
        )
        
        return validate_response(response, validation_type, schema_model)
        
    async def execute_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        schema_model: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        """Execute a prompt with tool support"""
        try:
            # Add JSON enforcement to request formatting
            request = await self.adapter.format_tool_request(
                f"""CRITICAL: You MUST respond with ONLY a valid JSON object.
                
                {prompt}
                
                Your response must:
                1. Start with {{
                2. End with }}
                3. Use double quotes for strings
                4. Have no trailing commas
                5. Be directly parseable by json.loads()
                
                NO other text or formatting allowed.""",
                tools
            )
            
            # Execute the request with retry/formatting logic
            response = await self.execute_request(request)
            original_response = response  # Save original response for formatter fallback
            
            # Try to validate and parse response
            attempt = 1
            retry_exhausted = False
            formatter_exhausted = False
            
            while attempt <= self.max_retries:
                # Validate response with schema if provided
                validation_result = await self.validate_and_parse(response, schema_model)
                
                if validation_result.is_valid:
                    break
                
                logger.warning(f"Invalid response (attempt {attempt}/{self.max_retries})")
                logger.warning(f"Validation error: {validation_result.error}")
                logger.warning(f"Raw response: {response}")
                
                # Determine which approach to try
                should_retry = (
                    self.response_handling in ["retry", "hybrid"] and 
                    not retry_exhausted
                )
                should_format = (
                    self.response_handling in ["formatter", "hybrid"] and
                    not formatter_exhausted and
                    (not should_retry or attempt > 1)
                )
                
                if should_retry:
                    logger.info("Attempting retry with error feedback")
                    retry_prompt = f"""Your previous response was invalid:

                    Error: {validation_result.error}
                    Response: {response}

                    Please try again and ensure your response is a valid JSON object.
                    Remember:
                    1. Start with {{
                    2. End with }}
                    3. Use double quotes for strings
                    4. No trailing commas
                    5. No text before or after the JSON

                    Original request: {prompt}"""
                    
                    response = await self.execute_request(retry_prompt)
                    retry_exhausted = True
                    
                elif should_format:
                    logger.info("Attempting to format response")
                    # Use formatter to convert plain text to JSON
                    format_str = json.dumps(self.formatter_format, indent=2)
                    formatter_request = self.formatter_prompt.format(
                        input=original_response if attempt == 1 else response,
                        format=format_str
                    )
                    
                    response = await self.execute_request(formatter_request)
                    formatter_exhausted = True
                
                else:
                    # Both approaches exhausted
                    break
                
                attempt += 1
            
            # Final validation check
            final_validation = await self.validate_and_parse(response, schema_model)
            if not final_validation.is_valid:
                return {
                    "status": "error",
                    "message": f"Failed to get valid response after {attempt-1} attempts: {final_validation.error}"
                }
            
            # Parse tool calls from validated response
            tool_call = await self.adapter.parse_tool_response(final_validation.data)
            
            if tool_call:
                return {
                    "status": "success",
                    "tool_call": tool_call,
                    "validated_data": final_validation.data
                }
            else:
                return {
                    "status": "error",
                    "message": "No valid tool call found in response"
                }
                
        except Exception as e:
            logger.error(f"Error in execute_with_tools: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            } 
