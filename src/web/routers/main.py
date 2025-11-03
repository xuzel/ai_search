"""Main page router"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the new home page with unified search box"""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "breadcrumb_section": "Home"
        }
    )
