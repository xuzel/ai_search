"""Main page router"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page with unified search box"""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
