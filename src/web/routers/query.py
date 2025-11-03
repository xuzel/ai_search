"""Unified Query Router - Auto-classify and route queries"""

import asyncio
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
import logging
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

from src.router import Router, TaskType
from src.llm import LLMManager
from src.agents import ResearchAgent, CodeAgent, ChatAgent
from src.tools import SearchTool, CodeExecutor, ScraperTool, HybridReranker, Reranker, CredibilityScorer, WeatherTool, FinanceTool, RoutingTool
from src.utils import get_config
from src.web import database

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (initialized once)
config = None
llm_manager = None
research_agent = None
code_agent = None
chat_agent = None
reranker = None
credibility_scorer = None
weather_tool = None
finance_tool = None
routing_tool = None


async def initialize_agents():
    """Initialize all agents and tools"""
    global config, llm_manager, research_agent, code_agent, chat_agent, reranker, credibility_scorer, weather_tool, finance_tool, routing_tool

    if llm_manager is None:
        config = get_config()
        llm_manager = LLMManager(config=config)

        # Initialize router (no constructor arguments needed)
        query_router = Router()

        # Initialize tools
        search_tool = SearchTool(api_key=config.search.serpapi_key)
        scraper_tool = ScraperTool()
        code_executor = CodeExecutor(
            timeout=config.code_execution.timeout,
            max_output_lines=config.code_execution.max_output_lines
        )

        # Initialize advanced tools
        # Try HybridReranker first (stronger), fallback to Reranker
        try:
            reranker = HybridReranker()
            logger.info("HybridReranker initialized (preferred)")
        except Exception as e:
            logger.warning(f"HybridReranker initialization failed, trying Reranker: {e}")
            try:
                reranker = Reranker()
                logger.info("Reranker initialized as fallback")
            except Exception as e2:
                logger.warning(f"Reranker initialization failed (optional): {e2}")
                reranker = None

        credibility_scorer = CredibilityScorer()

        # Initialize domain tools
        try:
            weather_tool = WeatherTool()
            logger.info("WeatherTool initialized")
        except Exception as e:
            logger.warning(f"WeatherTool initialization failed (optional): {e}")
            weather_tool = None

        try:
            finance_tool = FinanceTool()
            logger.info("FinanceTool initialized")
        except Exception as e:
            logger.warning(f"FinanceTool initialization failed (optional): {e}")
            finance_tool = None

        try:
            routing_tool = RoutingTool()
            logger.info("RoutingTool initialized")
        except Exception as e:
            logger.warning(f"RoutingTool initialization failed (optional): {e}")
            routing_tool = None

        # Initialize agents
        research_agent = ResearchAgent(
            llm_manager=llm_manager,
            search_tool=search_tool,
            scraper_tool=scraper_tool,
            config=config
        )
        code_agent = CodeAgent(
            llm_manager=llm_manager,
            code_executor=code_executor,
            config=config
        )
        chat_agent = ChatAgent(llm_manager=llm_manager)

        logger.info("All agents initialized successfully")


