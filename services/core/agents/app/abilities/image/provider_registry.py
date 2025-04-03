import importlib
import inspect
import logging
import os
import pkgutil
import sys
from typing import Dict, Any, List, Optional, Type

from .providers.base import ImageProvider

logger = logging.getLogger(__name__)

class ImageProviderRegistry:
    """
    Registry for image generation providers.
    
    This class manages the registration and discovery of image generation
    providers, allowing the system to use different providers (like DALL-E,
    Stable Diffusion, Flux, etc.) for image generation.
    """
    
    def __init__(self):
        """
        Initialize the provider registry.
        """
        self._providers = {}
        self._plugin_directories = []
        self._loaded = False
        
    def register_provider(self, provider_class: Type[ImageProvider]) -> bool:
        """
        Register a provider class.
        
        Args:
            provider_class (Type[ImageProvider]): The provider class to register
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        try:
            # Instantiate the provider
            provider = provider_class()
            
            # Validate the provider configuration
            if provider.validate_configuration():
                # Get the provider name
                name = provider.provider_name
                
                # Check if the provider name is valid
                if not name or not isinstance(name, str) or not name.strip():
                    logger.warning(f"Provider has invalid name: {name}, skipping registration")
                    return False
                
                # Add the provider to the registry
                self._providers[name] = provider
                logger.info(f"Registered image provider: {name}")
                return True
            else:
                logger.warning(f"Image provider {provider_class.__name__} not properly configured, skipping")
                return False
        except Exception as e:
            logger.error(f"Error registering provider {provider_class.__name__}: {str(e)}")
            return False
    
    def get_provider(self, provider_name: str) -> Optional[ImageProvider]:
        """
        Get a provider by name.
        
        Args:
            provider_name (str): The name of the provider to get
            
        Returns:
            Optional[ImageProvider]: The provider instance, or None if not found
        """
        # Make sure providers are loaded
        if not self._loaded:
            self.auto_discover_providers()
        
        # Return the provider if it exists
        return self._providers.get(provider_name)
        
    def list_providers(self) -> List[str]:
        """
        List all registered providers.
        
        Returns:
            List[str]: A list of provider names
        """
        # Make sure providers are loaded
        if not self._loaded:
            self.auto_discover_providers()
            
        # Return the list of provider names
        return list(self._providers.keys())
        
    def get_all_supported_models(self) -> Dict[str, List[str]]:
        """
        Get all supported models across all providers.
        
        Returns:
            Dict[str, List[str]]: A dictionary mapping provider names to their supported models
        """
        # Make sure providers are loaded
        if not self._loaded:
            self.auto_discover_providers()
            
        # Create a dictionary of provider models
        models = {}
        for name, provider in self._providers.items():
            models[name] = provider.supported_models
        return models
    
    def add_plugin_directory(self, directory: str) -> None:
        """
        Add a directory to search for external provider plugins.
        
        Args:
            directory (str): The directory path to search for plugins
        """
        if os.path.isdir(directory) and directory not in self._plugin_directories:
            self._plugin_directories.append(directory)
            logger.info(f"Added plugin directory: {directory}")
        
    def auto_discover_providers(self) -> None:
        """
        Automatically discover and register all providers.
        
        This method searches for provider implementations in:
        1. The internal providers package
        2. Any registered plugin directories
        """
        # Set the loaded flag to True
        self._loaded = True
        
        # Start by discovering internal providers
        self._discover_internal_providers()
        
        # Then discover plugins
        self._discover_external_plugins()
        
        # Log the results
        num_providers = len(self._providers)
        if num_providers > 0:
            logger.info(f"Discovered {num_providers} image providers: {', '.join(self._providers.keys())}")
        else:
            logger.warning("No image providers discovered")
            
    def _discover_internal_providers(self) -> None:
        """
        Discover and register all internal provider implementations.
        
        This method searches the providers package for classes that:
        1. Inherit from ImageProvider
        2. Are not the ImageProvider base class itself
        3. Have "Provider" in their name
        """
        try:
            # Import the providers package
            from . import providers
            
            # Get the providers package path
            provider_path = providers.__path__
            
            # Iterate through all modules in the providers package
            for _, name, is_pkg in pkgutil.iter_modules(provider_path):
                # Skip the base module and packages
                if name == "base" or is_pkg:
                    continue
                    
                try:
                    # Import the module
                    module = importlib.import_module(f"app.abilities.image.providers.{name}")
                    
                    # Find provider classes in the module
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, ImageProvider) and 
                                obj is not ImageProvider and 
                                "Provider" in obj.__name__):
                            # Register the provider
                            self.register_provider(obj)
                except Exception as e:
                    logger.error(f"Error loading provider module {name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error discovering internal providers: {str(e)}")
    
    def _discover_external_plugins(self) -> None:
        """
        Discover and register external provider plugins.
        
        This method searches registered plugin directories for Python modules
        that might contain provider implementations.
        """
        # Skip if no plugin directories
        if not self._plugin_directories:
            return
            
        # Original system path
        original_path = sys.path.copy()
        
        try:
            # Process each plugin directory
            for plugin_dir in self._plugin_directories:
                # Add the plugin directory to sys.path temporarily
                if plugin_dir not in sys.path:
                    sys.path.insert(0, plugin_dir)
                
                # Look for Python modules in the directory
                for entry in os.listdir(plugin_dir):
                    # Skip non-directories and hidden directories
                    if not os.path.isdir(os.path.join(plugin_dir, entry)) or entry.startswith('.'):
                        continue
                        
                    # Check if this is a Python package
                    if os.path.isfile(os.path.join(plugin_dir, entry, "__init__.py")):
                        try:
                            # Try to import the package
                            plugin_package = importlib.import_module(entry)
                            
                            # Look for provider modules in the package
                            logger.info(f"Checking for image providers in plugin: {entry}")
                            
                            # The import and registration should happen automatically
                            # when the package is imported, as the registration code
                            # should be in the package's __init__.py
                        except Exception as e:
                            logger.error(f"Error loading plugin package {entry}: {str(e)}")
        finally:
            # Restore the original system path
            sys.path = original_path


# Singleton instance for global access
_registry_instance = None

def get_registry() -> ImageProviderRegistry:
    """
    Get the global provider registry instance.
    
    Returns:
        ImageProviderRegistry: The global registry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ImageProviderRegistry()
    return _registry_instance


def register_external_provider(provider_class: Type[ImageProvider]) -> bool:
    """
    Register an external provider with the global registry.
    
    This function is meant to be called by external plugins to register
    their providers with the Posey image generation system.
    
    Args:
        provider_class (Type[ImageProvider]): The provider class to register
        
    Returns:
        bool: True if registration was successful, False otherwise
    """
    registry = get_registry()
    return registry.register_provider(provider_class) 
