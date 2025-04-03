"""
Image generation ability package.

This package provides the ability to generate images using various providers
like DALL-E, Stable Diffusion, Flux, and others. It uses a provider-based
architecture to make it easy to add new image generation capabilities.

The main components are:
- ImageAbility: The main ability class for generating images
- ImageProvider: The base class for provider implementations
- ImageProviderRegistry: Registry for managing available providers

External providers can be added as plugins by registering them using the
register_external_provider function.
"""

from .providers.base import ImageProvider
from .provider_registry import register_external_provider

__all__ = ["ImageProvider", "register_external_provider"] 
