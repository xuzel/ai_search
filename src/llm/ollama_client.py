"""Ollama Local Model Client"""

from typing import Any, Dict, List, Optional

import aiohttp
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.logger import get_logger
from .base import BaseLLM

logger = get_logger(__name__)


class OllamaClient(BaseLLM):
    """Ollama Local Model Client"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        temperature: float = 0.7,
    ):
        super().__init__("Ollama")
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.api_endpoint = f"{self.base_url}/api/chat"

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
        """Generate completion using Ollama API"""

        if not await self.is_available():
            raise RuntimeError("Ollama server not available")

        temp = temperature if temperature is not None else self.temperature

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temp,
                    "stream": False,
                }

                async with session.post(self.api_endpoint, json=payload) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Ollama API error: {resp.status}")

                    data = await resp.json()
                    return data.get("message", {}).get("content", "").strip()

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def is_available(self) -> bool:
        """Check if Ollama server is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"<OllamaClient: base_url={self.base_url}, model={self.model}>"
