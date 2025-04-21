import httpx
import os
import logging
from typing import List, Dict, Any
from .base_adapter import BaseSearchAdapter

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 15.0

class GoogleAdapter(BaseSearchAdapter):
    """Search adapter for Google Custom Search JSON API."""
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        key_found = bool(self.api_key)
        cse_found = bool(self.cse_id)
        
        # Log detailed status
        key_display = f"{self.api_key[:4]}...{self.api_key[-4:]}" if key_found else "MISSING"
        cse_display = self.cse_id if cse_found else "MISSING"
        logger.info(f"GoogleAdapter __init__: GOOGLE_API_KEY found: {key_found} (Value starts/ends: {key_display}), GOOGLE_CSE_ID found: {cse_found} (Value: {cse_display})")

        if not key_found:
            logger.warning("GOOGLE_API_KEY environment variable not set. Google search will not function.")
        if not cse_found:
            logger.warning("GOOGLE_CSE_ID environment variable not set. Google search will not function.")
        if key_found and cse_found:
             logger.info(f"GoogleAdapter initialized successfully.")

    async def search(self, query: str, limit: int, time_range: str) -> List[Dict[str, Any]]:
        """Perform search using Google Custom Search API.

        Note: The 'time_range' parameter is ignored as the API uses different params (e.g., 'dateRestrict').
              The 'limit' parameter maps to Google's 'num' parameter (max 10).
        """
        logger.info(f"GoogleAdapter: Starting search for query: '{query}'")
        
        # Log keys again just before use
        key_display = f"{self.api_key[:4]}...{self.api_key[-4:]}" if self.api_key else "MISSING"
        cse_display = self.cse_id if self.cse_id else "MISSING"
        logger.debug(f"GoogleAdapter search: Using API Key (start/end): {key_display}, CSE ID: {cse_display}")
        
        if not self.api_key or not self.cse_id:
            logger.error("GoogleAdapter: Cannot perform search, API key or CSE ID is missing when needed.")
            return []

        # Google API's 'num' parameter controls the number of results (max 10)
        num_results = min(limit, 10) 

        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": num_results
            # Optional: Add dateRestrict for time_range mapping later if needed
            # e.g., 'dateRestrict': 'd[7]' for past 7 days
        }

        logger.debug(f"GoogleAdapter: Sending request to {self.BASE_URL} with params: {params}")
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                logger.info("GoogleAdapter: Sending GET request...")
                response = await client.get(self.BASE_URL, params=params)
                logger.info(f"GoogleAdapter: Received response with status code: {response.status_code}")
                logger.debug(f"GoogleAdapter: Raw response content: {response.text[:500]}...")
                response.raise_for_status()
                logger.info("GoogleAdapter: Response status OK.")
                data = response.json()
                logger.debug("GoogleAdapter: Successfully parsed JSON response.")

                results = []
                api_results = data.get("items", []) # Results are in the "items" array
                logger.info(f"GoogleAdapter: Found {len(api_results)} results in API response.")

                for item in api_results:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""), # URL is in the "link" field
                        "snippet": item.get("snippet", "") # Snippet is in the "snippet" field
                    })
                    # No need to check limit here as Google's 'num' handles it
                
                logger.info(f"GoogleAdapter: Prepared {len(results)} results.")
                return results

        except httpx.TimeoutException as e:
            logger.error(f"Google Search API request timed out after {DEFAULT_TIMEOUT}s: {e}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Google Search API request error: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Search API status error: {e.response.status_code} - Response: {e.response.text[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Google Search - Unexpected error during API call or processing: {e}", exc_info=True)
            return [] 