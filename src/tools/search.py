"""Search Tool - Integration with search APIs"""

import asyncio
import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SearchCache:
    """LRU cache for search results with TTL support"""

    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Initialize search cache

        Args:
            max_size: Maximum number of cached entries
            ttl: Time-to-live in seconds (default 1 hour)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Tuple[List[Dict[str, str]], float]] = {}
        self._access_order: List[str] = []

    def _make_key(self, query: str, num_results: int, provider: str) -> str:
        """Generate cache key from query parameters"""
        key_str = f"{provider}:{query}:{num_results}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, num_results: int, provider: str) -> Optional[List[Dict[str, str]]]:
        """
        Get cached results if available and not expired

        Returns:
            Cached results or None if not found/expired
        """
        key = self._make_key(query, num_results, provider)

        if key not in self._cache:
            return None

        results, timestamp = self._cache[key]

        # Check TTL
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            logger.debug(f"Cache expired for query: {query[:50]}...")
            return None

        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Cache hit for query: {query[:50]}...")
        return results

    def set(self, query: str, num_results: int, provider: str, results: List[Dict[str, str]]) -> None:
        """
        Cache search results

        Args:
            query: Search query
            num_results: Number of results requested
            provider: Search provider
            results: Search results to cache
        """
        key = self._make_key(query, num_results, provider)

        # Evict LRU entry if at capacity
        while len(self._cache) >= self.max_size and self._access_order:
            old_key = self._access_order.pop(0)
            if old_key in self._cache:
                del self._cache[old_key]
                logger.debug(f"Evicted LRU cache entry")

        self._cache[key] = (results, time.time())
        self._access_order.append(key)
        logger.debug(f"Cached results for query: {query[:50]}...")

    def clear(self) -> None:
        """Clear all cached entries"""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Search cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
        }


class SearchTool:
    """Search Tool for querying search APIs with caching support"""

    def __init__(
        self,
        provider: str = "serpapi",
        api_key: Optional[str] = None,
        cache_enabled: bool = True,
        cache_max_size: int = 100,
        cache_ttl: int = 3600,
    ):
        """
        Initialize Search Tool

        Args:
            provider: Search provider (serpapi, google_search, bing)
            api_key: API key for the search provider
            cache_enabled: Whether to enable result caching
            cache_max_size: Maximum cache entries
            cache_ttl: Cache TTL in seconds
        """
        self.provider = provider
        self.api_key = api_key
        self.cache_enabled = cache_enabled
        self._cache = SearchCache(max_size=cache_max_size, ttl=cache_ttl) if cache_enabled else None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def search(
        self,
        query: str,
        num_results: int = 5,
        timeout: int = 10,
        use_cache: bool = True,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """
        Perform search query with optional caching

        Args:
            query: Search query string
            num_results: Number of results to return
            timeout: Request timeout in seconds
            use_cache: Whether to use cache for this query
            **kwargs: Additional parameters

        Returns:
            List of search results with 'title', 'link', 'snippet'
        """
        # Check cache first
        if use_cache and self._cache:
            cached = self._cache.get(query, num_results, self.provider)
            if cached is not None:
                return cached

        # Perform actual search
        if self.provider == "serpapi":
            results = await self._search_serpapi(query, num_results, timeout, **kwargs)
        elif self.provider == "google_search":
            results = await self._search_google(query, num_results, timeout, **kwargs)
        else:
            raise ValueError(f"Unknown search provider: {self.provider}")

        # Cache results
        if use_cache and self._cache and results:
            self._cache.set(query, num_results, self.provider, results)

        return results

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

    def clear_cache(self) -> None:
        """Clear the search cache"""
        if self._cache:
            self._cache.clear()

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics"""
        if self._cache:
            return self._cache.get_stats()
        return None

    def set_cache_enabled(self, enabled: bool) -> None:
        """Enable or disable caching"""
        self.cache_enabled = enabled
        if enabled and not self._cache:
            self._cache = SearchCache()
        logger.info(f"Search cache {'enabled' if enabled else 'disabled'}")
