"""Core Dependencies

Provides core service dependencies (config, LLM, agents, routers).
Uses singleton pattern with lazy initialization for performance.
"""

from typing import Optional
from functools import lru_cache

from src.utils import get_config as load_config
from src.utils.config import Config
from src.llm import LLMManager
from src.routing import create_router, BaseRouter
from src.agents import ResearchAgent, CodeAgent, ChatAgent
from src.agents.rag_agent import RAGAgent
from src.agents.master_agent import MasterAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Singleton instances (lazy-loaded)
_llm_manager: Optional[LLMManager] = None
_router: Optional[BaseRouter] = None
_research_agent: Optional[ResearchAgent] = None
_code_agent: Optional[CodeAgent] = None
_chat_agent: Optional[ChatAgent] = None
_rag_agent: Optional[RAGAgent] = None
_master_agent: Optional[MasterAgent] = None


@lru_cache()
def get_config() -> Config:
    """Get application configuration

    Returns:
        Config: Application configuration object

    Note:
        This is cached to avoid reloading config on every request.
    """
    return load_config()


async def get_llm_manager() -> LLMManager:
    """Get LLM manager instance

    Returns:
        LLMManager: Singleton LLM manager instance

    Note:
        This creates a singleton instance shared across all requests.
        Thread-safe for async contexts.
    """
    global _llm_manager

    if _llm_manager is None:
        config = get_config()
        _llm_manager = LLMManager(config=config)
        logger.info("LLMManager instance created")

    return _llm_manager


async def get_router() -> BaseRouter:
    """Get router instance

    Returns:
        BaseRouter: Singleton router instance
    """
    global _router

    if _router is None:
        # Get dependencies internally (no parameter injection)
        llm_manager = await get_llm_manager()
        config = get_config()

        # Create router
        _router = create_router(
            config=config,
            llm_manager=llm_manager,
            router_type='hybrid'
        )
        logger.info(f"Router instance created: {_router.name}")

    return _router


async def get_research_agent() -> ResearchAgent:
    """Get research agent instance

    Returns:
        ResearchAgent: Singleton research agent instance
    """
    global _research_agent

    if _research_agent is None:
        # Get dependencies internally
        llm_manager = await get_llm_manager()
        config = get_config()

        # Import here to avoid circular dependencies
        from src.web.dependencies.tools import get_search_tool, get_scraper_tool

        search_tool = await get_search_tool()
        scraper_tool = await get_scraper_tool()

        # Create agent
        _research_agent = ResearchAgent(
            llm_manager=llm_manager,
            search_tool=search_tool,
            scraper_tool=scraper_tool,
            config=config
        )
        logger.info("ResearchAgent instance created")

    return _research_agent


async def get_code_agent() -> CodeAgent:
    """Get code agent instance

    Returns:
        CodeAgent: Singleton code agent instance
    """
    global _code_agent

    if _code_agent is None:
        # Get dependencies internally
        llm_manager = await get_llm_manager()
        config = get_config()

        from src.web.dependencies.tools import get_code_executor

        code_executor = await get_code_executor()

        # Create agent
        _code_agent = CodeAgent(
            llm_manager=llm_manager,
            code_executor=code_executor,
            config=config
        )
        logger.info("CodeAgent instance created")

    return _code_agent


async def get_chat_agent() -> ChatAgent:
    """Get chat agent instance

    Returns:
        ChatAgent: Singleton chat agent instance
    """
    global _chat_agent

    if _chat_agent is None:
        # Get dependencies internally
        llm_manager = await get_llm_manager()
        config = get_config()

        # Create agent
        _chat_agent = ChatAgent(
            llm_manager=llm_manager,
            config=config
        )
        logger.info("ChatAgent instance created")

    return _chat_agent


async def get_rag_agent() -> RAGAgent:
    """Get RAG agent instance

    Returns:
        RAGAgent: Singleton RAG agent instance
    """
    global _rag_agent

    if _rag_agent is None:
        # Get dependencies internally
        llm_manager = await get_llm_manager()
        config = get_config()

        from src.web.dependencies.tools import get_vector_store

        vector_store = await get_vector_store()

        # Create agent
        _rag_agent = RAGAgent(
            llm_manager=llm_manager,
            vector_store=vector_store,
            config=config
        )
        logger.info("RAGAgent instance created")

    return _rag_agent


async def get_master_agent() -> MasterAgent:
    """Get MasterAgent instance

    Returns:
        MasterAgent: Singleton master agent instance
    """
    global _master_agent

    if _master_agent is None:
        # Get dependencies internally
        llm_manager = await get_llm_manager()
        config = get_config()

        from src.web.dependencies.tools import (
            get_search_tool,
            get_scraper_tool,
            get_code_executor,
            get_weather_tool,
            get_finance_tool,
            get_routing_tool,
            get_ocr_tool,
            get_vision_tool,
        )

        # Get all tools
        search_tool = await get_search_tool()
        scraper_tool = await get_scraper_tool()
        code_executor = await get_code_executor()
        weather_tool = await get_weather_tool()
        finance_tool = await get_finance_tool()
        routing_tool = await get_routing_tool()
        ocr_tool = await get_ocr_tool()
        vision_tool = await get_vision_tool()

        # Get RAG agent
        rag_agent = await get_rag_agent()

        # Create MasterAgent
        _master_agent = MasterAgent(
            llm_manager=llm_manager,
            search_tool=search_tool,
            scraper_tool=scraper_tool,
            code_executor=code_executor,
            weather_tool=weather_tool,
            finance_tool=finance_tool,
            routing_tool=routing_tool,
            ocr_tool=ocr_tool,
            vision_tool=vision_tool,
            rag_agent=rag_agent,
            config=config
        )
        logger.info("MasterAgent instance created")

    return _master_agent


# Cleanup function (called on app shutdown)
async def cleanup_dependencies():
    """Cleanup singleton instances

    Call this on app shutdown to properly cleanup resources.
    """
    global _llm_manager, _router, _research_agent, _code_agent, _chat_agent, _rag_agent, _master_agent

    logger.info("Cleaning up dependency instances")

    _llm_manager = None
    _router = None
    _research_agent = None
    _code_agent = None
    _chat_agent = None
    _rag_agent = None
    _master_agent = None