@router.post("/query", response_class=HTMLResponse)
async def unified_query(request: Request, query: str = Form(...)):
    """
    Unified query endpoint with intelligent routing

    This endpoint:
    1. Classifies the query using Router (hybrid approach)
    2. Routes to appropriate agent
    3. Returns unified result format
    """
    await initialize_agents()

    templates = request.app.state.templates

    try:
        # Step 1: Classify query
        logger.info(f"Classifying query: {query}")
        task_type, confidence, reason = await Router.classify_hybrid(query, llm_manager=llm_manager)

        logger.info(f"Classified as {task_type.value} with confidence {confidence:.2f} - {reason}")

        # Step 2: Route to appropriate agent
        if task_type == TaskType.RESEARCH:
            result = await handle_research(query)
            mode = "research"
        elif task_type == TaskType.CODE:
            result = await handle_code(query)
            mode = "code"
        elif task_type == TaskType.CHAT:
            result = await handle_chat(query)
            mode = "chat"
        elif task_type == TaskType.DOMAIN_WEATHER:
            result = await handle_weather(query)
            mode = "research"  # Render as research result
        elif task_type == TaskType.DOMAIN_FINANCE:
            result = await handle_finance(query)
            mode = "research"  # Render as research result
        elif task_type == TaskType.DOMAIN_ROUTING:
            result = await handle_routing(query)
            mode = "research"  # Render as research result
        else:
            # Default to research for unknown types
            logger.warning(f"Unknown task type {task_type}, defaulting to research")
            result = await handle_research(query)
            mode = "research"

        # Step 3: Save to history
        import json
        # Extract response based on mode
        if mode == "research":
            response_text = str(result.get('summary', ''))
        elif mode == "code":
            response_text = str(result.get('explanation', '')) + "\n\nOutput: " + str(result.get('output', ''))
        elif mode == "chat":
            response_text = str(result.get('message', '') or result.get('answer', ''))
        else:
            response_text = str(result)

        await database.save_conversation(
            mode=mode,
            query=query,
            response=response_text,
            metadata=json.dumps({
                "task_type": task_type.value,
                "confidence": confidence,
                "sources": result.get('sources', []) if isinstance(result.get('sources'), list) else []
            })
        )

        # Step 4: Process result for rendering
        # Convert markdown to HTML for text responses
        if mode in ["research", "chat", "rag"]:
            md = markdown.Markdown(
                extensions=[
                    FencedCodeExtension(),
                    CodeHiliteExtension(),
                    TableExtension(),
                    'nl2br',
                ]
            )

            if mode == "research" and result.get('summary'):
                result['summary'] = md.convert(result['summary'])

                # Add credibility scores to sources
                if credibility_scorer and result.get('sources'):
                    for source in result['sources']:
                        if source.get('url'):
                            score = credibility_scorer.score_source(
                                url=source['url'],
                                title=source.get('title', ''),
                                snippet=source.get('snippet', '')
                            )
                            source['credibility_score'] = score['overall_score']
                            source['credibility_details'] = score

            elif mode == "chat" and result.get('message'):
                result['message'] = md.convert(result['message'])
            elif mode == "chat" and result.get('answer'):
                result['answer'] = md.convert(result['answer'])
            elif mode == "rag" and result.get('answer'):
                result['answer'] = md.convert(result['answer'])

        # Render result
        return templates.TemplateResponse(
            f"components/result_{mode}.html",
            {
                "request": request,
                "query": query,
                "result": result,
                "task_type": task_type.value,
                "confidence": confidence
            }
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": str(e),
                "query": query
            }
        )


async def handle_research(query: str) -> dict:
    """Handle research queries"""
    logger.info(f"Executing research for: {query}")
    result = await research_agent.research(query)

    # Apply reranking to sources if available and we have sources
    if reranker and result.get('sources') and len(result['sources']) > 0:
        try:
            logger.info(f"Applying reranker to {len(result['sources'])} sources")
            snippets = [s.get('snippet', '') for s in result['sources']]

            # Only rerank if we have content
            if any(snippets):
                reranked = await reranker.rerank(query, snippets, top_k=min(10, len(result['sources'])))

                # Reorder sources based on reranked results
                if reranked and 'scores' in reranked:
                    # Create a mapping of scores to sources
                    scored_sources = []
                    for idx, score in enumerate(reranked.get('scores', [])):
                        if idx < len(result['sources']):
                            source = result['sources'][idx].copy()
                            source['rerank_score'] = score
                            scored_sources.append(source)

                    # Sort by rerank score (descending)
                    scored_sources.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
                    result['sources'] = scored_sources
                    logger.info(f"Reranking completed, top source rerank score: {scored_sources[0].get('rerank_score', 0):.3f}")
        except Exception as e:
            logger.warning(f"Reranking failed (non-critical): {e}")
            # Continue without reranking

    return result


