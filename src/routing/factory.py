"""Router Factory

Factory for creating router instances based on configuration.
"""

from typing import Optional, Any, TYPE_CHECKING

from src.routing.base import BaseRouter
from src.routing.keyword_router import KeywordRouter
from src.routing.llm_router import LLMRouter
from src.routing.hybrid_router import HybridRouter
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)


class RouterFactory:
    """Factory for creating router instances

    Usage:
        factory = RouterFactory()
        router = factory.create_router('hybrid', llm_manager, config)
    """

    @staticmethod
    def create_router(
        router_type: str,
        llm_manager: Optional['LLMManager'] = None,
        config: Optional[Any] = None,
        **kwargs: Any
    ) -> BaseRouter:
        """Create router instance

        Args:
            router_type: Type of router ('keyword', 'llm', 'hybrid')
            llm_manager: LLM manager (required for 'llm' and 'hybrid')
            config: Optional configuration
            **kwargs: Additional arguments for router

        Returns:
            Router instance

        Raises:
            ValueError: If router type is invalid or required args missing
        """
        router_type = router_type.lower()

        if router_type == 'keyword':
            logger.info("Creating KeywordRouter")
            return KeywordRouter(config=config)

        elif router_type == 'llm':
            if llm_manager is None:
                raise ValueError("llm_manager is required for LLMRouter")
            logger.info("Creating LLMRouter")
            return LLMRouter(llm_manager=llm_manager, config=config)

        elif router_type == 'hybrid':
            if llm_manager is None:
                raise ValueError("llm_manager is required for HybridRouter")
            logger.info("Creating HybridRouter")
            confidence_threshold = kwargs.get('confidence_threshold', 0.7)
            return HybridRouter(
                llm_manager=llm_manager,
                config=config,
                confidence_threshold=confidence_threshold
            )

        else:
            raise ValueError(
                f"Invalid router type: {router_type}. "
                f"Must be one of: 'keyword', 'llm', 'hybrid'"
            )

    @staticmethod
    def create_from_config(
        config: Any,
        llm_manager: Optional['LLMManager'] = None
    ) -> BaseRouter:
        """Create router from configuration

        Args:
            config: Configuration object with routing settings
            llm_manager: Optional LLM manager

        Returns:
            Router instance based on config
        """
        # Check if config has routing settings
        if hasattr(config, 'routing'):
            router_type = getattr(config.routing, 'type', 'hybrid')
            confidence_threshold = getattr(config.routing, 'confidence_threshold', 0.7)
        else:
            # Default to hybrid
            router_type = 'hybrid'
            confidence_threshold = 0.7

        logger.info(f"Creating router from config: type={router_type}")

        return RouterFactory.create_router(
            router_type=router_type,
            llm_manager=llm_manager,
            config=config,
            confidence_threshold=confidence_threshold
        )


def create_router(
    config: Optional[Any] = None,
    llm_manager: Optional['LLMManager'] = None,
    router_type: str = 'hybrid',
    **kwargs: Any
) -> BaseRouter:
    """Convenience function to create router

    Args:
        config: Optional configuration
        llm_manager: Optional LLM manager
        router_type: Type of router ('keyword', 'llm', 'hybrid')
        **kwargs: Additional router arguments

    Returns:
        Router instance

    Example:
        from src.routing import create_router
        from src.llm import LLMManager
        from src.utils import get_config

        config = get_config()
        llm_manager = LLMManager(config)
        router = create_router(config, llm_manager, 'hybrid')

        decision = await router.route("What's the weather in Beijing?")
    """
    # If config provided, try to create from config
    if config is not None and hasattr(config, 'routing'):
        return RouterFactory.create_from_config(config, llm_manager)

    # Otherwise create with explicit type
    return RouterFactory.create_router(
        router_type=router_type,
        llm_manager=llm_manager,
        config=config,
        **kwargs
    )
