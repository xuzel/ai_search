"""Tool Dependencies

Provides tool dependencies (search, scraper, code executor, etc.).
"""

from typing import Optional

from src.tools import SearchTool, ScraperTool, CodeExecutor
from src.tools.vector_store import VectorStore
from src.tools.weather_tool import WeatherTool
from src.tools.finance_tool import FinanceTool
from src.tools.routing_tool import RoutingTool
from src.tools.reranker import HybridReranker, Reranker
from src.tools.credibility_scorer import CredibilityScorer
from src.tools.ocr_tool import OCRTool
from src.tools.vision_tool import VisionTool
from src.tools.code_validator import SecurityLevel
from src.web.dependencies.core import get_config, get_llm_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Singleton instances
_search_tool: Optional[SearchTool] = None
_scraper_tool: Optional[ScraperTool] = None
_code_executor: Optional[CodeExecutor] = None
_vector_store: Optional[VectorStore] = None
_weather_tool: Optional[WeatherTool] = None
_finance_tool: Optional[FinanceTool] = None
_routing_tool: Optional[RoutingTool] = None
_reranker: Optional[Reranker] = None
_credibility_scorer: Optional[CredibilityScorer] = None
_ocr_tool: Optional[OCRTool] = None
_vision_tool: Optional[VisionTool] = None


async def get_search_tool() -> SearchTool:
    """Get search tool instance"""
    global _search_tool

    if _search_tool is None:
        config = get_config()
        _search_tool = SearchTool(
            provider=config.search.provider,
            api_key=config.search.serpapi_key
        )
        logger.info("SearchTool instance created")

    return _search_tool


async def get_scraper_tool() -> ScraperTool:
    """Get scraper tool instance"""
    global _scraper_tool

    if _scraper_tool is None:
        config = get_config()
        _scraper_tool = ScraperTool(
            timeout=config.scraper.timeout,
            max_workers=config.scraper.max_workers,
            user_agent=config.scraper.user_agent
        )
        logger.info("ScraperTool instance created")

    return _scraper_tool


async def get_code_executor() -> CodeExecutor:
    """Get code executor instance"""
    global _code_executor

    if _code_executor is None:
        config = get_config()
        _code_executor = CodeExecutor(
            timeout=config.code_execution.timeout,
            max_output_lines=config.code_execution.max_output_lines,
            security_level=SecurityLevel(config.code_execution.security_level),
            enable_docker=config.code_execution.enable_docker,
            enable_validation=config.code_execution.enable_validation,
            memory_limit=config.code_execution.memory_limit
        )
        # Initialize executor (pull Docker image if needed)
        await _code_executor.initialize()
        logger.info("CodeExecutor instance created and initialized")

    return _code_executor


async def get_vector_store() -> VectorStore:
    """Get vector store instance"""
    global _vector_store

    if _vector_store is None:
        config = get_config()
        _vector_store = VectorStore(
            embedding_model=config.rag.embedding_model,
            persist_directory=config.rag.persist_directory,
            collection_name=config.rag.collection_name
        )
        logger.info("VectorStore instance created")

    return _vector_store


async def get_weather_tool() -> Optional[WeatherTool]:
    """Get weather tool instance (if enabled)"""
    global _weather_tool

    config = get_config()
    if not config.domain_tools.weather.enabled:
        return None

    if _weather_tool is None:
        _weather_tool = WeatherTool(
            api_key=config.domain_tools.weather.api_key,
            units=config.domain_tools.weather.units,
            language=config.domain_tools.weather.language
        )
        logger.info("WeatherTool instance created")

    return _weather_tool


async def get_finance_tool() -> Optional[FinanceTool]:
    """Get finance tool instance (if enabled)"""
    global _finance_tool

    config = get_config()
    if not config.domain_tools.finance.enabled:
        return None

    if _finance_tool is None:
        _finance_tool = FinanceTool(
            alpha_vantage_key=config.domain_tools.finance.alpha_vantage_key
        )
        logger.info("FinanceTool instance created")

    return _finance_tool


async def get_routing_tool() -> Optional[RoutingTool]:
    """Get routing tool instance (if enabled)"""
    global _routing_tool

    config = get_config()
    if not config.domain_tools.routing.enabled:
        return None

    if _routing_tool is None:
        _routing_tool = RoutingTool(
            api_key=config.domain_tools.routing.api_key,
            default_profile=config.domain_tools.routing.default_profile
        )
        logger.info("RoutingTool instance created")

    return _routing_tool


async def get_reranker() -> Optional[Reranker]:
    """Get reranker instance (if enabled)"""
    global _reranker

    config = get_config()
    if not config.rag.reranking.enabled:
        return None

    if _reranker is None:
        _reranker = HybridReranker(
            model_name=config.rag.reranking.model,
            top_k=config.rag.reranking.top_k
        )
        logger.info("HybridReranker instance created")

    return _reranker


async def get_credibility_scorer() -> CredibilityScorer:
    """Get credibility scorer instance"""
    global _credibility_scorer

    if _credibility_scorer is None:
        _credibility_scorer = CredibilityScorer()
        logger.info("CredibilityScorer instance created")

    return _credibility_scorer


async def get_ocr_tool() -> Optional[OCRTool]:
    """Get OCR tool instance (if enabled)"""
    global _ocr_tool

    config = get_config()
    if not config.multimodal.ocr.enabled:
        return None

    if _ocr_tool is None:
        try:
            _ocr_tool = OCRTool()
            logger.info("OCRTool instance created")
        except Exception as e:
            logger.warning(f"OCRTool initialization failed: {e}")
            return None

    return _ocr_tool


async def get_vision_tool() -> Optional[VisionTool]:
    """Get vision tool instance (if enabled) - Now using Aliyun Qwen3-VL-Plus"""
    global _vision_tool

    config = get_config()
    if not config.multimodal.vision.enabled:
        return None

    if _vision_tool is None:
        try:
            # ✅ Updated to use Aliyun API with base_url
            _vision_tool = VisionTool(
                api_key=config.multimodal.vision.api_key,
                model=config.multimodal.vision.model,
                base_url=getattr(config.multimodal.vision, 'base_url',
                                'https://dashscope.aliyuncs.com/compatible-mode/v1')
            )
            logger.info(f"VisionTool instance created with Aliyun {config.multimodal.vision.model}")
        except Exception as e:
            logger.warning(f"VisionTool initialization failed: {e}")
            return None

    return _vision_tool


# Cleanup function
async def cleanup_tool_dependencies():
    """Cleanup tool singleton instances"""
    global _search_tool, _scraper_tool, _code_executor, _vector_store
    global _weather_tool, _finance_tool, _routing_tool, _reranker, _credibility_scorer
    global _ocr_tool, _vision_tool

    logger.info("Cleaning up tool dependency instances")

    _search_tool = None
    _scraper_tool = None
    _code_executor = None
    _vector_store = None
    _weather_tool = None
    _finance_tool = None
    _routing_tool = None
    _reranker = None
    _credibility_scorer = None
    _ocr_tool = None
    _vision_tool = None
