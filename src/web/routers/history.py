"""History management router"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse

from src.web import database
from src.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def view_history(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    mode: str = Query(None)
):
    """View conversation history"""
    templates = request.app.state.templates

    try:
        if mode:
            # Filter by mode
            conversations = await database.search_conversations(
                search_query="",
                mode=mode,
                limit=limit
            )
        else:
            # Get all recent conversations
            conversations = await database.get_recent_conversations(limit=limit)

        # Get statistics
        stats = await database.get_statistics()

        return templates.TemplateResponse(
            "history.html",
            {
                "request": request,
                "conversations": conversations,
                "stats": stats,
                "current_mode": mode
            }
        )

    except Exception as e:
        logger.error(f"History view error: {e}")
        return templates.TemplateResponse(
            "history.html",
            {
                "request": request,
                "conversations": [],
                "error": str(e)
            }
        )


@router.get("/search", response_class=HTMLResponse)
async def search_history(
    request: Request,
    q: str = Query(...),
    mode: str = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Search conversation history"""
    templates = request.app.state.templates

    try:
        conversations = await database.search_conversations(
            search_query=q,
            mode=mode,
            limit=limit
        )

        return templates.TemplateResponse(
            "components/history_list.html",
            {
                "request": request,
                "conversations": conversations,
                "search_query": q
            }
        )

    except Exception as e:
        logger.error(f"History search error: {e}")
        return HTMLResponse(
            content=f'<div class="error">Search error: {str(e)}</div>',
            status_code=500
        )


@router.get("/{conversation_id}", response_class=HTMLResponse)
async def get_conversation(request: Request, conversation_id: int):
    """Get a specific conversation"""
    templates = request.app.state.templates

    try:
        conversation = await database.get_conversation_by_id(conversation_id)

        if not conversation:
            return HTMLResponse(
                content='<div class="error">Conversation not found</div>',
                status_code=404
            )

        return templates.TemplateResponse(
            "components/conversation_detail.html",
            {
                "request": request,
                "conversation": conversation
            }
        )

    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        return HTMLResponse(
            content=f'<div class="error">Error: {str(e)}</div>',
            status_code=500
        )


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation"""

    try:
        success = await database.delete_conversation(conversation_id)

        if success:
            return JSONResponse(
                content={"status": "ok", "message": "Conversation deleted"},
                status_code=200
            )
        else:
            return JSONResponse(
                content={"status": "error", "message": "Conversation not found"},
                status_code=404
            )

    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


@router.delete("/")
async def clear_all_history():
    """Clear all conversation history"""

    try:
        count = await database.clear_all_history()

        return JSONResponse(
            content={
                "status": "ok",
                "message": f"Deleted {count} conversations"
            },
            status_code=200
        )

    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


@router.get("/stats/summary")
async def get_statistics():
    """Get history statistics"""

    try:
        stats = await database.get_statistics()

        return JSONResponse(
            content=stats,
            status_code=200
        )

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )
