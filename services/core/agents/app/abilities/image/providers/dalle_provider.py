import os
from typing import Dict, Any, List, Optional
import aiohttp
import logging
import base64
from app.abilities.image.providers.base import ImageProvider

logger = logging.getLogger(__name__)

class DalleProvider(ImageProvider):
    """Provider for OpenAI's DALL-E image generation models"""
    
    @property
    def provider_name(self) -> str:
        return "dalle"
        
    @property
    def supported_models(self) -> List[str]:
        return ["dall-e-3", "dall-e-2"]
    
    def __init__(self):
        """Initialize the DALL-E provider"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.organization = os.getenv("OPENAI_ORGANIZATION")
        
    def validate_configuration(self) -> bool:
        """Check if the provider is properly configured"""
        if not self.api_key:
            logger.warning("OpenAI API key not set - DALL-E image generation will be unavailable")
            return False
        return True
    
    def get_capabilities(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get capabilities for the specified DALL-E model"""
        model = model or self.default_model
        
        # Base capabilities
        capabilities = super().get_capabilities(model)
        
        # Common capabilities for all DALL-E models
        capabilities.update({
            "supports_size_adjustment": True,
            "supports_negative_prompt": False,  # DALL-E doesn't support negative prompts natively
            "supports_style": False,
            "supported_formats": ["png", "webp"]
        })
        
        # Model-specific capabilities
        if model == "dall-e-3":
            capabilities.update({
                "supports_size_adjustment": True,
                "supported_sizes": ["1024x1024", "1792x1024", "1024x1792"],
                "max_prompt_length": 4000,
                "supports_style": True,
                "supported_styles": ["vivid", "natural"],
                "supports_quality": True,
                "supported_quality": ["standard", "hd"]
            })
        elif model == "dall-e-2":
            capabilities.update({
                "supported_sizes": ["256x256", "512x512", "1024x1024"],
                "max_prompt_length": 1000
            })
            
        return capabilities
        
    async def generate(self, prompt: str, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using the DALL-E API"""
        try:
            # Get parameters with defaults
            size = params.get("size", "1024x1024")
            quality = params.get("quality", "standard")
            style = params.get("style", "vivid")
            output_format = params.get("output_format", "webp")
            response_format = "b64_json" if params.get("return_data", False) else "url"
            
            # Log the request
            logger.info(f"Generating image with {model}, size: {size}, style: {style}, quality: {quality}")
            
            # Set up the headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            if self.organization:
                headers["OpenAI-Organization"] = self.organization
                
            # Set up the request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "n": 1,
                "size": size,
                "response_format": response_format
            }
            
            # Add model-specific parameters
            if model == "dall-e-3":
                payload["quality"] = quality
                payload["style"] = style
                
            # Start time tracking
            start_time = __import__('time').time()
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/images/generations",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DALL-E API error: {error_text}")
                        return {
                            "status": "error",
                            "error": f"DALL-E API error: {response.status} - {error_text}",
                            "metadata": {
                                "provider": "dalle",
                                "model": model
                            }
                        }
                    
                    # Get the response data
                    result = await response.json()
                    
                    # Calculate duration
                    duration = __import__('time').time() - start_time
                    
                    # Check if we have an image
                    if not result.get("data") or len(result["data"]) == 0:
                        return {
                            "status": "error",
                            "error": "No image generated by DALL-E API",
                            "metadata": result
                        }
                    
                    # Get the first image from the response
                    image_data = result["data"][0]
                    
                    # Extract image URL or base64 data
                    if response_format == "url":
                        image_url = image_data.get("url")
                        image_b64 = None
                    else:  # b64_json
                        image_url = None
                        image_b64 = image_data.get("b64_json")
                    
                    # Return the result
                    metadata = {
                        "provider": "dalle",
                        "model": model,
                        "prompt": prompt,
                        "size": size,
                        "style": style if model == "dall-e-3" else None,
                        "quality": quality if model == "dall-e-3" else None,
                        "duration": duration,
                        "revised_prompt": image_data.get("revised_prompt"),
                        "output_format": output_format
                    }
                    
                    if image_url:
                        return {
                            "status": "success",
                            "url": image_url,
                            "metadata": metadata
                        }
                    elif image_b64:
                        return {
                            "status": "success",
                            "data": image_b64,
                            "metadata": metadata
                        }
                    else:
                        return {
                            "status": "error",
                            "error": "No image URL or data in DALL-E response",
                            "metadata": metadata
                        }
            
        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {str(e)}")
            return {
                "status": "error",
                "error": f"DALL-E image generation failed: {str(e)}",
                "metadata": {
                    "provider": "dalle",
                    "model": model
                }
            } 
