"""Unified Query Router - Refactored with Dependency Injection

This is the refactored version of query.py with:
- No global variables
- Dependency injection
- Smaller, focused functions
- Better separation of concerns
"""

import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
import markdown

# Use new unified routing system
from src.routing import BaseRouter, RoutingDecision, TaskType
from src.agents import ResearchAgent, CodeAgent, ChatAgent
from src.tools import WeatherTool, FinanceTool, RoutingTool, CredibilityScorer
from src.web import database
from src.web.middleware import limiter, get_limit
from src.web.dependencies import (
    get_router,
    get_research_agent,
    get_code_agent,
    get_chat_agent,
    get_weather_tool,
    get_finance_tool,
    get_routing_tool,
    get_credibility_scorer,
    get_markdown_processor,
    convert_markdown_to_html,
)
from src.utils.logger import get_logger
from src.utils import extract_location, extract_stock_symbol, extract_route

logger = get_logger(__name__)

router = APIRouter()


# ============================================
# Task Execution Functions (Separated)
# ============================================

async def execute_research_task(
    query: str,
    research_agent: ResearchAgent
) -> Dict[str, Any]:
    """Execute research task

    Args:
        query: User query
        research_agent: Research agent instance

    Returns:
        Research result dictionary
    """
    logger.info(f"Executing research task: {query}")
    result = await research_agent.research(query, show_progress=False)
    return result


async def execute_code_task(
    query: str,
    code_agent: CodeAgent
) -> Dict[str, Any]:
    """Execute code generation and execution task

    Args:
        query: User query
        code_agent: Code agent instance

    Returns:
        Code execution result dictionary
    """
    logger.info(f"Executing code task: {query}")
    result = await code_agent.solve(query)
    return result


async def execute_chat_task(
    query: str,
    chat_agent: ChatAgent
) -> Dict[str, Any]:
    """Execute chat task

    Args:
        query: User query
        chat_agent: Chat agent instance

    Returns:
        Chat response dictionary
    """
    logger.info(f"Executing chat task: {query}")
    result = await chat_agent.chat(query)
    return result


async def execute_weather_task(
    query: str,
    weather_tool: Optional[WeatherTool]
) -> Dict[str, Any]:
    """Execute weather query task

    Args:
        query: User query
        weather_tool: Weather tool instance

    Returns:
        Weather result dictionary
    """
    if weather_tool is None:
        return {
            "error": "Weather tool not enabled. Please configure OPENWEATHERMAP_API_KEY."
        }

    logger.info(f"Executing weather task: {query}")

    # Extract location from query using entity extractor
    location = extract_location(query)
    logger.debug(f"Extracted location: {location}")

    result = await weather_tool.get_weather(location)
    return {
        "location": location,
        "weather_data": result,
        "summary": _format_weather_summary(result)
    }


async def execute_finance_task(
    query: str,
    finance_tool: Optional[FinanceTool]
) -> Dict[str, Any]:
    """Execute finance query task

    Args:
        query: User query
        finance_tool: Finance tool instance

    Returns:
        Finance result dictionary
    """
    if finance_tool is None:
        return {
            "error": "Finance tool not enabled. Please configure ALPHA_VANTAGE_API_KEY."
        }

    logger.info(f"Executing finance task: {query}")

    # Extract stock symbol from query using entity extractor
    symbol = extract_stock_symbol(query)
    logger.debug(f"Extracted stock symbol: {symbol}")

    result = await finance_tool.get_stock_quote(symbol)
    return {
        "symbol": symbol,
        "stock_data": result,
        "summary": _format_finance_summary(result)
    }


async def execute_routing_task(
    query: str,
    routing_tool: Optional[RoutingTool]
) -> Dict[str, Any]:
    """Execute routing/navigation task

    Args:
        query: User query
        routing_tool: Routing tool instance

    Returns:
        Routing result dictionary
    """
    if routing_tool is None:
        return {
            "error": "Routing tool not enabled. Please configure OPENROUTESERVICE_API_KEY."
        }

    logger.info(f"Executing routing task: {query}")

    # Extract origin and destination from query using entity extractor
    origin, destination = extract_route(query)
    logger.debug(f"Extracted route: {origin} -> {destination}")

    if not origin or not destination:
        return {
            "query": query,
            "summary": "Could not extract origin and destination. Please specify 'from X to Y' format."
        }

    # Get route using routing tool
    result = await routing_tool.get_route(
        origin=origin,
        destination=destination,
        profile="driving-car"
    )

    return {
        "origin": origin,
        "destination": destination,
        "route_data": result,
        "summary": f"Route from {origin} to {destination}"
    }


# ============================================
# Helper Functions
# ============================================

def _format_weather_summary(weather_data: Dict[str, Any]) -> str:
    """Format weather data into readable summary"""
    if "error" in weather_data:
        return f"Error: {weather_data['error']}"

    return (
        f"Temperature: {weather_data.get('temperature', 'N/A')}°C, "
        f"Condition: {weather_data.get('description', 'N/A')}, "
        f"Humidity: {weather_data.get('humidity', 'N/A')}%"
    )


def _format_finance_summary(stock_data: Dict[str, Any]) -> str:
    """Format stock data into readable summary"""
    if "error" in stock_data:
        return f"Error: {stock_data['error']}"

    return (
        f"Price: ${stock_data.get('price', 'N/A')}, "
        f"Change: {stock_data.get('change', 'N/A')} "
        f"({stock_data.get('change_percent', 'N/A')}%)"
    )


