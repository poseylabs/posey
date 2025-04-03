import os
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
import logging
from .base import ImageProvider

logger = logging.getLogger(__name__)

class FluxProvider(ImageProvider):
    """Provider for Black Forest Labs Flux image generation models"""
    
    @property
    def provider_name(self) -> str:
        return "flux"
        
    @property
    def supported_models(self) -> List[str]:
        return ["flux-pro-1.1-ultra", "flux-pro-1.1", "flux-pro", "flux-dev"]
    
    def __init__(self):
        """Initialize the Flux provider"""
        self.api_key = os.getenv("BFL_API_KEY")
        self.api_base = os.getenv("BFL_API_BASE", "https://api.us1.bfl.ai/v1")
        
    def validate_configuration(self) -> bool:
        """Check if the provider is properly configured"""
        if not self.api_key:
            logger.warning("BFL API key not set - Flux image generation will be unavailable")
            return False
        return True
    
    def get_capabilities(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get capabilities for the specified Flux model"""
        capabilities = super().get_capabilities(model)
        
        # Common capabilities for all Flux models
        capabilities.update({
            "supports_size_adjustment": True,
            "supports_negative_prompt": True,
            "supports_seed": True,
            "supports_style": False,
            "supported_formats": ["png", "webp", "jpg", "jpeg"],
            "max_prompt_length": 4000
        })
        
        return capabilities
        
    async def generate(self, prompt: str, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using the Flux API"""
        try:
            # Get size parameters
            size = params.get("size", "1024x1024")
            
            # Parse width and height from size
            if "x" in size:
                width, height = map(int, size.split("x"))
            else:
                # Default to square image if size format is not recognized
                width = height = 1024
            
            # Get other parameters
            negative_prompt = params.get("negative_prompt", "")
            seed = params.get("seed")
            output_format = params.get("output_format", "webp")
            num_inference_steps = params.get("steps", 50)
            guidance_scale = params.get("guidance_scale", 7.5)
            
            # Log the request
            logger.info(f"Generating image with Flux {model}, size: {width}x{height}")
            
            # Prepare the request payload
            payload = {
                "prompt": prompt,
                "width": width,
                "height": height
            }
            
            # Set up parameters
            parameters = {}
            
            # Add optional parameters if provided
            if negative_prompt:
                parameters["negative_prompt"] = negative_prompt
            
            if seed is not None:
                parameters["seed"] = seed
                
            if output_format:
                parameters["output_format"] = output_format
                
            if num_inference_steps:
                parameters["num_inference_steps"] = num_inference_steps
                
            if guidance_scale:
                parameters["guidance_scale"] = guidance_scale
                
            # Add parameters to payload if any are present
            if parameters:
                payload["parameters"] = parameters
            
            # Set up headers
            headers = {
                "Accept": "application/json",
                "x-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Start time tracking
            start_time = __import__('time').time()
            
            # Make API request to initiate generation
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/{model}",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Flux API error: {error_text}")
                        return {
                            "status": "error",
                            "error": f"Flux API error: {response.status} - {error_text}",
                            "metadata": {
                                "provider": "flux",
                                "model": model
                            }
                        }
                    
                    # Get the request ID
                    result = await response.json()
                    request_id = result.get("id")
                    
                    if not request_id:
                        return {
                            "status": "error",
                            "error": "No request ID returned from Flux API",
                            "metadata": result
                        }
                    
                    # Poll for the result
                    image_url = await self._poll_for_result(session, request_id, headers)
                    
                    # Calculate duration
                    duration = __import__('time').time() - start_time
                    
                    if not image_url:
                        return {
                            "status": "error",
                            "error": "Flux image generation timed out or failed",
                            "metadata": {
                                "provider": "flux",
                                "model": model,
                                "request_id": request_id
                            }
                        }
                    
                    # Return the result
                    return {
                        "status": "success",
                        "url": image_url,
                        "metadata": {
                            "provider": "flux",
                            "model": model,
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "width": width,
                            "height": height,
                            "seed": seed,
                            "duration": duration,
                            "request_id": request_id,
                            "output_format": output_format
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error generating image with Flux: {str(e)}")
            return {
                "status": "error",
                "error": f"Flux image generation failed: {str(e)}",
                "metadata": {
                    "provider": "flux",
                    "model": model
                }
            }
    
    async def _poll_for_result(self, session: aiohttp.ClientSession, request_id: str, headers: Dict[str, str], timeout: int = 60) -> Optional[str]:
        """
        Poll for the result of a Flux image generation request
        
        Args:
            session: The aiohttp ClientSession to use
            request_id: The request ID to poll for
            headers: The headers to use for the request
            timeout: Maximum time to wait in seconds
            
        Returns:
            The image URL or None if timed out or failed
        """
        poll_interval = 1  # seconds
        total_time = 0
        
        while total_time < timeout:
            try:
                async with session.get(
                    f"{self.api_base}/get_result?id={request_id}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Error polling Flux: {response.status}")
                        await asyncio.sleep(poll_interval)
                        total_time += poll_interval
                        continue
                    
                    result = await response.json()
                    status = result.get("status")
                    
                    if status == "Ready":
                        # Image is ready, return the URL
                        return result.get("result", {}).get("sample")
                    elif status in ["error", "Error"]:
                        # Error occurred
                        logger.error(f"Flux generation error: {result.get('error', 'Unknown error')}")
                        return None
                    
                    # Still processing, wait and try again
                    await asyncio.sleep(poll_interval)
                    total_time += poll_interval
                    
            except Exception as e:
                logger.error(f"Error polling Flux API: {str(e)}")
                await asyncio.sleep(poll_interval)
                total_time += poll_interval
        
        # Timed out
        logger.warning(f"Flux generation for request {request_id} timed out after {timeout} seconds")
        return None 
