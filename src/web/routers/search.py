"""Search/Research mode router"""

import json
from typing import AsyncGenerator
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from src.agents import ResearchAgent
from src.llm import LLMManager
from src.tools import SearchTool, ScraperTool
from src.utils import get_config, get_logger
from src.web import database
from src.web.dependencies.formatters import convert_markdown_to_html

logger = get_logger(__name__)
router = APIRouter()

# Initialize components
config = get_config()
llm_manager = LLMManager(config=config)
search_tool = SearchTool(
    provider=config.search.provider,
    api_key=config.search.serpapi_key,
)
scraper_tool = ScraperTool(
    timeout=config.scraper.timeout,
    max_workers=config.scraper.max_workers,
    user_agent=config.scraper.user_agent,
)
research_agent = ResearchAgent(
    llm_manager=llm_manager,
    search_tool=search_tool,
    scraper_tool=scraper_tool,
    config=config,
)


@router.post("/", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...)):
    """
    Execute research query and return results
    """
    templates = request.app.state.templates

    try:
        # Execute research
        logger.info(f"Research query: {query}")
        result = await research_agent.research(query, show_progress=False)

        # Render summary as Markdown (using singleton processor)
        summary_html = convert_markdown_to_html(result["summary"])

        # Save to history
        await database.save_conversation(
            mode="research",
            query=query,
            response=result["summary"],
            metadata=json.dumps({
                "sources": result.get("sources", []),
                "plan": result.get("plan", {})
            })
        )

        return templates.TemplateResponse(
            "search_result.html",
            {
                "request": request,
                "query": query,
                "summary": summary_html,
                "sources": result.get("sources", []),
                "success": True
            }
        )

    except Exception as e:
        logger.error(f"Research error: {e}")
        return templates.TemplateResponse(
            "search_result.html",
            {
                "request": request,
                "query": query,
                "error": str(e),
                "success": False
            }
        )


async def stream_research_response(query: str) -> AsyncGenerator[dict, None]:
    """
    Stream research response with progress updates and summary chunks

    Yields SSE events:
    - 'progress': Stage updates (plan, search, scrape, synthesis)
    - 'sources': List of research sources
    - 'content': Summary text chunks
    - 'done': Research completion
    """
    full_summary = ""
    sources = []

    try:
        async for item in research_agent.stream_research(query):
            if isinstance(item, dict):
                if item.get("type") == "progress":
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "stage": item.get("stage"),
                            "message": item.get("message"),
                            "queries": item.get("queries", [])
                        })
                    }
                elif item.get("type") == "sources":
                    sources = item.get("sources", [])
                    yield {
                        "event": "sources",
                        "data": json.dumps(sources)
                    }
            else:
                # String chunk from synthesis
                full_summary += item
                yield {
                    "event": "content",
                    "data": item
                }

        # Save to history after completion
        await database.save_conversation(
            mode="research",
            query=query,
            response=full_summary,
            metadata=json.dumps({"sources": sources})
        )

        yield {"event": "done", "data": ""}

    except Exception as e:
        logger.error(f"Streaming research error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }


@router.post("/stream")
async def search_stream(query: str = Form(...)):
    """
    Execute streaming research query with SSE
    """
    return EventSourceResponse(stream_research_response(query))
