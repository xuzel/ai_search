"""Base Router Interface

Defines the abstract interface that all routers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.routing.task_types import TaskType
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToolRequirement:
    """Represents a tool required for executing a task"""

    tool_name: str
    tool_type: str
    required: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        req_str = "required" if self.required else "optional"
        return f"{self.tool_name} ({self.tool_type}, {req_str})"


@dataclass
class RoutingDecision:
    """Represents the result of query routing

    Attributes:
        query: Original query string
        primary_task_type: Main task type for this query
        task_confidence: Confidence score (0.0-1.0)
        reasoning: Explanation of routing decision
        tools_needed: List of tools required
        multi_intent: Whether query has multiple intents
        alternative_task_types: Other possible task types
        metadata: Additional routing metadata
    """

    query: str
    primary_task_type: TaskType
    task_confidence: float
    reasoning: str
    tools_needed: List[ToolRequirement] = field(default_factory=list)
    multi_intent: bool = False
    alternative_task_types: List[TaskType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate decision after initialization"""
        if not 0.0 <= self.task_confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.task_confidence}")

    def __str__(self) -> str:
        return (
            f"RoutingDecision(task={self.primary_task_type.value}, "
            f"confidence={self.task_confidence:.2f}, "
            f"tools={len(self.tools_needed)})"
        )


class BaseRouter(ABC):
    """Abstract base class for all routers

    All router implementations must inherit from this class and implement
    the route() method.
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize router

        Args:
            config: Configuration object
        """
        self.config = config

    @abstractmethod
    async def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """Route a query to the appropriate task type

        Args:
            query: User query to route
            context: Optional context (e.g., language, user preferences)

        Returns:
            RoutingDecision with task type and metadata

        Raises:
            ValueError: If query is invalid
        """

    def validate_query(self, query: str) -> None:
        """Validate query string

        Args:
            query: Query to validate

        Raises:
            ValueError: If query is invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if len(query) > 10000:
            raise ValueError("Query is too long (max 10000 characters)")

    @property
    @abstractmethod
    def name(self) -> str:
        """Return router name for logging"""
