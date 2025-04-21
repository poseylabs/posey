import httpx
import os
import logging
from typing import List, Dict, Any
from .base_adapter import BaseSearchAdapter

logger = logging.getLogger(__name__)

# Define a default timeout (in seconds)
DEFAULT_TIMEOUT = 15.0

class BraveAdapter(BaseSearchAdapter):
    """Search adapter for Brave Search API."""
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self):
        self.api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        if not self.api_key:
            logger.warning("BRAVE_SEARCH_API_KEY environment variable not set. Brave search will not function.")
        else:
            # Log only the first few chars for verification without exposing the full key
            logger.info(f"BraveAdapter initialized with API key starting: {self.api_key[:4]}...")

    async def search(self, query: str, limit: int, time_range: str) -> List[Dict[str, Any]]:
        """Perform search using Brave Search API."""
        logger.info(f"BraveAdapter: Starting search for query: '{query}'")
        if not self.api_key:
            logger.error("BraveAdapter: Cannot perform search, API key is missing.")
            return []

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {
            "q": query,
            "count": limit
            # Brave API time range parameters differ from DDG and are less granular.
            # Mapping 'time_range' might require more specific logic if needed.
            # For now, omitting time range filter for Brave.
            # 'freshness': time_range if time_range in [...] else None 
        }

        logger.debug(f"BraveAdapter: Sending request to {self.BASE_URL} with params: {params}")
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                logger.info("BraveAdapter: Sending GET request...")
                response = await client.get(self.BASE_URL, headers=headers, params=params)
                logger.info(f"BraveAdapter: Received response with status code: {response.status_code}")
                
                # Log response content before raising status
                logger.debug(f"BraveAdapter: Raw response content: {response.text[:500]}...") # Log first 500 chars
                
                response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
                logger.info("BraveAdapter: Response status OK.")
                data = response.json()
                logger.debug("BraveAdapter: Successfully parsed JSON response.")

                results = []
                # Adjust based on actual Brave API response structure
                # Assuming response structure like {'web': {'results': [...]}}
                # and each result has 'title', 'url', 'description'
                api_results = data.get("web", {}).get("results", [])
                logger.info(f"BraveAdapter: Found {len(api_results)} results in API response.")
                
                for item in api_results:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", "") # Brave uses 'description'
                    })
                    if len(results) >= limit:
                        logger.debug(f"BraveAdapter: Reached result limit ({limit}).")
                        break
                logger.info(f"BraveAdapter: Prepared {len(results)} results.")
                return results

        except httpx.TimeoutException as e:
            logger.error(f"Brave Search API request timed out after {DEFAULT_TIMEOUT}s: {e}")
            return [] # Return empty on timeout
        except httpx.RequestError as e:
            logger.error(f"Brave Search API request error: {e}")
            return []
        except httpx.HTTPStatusError as e:
            # Log the response body for status errors too
            logger.error(f"Brave Search API status error: {e.response.status_code} - Response: {e.response.text[:500]}...")
            return []
        except Exception as e:
            # Catch any other unexpected error during request/processing
            logger.error(f"Brave Search - Unexpected error during API call or processing: {e}", exc_info=True)
            return [] 