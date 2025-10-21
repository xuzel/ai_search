"""LLM Provider Manager"""

from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger
from .base import BaseLLM
from .openai_client import OpenAIClient
from .ollama_client import OllamaClient

logger = get_logger(__name__)


class LLMManager:
    """Unified LLM Manager with fallback support"""

    def __init__(self, config: Any = None):
        """
        Initialize LLM Manager

        Args:
            config: Configuration object with LLM settings
        """
        self.config = config
        self.providers: Dict[str, BaseLLM] = {}
        self._primary_provider: Optional[str] = None
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all configured LLM providers"""

        # Initialize OpenAI - check both enabled flag AND api_key
        if (self.config and
            getattr(self.config.llm, 'openai_enabled', True) and  # Check enabled flag
            self.config.llm.openai_api_key):
            self.providers["openai"] = OpenAIClient(
                api_key=self.config.llm.openai_api_key,
                model=self.config.llm.openai_model,
                temperature=self.config.llm.openai_temperature,
                max_tokens=self.config.llm.openai_max_tokens,
                base_url=self.config.llm.openai_base_url,
                provider_name=self.config.llm.openai_provider_name,
            )
            if not self._primary_provider:
                self._primary_provider = "openai"
            logger.info("OpenAI provider initialized")

        # Initialize Aliyun DashScope (OpenAI-compatible)
        if (self.config and
            getattr(self.config.llm, 'dashscope_enabled', True) and  # Check enabled flag
            self.config.llm.dashscope_api_key):
            self.providers["dashscope"] = OpenAIClient(
                api_key=self.config.llm.dashscope_api_key,
                model=self.config.llm.dashscope_model,
                base_url=self.config.llm.dashscope_base_url,
                provider_name="Aliyun DashScope",
            )
            if not self._primary_provider:
                self._primary_provider = "dashscope"
            logger.info("Aliyun DashScope provider initialized")

        # Initialize DeepSeek (OpenAI-compatible)
        if self.config and self.config.llm.deepseek_enabled and self.config.llm.deepseek_api_key:
            self.providers["deepseek"] = OpenAIClient(
                api_key=self.config.llm.deepseek_api_key,
                model=self.config.llm.deepseek_model,
                base_url=self.config.llm.deepseek_base_url,
                provider_name="DeepSeek",
            )
            logger.info("DeepSeek provider initialized")

        # Initialize Local OpenAI-compatible server
        if self.config and self.config.llm.local_compatible_enabled:
            self.providers["local_compatible"] = OpenAIClient(
                api_key=self.config.llm.local_compatible_api_key,
                model=self.config.llm.local_compatible_model,
                base_url=self.config.llm.local_compatible_base_url,
                provider_name="LocalOpenAI",
            )
            logger.info("Local OpenAI-compatible server initialized")

        # Initialize Ollama if enabled
        if self.config and self.config.llm.ollama_enabled:
            self.providers["ollama"] = OllamaClient(
                base_url=self.config.llm.ollama_base_url,
                model=self.config.llm.ollama_model,
            )

        if not self.providers:
            logger.warning("No LLM providers configured")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        preferred_provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Generate completion with fallback support

        Args:
            messages: List of message dicts
            preferred_provider: Preferred provider name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional arguments

        Returns:
            Generated text
        """

        provider_order = []

        # Add preferred provider first
        if preferred_provider and preferred_provider in self.providers:
            provider_order.append(preferred_provider)

        # Add primary provider
        if self._primary_provider and self._primary_provider not in provider_order:
            provider_order.append(self._primary_provider)

        # Add remaining providers
        for name in self.providers:
            if name not in provider_order:
                provider_order.append(name)

        if not provider_order:
            raise RuntimeError("No LLM providers available")

        # Try each provider in order
        last_error = None
        for provider_name in provider_order:
            try:
                provider = self.providers[provider_name]

                if not await provider.is_available():
                    logger.warning(f"{provider_name} not available, trying next...")
                    continue

                logger.debug(f"Using {provider_name} for completion")
                return await provider.complete(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                last_error = e
                continue

        # All providers failed
        raise RuntimeError(
            f"All LLM providers failed. Last error: {last_error}"
        )

    def add_provider(self, name: str, provider: BaseLLM):
        """Add a new provider"""
        self.providers[name] = provider
        if not self._primary_provider:
            self._primary_provider = name

    def get_provider(self, name: str) -> Optional[BaseLLM]:
        """Get a specific provider"""
        return self.providers.get(name)

    def list_providers(self) -> List[str]:
        """List all configured providers"""
        return list(self.providers.keys())

    def __repr__(self) -> str:
        providers = ", ".join(self.list_providers())
        return f"<LLMManager: providers=[{providers}]>"
