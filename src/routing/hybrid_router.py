"""Hybrid Router

Combines keyword-based and LLM-based routing for optimal speed and accuracy.
Includes caching for improved performance and feedback mechanism for learning.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import json
import time

from src.routing.base import BaseRouter, RoutingDecision
from src.routing.task_types import TaskType
from src.routing.keyword_router import KeywordRouter
from src.routing.llm_router import LLMRouter
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)

# Global cache for routing decisions (LRU cache with 1000 entries)
_routing_cache = {}


@dataclass
class RoutingFeedback:
    """Feedback for a routing decision"""
    query: str
    routed_task: TaskType
    correct_task: Optional[TaskType]
    is_correct: bool
    timestamp: float = field(default_factory=time.time)
    user_comment: Optional[str] = None


class RoutingFeedbackTracker:
    """Tracks routing feedback for learning and statistics"""

    def __init__(self, max_history: int = 1000):
        """
        Initialize feedback tracker

        Args:
            max_history: Maximum feedback entries to keep
        """
        self.max_history = max_history
        self._feedback_history: List[RoutingFeedback] = []
        self._correction_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # correction_counts[routed_task][correct_task] = count

    def record_feedback(
        self,
        query: str,
        routed_task: TaskType,
        correct_task: Optional[TaskType] = None,
        is_correct: bool = True,
        user_comment: Optional[str] = None
    ) -> None:
        """
        Record feedback for a routing decision

        Args:
            query: The original query
            routed_task: The task type that was routed
            correct_task: The correct task type (if different)
            is_correct: Whether the routing was correct
            user_comment: Optional user comment
        """
        feedback = RoutingFeedback(
            query=query,
            routed_task=routed_task,
            correct_task=correct_task if not is_correct else routed_task,
            is_correct=is_correct,
            user_comment=user_comment
        )

        self._feedback_history.append(feedback)

        # Track corrections for learning
        if not is_correct and correct_task:
            self._correction_counts[routed_task.value][correct_task.value] += 1
            logger.info(f"Routing correction recorded: {routed_task.value} -> {correct_task.value}")

        # Trim history if needed
        if len(self._feedback_history) > self.max_history:
            self._feedback_history = self._feedback_history[-self.max_history:]

    def get_accuracy(self, task_type: Optional[TaskType] = None) -> float:
        """
        Get routing accuracy

        Args:
            task_type: Optional task type to filter by

        Returns:
            Accuracy as float (0.0 - 1.0)
        """
        if not self._feedback_history:
            return 1.0

        if task_type:
            relevant = [f for f in self._feedback_history if f.routed_task == task_type]
        else:
            relevant = self._feedback_history

        if not relevant:
            return 1.0

        correct = sum(1 for f in relevant if f.is_correct)
        return correct / len(relevant)

    def get_common_corrections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most common routing corrections

        Args:
            limit: Maximum number of corrections to return

        Returns:
            List of correction patterns with counts
        """
        corrections = []
        for routed, correct_counts in self._correction_counts.items():
            for correct, count in correct_counts.items():
                corrections.append({
                    "from": routed,
                    "to": correct,
                    "count": count
                })

        corrections.sort(key=lambda x: x["count"], reverse=True)
        return corrections[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        total = len(self._feedback_history)
        correct = sum(1 for f in self._feedback_history if f.is_correct)

        return {
            "total_feedback": total,
            "correct_count": correct,
            "incorrect_count": total - correct,
            "overall_accuracy": self.get_accuracy(),
            "common_corrections": self.get_common_corrections(5),
        }

    def should_adjust_threshold(self, task_type: TaskType) -> Optional[float]:
        """
        Suggest threshold adjustment based on feedback

        Args:
            task_type: Task type to check

        Returns:
            Suggested threshold adjustment or None
        """
        accuracy = self.get_accuracy(task_type)

        # If accuracy is low, suggest lowering threshold to use LLM more
        if accuracy < 0.7:
            return -0.1  # Suggest lowering threshold by 0.1
        elif accuracy > 0.95:
            return 0.05  # Suggest raising threshold by 0.05

        return None

    def clear(self) -> None:
        """Clear all feedback history"""
        self._feedback_history.clear()
        self._correction_counts.clear()
        logger.info("Feedback history cleared")


class HybridRouter(BaseRouter):
    """Hybrid router combining keyword and LLM strategies

    Strategy:
    1. Try keyword-based routing first (fast)
    2. If confidence >= threshold, use keyword result
    3. Otherwise, fall back to LLM routing (accurate)

    This provides the best of both worlds:
    - Fast for obvious queries
    - Accurate for ambiguous queries

    Includes feedback mechanism for learning from corrections.
    """

    def __init__(
        self,
        llm_manager: 'LLMManager',
        config: Optional[Any] = None,
        confidence_threshold: float = 0.7,
        enable_feedback: bool = True
    ):
        """Initialize hybrid router

        Args:
            llm_manager: LLM manager for fallback
            config: Optional configuration
            confidence_threshold: Minimum confidence to accept keyword routing
                                (default: 0.7, use LLM if keyword < 0.7)
            enable_feedback: Whether to enable feedback tracking
        """
        super().__init__(config)
        self.keyword_router = KeywordRouter(config)
        self.llm_router = LLMRouter(llm_manager, config)
        self.confidence_threshold = confidence_threshold
        self._initial_threshold = confidence_threshold
        self.feedback_tracker = RoutingFeedbackTracker() if enable_feedback else None

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

    def record_feedback(
        self,
        query: str,
        routed_task: TaskType,
        correct_task: Optional[TaskType] = None,
        is_correct: bool = True,
        user_comment: Optional[str] = None
    ) -> None:
        """
        Record feedback for a routing decision

        Args:
            query: The original query
            routed_task: The task type that was routed
            correct_task: The correct task type (if different)
            is_correct: Whether the routing was correct
            user_comment: Optional user comment
        """
        if self.feedback_tracker:
            self.feedback_tracker.record_feedback(
                query=query,
                routed_task=routed_task,
                correct_task=correct_task,
                is_correct=is_correct,
                user_comment=user_comment
            )

            # Invalidate cache for this query if it was incorrect
            if not is_correct:
                cache_key = self._get_cache_key(query)
                if cache_key in _routing_cache:
                    del _routing_cache[cache_key]
                    logger.debug(f"Invalidated cache for corrected query")

    def get_feedback_stats(self) -> Optional[Dict[str, Any]]:
        """Get feedback statistics"""
        if self.feedback_tracker:
            return self.feedback_tracker.get_stats()
        return None

    def auto_adjust_threshold(self) -> bool:
        """
        Automatically adjust confidence threshold based on feedback

        Returns:
            True if threshold was adjusted
        """
        if not self.feedback_tracker:
            return False

        # Check overall accuracy and adjust
        stats = self.feedback_tracker.get_stats()
        accuracy = stats.get("overall_accuracy", 1.0)

        old_threshold = self.confidence_threshold

        if accuracy < 0.7 and self.confidence_threshold > 0.5:
            # Lower threshold to use LLM more often
            self.confidence_threshold = max(0.5, self.confidence_threshold - 0.1)
            logger.info(f"Lowered confidence threshold: {old_threshold:.2f} -> {self.confidence_threshold:.2f}")
            return True
        elif accuracy > 0.95 and self.confidence_threshold < 0.9:
            # Raise threshold to use keyword more often (faster)
            self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
            logger.info(f"Raised confidence threshold: {old_threshold:.2f} -> {self.confidence_threshold:.2f}")
            return True

        return False

    def reset_threshold(self) -> None:
        """Reset confidence threshold to initial value"""
        self.confidence_threshold = self._initial_threshold
        logger.info(f"Reset confidence threshold to {self._initial_threshold}")

    def clear_feedback(self) -> None:
        """Clear feedback history"""
        if self.feedback_tracker:
            self.feedback_tracker.clear()

    def clear_cache(self) -> None:
        """Clear routing cache"""
        global _routing_cache
        _routing_cache.clear()
        logger.info("Routing cache cleared")
