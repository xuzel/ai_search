"""Code execution mode router"""

import json
from typing import AsyncGenerator
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from sse_starlette.sse import EventSourceResponse

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


async def stream_code_response(query: str, auto_fix: bool = True) -> AsyncGenerator[dict, None]:
    """
    Stream code execution response with progress updates and explanation chunks

    Yields SSE events:
    - 'progress': Stage updates (generate, validate, execute, explain)
    - 'code': Generated or fixed code
    - 'output': Execution output
    - 'error': Execution errors
    - 'fix_attempt': Auto-fix attempts info
    - 'content': Streaming explanation chunks
    - 'done': Completion
    """
    final_code = ""
    final_output = ""
    final_error = ""
    success = False

    try:
        async for item in code_agent.stream_solve(query, auto_fix=auto_fix):
            if isinstance(item, dict):
                item_type = item.get("type")

                if item_type == "progress":
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "stage": item.get("stage"),
                            "message": item.get("message")
                        })
                    }
                elif item_type == "code":
                    final_code = item.get("code", "")
                    yield {
                        "event": "code",
                        "data": json.dumps({"code": final_code})
                    }
                elif item_type == "output":
                    final_output = item.get("output", "")
                    success = True
                    yield {
                        "event": "output",
                        "data": json.dumps({"output": final_output})
                    }
                elif item_type == "error":
                    final_error = item.get("error", "")
                    yield {
                        "event": "error",
                        "data": json.dumps({
                            "error": final_error,
                            "stage": item.get("stage")
                        })
                    }
                elif item_type == "fix_attempt":
                    yield {
                        "event": "fix_attempt",
                        "data": json.dumps({
                            "attempt": item.get("attempt"),
                            "error": item.get("error"),
                            "message": item.get("message")
                        })
                    }
            else:
                # String chunk from streaming explanation
                yield {
                    "event": "content",
                    "data": item
                }

        # Save to history after completion
        await database.save_conversation(
            mode="code",
            query=query,
            response="",  # Explanation was streamed
            metadata=json.dumps({
                "code": final_code,
                "output": final_output,
                "error": final_error,
                "success": success
            })
        )

        yield {"event": "done", "data": ""}

    except Exception as e:
        logger.error(f"Streaming code execution error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }


@router.post("/stream")
@limiter.limit(get_limit("compute"))
async def code_stream(request: Request, query: str = Form(...), auto_fix: bool = Form(True)):
    """
    Execute streaming code generation with auto-fix support
    """
    return EventSourceResponse(stream_code_response(query, auto_fix=auto_fix))
