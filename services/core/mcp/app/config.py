from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """MCP Server Settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = os.getenv("MCP_PORT", 5050)
    DEBUG: bool = False
    
    # Service URLs
    AGENTS_SERVICE_URL: str = os.getenv("AGENTS_SERVICE_URL", "http://agents:5555")
    
    # Security
    API_KEY: Optional[str] = os.getenv("MCP_API_KEY")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Tool settings
    DEFAULT_TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 
