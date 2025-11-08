"""Code execution mode router"""

import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

from src.agents import CodeAgent
from src.llm import LLMManager
from src.tools import CodeExecutor
from src.utils import get_config, get_logger
from src.web import database
from src.web.middleware import limiter, get_limit

logger = get_logger(__name__)
router = APIRouter()

# Initialize components
config = get_config()
llm_manager = LLMManager(config=config)
code_executor = CodeExecutor(
    timeout=config.code_execution.timeout,
    max_output_lines=config.code_execution.max_output_lines,
)
code_agent = CodeAgent(
    llm_manager=llm_manager,
    code_executor=code_executor,
    config=config,
)


@router.post("/", response_class=HTMLResponse)
@limiter.limit(get_limit("compute"))  # 5 requests/minute
async def execute_code(request: Request, query: str = Form(...)):
    """
    Execute code generation and execution
    """
    templates = request.app.state.templates

    try:
        # Execute code agent
        logger.info(f"Code query: {query}")
        result = await code_agent.solve(query, show_progress=False)

        # Highlight code with Pygments
        code_html = highlight(
            result.get("code", ""),
            PythonLexer(),
            HtmlFormatter(
                style='monokai',
                linenos='table',
                cssclass='highlight'
            )
        )

        # Get Pygments CSS
        formatter = HtmlFormatter(style='monokai')
        pygments_css = formatter.get_style_defs('.highlight')

        # Save to history
        await database.save_conversation(
            mode="code",
            query=query,
            response=result.get("explanation", ""),
            metadata=json.dumps({
                "code": result.get("code", ""),
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "success": result.get("success", False)
            })
        )

        return templates.TemplateResponse(
            "code_result.html",
            {
                "request": request,
                "query": query,
                "code_html": code_html,
                "code_raw": result.get("code", ""),
                "output": result.get("output", ""),
                "explanation": result.get("explanation", ""),
                "error": result.get("error", ""),
                "success": result.get("success", False),
                "pygments_css": pygments_css
            }
        )

    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return templates.TemplateResponse(
            "code_result.html",
            {
                "request": request,
                "query": query,
                "error": str(e),
                "success": False
            }
        )
