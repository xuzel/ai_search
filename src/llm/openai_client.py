"""OpenAI-compatible API Client

Supports OpenAI and other OpenAI-compatible APIs (DeepSeek, Claude, etc.)
by allowing custom API endpoints.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.logger import get_logger
from .base import BaseLLM

logger = get_logger(__name__)


class OpenAIClient(BaseLLM):
    """OpenAI-compatible API Client

    Supports:
    - OpenAI (https://api.openai.com/v1)
    - DeepSeek (https://api.deepseek.com)
    - Other OpenAI-compatible APIs
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        base_url: Optional[str] = None,
        provider_name: str = "OpenAI",
    ):
        """
        Initialize OpenAI-compatible client

        Args:
            api_key: API key for the service
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            base_url: Custom API endpoint URL
                      Examples:
                      - OpenAI: https://api.openai.com/v1
                      - DeepSeek: https://api.deepseek.com
                      - Local: http://localhost:8000/v1
            provider_name: Display name for the provider
        """
        super().__init__(provider_name)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url or "https://api.openai.com/v1"
        self.provider_name = provider_name

        # Initialize OpenAI client with custom base_url
        if self.api_key:
            try:
                # Create client - proxy settings are handled by environment variables
                # If there's an issue, we can use http_client parameter
                import httpx

                # Create a custom http client that ignores proxy issues
                http_client = httpx.Client(
                    proxies=None,  # Disable proxies for OpenAI API
                    verify=True
                )

                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    http_client=http_client,
                )
                if self.base_url and self.base_url != "https://api.openai.com/v1":
                    logger.info(f"Using custom API base URL: {self.base_url}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                logger.info("Attempting initialization without custom http_client...")
                try:
                    # Fallback: try without http_client
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url=self.base_url,
                    )
                    logger.info("OpenAI client initialized without custom http_client")
                except Exception as e2:
                    logger.error(f"Failed to initialize OpenAI client (fallback): {e2}")
                    self.client = None
        else:
            self.client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate completion using OpenAI-compatible API"""

        if not await self.is_available():
            raise RuntimeError(f"{self.provider_name} API key not configured")

        if not self.client:
            raise RuntimeError(f"{self.provider_name} client not initialized")

        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        try:
            # Use asyncio to run sync client in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                    **kwargs
                )
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"{self.provider_name} API error: {e}")
            raise

    async def is_available(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key) and self.client is not None

    def __repr__(self) -> str:
        return f"<{self.provider_name}Client: model={self.model}, base_url={self.base_url}>"
