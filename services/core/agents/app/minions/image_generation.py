from pydantic_ai import RunContext, Agent
from pydantic import BaseModel, Field
from app.abilities.image_ability import ImageAbility
from app.config import logger
from app.config.prompts.base import (
    generate_base_prompt,
    get_default_context,
    BasePromptContext,
    UserContext,
    MemoryContext,
    SystemContext
)
from app.config.defaults import LLM_CONFIG
from app.minions.base import BaseMinion
from typing import Dict, Any, List, Optional
import time
from datetime import datetime

class ImageRequest(BaseModel):
    """Model for image generation requests"""
    prompt: str
    style: str = "realistic"
    size: str = "1024x1024"
    model: str = "dalle-3"
    color_palette: Optional[List[str]] = Field(default=None, description="Optional list of color hex values to use in the generated image")
    reference_images: Optional[List[str]] = Field(default=None, description="Optional list of URLs to reference images to guide the generation")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata for the request")

class ImageResponse(BaseModel):
    """Model for image generation responses"""
    status: str
    url: str | None = None
    error: str | None = None
    error_type: str | None = None
    attempted_operation: str | None = None
    metadata: dict | None = None

class ImageGenerationMinion(BaseMinion):
    """AI Image Generation minion"""

    def __init__(self):
        super().__init__(
            name="image_generation",
            description="Generate images using AI models"
        )

    def setup(self):
        """Initialize minion-specific components"""
        self.ability = ImageAbility()
        
        # Get base prompt with default context for initialization
        base_prompt = generate_base_prompt(get_default_context())
        
        # Override system prompt to include base prompt
        custom_system_prompt = "\n".join([
            base_prompt,  # Start with shared base prompt
            self.get_system_prompt()
        ])
        
        logger.debug(f"System prompt configured for image generation minion")

        # Create agent for prompt optimization
        self.agent = self.create_agent(result_type=ImageRequest, model_key="reasoning")
        logger.info(f"Image generation agent created with model: {LLM_CONFIG['reasoning']['model']}")

    def create_prompt_context(self, context: Dict[str, Any], image_data: Dict[str, Any] = None) -> BasePromptContext:
        """Create a properly structured prompt context for image generation operations"""
        # Extract user information from context
        user_id = context.get("user_id", "anonymous")
        user_name = context.get("user_name", "User")
        
        # Create user context
        user_context = UserContext(
            id=user_id,
            name=user_name,
            preferences=context.get("preferences", {}),
        )
        
        # Create memory context
        memory_context = MemoryContext(
            recent_memories=context.get("recent_memories", []),
            relevant_memories=context.get("relevant_memories", [])
        )
        
        # Create system context
        system_context = SystemContext(
            current_time=context.get("timestamp", datetime.now().isoformat()),
            agent_capabilities=["image_generation", "prompt_optimization"],
            uploaded_files=context.get("uploaded_files", []),
            **context.get("system", {})
        )
        
        # Add image-specific data to the appropriate context
        if image_data:
            # Add prompt-related info to user context
            if "prompt" in image_data:
                user_context.prompt = image_data["prompt"]
            if "style" in image_data:
                user_context.style_preference = image_data["style"]
                
            # Add image-specific fields to system context
            if "model" in image_data:
                system_context.model = image_data["model"]
            if "operation" in image_data:
                system_context.current_operation = image_data["operation"]
            if "reference_images" in image_data:
                system_context.reference_images = image_data["reference_images"]
        
        # Return complete context
        return BasePromptContext(
            user=user_context,
            memory=memory_context,
            system=system_context
        )

    async def optimize_prompt(self, prompt: str, style: str = "realistic", color_palette: Optional[List[str]] = None, reference_images: Optional[List[str]] = None, context: Dict[str, Any] = None) -> ImageRequest:
        """Optimize the prompt for image generation"""
        start_time = time.time()
        context = context or {}
        
        try:
            # Create image-specific context data
            image_data = {
                "prompt": prompt,
                "style": style,
                "operation": "optimize_prompt",
                "color_palette": color_palette,
                "reference_images": reference_images
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, image_data)
            
            # Get user prompt from configuration
            user_prompt = self.get_task_prompt(
                "prompt_optimization",
                context=prompt_context,
                original_prompt=prompt,
                requested_style=style,
                color_palette=color_palette if color_palette else "No specific color palette provided",
                reference_images=reference_images if reference_images else "No reference images provided"
            )
            
            # Create the messages array
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": user_prompt}
            ]
            
            # Run the agent with the messages
            logger.info(f"Optimizing image prompt: {prompt[:100]}...")
            result = await self.agent.run(user_prompt)
            
            # Log the result
            if isinstance(result, ImageRequest):
                optimized_request = result
                logger.info(f"Optimized prompt: {optimized_request.prompt[:100]}...")
            else:
                logger.warning(f"Unexpected result type: {type(result)}")
                # Create default image request with original prompt
                optimized_request = ImageRequest(
                    prompt=prompt,
                    style=style,
                    color_palette=color_palette,
                    reference_images=reference_images
                )
            
            execution_time = time.time() - start_time
            logger.info(f"Prompt optimization completed in {execution_time:.2f}s")
            return optimized_request
            
        except Exception as e:
            logger.error(f"Error optimizing prompt: {str(e)}")
            execution_time = time.time() - start_time
            logger.info(f"Optimization failed after {execution_time:.2f}s")
            
            # Get detailed error info
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error traceback:\n{error_traceback}")
            
            # Add error information to metadata
            optimized_request = ImageRequest(
                prompt=prompt,
                style=style,
                color_palette=color_palette,
                reference_images=reference_images,
                metadata={
                    "error": str(e),
                    "error_type": "prompt_optimization_exception",
                    "attempted_operation": "optimize_prompt",
                    "execution_time": execution_time,
                    "error_traceback": error_traceback.split("\n")[-3:]
                }
            )
            return optimized_request
    
    async def generate_image(self, params: Dict[str, Any]) -> ImageResponse:
        """Generate an image using the image ability"""
        start_time = time.time()
        
        try:
            # Extract parameters for image generation
            prompt = params.get("prompt", "")
            style = params.get("style", "realistic")
            size = params.get("size", "1024x1024")
            model = params.get("model", "dalle-3")
            color_palette = params.get("color_palette", None)
            reference_images = params.get("reference_images", None)
            context = params.get("context", {})
            
            if not prompt:
                return ImageResponse(
                    status="error",
                    error="No prompt provided",
                    error_type="missing_parameter",
                    attempted_operation="generate_image",
                    metadata={
                        "execution_time": time.time() - start_time,
                        "minion": "image_generation"
                    }
                )
            
            # Create image-specific context data
            image_data = {
                "prompt": prompt,
                "style": style,
                "model": model,
                "operation": "generate_image",
                "color_palette": color_palette,
                "reference_images": reference_images
            }
            
            # Create proper prompt context for logging and future use
            prompt_context = self.create_prompt_context(context, image_data)
            
            # Optimize the prompt if needed
            if params.get("optimize_prompt", True):
                image_request = await self.optimize_prompt(
                    prompt, 
                    style, 
                    color_palette, 
                    reference_images, 
                    context
                )
                prompt = image_request.prompt
                style = image_request.style
                logger.info(f"Using optimized prompt: {prompt[:100]}...")

            # Generate the image
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            # Log if reference images are being used
            if reference_images and len(reference_images) > 0:
                logger.info(f"Using {len(reference_images)} reference images for generation")
                
            result = await self.ability.generate_image(
                prompt=prompt,
                style=style,
                size=size,
                model=model,
                reference_images=reference_images
            )
            
            execution_time = time.time() - start_time
            logger.info(f"Image generation completed in {execution_time:.2f}s")
            
            # Create response
            if result.get("success", False):
                return ImageResponse(
                    status="success",
                    url=result.get("url"),
                    metadata={
                        "model": model,
                        "size": size,
                        "style": style,
                        "color_palette": color_palette,
                        "reference_images": reference_images,
                        "execution_time": execution_time,
                        "minion": "image_generation"
                    }
                )
            else:
                return ImageResponse(
                    status="error",
                    error=result.get("error", "Unknown error"),
                    error_type="image_generation_failed",
                    attempted_operation="generate_image",
                    metadata={
                        "model": model,
                        "size": size,
                        "style": style,
                        "execution_time": execution_time,
                        "minion": "image_generation",
                        "result": result
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            execution_time = time.time() - start_time
            logger.info(f"Generation failed after {execution_time:.2f}s")
            
            # Get detailed error info
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error traceback:\n{error_traceback}")
            
            return ImageResponse(
                status="error",
                error=str(e),
                error_type="image_generation_exception",
                attempted_operation="generate_image",
                metadata={
                    "execution_time": execution_time,
                    "minion": "image_generation",
                    "error_traceback": error_traceback.split("\n")[-3:],
                    "parameters": {
                        "style": style if 'style' in locals() else params.get("style", "realistic"),
                        "size": size if 'size' in locals() else params.get("size", "1024x1024"),
                        "model": model if 'model' in locals() else params.get("model", "dalle-3")
                    }
                }
            )
    
    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute image generation minion operations"""
        start_time = time.time()
        minion_name = self.name
        
        try:
            operation = params.get("operation", "generate")
            
            # Extract context from RunContext
            run_context = context.deps if hasattr(context, "deps") else {}
            
            # Add context to params
            params["context"] = run_context
            
            if operation == "generate":
                response = await self.generate_image(params)
                if isinstance(response, ImageResponse) and response.metadata:
                    response.metadata["minion"] = minion_name
                return response.model_dump()
            elif operation == "optimize_prompt":
                image_request = await self.optimize_prompt(
                    params.get("prompt", ""),
                    params.get("style", "realistic"),
                    params.get("color_palette", None),
                    params.get("reference_images", None),
                    run_context
                )
                if isinstance(image_request, ImageRequest) and image_request.metadata:
                    image_request.metadata["minion"] = minion_name
                return image_request.model_dump()
            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation: {operation}",
                    "error_type": "invalid_operation",
                    "attempted_operation": operation,
                    "metadata": {
                        "available_operations": ["generate", "optimize_prompt"],
                        "execution_time": time.time() - start_time,
                        "minion": minion_name
                    }
                }
        except Exception as e:
            logger.error(f"Error in image generation minion execute: {str(e)}")
            
            # Get detailed error info
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Traceback: {error_traceback}")
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": "image_generation_minion_exception",
                "attempted_operation": params.get("operation", "generate"),
                "url": None,
                "metadata": {
                    "error_traceback": error_traceback.split("\n")[-3:],
                    "execution_time": time.time() - start_time,
                    "minion": minion_name,
                    "parameters": {k: v for k, v in params.items() if k != "prompt"}
                }
            }
