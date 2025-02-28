from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, is_dataclass
from pydantic import BaseModel as PydanticBaseModel, Field
from pydantic.config import ConfigDict
from pathlib import Path
from app.config.defaults import LLM_CONFIG
import os
from json import JSONEncoder

# Model Defaults
MAX_TOKENS_XS = 4096
MAX_TOKENS_SMALL = MAX_TOKENS_XS * 2
MAX_TOKENS_MEDIUM = MAX_TOKENS_SMALL * 2
MAX_TOKENS_LARGE = MAX_TOKENS_MEDIUM * 2
MAX_TOKENS_XL = MAX_TOKENS_LARGE * 2

DEFAULT_MODEL_TEMP = 1
DEFAULT_MODEL_MAX_TOKENS = 16384
DEFAULT_MODEL_CONTEXT_WINDOW = 128000

# Model Constants
DEFAULT_MODEL = LLM_CONFIG["default"]["model"]
EMBEDDING_CACHE_DIR = os.getenv('EMBEDDING_CACHE_DIR', '/app/models')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'thenlper/gte-large')
EMBEDDING_FALLBACK = 'BAAI/bge-large-en-v1.5'  # Reliable fallback

# Add these near the top with other constants
VECTOR_DIMENSIONS = 384  # Standard dimension for text embeddings
MAX_TOKEN_LENGTH = 8192  # Maximum tokens for text processing
REVISION_HASH = "v1.0.0"  # Version tracking
DEFAULT_THREADS = 4  # Default number of processing threads

@dataclass
class ModelBase:
    id: str
    name: str
    provider: str
    description: str = ""

@dataclass
class LLMModel(ModelBase):
    context_window: int = DEFAULT_MODEL_CONTEXT_WINDOW
    default_temp: float = DEFAULT_MODEL_TEMP
    max_tokens: int = MAX_TOKENS_MEDIUM
    ocr_capable: bool = False

@dataclass
class ImageModel(ModelBase):
    path: Optional[str] = None

# Provider Namespaces
class Provider(str, Enum):
    # LLM Providers
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    
    # Image Providers
    FLUX = "flux"
    DALLE = "dalle"
    STABILITY = "stability"

# LLM Models
OLLAMA_MODELS: List[LLMModel] = [
    LLMModel(
        id="deepseek-r1",
        name="DeepSeek R1 (7B)",
        provider=Provider.OLLAMA,
        description="",
        max_tokens=MAX_TOKENS_MEDIUM,
        ocr_capable=True
    ),
    LLMModel(
        id="llama3.1",
        name="Llama 3.1 (7b)",
        provider=Provider.OLLAMA,
        description="Llama 3.1 is a 7B parameter open model",
        max_tokens=MAX_TOKENS_MEDIUM,
        ocr_capable=True
    ),
]

# Image Models
FLUX_MODELS: List[ImageModel] = [
    ImageModel(
        id="flux-pro-1.1-ultra",
        name="Flux Pro 1.1 Ultra",
        provider=Provider.FLUX,
        description="Most intelligent model. Highest level of intelligence and capability."
    ),
]

STABILITY_MODELS: List[ImageModel] = [
    ImageModel(
        id="stable-diffusion-3.5",
        name="Stable Diffusion 3.5",
        provider=Provider.STABILITY,
    ),
]

# Model Configurations
LLM_MODELS = {
    Provider.OLLAMA: OLLAMA_MODELS,
    Provider.ANTHROPIC: [],  # Add if needed
    Provider.OPENAI: [],     # Add if needed
}

IMAGE_MODELS = {
    Provider.FLUX: FLUX_MODELS,
    Provider.STABILITY: STABILITY_MODELS,
}

# Default Models
DEFAULT_LLM_MODEL = OLLAMA_MODELS[0]
DEFAULT_IMAGE_MODEL = STABILITY_MODELS[0]

# Model Registry for Abilities
MODEL_REGISTRY = {
    "code_generation": {
        "preferred": ["deepseek-r1", "llama3.1"],
        "fallback": ["gpt-4", "claude-3"]
    },
    "image_generation": {
        "preferred": ["flux"],
        "fallback": ["stable-diffusion-3.5"]
    },
    "image_editing": {
        "preferred": ["flux"],
        "fallback": ["stable-diffusion-3.5"]
    },
    "video_generation": {
        "preferred": ["stable-video-1"],
        "fallback": ["runway"]
    }
}

def get_model_for_ability(ability: str, prefer_local: bool = True) -> str:
    """Get appropriate model for a given ability"""
    if ability not in MODEL_REGISTRY:
        raise ValueError(f"No models registered for ability: {ability}")
        
    models = MODEL_REGISTRY[ability]
    return models["preferred"][0] if prefer_local else models["fallback"][0]

