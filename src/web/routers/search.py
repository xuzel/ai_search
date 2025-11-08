"""Search/Research mode router"""

import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

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
