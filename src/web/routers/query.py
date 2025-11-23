"""Unified Query Router - Powered by MasterAgent

This is the new simplified version using MasterAgent for automatic tool orchestration.

Key changes:
- Single MasterAgent handles all queries and file uploads
- Automatic tool detection and orchestration
- Unified result format
- LLM-enhanced outputs
"""

import json
from typing import Optional
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse
import markdown

from src.agents.master_agent import MasterAgent
from src.web import database
from src.web.middleware import limiter, get_limit
from src.web.dependencies import (
    get_master_agent,
    get_markdown_processor,
    convert_markdown_to_html,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================
# Utility Functions
# ============================================

def _convert_markdown(text: str, md_processor: markdown.Markdown) -> str:
    """Convert markdown text to HTML"""
    return convert_markdown_to_html(text, md_processor)


async def save_conversation_to_db(
    query: str,
    result: dict,
    tools_used: list
) -> None:
    """Save conversation to database"""
    response_text = result.get("answer", "")

    await database.save_conversation(
        mode="unified",
        query=query,
        response=response_text,
        metadata=json.dumps({
            "tools_used": tools_used,
            "confidence": result.get("confidence", 0.0),
            "sources": result.get("sources", [])
        })
    )


# ============================================
# Main Query Endpoint (Simplified)
# ============================================

@router.post("/query", response_class=HTMLResponse)
@limiter.limit(get_limit("query"))  # 30 requests/minute
async def unified_query(
    request: Request,
    query: str = Form(""),  # Optional now, can be empty if only uploading file
    file: Optional[UploadFile] = File(None),
    # Dependency injection
    master_agent: MasterAgent = Depends(get_master_agent),
    md_processor: markdown.Markdown = Depends(get_markdown_processor),
):
    """Unified query endpoint with automatic tool orchestration

    This endpoint:
    1. Accepts text query and/or file upload
    2. Uses MasterAgent to automatically:
       - Process files (OCR/Vision/RAG)
       - Decompose complex queries
       - Call appropriate tools
       - Aggregate results
    3. Returns LLM-enhanced natural language response

    Args:
        request: FastAPI request
        query: User query (optional if file provided)
        file: Uploaded file (optional)
        master_agent: MasterAgent instance (injected)
        md_processor: Markdown processor (injected)

    Returns:
        HTML response with unified result
    """
    templates = request.app.state.templates

    try:
        # Validate input
        if not query and not file:
            return templates.TemplateResponse("components/result_unified.html", {
                "request": request,
                "error": "Please provide a query or upload a file.",
            })

        # If file but no query, set default query
        if file and not query:
            if file.filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                query = "What's in this image?"
            else:
                query = "Summarize this document"

        logger.info(f"Processing query: '{query[:100]}...' with file: {file.filename if file else 'None'}")

        # Process with MasterAgent
        result = await master_agent.process_query(
            query=query,
            uploaded_file=file
        )

        # Check for errors
        if "error" in result:
            return templates.TemplateResponse("components/result_unified.html", {
                "request": request,
                "error": result["error"],
            })

        # Extract result fields
        answer = result.get("answer", "")
        tools_used = result.get("tools_used", [])
        sources = result.get("sources", [])
        details = result.get("details", {})
        confidence = result.get("confidence", 0.0)
        key_points = result.get("key_points", [])

        # Convert answer markdown to HTML
        answer_html = _convert_markdown(answer, md_processor)

        # Save to database
        await save_conversation_to_db(query, result, tools_used)

        logger.info(
            f"Query processed successfully. Tools used: {', '.join(tools_used)}, "
            f"Confidence: {confidence:.2f}"
        )

        # Render unified result template
        return templates.TemplateResponse("components/result_unified.html", {
            "request": request,
            "query": query,
            "answer": answer_html,
            "tools_used": tools_used,
            "sources": sources,
            "key_points": key_points,
            "confidence": confidence,
            "details": details,
            "has_file": file is not None,
            "filename": file.filename if file else None,
        })

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)

        return templates.TemplateResponse("components/result_unified.html", {
            "request": request,
            "error": f"An error occurred: {str(e)}",
            "query": query,
        })
