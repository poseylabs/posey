"""
Provider implementations for various image generation services.

This package contains provider implementations for various image generation
services, such as DALL-E, Stable Diffusion, Flux, etc. These providers can
be registered with the ImageProviderRegistry to enable image generation
with different services.

New providers can be added by creating a new class that inherits from
ImageProvider and implements its abstract methods.
"""

from ..provider_registry import register_external_provider
from .base import ImageProvider

__all__ = ["ImageProvider", "register_external_provider"] 