class ModelConfig(PydanticBaseModel):
    """Configuration for a specific model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    adapter: str
    model: str
    config: Dict[str, Any] = Field(default_factory=dict)

class ModelSizeConfig(PydanticBaseModel):
    """Configuration for different model sizes"""
    small: ModelConfig
    medium: ModelConfig
    large: ModelConfig

class ModelTypeConfig(PydanticBaseModel):
    """Configuration for different model types"""
    standard: ModelSizeConfig
    reasoning: ModelSizeConfig

class AbilityConfig(PydanticBaseModel):
    """Configuration for an ability"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    description: str
    type: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)

class AgentConfig(PydanticBaseModel):
    """Configuration for an agent"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    description: str
    type: str
    enabled: bool = True
    abilities: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)

class ServiceConfig(PydanticBaseModel):
    """Configuration for the service"""
    name: str
    version: str
    log_level: str = "INFO"
    abilities: List[AbilityConfig] = Field(default_factory=list)
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    image_models: Dict[str, ModelSizeConfig] = Field(default_factory=dict)
    llm_models: ModelTypeConfig
    port: Optional[int] = 5555
    host: Optional[str] = "0.0.0.0"
    debug: bool = False
    environment: str = "development"

class LocaleConfig(PydanticBaseModel):
    """Configuration for localization"""
    default: str = "en-US"
    supported: List[str] = ["en-US"]

class DatabaseConfig(PydanticBaseModel):
    """Configuration for database connections"""
    host: str
    port: int
    user: str
    password: str
    database: str
    ssl: bool = False
    min_connections: int = 1
    max_connections: int = 10

class CacheConfig(PydanticBaseModel):
    """Configuration for caching"""
    enabled: bool = True
    ttl: int = 3600  # seconds
    max_size: int = 1000  # entries

class SecurityConfig(PydanticBaseModel):
    """Configuration for security settings"""
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # seconds
    encryption_key: Optional[str] = None
    allowed_origins: List[str] = ["*"]
    cors_enabled: bool = True

class LoggingConfig(PydanticBaseModel):
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    rotation: str = "1 day"
    retention: str = "30 days"

# Add this before DEFAULT_MODEL_SETTINGS
class ModelSettings(PydanticBaseModel):
    """Full model settings configuration"""
    provider: Provider
    model_id: str = Field(default=DEFAULT_MODEL)
    capabilities: Dict[str, bool] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    cache_dir: Path = Field(default=EMBEDDING_CACHE_DIR)

# Then update DEFAULT_MODEL_SETTINGS to use Provider instead of ModelProvider
DEFAULT_MODEL_SETTINGS = ModelSettings(
    provider=Provider.ANTHROPIC,
    model_id=DEFAULT_MODEL,
    capabilities={},
    config={
        "temperature": 0.7,
        "max_tokens": 4096
    }
)

# Add this new class after the existing model classes
class PoseyJSONEncoder(JSONEncoder):
    """Custom JSON encoder for Posey-specific types"""
    def default(self, obj):
        # Handle RunContext specifically
        if hasattr(obj, '__class__') and 'RunContext' in obj.__class__.__name__:
            return obj.model_dump()
            
        # Handle dataclass objects
        if is_dataclass(obj):
            return asdict(obj)
            
        # Handle Pydantic models
        if hasattr(obj, 'model_dump'):  # Pydantic v2
            return obj.model_dump()
        elif hasattr(obj, 'dict'):      # Pydantic v1
            return obj.dict()
            
        # Handle Path objects
        if isinstance(obj, Path):
            return str(obj)
            
        # Let the base class handle anything else
        return super().default(obj)

# Export all models
__all__ = [
    'ModelConfig',
    'ModelSizeConfig',
    'ModelTypeConfig',
    'AbilityConfig',
    'AgentConfig',
    'ServiceConfig',
    'LocaleConfig',
    'DatabaseConfig',
    'CacheConfig',
    'SecurityConfig',
    'LoggingConfig',
    'DEFAULT_MODEL',
    'EMBEDDING_CACHE_DIR',
    'VECTOR_DIMENSIONS',
    'MAX_TOKEN_LENGTH',
    'REVISION_HASH',
    'DEFAULT_THREADS',
    'ModelSizeConfig',
    'ModelTypeConfig',
    'ModelConfig',
    'ModelProvider',
    'ModelCapabilities',
    'ModelSettings',
    'DEFAULT_MODEL_SETTINGS',
    'PoseyJSONEncoder'
]
