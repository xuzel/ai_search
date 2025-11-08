"""Hybrid Router

Combines keyword-based and LLM-based routing for optimal speed and accuracy.
Includes caching for improved performance.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
import hashlib
import json

from src.routing.base import BaseRouter, RoutingDecision
from src.routing.keyword_router import KeywordRouter
from src.routing.llm_router import LLMRouter
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)

# Global cache for routing decisions (LRU cache with 1000 entries)
_routing_cache = {}


class HybridRouter(BaseRouter):
    """Hybrid router combining keyword and LLM strategies

    Strategy:
    1. Try keyword-based routing first (fast)
    2. If confidence >= threshold, use keyword result
    3. Otherwise, fall back to LLM routing (accurate)

    This provides the best of both worlds:
    - Fast for obvious queries
    - Accurate for ambiguous queries
    """

    def __init__(
        self,
        llm_manager: 'LLMManager',
        config: Optional[Any] = None,
        confidence_threshold: float = 0.7
    ):
        """Initialize hybrid router

        Args:
            llm_manager: LLM manager for fallback
            config: Optional configuration
            confidence_threshold: Minimum confidence to accept keyword routing
                                (default: 0.7, use LLM if keyword < 0.7)
        """
        super().__init__(config)
        self.keyword_router = KeywordRouter(config)
        self.llm_router = LLMRouter(llm_manager, config)
        self.confidence_threshold = confidence_threshold

    async def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """Route query using hybrid strategy with caching

        Args:
            query: User query
            context: Optional context for routing

        Returns:
            RoutingDecision from keyword or LLM router (cached if available)
        """
        self.validate_query(query)

        # Step 0: Check cache
        cache_key = self._get_cache_key(query, context)
        if cache_key in _routing_cache:
            logger.debug(f"Cache HIT for query: {query[:50]}...")
            cached_decision = _routing_cache[cache_key]
            cached_decision.metadata["cached"] = True
            return cached_decision

        logger.debug(f"Cache MISS for query: {query[:50]}...")

        # Step 1: Try keyword routing
        keyword_decision = await self.keyword_router.route(query, context)

        logger.debug(
            f"Keyword routing: {keyword_decision.primary_task_type.value} "
            f"(confidence: {keyword_decision.task_confidence:.2f})"
        )

        # Step 2: Check if confidence is high enough
        if keyword_decision.task_confidence >= self.confidence_threshold:
            logger.info(
                f"Using keyword routing (confidence {keyword_decision.task_confidence:.2f} "
                f">= threshold {self.confidence_threshold})"
            )
            keyword_decision.metadata["method"] = "hybrid_keyword"
            keyword_decision.metadata["keyword_confidence"] = keyword_decision.task_confidence
            keyword_decision.metadata["cached"] = False

            # Cache the decision
            self._cache_decision(cache_key, keyword_decision)
            return keyword_decision

        # Step 3: Use LLM for low-confidence cases
        logger.info(
            f"Keyword confidence too low ({keyword_decision.task_confidence:.2f} "
            f"< {self.confidence_threshold}), using LLM router"
        )

        try:
            llm_decision = await self.llm_router.route(query, context)
            llm_decision.metadata["method"] = "hybrid_llm"
            llm_decision.metadata["keyword_confidence"] = keyword_decision.task_confidence
            llm_decision.metadata["keyword_task"] = keyword_decision.primary_task_type.value
            llm_decision.metadata["cached"] = False

            # Cache the decision
            self._cache_decision(cache_key, llm_decision)
            return llm_decision

        except Exception as e:
            logger.error(f"LLM routing failed, falling back to keyword: {e}")
            keyword_decision.metadata["method"] = "hybrid_keyword_fallback"
            keyword_decision.metadata["llm_error"] = str(e)
            keyword_decision.metadata["cached"] = False

            # Cache fallback decision
            self._cache_decision(cache_key, keyword_decision)
            return keyword_decision

    def _get_cache_key(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for query and context

        Args:
            query: User query
            context: Optional context

        Returns:
            Cache key string
        """
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()

        # Include context in cache key if present
        if context:
            context_str = json.dumps(context, sort_keys=True)
            cache_input = f"{normalized_query}|{context_str}"
        else:
            cache_input = normalized_query

        # Hash to keep key size reasonable
        return hashlib.md5(cache_input.encode()).hexdigest()

    def _cache_decision(self, cache_key: str, decision: RoutingDecision) -> None:
        """Cache a routing decision

        Args:
            cache_key: Cache key
            decision: Routing decision to cache
        """
        global _routing_cache

        # Implement simple LRU: if cache too large, clear it
        if len(_routing_cache) > 1000:
            logger.info("Routing cache full (>1000 entries), clearing...")
            _routing_cache.clear()

        _routing_cache[cache_key] = decision
        logger.debug(f"Cached routing decision (cache size: {len(_routing_cache)})")

    @property
    def name(self) -> str:
        return "HybridRouter"
