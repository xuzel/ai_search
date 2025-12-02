"""Chat mode router with streaming support"""

from typing import AsyncGenerator
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from src.agents import ChatAgent
from src.llm import LLMManager
from src.utils import get_config, get_logger
from src.web import database

logger = get_logger(__name__)
router = APIRouter()

# Initialize components
config = get_config()
llm_manager = LLMManager(config=config)
chat_agent = ChatAgent(llm_manager=llm_manager, config=config)


@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Render chat interface"""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "chat.html",
        {"request": request}
    )


@router.post("/message", response_class=HTMLResponse)
async def chat_message(request: Request, message: str = Form(...)):
    """
    Handle chat message (non-streaming version)
    """
    templates = request.app.state.templates

    try:
        # Get response from chat agent
        logger.info(f"Chat message: {message}")
        response = await chat_agent.chat(message)

        # Save to history
        await database.save_conversation(
            mode="chat",
            query=message,
            response=response
        )

        return templates.TemplateResponse(
            "components/chat_message.html",
            {
                "request": request,
                "message": response,
                "role": "assistant"
            }
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return templates.TemplateResponse(
            "components/chat_message.html",
            {
                "request": request,
                "message": f"Error: {str(e)}",
                "role": "error"
            }
        )


async def stream_chat_response(message: str) -> AsyncGenerator[str, None]:
    """
    Stream chat response using real LLM streaming

    Uses the ChatAgent's stream_chat method for true streaming output
    from LLM providers (OpenAI, DashScope, DeepSeek, Ollama).
    """
    full_response = ""

    try:
        # Use real streaming from chat agent
        async for chunk in chat_agent.stream_chat(message):
            full_response += chunk
            yield chunk

        # Save complete response to history after streaming completes
        await database.save_conversation(
            mode="chat",
            query=message,
            response=full_response
        )

    except Exception as e:
        logger.error(f"Chat streaming error: {e}")
        yield f"Error: {str(e)}"


@router.post("/stream")
async def chat_stream(message: str = Form(...)):
    """
    Handle chat message with Server-Sent Events streaming
    """

    async def event_generator():
        async for chunk in stream_chat_response(message):
            yield {
                "event": "message",
                "data": chunk
            }
        # Send completion event
        yield {
            "event": "done",
            "data": ""
        }

    return EventSourceResponse(event_generator())


@router.post("/clear")
async def clear_history(request: Request):
    """Clear chat history in session"""
    chat_agent.clear_history()
    return {"status": "ok", "message": "Chat history cleared"}