async def handle_code(query: str) -> dict:
    """Handle code generation/execution queries"""
    logger.info(f"Executing code generation for: {query}")
    result = await code_agent.solve(query, show_progress=False)
    return result


async def handle_chat(query: str) -> dict:
    """Handle chat queries"""
    logger.info(f"Executing chat for: {query}")
    response = await chat_agent.chat(query)
    return {
        "message": response,
        "answer": response
    }


async def handle_weather(query: str) -> dict:
    """Handle weather queries"""
    logger.info(f"Executing weather query for: {query}")
    if not weather_tool:
        logger.warning("WeatherTool not available")
        return {
            "summary": "Weather tool is not available. Please try again later.",
            "sources": []
        }

    try:
        result = await weather_tool.get_weather(query)
        return {
            "summary": result.get("summary", str(result)),
            "sources": [{"title": "Weather Data", "snippet": result.get("summary", str(result)), "url": ""}]
        }
    except Exception as e:
        logger.error(f"Weather query failed: {e}")
        return {
            "summary": f"Unable to fetch weather information: {str(e)}",
            "sources": []
        }


async def handle_finance(query: str) -> dict:
    """Handle finance queries"""
    logger.info(f"Executing finance query for: {query}")
    if not finance_tool:
        logger.warning("FinanceTool not available")
        return {
            "summary": "Finance tool is not available. Please try again later.",
            "sources": []
        }

    try:
        result = await finance_tool.get_stock_info(query)
        return {
            "summary": result.get("summary", str(result)),
            "sources": [{"title": "Stock Data", "snippet": result.get("summary", str(result)), "url": ""}]
        }
    except Exception as e:
        logger.error(f"Finance query failed: {e}")
        return {
            "summary": f"Unable to fetch finance information: {str(e)}",
            "sources": []
        }


async def handle_routing(query: str) -> dict:
    """Handle routing queries"""
    logger.info(f"Executing routing query for: {query}")
    if not routing_tool:
        logger.warning("RoutingTool not available")
        return {
            "summary": "Routing tool is not available. Please try again later.",
            "sources": []
        }

    try:
        result = await routing_tool.get_route(query)
        return {
            "summary": result.get("summary", str(result)),
            "sources": [{"title": "Route Information", "snippet": result.get("summary", str(result)), "url": ""}]
        }
    except Exception as e:
        logger.error(f"Routing query failed: {e}")
        return {
            "summary": f"Unable to fetch routing information: {str(e)}",
            "sources": []
        }


@router.post("/classify", response_class=HTMLResponse)
async def classify_query(request: Request, query: str = Form(...)):
    """
    Classify query without executing it
    Used for showing the detected mode before execution
    """
    await initialize_agents()

    templates = request.app.state.templates

    try:
        task_type, confidence, reason = await Router.classify_hybrid(query, llm_manager=llm_manager)

        # Map task types to icons and labels
        type_info = {
            TaskType.RESEARCH: {"icon": "🔍", "label": "Research", "color": "primary"},
            TaskType.CODE: {"icon": "💻", "label": "Code", "color": "success"},
            TaskType.CHAT: {"icon": "💬", "label": "Chat", "color": "secondary"},
        }

        info = type_info.get(task_type, {"icon": "❓", "label": "Unknown", "color": "secondary"})

        return f"""
        <div class="search-type-indicator" id="typeIndicator">
            <span>Detected mode:</span>
            <span class="search-type-badge badge-{info['color']}">
                {info['icon']} {info['label']} - {int(confidence * 100)}% confidence
            </span>
            <span style="margin-left: auto;">
                <button class="btn btn-ghost btn-sm" onclick="document.getElementById('typeIndicator').style.display='none'">
                    Change
                </button>
            </span>
        </div>
        """

    except Exception as e:
        logger.error(f"Error classifying query: {e}", exc_info=True)
        return ""
