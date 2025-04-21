from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseSearchAdapter(ABC):
    """Abstract base class for search engine adapters."""

    @abstractmethod
    async def search(self, query: str, limit: int, time_range: str) -> List[Dict[str, Any]]:
        """
        Perform a web search.

        Args:
            query: The search query string.
            limit: The maximum number of results to return.
            time_range: The time range for the search (e.g., 'd' for day, 'w' for week, 'm' for month, 'y' for year, or empty for any).

        Returns:
            A list of search result dictionaries, each typically containing 'title', 'url', and 'snippet'.
        """
        pass 