"""
Midjourney image generation provider plugin for Posey

This plugin integrates Midjourney's image generation capabilities into Posey's
image generation system, allowing users to create images using Midjourney's
advanced AI image models.

Features:
- Support for Midjourney v6, v5.2, v5.1, v5.0 and Niji-5 models
- Aspect ratio control
- Style parameters
- Negative prompts
- Seed control for reproducibility

To use this plugin:
1. Install this package
2. Set the following environment variables:
   - MIDJOURNEY_API_URL: URL to the Midjourney API
   - MIDJOURNEY_API_KEY: Your API key for Midjourney
3. The provider will be automatically registered with Posey

Example usage through Posey:
"Generate an image of a futuristic cityscape at night with neon lights using Midjourney"
"""

# The provider is imported and registered automatically
from .midjourney_provider import MidjourneyProvider

__all__ = ["MidjourneyProvider"] 
