from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import RunContext, Agent
from app.utils.result import AgentResult
from app.utils import prepare_system_user_messages
from app.config import logger
from app.config.prompts import PromptLoader
from app.config.prompts.base import BasePromptContext
from app.minions.base import BaseMinion
import time
import json
import traceback
from sqlalchemy.ext.asyncio import AsyncSession


# Define expected output structure for analysis
class ImageProcessingAnalysis(BaseModel):
    action_required: str = Field(..., description="The primary image processing action required (e.g., 'convert', 'remove_background', 'overlay_text', 'generate_variation', 'none')")
    source_filename: Optional[str] = Field(None, description="The filename of the uploaded image to process, if applicable")
    target_format: Optional[str] = Field(None, description="The desired output format (e.g., 'png', 'gif', 'webp')")
    processing_details: Dict[str, Any] = Field(default_factory=dict, description="Specific parameters for the action (e.g., {'text_to_overlay': 'Hello'})")
    delegation_needed: bool = Field(False, description="Whether this task needs delegation to another ability/minion")
    delegation_target: Optional[str] = Field(None, description="The target ability/minion for delegation (e.g., 'file_processing', 'image_generation')")
    delegation_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the delegated task")
    reasoning: str = Field(..., description="Explanation of the analysis and decisions made")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0) in the analysis")

class ImageProcessingMinion(BaseMinion):
    """Image Processing Minion - analyzes requests involving images and determines processing steps or delegates to generation."""
    # Agent is inherited and defaults to None

    def create_prompt_context(self, context: Dict[str, Any], analysis_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create prompt context dictionary for the image processing analysis task."""
        output_schema_json = ImageProcessingAnalysis.model_json_schema()

        full_context = {
            "minion_name": self.name,
            "minion_description": self.description,
            "tools_description": "N/A for analysis task.",
            "output_format_description": f"Respond ONLY with a JSON object conforming to the ImageProcessingAnalysis schema.",
            "output_format_json": json.dumps(output_schema_json, indent=2),
            **(analysis_data or {}) # Merge analysis_data (prompt, files, targets)
        }
        return full_context

    async def analyze_request(self, prompt: str, context: Dict[str, Any]) -> ImageProcessingAnalysis:
        """Analyze the user prompt and context (especially uploaded files) to determine the required image action."""
        start_time = time.time()
        logger.info(f"Analyzing image processing request: {prompt[:100]}...")
        uploaded_files = context.get("uploaded_files", [])
        logger.info(f"Uploaded files for analysis: {json.dumps(uploaded_files)}")

        if not uploaded_files and "image" not in prompt.lower():
             logger.info("No uploaded images and prompt doesn't mention images. Skipping analysis.")
             return ImageProcessingAnalysis(
                 action_required="none",
                 reasoning="No uploaded image and prompt does not appear image-related.",
                 confidence=0.9
             )

        try:
            # 1. Prepare data for context and prompt
            uploaded_files_json = json.dumps(uploaded_files)
            available_delegation_targets_json = json.dumps(self.available_abilities)
            analysis_context_data = {
                "prompt": prompt,
                "uploaded_files_json": uploaded_files_json,
                "available_delegation_targets_json": available_delegation_targets_json
            }

            # 2. Create Prompt Context Dictionary
            # Get the combined dictionary from the updated helper
            full_format_context = self.create_prompt_context(context, analysis_context_data)

            # 3. Get System and User Task Prompts - MANUAL FORMATTING
            try:
                # Format System Prompt
                system_template_list = self.prompt_config["system_prompt_template"]["template"]
                system_template = "\n".join(system_template_list)
                # Use the full context dictionary for formatting
                system_base_prompt = system_template.format(**full_format_context)

                # Format User Task Prompt
                user_template_list = self.prompt_config["tasks"]["analysis"]["template"]
                user_template = "\n".join(user_template_list)
                # Use the full context dictionary for formatting
                user_task_prompt = user_template.format(**full_format_context)

            except KeyError as e:
                logger.error(f"Missing key in prompt config for image_processing: {e}")
                raise ValueError(f"Invalid prompt configuration structure: Missing key {e}")
            except Exception as e:
                logger.error(f"Error formatting prompt: {e}", exc_info=True)
                raise

            logger.debug(f"System Prompt: {system_base_prompt}")
            logger.debug(f"User Task Prompt: {user_task_prompt}")

            # 4. Prepare Messages for the agent
            messages = prepare_system_user_messages(system_base_prompt, user_task_prompt)

            # 5. Run Analysis Agent
            result = await self.agent.run_with_messages(messages=messages)

            execution_time = time.time() - start_time
            logger.info(f"Image processing analysis completed in {execution_time:.2f}s")

            if isinstance(result, ImageProcessingAnalysis):
                return result
            else:
                logger.error(f"Image processing analysis returned unexpected type: {type(result)}")
                # Attempt to parse if it's a string representation
                try:
                    if isinstance(result, str):
                        parsed = json.loads(result)
                        return ImageProcessingAnalysis(**parsed)
                except Exception as parse_error:
                    logger.error(f"Failed to parse string result: {parse_error}")
                
                raise ValueError("Analysis agent did not return ImageProcessingAnalysis object.")

        except Exception as e:
            logger.error(f"Error during image processing analysis: {e}")
            logger.error(traceback.format_exc())
            # Return a default error analysis
            return ImageProcessingAnalysis(
                action_required="error",
                reasoning=f"Failed to analyze request: {e}",
                confidence=0.1,
                delegation_needed=False
            )

    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Main execution entry point. Performs analysis and returns the plan or result."""
        logger.info("Executing ImageProcessingMinion")
        run_context = context.deps if hasattr(context, "deps") else {}
        prompt = params.get("prompt") or run_context.get("prompt") # Get prompt from params or context

        if not prompt:
            return {"status": "error", "error": "No prompt provided for image processing analysis.", "minion": self.name}

        # Ensure run_context includes uploaded_files if they exist in the original context
        if "uploaded_files" not in run_context and "uploaded_files" in context:
             run_context["uploaded_files"] = context["uploaded_files"]

        # Perform analysis
        analysis_result = await self.analyze_request(prompt, run_context)

        # For now, just return the analysis result. Actual delegation/execution would happen here or be orchestrated.
        logger.info(f"ImageProcessingMinion analysis result: {analysis_result.model_dump_json(indent=2)}")
        return {
            "status": "success",
            "result_type": "analysis",
            "data": analysis_result.model_dump(),
            "minion": self.name
        } 