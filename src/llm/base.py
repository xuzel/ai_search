"""Base LLM Client Abstract Class"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional


class BaseLLM(ABC):
    """Abstract base class for LLM clients"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Generate completion from messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated text response
        """

    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming completion from messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Yields:
            Generated text chunks as they arrive
        """
        # This is needed for the abstract method to be a generator
        yield ""  # pragma: no cover

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM provider is available"""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