async def add_credibility_scores(
    sources: list,
    credibility_scorer: Optional[CredibilityScorer]
) -> list:
    """Add credibility scores to research sources

    Args:
        sources: List of source dictionaries
        credibility_scorer: Credibility scorer instance

    Returns:
        Sources with credibility scores added
    """
    if not credibility_scorer or not sources:
        return sources

    for source in sources:
        if source.get('url'):
            score = credibility_scorer.score_source(
                url=source['url'],
                title=source.get('title', ''),
                snippet=source.get('snippet', '')
            )
            source['credibility_score'] = score['overall_score']
            source['credibility_details'] = score

    return sources


# Markdown conversion moved to src.web.dependencies.formatters
# Kept as wrapper for backward compatibility
def _convert_markdown(text: str, md_processor: markdown.Markdown) -> str:
    """Convert markdown text to HTML using provided processor

    Args:
        text: Markdown text
        md_processor: Markdown processor instance

    Returns:
        HTML string
    """
    return convert_markdown_to_html(text, md_processor)


async def save_conversation_to_db(
    mode: str,
    query: str,
    result: Dict[str, Any],
    task_type: TaskType,
    confidence: float
) -> None:
    """Save conversation to database

    Args:
        mode: Conversation mode (research, code, chat)
        query: User query
        result: Task execution result
        task_type: Classified task type
        confidence: Classification confidence
    """
    # Extract response text based on mode
    if mode == "research":
        response_text = str(result.get('summary', ''))
    elif mode == "code":
        response_text = (
            str(result.get('explanation', '')) +
            "\n\nOutput: " +
            str(result.get('output', ''))
        )
    elif mode == "chat":
        response_text = str(result.get('message', '') or result.get('answer', ''))
    else:
        response_text = str(result)

    # Save to database
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


# ============================================
# Main Query Endpoint (Refactored)
# ============================================

@router.post("/query", response_class=HTMLResponse)
@limiter.limit(get_limit("query"))  # 30 requests/minute
async def unified_query(
    request: Request,
    query: str = Form(...),
    # Dependency injection (no more global variables!)
    router_instance: BaseRouter = Depends(get_router),
    research_agent: ResearchAgent = Depends(get_research_agent),
    code_agent: CodeAgent = Depends(get_code_agent),
    chat_agent: ChatAgent = Depends(get_chat_agent),
    weather_tool: Optional[WeatherTool] = Depends(get_weather_tool),
    finance_tool: Optional[FinanceTool] = Depends(get_finance_tool),
    routing_tool: Optional[RoutingTool] = Depends(get_routing_tool),
    credibility_scorer: Optional[CredibilityScorer] = Depends(get_credibility_scorer),
    md_processor: markdown.Markdown = Depends(get_markdown_processor),
):
    """Unified query endpoint with intelligent routing

    This endpoint:
    1. Classifies the query using the unified router
    2. Routes to appropriate task executor
    3. Saves conversation history
    4. Returns formatted response

    Args:
        request: FastAPI request
        query: User query from form
        router_instance: Router for query classification (injected)
        research_agent: Research agent (injected)
        code_agent: Code agent (injected)
        chat_agent: Chat agent (injected)
        weather_tool: Weather tool (injected, optional)
        finance_tool: Finance tool (injected, optional)
        routing_tool: Routing tool (injected, optional)
        credibility_scorer: Credibility scorer (injected, optional)
        md_processor: Markdown processor (injected)

    Returns:
        HTML response with query result
    """
    templates = request.app.state.templates

    try:
        # Step 1: Classify query
        logger.info(f"Classifying query: {query}")
        decision: RoutingDecision = await router_instance.route(
            query=query,
            context={'language': 'zh'}  # Chinese context
        )

        task_type = decision.primary_task_type
        confidence = decision.task_confidence
        reasoning = decision.reasoning

        logger.info(
            f"Classification: {task_type.value} "
            f"(confidence: {confidence:.2f}, reason: {reasoning})"
        )

        # Step 2: Execute task based on classification
        if task_type == TaskType.RESEARCH:
            result = await execute_research_task(query, research_agent)
            mode = "research"

        elif task_type == TaskType.CODE:
            result = await execute_code_task(query, code_agent)
            mode = "code"

        elif task_type == TaskType.CHAT:
            result = await execute_chat_task(query, chat_agent)
            mode = "chat"

        elif task_type == TaskType.DOMAIN_WEATHER:
            result = await execute_weather_task(query, weather_tool)
            mode = "research"  # Render as research

        elif task_type == TaskType.DOMAIN_FINANCE:
            result = await execute_finance_task(query, finance_tool)
            mode = "research"  # Render as research

        elif task_type == TaskType.DOMAIN_ROUTING:
            result = await execute_routing_task(query, routing_tool)
            mode = "research"  # Render as research

        else:
            # Fallback to chat
            logger.warning(f"Unknown task type {task_type}, defaulting to chat")
            result = await execute_chat_task(query, chat_agent)
            mode = "chat"

        # Step 3: Post-process results
        if mode == "research":
            # Convert markdown to HTML using singleton processor
            if result.get('summary'):
                result['summary'] = _convert_markdown(result['summary'], md_processor)

            # Add credibility scores
            if result.get('sources'):
                result['sources'] = await add_credibility_scores(
                    result['sources'],
                    credibility_scorer
                )

        elif mode == "chat":
            # Convert markdown to HTML for chat responses using singleton processor
            if result.get('message'):
                result['message'] = _convert_markdown(result['message'], md_processor)
            elif result.get('answer'):
                result['answer'] = _convert_markdown(result['answer'], md_processor)

        # Step 4: Save to database
        await save_conversation_to_db(mode, query, result, task_type, confidence)

        # Step 5: Render response
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
