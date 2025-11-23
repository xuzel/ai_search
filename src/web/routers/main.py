"""Main page router"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

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


# Redirect specialized pages to unified main page
@router.get("/rag")
async def redirect_rag():
    """Redirect RAG page to main page (功能已集成到主页面)"""
    return RedirectResponse(url="/", status_code=302)


@router.get("/multimodal")
async def redirect_multimodal():
    """Redirect Multimodal page to main page (功能已集成到主页面)"""
    return RedirectResponse(url="/", status_code=302)


@router.get("/tools")
async def redirect_tools():
    """Redirect Tools page to main page (功能已集成到主页面)"""
    return RedirectResponse(url="/", status_code=302)


@router.get("/workflow")
async def redirect_workflow():
    """Redirect Workflow page to main page (功能已集成到主页面)"""
    return RedirectResponse(url="/", status_code=302)
