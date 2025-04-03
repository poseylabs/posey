import httpx
from typing import Dict, Any
import asyncio
from app.config import logger

async def test_llm_connection(provider: str, base_url: str) -> bool:
    """Test connection to LLM provider"""
    try:
        if provider == "ollama":
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/health")
                logger.info(f"Ollama health check response: {response.status_code}")
                return response.status_code == 200
                
        elif provider == "openai":
            # Test OpenAI connection
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"})
                logger.info(f"OpenAI API check response: {response.status_code}")
                return response.status_code == 200
                
        return True  # Default for other providers
        
    except Exception as e:
        logger.error(f"Connection test failed for {provider}: {str(e)}", exc_info=True)
        return False

async def verify_connections(config: Dict[str, Any]) -> Dict[str, bool]:
    """Verify all required service connections"""
    results = {}
    
    # Test LLM providers
    for provider, settings in config.get("llm", {}).items():
        if isinstance(settings, dict) and "base_url" in settings:
            results[f"llm_{provider}"] = await test_llm_connection(
                provider, 
                settings["base_url"]
            )
    
    return results 
