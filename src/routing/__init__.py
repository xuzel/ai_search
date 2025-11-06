"""Unified Routing System

This module provides a unified interface for query routing with pluggable strategies.

Architecture:
    - BaseRouter: Abstract interface for all routers
    - KeywordRouter: Fast keyword-based classification
    - LLMRouter: Accurate LLM-based classification
    - HybridRouter: Combines keyword + LLM strategies
    - RouterFactory: Creates router instances based on config

Usage:
    from src.routing import create_router, TaskType

    # Create router
    router = create_router(config, llm_manager)

    # Route query
    decision = await router.route("What's the weather in Beijing?")
    print(decision.task_type)  # TaskType.DOMAIN_WEATHER

Backward Compatibility:
    The old Router class from src/router.py is still available but deprecated.
    Use the new routing system for better flexibility and maintainability.
"""

from src.routing.base import BaseRouter, RoutingDecision, ToolRequirement
from src.routing.factory import create_router, RouterFactory
from src.routing.task_types import TaskType
from src.routing.keyword_router import KeywordRouter
from src.routing.llm_router import LLMRouter
from src.routing.hybrid_router import HybridRouter

__all__ = [
    # Core interfaces
    'BaseRouter',
    'RoutingDecision',
    'ToolRequirement',
    'TaskType',
    # Factory
    'create_router',
    'RouterFactory',
    # Router implementations
    'KeywordRouter',
    'LLMRouter',
    'HybridRouter',
]
