from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ImageProvider(ABC):
    """
    Base abstract class for image generation providers.
    
    All image generation providers must implement this interface to be
    compatible with the Posey image generation system.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the provider's unique identifier.
        
        This name will be used as the key for the provider in the registry
        and should be lowercase alphanumeric with optional underscores.
        
        Returns:
            str: The provider's unique name
        """
        pass
        
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """
        Return a list of supported model identifiers.
        
        These identifiers will be used to select a specific model
        when generating images with this provider.
        
        Returns:
            List[str]: A list of supported model identifiers
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that the provider is properly configured.
        
        This method should check that all required environment variables
        and configuration options are set and valid.
        
        Returns:
            bool: True if the provider is properly configured, False otherwise
        """
        pass
        
    @abstractmethod
    async def generate(self, prompt: str, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an image with the specified parameters.
        
        Args:
            prompt (str): The text prompt to generate an image from
            model (str): The model identifier to use for generation
            params (Dict[str, Any]): Additional parameters for generation
                - style: The style of the image (e.g., "realistic", "anime")
                - size: The size/aspect ratio (e.g., "1:1", "16:9")
                - negative_prompt: Things to avoid in the image
                - seed: A seed value for reproducibility
                - ...other provider-specific parameters
                
        Returns:
            Dict[str, Any]: The generation result containing:
                - status: "success" or "error"
                - url: URL to the generated image (if successful)
                - error: Error message (if failed)
                - metadata: Additional metadata about the generation
        """
        pass
        
    @property
    def default_model(self) -> Optional[str]:
        """
        Return the default model for this provider.
        
        Returns:
            Optional[str]: The default model name, or None if no models are available
        """
        models = self.supported_models
        return models[0] if models else None
        
    def get_capabilities(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Return the capabilities of the specified model or provider.
        
        Providers should override this method to specify their capabilities,
        which helps the system understand what features are available.
        
        Args:
            model (Optional[str]): The specific model to get capabilities for,
                                   or None for provider-wide capabilities
                                   
        Returns:
            Dict[str, Any]: A dictionary of capabilities, which may include:
                - supports_size_adjustment: Whether size can be adjusted
                - supported_sizes: List of supported sizes/ratios
                - supports_negative_prompt: Whether negative prompts are supported
                - supports_seed: Whether seed values are supported
                - supports_style: Whether style parameters are supported
                - ...other provider-specific capabilities
        """
        # Default capabilities - providers should override this
        return {
            "supports_size_adjustment": False,
            "supports_negative_prompt": False,
            "supports_seed": False,
            "supports_style": False,
            "supports_image_to_image": False
        }
    
    def describe(self) -> Dict[str, Any]:
        """
        Provide a complete description of this provider and its capabilities
        
        Returns:
            Dictionary containing provider details, models and capabilities
        """
        return {
            "name": self.provider_name,
            "models": self.supported_models,
            "default_model": self.default_model,
            "capabilities": self.get_capabilities(),
            "configured": self.validate_configuration()
        } 
