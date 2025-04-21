from typing import Dict, Any
from app.abilities.base import BaseAbility
from app.config import logger
import asyncio
import base64
from hashlib import md5
from dotenv import load_dotenv
from app.abilities.image.provider_registry import get_registry
from app.utils.file_storage import upload_file, copy_generated_image, get_file_url
import logging
import time
import uuid

logger = logging.getLogger(__name__)

class ImageAbility(BaseAbility):
    """
    Ability to generate and manipulate images using various providers.
    
    This ability uses the provider system to generate images using different
    providers like DALL-E, Stable Diffusion, Flux, etc. It provides a uniform
    interface for image generation regardless of the underlying provider.
    """
    
    def __init__(self):
        """Initialize the image ability with available providers."""
        super().__init__()
        
        # Get the provider registry
        self.provider_registry = get_registry()
        
        # Cache supported models for quick access
        self.supported_models = self.provider_registry.get_all_supported_models()
        
        # Log the available providers
        providers = self.provider_registry.list_providers()
        logger.info(f"Initialized image ability with {len(providers)} providers: {', '.join(providers)}")
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute image generation with the specified parameters.
        
        Args:
            params (Dict[str, Any]): Parameters for image generation
                - prompt: Text prompt for the image
                - config: Configuration for generation
                  - adapter: Provider to use (e.g., "dalle", "flux")
                  - model: Model to use (e.g., "dall-e-3")
                  - style: Style for the image
                  - width: Width of the image
                  - height: Height of the image
                  - negative_prompt: Things to avoid in the image
                  - seed: Seed for reproducibility
                - user_id: ID of the user generating the image
                - agent_id: ID of the agent generating the image
                
        Returns:
            Dict[str, Any]: Result of image generation
                - status: "success" or "error"
                - url: URL to the generated image (if successful)
                - error: Error message (if failed)
                - metadata: Additional information about the generation
        """
        try:
            # Extract the prompt
            prompt = params.get("prompt")
            if not prompt:
                raise ValueError("Prompt is required for image generation")
                
            # Get configuration
            config = params.get("config", {})
            
            # Extract user and agent IDs for storage
            user_id = params.get("user_id")
            agent_id = params.get("agent_id")
            
            # Extract provider and model
            provider_name = config.get("adapter")
            model = config.get("model")
            
            # Apply defaults if not provided
            if not provider_name:
                # Default to DALL-E if available, otherwise use the first available provider
                providers = self.provider_registry.list_providers()
                provider_name = "dalle" if "dalle" in providers else (providers[0] if providers else None)
                
                if not provider_name:
                    raise ValueError("No image providers available")
                    
                logger.info(f"No provider specified, using default: {provider_name}")
            
            # Get the provider instance
            provider = self.provider_registry.get_provider(provider_name)
            if not provider:
                available_providers = self.provider_registry.list_providers()
                raise ValueError(f"Invalid provider: {provider_name}. Available providers: {available_providers}")
            
            # If no model specified, use the provider's default
            if not model:
                model = provider.default_model
                if not model:
                    raise ValueError(f"Provider {provider_name} has no available models")
                    
                logger.info(f"No model specified, using default: {model}")
                
            # Check if the model is supported by this provider
            if model not in provider.supported_models:
                available_models = provider.supported_models
                raise ValueError(f"Invalid model {model} for provider {provider_name}. Available models: {available_models}")
            
            # Extract technical parameters
            size = self._extract_size_parameter(config, provider, model)
            style = config.get("style")
            quality = config.get("quality", "standard")
            negative_prompt = config.get("negative_prompt")
            seed = config.get("seed")
            output_format = config.get("output_format", "webp")
            
            # Prepare generation parameters
            generation_params = {
                "size": size,
                "style": style,
                "quality": quality,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "output_format": output_format
            }
            
            # Log the request
            logger.info(f"Generating image with {provider_name} ({model}): '{prompt}'")
            
            # Generate the image
            start_time = time.time()
            result = await provider.generate(prompt, model, generation_params)
            duration = time.time() - start_time
            
            # Check if generation was successful
            if result.get("status") != "success":
                logger.error(f"Image generation failed: {result.get('error')}")
                return result
                
            # If we have image data and need to store it
            if result.get("url") and user_id and agent_id:
                try:
                    # Store the generated image
                    upload_url = await self._store_generated_image(
                        result["url"],
                        user_id,
                        agent_id,
                        prompt,
                        provider_name,
                        model,
                        output_format
                    )
                    
                    # Update the result with the stored URL
                    result["url"] = upload_url
                except Exception as e:
                    logger.error(f"Error storing generated image: {str(e)}")
                    # Continue with the original URL if storage fails
            
            # Add overall duration to metadata
            if "metadata" in result:
                result["metadata"]["total_duration"] = duration
                
            return result
            
        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "metadata": {
                    "provider": provider_name if 'provider_name' in locals() else None,
                    "model": model if 'model' in locals() else None
                }
            }
    
    def _extract_size_parameter(self, config: Dict[str, Any], provider: Any, model: str) -> str:
        """
        Extract and validate the size parameter from configuration.
        
        This method handles different ways of specifying image size, including:
        - Direct size specification (e.g., "1024x1024")
        - Width and height as separate parameters
        - Aspect ratio (e.g., "16:9")
        
        Args:
            config: The configuration dictionary
            provider: The provider instance
            model: The model to use
            
        Returns:
            str: The size parameter in the format expected by the provider
        """
        # Get capabilities to check supported sizes
        capabilities = provider.get_capabilities(model)
        supported_sizes = capabilities.get("supported_sizes", [])
        
        # Check for direct size specification
        size = config.get("size")
        if size:
            # Verify the size is supported
            if supported_sizes and size not in supported_sizes:
                logger.warning(f"Size {size} not explicitly supported by {provider.provider_name}. Supported sizes: {supported_sizes}")
            return size
            
        # Check for width and height
        width = config.get("width")
        height = config.get("height")
        if width and height:
            size = f"{width}x{height}"
            # Check if this exact size is supported
            if supported_sizes and size not in supported_sizes:
                logger.warning(f"Size {size} not explicitly supported by {provider.provider_name}. Supported sizes: {supported_sizes}")
            return size
            
        # Check for aspect ratio
        aspect_ratio = config.get("aspect_ratio")
        if aspect_ratio:
            # Some providers use aspect ratio notation like "16:9"
            if supported_sizes and aspect_ratio not in supported_sizes:
                logger.warning(f"Aspect ratio {aspect_ratio} not explicitly supported by {provider.provider_name}. Supported sizes: {supported_sizes}")
            return aspect_ratio
        
        # If we get here, use the default size for the model
        if supported_sizes:
            return supported_sizes[0]
        else:
            # Fallback to a common default
            return "1024x1024"
    
    async def _store_generated_image(
        self, 
        image_url: str, 
        user_id: str, 
        agent_id: str, 
        prompt: str,
        provider: str,
        model: str,
        output_format: str = "webp"
    ) -> str:
        """
        Store a generated image in DigitalOcean Spaces.
        
        Args:
            image_url: URL or data URI of the image
            user_id: ID of the user who generated the image
            agent_id: ID of the agent that generated the image
            prompt: The prompt used to generate the image
            provider: The provider used for generation
            model: The model used for generation
            output_format: The image format (png, webp, etc.)
            
        Returns:
            str: URL of the stored image
        """
        # Generate a unique ID for the image
        image_id = str(uuid.uuid4())
        
        # Generate a file name using a hash of the prompt
        op_id = md5(prompt.encode()).hexdigest()[:8]
        file_name = f"{op_id}_{image_id}.{output_format}"
        
        # For base64 data URLs, extract the file extension from the header and decode
        if image_url.startswith("data:"):
            try:
                header, b64_data = image_url.split(",", 1)
                file_bytes = base64.b64decode(b64_data)
                # Use the synchronous upload function within an asyncio thread
                return await asyncio.to_thread(upload_file, file_bytes, user_id, agent_id, file_name)
            except Exception as e:
                logger.error(f"Error processing base64 image: {str(e)}")
                # Return original URL if processing fails
                return image_url
        
        # For HTTP URLs, simply download and re-upload the file
        elif image_url.startswith("http"):
            try:
                # Use the async copy function directly
                return await copy_generated_image(image_url, user_id, agent_id, file_name)
            except Exception as e:
                logger.error(f"Error copying image from URL: {str(e)}")
                # Return original URL if copy fails
                return image_url
        
        # If the format is unrecognized, return the original URL
        return image_url

    async def generate_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate an image with the specified parameters
        
        This is a convenience method that maps to execute()
        """
        return await self.execute(kwargs)
            
    async def optimize_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize image generation prompt and parameters"""
        try:
            request = params.get("request")
            if not request:
                raise ValueError("Request is required for optimization")
                
            config = params.get("config", {})
            metadata = params.get("metadata", {})
            
            # TODO: Implement actual prompt optimization
            return {
                "status": "success",
                "optimization": {
                    "prompt": request,  # Enhanced prompt would go here
                    "parameters": config,
                    "reasoning": {
                        "prompt_changes": "No optimization applied yet",
                        "parameter_adjustments": "Using default parameters"
                    },
                    "recommendations": [
                        "Consider adding more detail to the prompt",
                        "Consider specifying art style"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing prompt: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 
