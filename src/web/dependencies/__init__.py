"""Dependency Injection System for Web UI

This module provides FastAPI dependencies for injecting services into routes.

Benefits:
- No global variables
- Thread-safe singleton pattern
- Easy testing (can override dependencies)
- Clear dependency graph

Usage:
    from fastapi import Depends
    from src.web.dependencies import get_llm_manager, get_router

    @router.post("/query")
    async def query(
        query: str = Form(...),
        llm_manager = Depends(get_llm_manager),
        router = Depends(get_router)
    ):
        decision = await router.route(query)
        ...
"""

from src.web.dependencies.core import (
    get_config,
    get_llm_manager,
    get_router,
    get_research_agent,
    get_code_agent,
    get_chat_agent,
    get_rag_agent,
)

from src.web.dependencies.tools import (
    get_search_tool,
    get_scraper_tool,
    get_code_executor,
    get_vector_store,
    get_weather_tool,
    get_finance_tool,
    get_routing_tool,
    get_reranker,
    get_credibility_scorer,
    get_ocr_tool,
    get_vision_tool,
)

from src.web.dependencies.formatters import (
    get_markdown_processor,
    convert_markdown_to_html,
)

__all__ = [
    # Core dependencies
    'get_config',
    'get_llm_manager',
    'get_router',
    'get_research_agent',
    'get_code_agent',
    'get_chat_agent',
    'get_rag_agent',
    # Tool dependencies
    'get_search_tool',
    'get_scraper_tool',
    'get_code_executor',
    'get_vector_store',
    'get_weather_tool',
    'get_finance_tool',
    'get_routing_tool',
    'get_reranker',
    'get_credibility_scorer',
    'get_ocr_tool',
    'get_vision_tool',
    # Formatter dependencies
    'get_markdown_processor',
    'convert_markdown_to_html',
]
