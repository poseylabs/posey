from openai import AsyncOpenAI
import httpx
from app.config import logger

class OllamaAdapter:
    def __init__(self, base_url: str):
        self.client = AsyncOpenAI(
            api_key='posey-api',
            base_url=base_url,
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_retries=3)
            )
        )

    async def generate(self, messages, **kwargs):
        try:
            response = await self.client.chat.completions.create(
                api_key='posey-api',
                model=kwargs.get('model', 'llama3.1:latest'),
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ollama generation error: {str(e)}", exc_info=True)
            raise 
