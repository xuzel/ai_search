"""FastAPI Web Application for AI Search Engine"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from src.web import database
from src.web.middleware import setup_rate_limiting
from src.web.routers import main, search, code, chat, history, query, rag, multimodal, tools, workflow
from src.utils import get_logger

logger = get_logger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AI Search Engine Web UI...")
    await database.init_db()
    logger.info("Database initialized (with connection pooling)")
    yield
    # Shutdown
    logger.info("Shutting down AI Search Engine Web UI...")
    await database.close_db_pool()
    logger.info("Database connection pool closed")


# Create FastAPI app
app = FastAPI(
    title="AI Search Engine",
    description="LLM-powered search engine with research, code execution, and chat capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware with environment-based configuration
# Security: Use whitelist in production, wildcard only in development
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
cors_origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Set CORS_ORIGINS="http://localhost:3000,https://example.com" in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Setup rate limiting
setup_rate_limiting(app)

# Get paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOADS_DIR = BASE_DIR / "uploads"

# Create uploads directory if it doesn't exist
UPLOADS_DIR.mkdir(exist_ok=True)
(UPLOADS_DIR / "rag_documents").mkdir(exist_ok=True)
(UPLOADS_DIR / "images").mkdir(exist_ok=True)
(UPLOADS_DIR / "temp").mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Make templates available to routers
app.state.templates = templates

# Include routers
app.include_router(main.router, tags=["main"])
app.include_router(query.router, tags=["query"])  # Unified query router with intelligent routing
app.include_router(rag.router, tags=["rag"])  # RAG document Q&A
app.include_router(multimodal.router, tags=["multimodal"])  # Multimodal - OCR & Vision
app.include_router(tools.router, tags=["tools"])  # Domain Tools - Weather, Finance, Routing
app.include_router(workflow.router, tags=["workflow"])  # Workflow - Multi-step task orchestration
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(code.router, prefix="/code", tags=["code"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(history.router, prefix="/history", tags=["history"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Search Engine is running"}


# Run with: uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8000"))

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "src.web.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
