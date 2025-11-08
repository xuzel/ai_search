"""Search Tool - Integration with search APIs"""

import asyncio
from typing import Any, Dict, List, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SearchTool:
    """Search Tool for querying search APIs"""

    def __init__(self, provider: str = "serpapi", api_key: Optional[str] = None):
        """
        Initialize Search Tool

        Args:
            provider: Search provider (serpapi, google_search, bing)
            api_key: API key for the search provider
        """
        self.provider = provider
        self.api_key = api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def search(
        self,
        query: str,
        num_results: int = 5,
        timeout: int = 10,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """
        Perform search query

        Args:
            query: Search query string
            num_results: Number of results to return
            timeout: Request timeout in seconds
            **kwargs: Additional parameters

        Returns:
            List of search results with 'title', 'link', 'snippet'
        """

        if self.provider == "serpapi":
            return await self._search_serpapi(query, num_results, timeout, **kwargs)
        elif self.provider == "google_search":
            return await self._search_google(query, num_results, timeout, **kwargs)
        else:
            raise ValueError(f"Unknown search provider: {self.provider}")

    async def _search_serpapi(
        self,
        query: str,
        num_results: int,
        timeout: int,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """Search using SerpAPI"""

        if not self.api_key:
            raise RuntimeError("SerpAPI key not configured")

        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=timeout) as resp:
                    if resp.status != 200:
                        logger.error(f"SerpAPI error: {resp.status}")
                        return []

                    data = await resp.json()
                    results = []

                    for item in data.get("organic_results", [])[:num_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                        })

                    return results

        except Exception as e:
            logger.error(f"SerpAPI request failed: {e}")
            return []

    async def _search_google(
        self,
        query: str,
        num_results: int,
        timeout: int,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """Search using google-search-results"""

        try:
            from googlesearch import search

            results = []
            for i, url in enumerate(search(query, num_results=num_results)):
                results.append({
                    "title": f"Result {i+1}",
                    "link": url,
                    "snippet": "",
                })

            return results

        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []

    async def batch_search(
        self,
        queries: List[str],
        num_results_per_query: int = 5,
        timeout: int = 10,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Perform multiple searches concurrently

        Args:
            queries: List of search queries
            num_results_per_query: Results per query
            timeout: Request timeout

        Returns:
            Dict mapping query to results
        """

        tasks = [
            self.search(query, num_results_per_query, timeout)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for query, result in zip(queries, results):
            if isinstance(result, Exception):
                logger.error(f"Search failed for '{query}': {result}")
                output[query] = []
            else:
                output[query] = result

        return output
