import os
from typing import Dict, Any, List
import aiohttp
import asyncio
import logging

# Import the base provider interface
# Note: In a real plugin, this would be imported from Posey's package
from app.abilities.image.providers.base import ImageProvider

logger = logging.getLogger(__name__)

class MidjourneyProvider(ImageProvider):
    """Plugin provider for Midjourney image generation via third-party API"""
    
    @property
    def provider_name(self) -> str:
        return "midjourney"
        
    @property
    def supported_models(self) -> List[str]:
        return ["mj-6", "mj-5.2", "mj-5.1", "mj-5.0", "niji-5"]
    
    def __init__(self):
        """Initialize the Midjourney provider"""
        self.api_url = os.getenv("MIDJOURNEY_API_URL")
        self.api_key = os.getenv("MIDJOURNEY_API_KEY")
        
    def validate_configuration(self) -> bool:
        """Check if the provider is properly configured"""
        if not self.api_url or not self.api_key:
            logger.warning("Midjourney API configuration incomplete - Midjourney image generation will be unavailable")
            return False
        return True
    
    def get_capabilities(self, model: str = None) -> Dict[str, Any]:
        """Get capabilities for the specified model"""
        capabilities = super().get_capabilities(model)
        
        # Set Midjourney-specific capabilities
        capabilities.update({
            "supports_size_adjustment": True,
            "supported_sizes": ["1:1", "2:3", "3:2", "16:9", "9:16"],
            "supported_formats": ["png", "webp"],
            "max_prompt_length": 6000,
            "supports_negative_prompt": True,
            "supports_seed": True,
            "supports_style": True,
            "supports_version_control": True,
            "supports_upscaling": True,
            "supports_variations": True,
            "supports_image_to_image": True
        })
            
        return capabilities
        
    async def generate(self, prompt: str, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using the Midjourney API"""
        try:
            # Process parameters
            aspect_ratio = params.get("size", "1:1")
            style = params.get("style", "raw")
            negative_prompt = params.get("negative_prompt", "")
            seed = params.get("seed")
            output_format = params.get("output_format", "webp")
            
            # Log the request
            logger.info(f"Generating image with Midjourney {model}, ratio: {aspect_ratio}, style: {style}")
            
            async with aiohttp.ClientSession() as session:
                # Set up payload
                payload = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "model_version": model,
                    "aspect_ratio": aspect_ratio,
                    "style": style,
                    "output_format": output_format
                }
                
                if seed:
                    payload["seed"] = seed
                
                # Set headers
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Start time tracking
                start_time = __import__('time').time()
                
                # Make API request
                async with session.post(
                    f"{self.api_url}/imagine",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Midjourney API error: {error_text}")
                        return {
                            "status": "error",
                            "error": f"Midjourney API error: {response.status} - {error_text}",
                            "metadata": {
                                "provider": "midjourney",
                                "model": model
                            }
                        }
                    
                    # Get response data
                    result = await response.json()
                    
                    # Calculate duration
                    duration = __import__('time').time() - start_time
                    
                    # Check if we have job ID or direct result
                    job_id = result.get("job_id")
                    if job_id:
                        # Poll for result
                        image_url = await self._poll_for_result(job_id, headers)
                        if not image_url:
                            return {
                                "status": "error",
                                "error": "Midjourney generation timed out",
                                "metadata": {
                                    "provider": "midjourney",
                                    "model": model,
                                    "job_id": job_id
                                }
                            }
                    else:
                        # Direct result
                        image_url = result.get("image_url")
                        if not image_url:
                            return {
                                "status": "error",
                                "error": "No image URL in Midjourney response",
                                "metadata": result
                            }
                    
                    # Return the result
                    return {
                        "status": "success",
                        "url": image_url,
                        "metadata": {
                            "provider": "midjourney",
                            "model": model,
                            "prompt": prompt,
                            "aspect_ratio": aspect_ratio,
                            "style": style,
                            "seed": seed,
                            "duration": duration,
                            "job_id": job_id,
                            "output_format": output_format
                        }
                    }
            
        except Exception as e:
            logger.error(f"Error generating image with Midjourney: {str(e)}")
            return {
                "status": "error",
                "error": f"Midjourney image generation failed: {str(e)}",
                "metadata": {
                    "provider": "midjourney",
                    "model": model
                }
            }
            
    async def _poll_for_result(self, job_id: str, headers: Dict[str, str], timeout: int = 120) -> str:
        """
        Poll the Midjourney API for a job result
        
        Args:
            job_id: The job ID to poll for
            headers: Request headers for authentication
            timeout: Maximum time to wait in seconds
            
        Returns:
            Image URL or None if timed out
        """
        async with aiohttp.ClientSession() as session:
            poll_interval = 3  # seconds
            total_time = 0
            
            while total_time < timeout:
                try:
                    async with session.get(
                        f"{self.api_url}/job/{job_id}",
                        headers=headers
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"Error polling Midjourney: {response.status}")
                            await asyncio.sleep(poll_interval)
                            total_time += poll_interval
                            continue
                        
                        result = await response.json()
                        status = result.get("status")
                        
                        if status == "completed":
                            return result.get("image_url")
                        elif status == "failed":
                            logger.error(f"Midjourney job failed: {result.get('error')}")
                            return None
                        
                        # Still processing, wait and try again
                        await asyncio.sleep(poll_interval)
                        total_time += poll_interval
                        
                except Exception as e:
                    logger.error(f"Error polling Midjourney: {str(e)}")
                    await asyncio.sleep(poll_interval)
                    total_time += poll_interval
            
            # Timed out
            logger.warning(f"Midjourney job {job_id} timed out after {timeout} seconds")
            return None


# Register this provider with Posey's plugin system
try:
    from app.abilities.image.providers import register_external_provider
    register_external_provider(MidjourneyProvider)
    logger.info("Registered Midjourney provider plugin")
except ImportError:
    logger.warning("Could not register Midjourney provider plugin - Posey provider API not found") 
