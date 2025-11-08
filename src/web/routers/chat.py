"""Chat mode router with streaming support"""

import asyncio
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
    Stream chat response character by character

    Note: This is a simulation. For real streaming, you'd need to modify
    the LLM client to support streaming responses.
    """

    try:
        # Get response from chat agent
        response = await chat_agent.chat(message)

        # Save to history
        await database.save_conversation(
            mode="chat",
            query=message,
            response=response
        )

        # Simulate streaming by yielding characters with small delay
        # In production, you'd use the LLM's native streaming capability
        words = response.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word
            await asyncio.sleep(0.05)  # Small delay for typing effect

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
