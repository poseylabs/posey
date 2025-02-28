import os
from typing import Dict, Any, List, Optional
import aiohttp
import base64
import logging
from .base import ImageProvider

logger = logging.getLogger(__name__)

class StableDiffusionProvider(ImageProvider):
    """Provider for Stability AI's Stable Diffusion image generation models"""
    
    @property
    def provider_name(self) -> str:
        return "stable-diffusion"
        
    @property
    def supported_models(self) -> List[str]:
        return ["sd3", "ultra", "core"]
    
    def __init__(self):
        """Initialize the Stable Diffusion provider"""
        self.api_key = os.getenv("STABILITY_API_KEY")
        self.api_base = os.getenv("STABILITY_API_BASE", "https://api.stability.ai")
        
    def validate_configuration(self) -> bool:
        """Check if the provider is properly configured"""
        if not self.api_key:
            logger.warning("STABILITY_API_KEY not set - Stable Diffusion image generation will be unavailable")
            return False
        return True
    
    def get_capabilities(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get capabilities for the specified Stable Diffusion model"""
        capabilities = super().get_capabilities(model)
        
        # Common capabilities for all Stable Diffusion models
        capabilities.update({
            "supports_size_adjustment": True,
            "supports_negative_prompt": True,
            "supports_seed": True,
            "supports_style": True,
            "supports_image_to_image": True,
            "supported_formats": ["png", "webp", "jpg", "jpeg"],
            "supported_aspect_ratios": ["16:9", "1:1", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"],
            "max_prompt_length": 10000
        })
        
        # Model-specific capabilities
        if model == "sd3":
            capabilities.update({
                "supports_style_presets": True,
                "supported_style_presets": [
                    "3d-model", "analog-film", "anime", "cinematic", "comic-book",
                    "digital-art", "fantasy-art", "isometric", "line-art", "low-poly",
                    "modeling-compound", "neon-punk", "origami", "photographic",
                    "pixel-art", "tile-texture"
                ]
            })
        
        return capabilities
        
    async def generate(self, prompt: str, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using the Stable Diffusion API"""
        try:
            # Get size parameters
            size = params.get("size", "1024x1024")
            
            # Parse dimensions - depending on the format (1024x1024 or 16:9)
            if "x" in size and ":" not in size:
                # Exact dimensions format (e.g., 1024x1024)
                width, height = map(int, size.split("x"))
                aspect_ratio = self._calculate_aspect_ratio(width, height)
            elif ":" in size:
                # Aspect ratio format (e.g., 16:9)
                aspect_ratio = size
                # Set reasonable dimensions based on aspect ratio
                width, height = self._dimensions_from_aspect_ratio(aspect_ratio, 1024)
            else:
                # Default to square if format not recognized
                width = height = 1024
                aspect_ratio = "1:1"
            
            # Get other parameters
            negative_prompt = params.get("negative_prompt", "")
            seed = params.get("seed")
            style_preset = params.get("style", "")
            output_format = params.get("output_format", "webp")
            
            # Log the request
            logger.info(f"Generating image with StableDiffusion {model}, aspect ratio: {aspect_ratio}")
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                # Create multipart writer
                with aiohttp.MultipartWriter("form-data") as multipart:
                    # Add prompt
                    part = multipart.append(prompt)
                    part.set_content_disposition("form-data", name="prompt")
                    
                    # Add required empty field
                    part = multipart.append("")
                    part.set_content_disposition("form-data", name="none")
                    
                    # Add output format
                    part = multipart.append(output_format)
                    part.set_content_disposition("form-data", name="output_format")
                    
                    # Add negative prompt if provided
                    if negative_prompt:
                        part = multipart.append(negative_prompt)
                        part.set_content_disposition("form-data", name="negative_prompt")
                    
                    # Add seed if provided
                    if seed is not None:
                        part = multipart.append(str(seed))
                        part.set_content_disposition("form-data", name="seed")
                    
                    # Add style preset if provided
                    if style_preset:
                        part = multipart.append(style_preset)
                        part.set_content_disposition("form-data", name="style_preset")
                    
                    # Add aspect ratio
                    part = multipart.append(aspect_ratio)
                    part.set_content_disposition("form-data", name="aspect_ratio")
                    
                    # Add image for image-to-image if provided
                    has_image = False
                    init_image = params.get("init_image")
                    if init_image:
                        part = multipart.append(init_image)
                        part.set_content_disposition("form-data", name="image", filename="image.png")
                        part.headers[aiohttp.hdrs.CONTENT_TYPE] = "image/png"  # Assuming PNG format
                        
                        # Add strength parameter for image-to-image
                        strength = str(params.get("strength", 0.7))
                        part = multipart.append(strength)
                        part.set_content_disposition("form-data", name="strength")
                        has_image = True
                
                # Set up headers
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
                
                # Determine which endpoint to use based on the model
                url = f"{self.api_base}/stable-image/generate/{model}"
                
                # Start time tracking
                start_time = __import__('time').time()
                
                # Make the API request
                async with session.post(
                    url,
                    data=multipart,
                    headers=headers,
                    timeout=60
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Stable Diffusion API error: {response.status} - {error_text}")
                        return {
                            "status": "error",
                            "error": f"Stable Diffusion API error: {response.status} - {error_text}",
                            "metadata": {
                                "provider": "stable-diffusion",
                                "model": model
                            }
                        }
                    
                    # Get the response data
                    result = await response.json()
                    
                    # Calculate duration
                    duration = __import__('time').time() - start_time
                    
                    # Extract image data - check for different response formats
                    if "base64" in result:
                        image_data = result["base64"]
                        image_url = f"data:image/{output_format};base64,{image_data}"
                    elif "image" in result:
                        image_data = result["image"]
                        image_url = f"data:image/{output_format};base64,{image_data}"
                    elif "output" in result:
                        image_url = result["output"]
                    elif "url" in result:
                        image_url = result["url"]
                    else:
                        return {
                            "status": "error",
                            "error": "No image data or URL in Stable Diffusion response",
                            "metadata": result
                        }
                    
                    # Return the result
                    return {
                        "status": "success",
                        "url": image_url,
                        "metadata": {
                            "provider": "stable-diffusion",
                            "model": model,
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "aspect_ratio": aspect_ratio,
                            "width": width,
                            "height": height,
                            "seed": seed if seed is not None else result.get("seed"),
                            "duration": duration,
                            "output_format": output_format,
                            "is_image_to_image": has_image,
                            "style_preset": style_preset,
                            "finish_reason": result.get("finish_reason")
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error generating image with Stable Diffusion: {str(e)}")
            return {
                "status": "error",
                "error": f"Stable Diffusion image generation failed: {str(e)}",
                "metadata": {
                    "provider": "stable-diffusion",
                    "model": model
                }
            }
    
    def _calculate_aspect_ratio(self, width: int, height: int) -> str:
        """
        Calculate the closest standard aspect ratio based on dimensions
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            The closest standard aspect ratio (e.g., "16:9", "1:1")
        """
        ratio = width / height
        standard_ratios = {
            "16:9": 16/9,
            "1:1": 1,
            "21:9": 21/9,
            "2:3": 2/3,
            "3:2": 3/2,
            "4:5": 4/5,
            "5:4": 5/4,
            "9:16": 9/16,
            "9:21": 9/21
        }
        
        # Find the closest standard ratio
        closest_ratio = min(standard_ratios.items(), key=lambda x: abs(x[1] - ratio))
        return closest_ratio[0]

    def _dimensions_from_aspect_ratio(self, aspect_ratio: str, base_size: int = 1024) -> tuple:
        """
        Calculate width and height from aspect ratio
        
        Args:
            aspect_ratio: Aspect ratio (e.g., "16:9")
            base_size: Base size for dimension calculation
            
        Returns:
            (width, height) tuple
        """
        if ":" not in aspect_ratio:
            return (base_size, base_size)
            
        width_ratio, height_ratio = map(int, aspect_ratio.split(":"))
        ratio = width_ratio / height_ratio
        
        # Keep total pixels approximately constant
        if ratio >= 1:
            # Wider than tall
            height = int(base_size / (ratio ** 0.5))
            width = int(height * ratio)
        else:
            # Taller than wide
            width = int(base_size * (ratio ** 0.5))
            height = int(width / ratio)
        
        # Make sure dimensions are multiples of 8 (common requirement for ML models)
        width = (width // 8) * 8
        height = (height // 8) * 8
        
        return (width, height) 
