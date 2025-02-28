import os
import httpx
from typing import Dict, Any

VOYAGER_DOMAIN = os.getenv("VOYAGER_DOMAIN")
VOYAGER_PORT = os.getenv("VOYAGER_PORT")

async def scrape_url(url: str, **kwargs) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"//{VOYAGER_DOMAIN}:{VOYAGER_PORT}/voyager/run",
            json={
                "url": url,
                **kwargs
            }
        )
        return response.json() 
