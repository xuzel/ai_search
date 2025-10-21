"""Web Scraper Tool"""

import asyncio
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from trafilatura import extract

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ScraperTool:
    """Web Scraper Tool for extracting content from URLs"""

    def __init__(
        self,
        timeout: int = 10,
        max_workers: int = 5,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize Scraper Tool

        Args:
            timeout: Request timeout in seconds
            max_workers: Maximum concurrent workers
            user_agent: Custom user agent
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.user_agent = (
            user_agent or
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.headers = {"User-Agent": self.user_agent}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if failed
        """

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ssl=False,
                ) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    else:
                        logger.warning(
                            f"Failed to fetch {url}: status {resp.status}"
                        )
                        return None

        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None

    def extract_content(self, html: str, max_length: int = 3000) -> str:
        """
        Extract main content from HTML

        Args:
            html: HTML content
            max_length: Maximum content length

        Returns:
            Extracted text content
        """

        try:
            content = extract(html)
            if content:
                return content[:max_length]
            return ""
        except Exception as e:
            logger.warning(f"Error extracting content: {e}")
            return ""

    async def scrape_url(
        self,
        url: str,
        extract_text: bool = True,
        max_content_length: int = 3000,
    ) -> Dict[str, str]:
        """
        Scrape a URL and extract content

        Args:
            url: URL to scrape
            extract_text: Whether to extract main text
            max_content_length: Maximum content length

        Returns:
            Dict with 'url', 'title', 'content'
        """

        html = await self.fetch_url(url)
        if not html:
            return {"url": url, "title": "", "content": ""}

        if extract_text:
            content = self.extract_content(html, max_content_length)
        else:
            content = html[:max_content_length]

        # Try to extract title
        title = ""
        try:
            import re
            match = re.search(r"<title[^>]*>(.+?)</title>", html, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
        except Exception as e:
            logger.debug(f"Error extracting title: {e}")

        return {
            "url": url,
            "title": title,
            "content": content,
        }

    async def batch_scrape(
        self,
        urls: List[str],
        extract_text: bool = True,
        max_content_length: int = 3000,
    ) -> List[Dict[str, str]]:
        """
        Scrape multiple URLs concurrently

        Args:
            urls: List of URLs to scrape
            extract_text: Whether to extract main text
            max_content_length: Maximum content length per URL

        Returns:
            List of scraped content
        """

        # Limit concurrent workers
        semaphore = asyncio.Semaphore(self.max_workers)

        async def scrape_with_semaphore(url: str) -> Dict[str, str]:
            async with semaphore:
                return await self.scrape_url(
                    url,
                    extract_text=extract_text,
                    max_content_length=max_content_length,
                )

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Scrape failed for {url}: {result}")
                output.append({"url": url, "title": "", "content": ""})
            else:
                output.append(result)

        return output
