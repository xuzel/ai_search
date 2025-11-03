# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Search Engine - An LLM-powered search engine with multiple modes:
- **Research Mode**: Web search, content scraping, and LLM-based synthesis
- **Code Mode**: Generates and executes Python code for math/computation problems
- **Chat Mode**: General conversational AI
- **RAG Mode**: Document Q&A with vector search (PDF, DOCX, etc.)
- **Domain Tools**: Weather (OpenWeatherMap), Finance (Alpha Vantage/yfinance), Routing (OpenRouteService)
- **Multimodal**: OCR (PaddleOCR) and Vision API (Gemini)
- **Workflow**: Multi-step task orchestration

The system uses an intelligent **Router** that classifies queries and routes them to the appropriate agent (keyword-based for speed, LLM-based for accuracy on ambiguous cases).

## Running the Application

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys (edit config/config.yaml or set environment variables)
export DASHSCOPE_API_KEY="your-key"  # For Aliyun Qwen models
export SERPAPI_API_KEY="your-key"    # For web search
```

### Common Commands

#### Web UI (Recommended)
```bash
# Start web server
python -m src.web.app

# Or using uvicorn directly
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000

# With custom configuration
WEB_HOST=127.0.0.1 WEB_PORT=8080 python -m src.web.app

# Access at http://localhost:8000
```

#### CLI
```bash
# Run as module (recommended)
python -m src.main search "query here"
python -m src.main solve "math problem"
python -m src.main ask "question" --auto  # Auto-routes to correct agent
python -m src.main chat                   # Interactive mode
python -m src.main info                   # System status

# Direct Python execution
python src/main.py search "query"

# Run tests
pytest tests/
pytest tests/test_router.py  # Specific test file
```

## Architecture

### Core Components

**1. Agents** (`src/agents/`)
- `ResearchAgent`: Generates search plan → executes queries → scrapes content → synthesizes summary
- `CodeAgent`: Generates Python code → validates → executes in sandbox → explains results
- `ChatAgent`: Simple conversational interface

**2. Router** (`src/router.py`)
- `Router.classify()`: Fast keyword-based classification
- `Router.classify_with_llm()`: Accurate LLM-based classification
- `Router.classify_hybrid()`: Combines both (use keyword if confidence ≥ threshold, else LLM)
- Uses TaskType enum: `RESEARCH`, `CODE`, `CHAT`, `RAG`, `DOMAIN_WEATHER`, `DOMAIN_FINANCE`, `DOMAIN_ROUTING`
- Priority order for classification: Domain-specific → Explicit keywords → Math patterns → Unit conversions → Calculation indicators → Research keywords → Question marks

**3. LLM Manager** (`src/llm/manager.py`)
- Unified interface for multiple LLM providers
- Automatic fallback: tries preferred → primary → remaining providers
- Providers initialized based on `config.yaml` enabled flags and API keys
- Currently supports:
  - OpenAI (via `OpenAIClient`)
  - Aliyun DashScope/Qwen (via `OpenAIClient` with custom base_url)
  - DeepSeek (via `OpenAIClient` with custom base_url)
  - Ollama (local models)
  - Any OpenAI-compatible endpoint

**4. Tools** (`src/tools/`)
- `SearchTool`: Web search via SerpAPI
- `ScraperTool`: Async web scraping with trafilatura
- `CodeExecutor`: Safe Python code execution with timeout, import restrictions, pattern detection
- `VectorStore`: ChromaDB-based vector storage for RAG
- `DocumentProcessor`: Extracts text from PDF, DOCX, TXT
- `ChunkingTool`: Semantic/fixed/recursive text chunking
- `Reranker`: BGE reranker for improved retrieval
- `CredibilityScorer`: Source credibility scoring
- `WeatherTool`: OpenWeatherMap integration
- `FinanceTool`: Alpha Vantage/yfinance stock data
- `RoutingTool`: OpenRouteService for directions
- `OCRTool`: PaddleOCR for text extraction from images
- `VisionTool`: Gemini Vision API for image analysis

### Configuration System

**`config/config.yaml`** - Main configuration file
- Uses `${ENV_VAR}` for environment variable substitution
- LLM providers: Set `enabled: true/false` to control which providers are initialized
- Each provider configured separately (api_key, model, base_url, temperature, etc.)

**`src/utils/config.py`** - Pydantic-based config loader
- Loads YAML + environment variables
- Validates configuration schema
- Access via `get_config()` which returns cached `Config` instance

### Entry Points

**CLI**: `src/main.py`
- Uses Typer for CLI framework
- Commands: `search`, `solve`, `ask`, `chat`, `info`
- Global instances initialized once (llm_manager, agents, tools)

**Web UI**: `src/web/`
- **FastAPI** application with Jinja2 templates
- **HTMX** for dynamic interactions without heavy JavaScript
- **Architecture**:
  - `app.py`: Main FastAPI app with CORS, static files, lifespan events
  - `database.py`: SQLite async database for conversation and document history (using aiosqlite)
  - `routers/`: Separate routers for each mode:
    - `main.py`: Home page
    - `query.py`: Unified query router with intelligent routing
    - `rag.py`: RAG document Q&A
    - `multimodal.py`: OCR & Vision
    - `tools.py`: Domain tools (Weather, Finance, Routing)
    - `workflow.py`: Multi-step task orchestration
    - `search.py`, `code.py`, `chat.py`: Original mode routers
    - `history.py`: Conversation history management
  - `templates/`: Jinja2 templates with base layout and component partials
  - `static/`: CSS (warm neutral theme), JS (HTMX utilities)
  - `uploads/`: File uploads directory (rag_documents/, images/, temp/)
  - `upload_manager.py`: File upload handling with hashing and validation
- **Features**:
  - Unified search box with auto-routing
  - Code syntax highlighting (Pygments)
  - Markdown rendering for research summaries
  - Streaming chat responses (SSE)
  - Full conversation history with search/filter/delete
  - RAG document upload and Q&A
  - Image OCR and vision analysis
  - Domain-specific queries (weather, stocks, routing)
- **Database Schema**:
  - Table: `conversation_history` (id, timestamp, mode, query, response, metadata)
  - Table: `rag_documents` (id, filename, saved_filename, filepath, file_type, file_size, file_hash, upload_timestamp, processing_status, num_chunks, vector_store_ids, metadata)
  - Indexes on timestamp, mode, upload_timestamp, and processing_status for fast queries

**Programmatic**: `src/__init__.py` exports all major classes
```python
from src.agents import ResearchAgent, CodeAgent
from src.llm import LLMManager
from src.utils import get_config
```

## Development Notes

### Web UI Development

**Adding a New Route:**
1. Create router file in `src/web/routers/`
2. Define router: `router = APIRouter()`
3. Add route handlers with proper response types
4. Include router in `app.py`: `app.include_router(your_router, prefix="/path", tags=["tag"])`

**Template Development:**
- Base templates: `templates/base.html` or `templates/base_new.html` (includes HTMX, CSS)
- Use Jinja2 template inheritance: `{% extends "base.html" %}`
- Component templates in `templates/components/`:
  - `result_*.html`: Result cards for different modes (chat, code, research, rag, weather, finance, routing, ocr, vision, workflow)
  - `loading.html`, `error.html`, `upload_success.html`: Reusable components
  - `document_list.html`, `file_upload.html`: RAG-specific components
- HTMX attributes for dynamic updates:
  - `hx-post="/endpoint"` - POST request
  - `hx-target="#element-id"` - Target for response
  - `hx-swap="innerHTML"` - How to swap content
  - `hx-indicator="#loading"` - Show loading state

**Styling:**
- CSS files: `static/css/style.css`, `static/css/new-style.css`
- Warm neutral color scheme: `--bg-primary`, `--accent-warm`, etc.
- Responsive design with mobile breakpoints
- Component classes: `.card`, `.btn`, `.form-input`

**Database Operations:**
- All database functions are async (use `await`)
- Import from `src.web.database`
- Always save conversations after completion: `await database.save_conversation(mode, query, response, metadata)`
- RAG document management: `save_rag_document()`, `update_rag_document_status()`, `get_rag_documents()`, `delete_rag_document()`

**File Upload Management:**
- Use `upload_manager.py` for file handling
- Supports duplicate detection via file hashing
- Validates file types and sizes
- Stores files in `uploads/` with timestamped filenames

**Common Patterns:**
```python
# Router with template response
@router.get("/page")
async def page(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse("page.html", {"request": request})

# HTMX POST with form data
@router.post("/submit")
async def submit(request: Request, field: str = Form(...)):
    # Process...
    return templates.TemplateResponse("result.html", {...})

# File upload with duplicate check
from src.web.upload_manager import save_uploaded_file
file_info = await save_uploaded_file(upload_file, "rag_documents")
```

### Adding a New LLM Provider

1. If OpenAI-compatible:
   - Add configuration to `config.yaml` under `llm.openai_compatible`
   - Add fields to `LLMConfig` in `src/utils/config.py`
   - Add initialization logic in `LLMManager._initialize_providers()` (src/llm/manager.py:28)

2. If custom API:
   - Create new client in `src/llm/` inheriting from `BaseLLM`
   - Implement `complete()` and `is_available()` methods
   - Register in `LLMManager._initialize_providers()`

### Adding a New Search Provider

Modify `SearchTool` in `src/tools/search.py`:
- Add new `_search_<provider>()` method
- Update routing logic in `search()` method

### Adding RAG/Domain-Specific Features

**RAG System** (`src/tools/`):
- Documents stored in `data/vector_store/` (ChromaDB)
- Chunking strategies: semantic, fixed, recursive (configured in `config.yaml`)
- Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- Retrieval: top_k=10, similarity_threshold=0.7
- Optional reranking: BGE reranker (enabled in config)
- Document processing: `DocumentProcessor` extracts text from PDF, DOCX, TXT
- Web UI uploads saved to `src/web/uploads/rag_documents/`

**Domain Tools** (`src/tools/`):
- Weather: `WeatherTool` with OpenWeatherMap API
- Finance: `FinanceTool` with Alpha Vantage (primary) + yfinance (fallback)
- Routing: `RoutingTool` with OpenRouteService
- Each tool has `enabled` flag in `config.yaml`
- Router prioritizes domain-specific keywords over general classification

**Multimodal** (`src/tools/`):
- OCR: `OCRTool` using PaddleOCR (supports Chinese/English)
- Vision: `VisionTool` using Gemini Vision API
- Image uploads saved to `src/web/uploads/images/`

### Modifying Router Classification

**Keyword patterns** (`src/router.py`):
- Domain-specific keywords (highest priority): `WEATHER_KEYWORDS`, `FINANCE_KEYWORDS`, `ROUTING_KEYWORDS`, `RAG_KEYWORDS`
- `CODE_KEYWORDS`: Triggers code execution
- `RESEARCH_KEYWORDS`: Triggers research mode
- `CALCULATION_INDICATORS`: Catches questions like "how many hours in a week"
- `MATH_PATTERNS`: Regex patterns for math operators/symbols
- `UNIT_CONVERSION_PATTERNS`: Regex for unit conversion questions

**LLM classification** (`Router.classify_with_llm`):
- Modify prompt in `classification_prompt` string (src/router.py:293)
- Returns JSON with `{"task_type": "DOMAIN_WEATHER|DOMAIN_FINANCE|DOMAIN_ROUTING|RAG|CODE|RESEARCH|CHAT", "confidence": 0.0-1.0, "reason": "..."}`
- Classification priority: Domain tools → RAG → CODE → RESEARCH → CHAT

### Code Execution Security

`CodeExecutor` (src/tools/code_executor.py) implements:
- Timeout enforcement (default 30s)
- Import whitelist checking
- Dangerous pattern detection (eval, exec, os.system, etc.)
- Output line limiting
- Subprocess isolation

When modifying security rules, update:
- `allowed_imports` in config
- `DANGEROUS_PATTERNS` list in code_executor.py
- `validate_code()` method

### Testing

The codebase uses pytest. Test files are in `tests/`:
```bash
pytest tests/                    # Run all tests
pytest tests/test_router.py -v   # Verbose output
pytest -k "test_classify"        # Run specific test pattern

# Specific test files
pytest tests/test_basic_functions.py    # Basic functionality tests
pytest tests/test_complete_system.py    # Complete system integration tests
pytest tests/comprehensive_test.py      # Comprehensive feature tests
pytest tests/test_web_ui.py            # Web UI tests
pytest tests/final_test.py             # Final validation tests
pytest tests/quick_test.py             # Quick smoke tests
```

## API Keys Configuration Priority

1. Environment variables (`.env` file) - highest priority
2. `config/config.yaml` using `${VAR_NAME}` syntax for env variable substitution
3. Direct values in `config.yaml` (not recommended for secrets)

**Key environment variables:**
- `DASHSCOPE_API_KEY`: Aliyun Qwen models (primary LLM)
- `OPENAI_API_KEY`: OpenAI GPT models
- `DEEPSEEK_API_KEY`: DeepSeek models
- `SERPAPI_API_KEY`: Web search (required for research mode)
- `GOOGLE_API_KEY`: Gemini Vision API
- `OPENWEATHERMAP_API_KEY`: Weather data
- `ALPHA_VANTAGE_API_KEY`: Stock/finance data
- `OPENROUTESERVICE_API_KEY`: Routing/navigation

**Enabling/Disabling Providers:**
- Each LLM provider has an `enabled` flag in `config.yaml`
- Set `enabled: true/false` to control initialization
- LLMManager only initializes enabled providers with valid API keys
- Priority order: preferred → primary (first initialized) → remaining providers

## Important Architectural Patterns

**Async/Await Everywhere:**
- All agent methods, tools, and database operations are async
- Use `asyncio.run()` for CLI entry points
- FastAPI routes are async by default
- Always use `await` when calling async functions

**Configuration Management:**
- Config loaded once and cached via `get_config()`
- Pydantic models provide type safety and validation
- Environment variable substitution happens in `load_config()` (src/utils/config.py:215)
- `enabled` flags extracted from nested YAML structure (src/utils/config.py:240-253)

**LLM Provider Fallback:**
- LLMManager tries providers in order: preferred → primary → remaining
- Each provider checked with `is_available()` before use
- Automatic retry on failure with next provider
- See `LLMManager.complete()` (src/llm/manager.py:91-157)

**Database Operations:**
- All functions in `src/web/database.py` are async
- Use `aiosqlite` for async SQLite
- Always call `await db.commit()` after writes
- Row factory pattern: `db.row_factory = aiosqlite.Row` for dict results

**File Upload Security:**
- Hash-based duplicate detection (SHA-256)
- File type validation (MIME type and extension)
- Timestamped filenames to prevent collisions
- Separate directories for different file types (rag_documents/, images/, temp/)

## Common Troubleshooting

**"No LLM providers available"**
- Check that at least one provider has `enabled: true` in config.yaml
- Verify API key is set (environment variable or config)
- Check `LLMManager._initialize_providers()` logs (src/llm/manager.py:28)

**Research mode fails**
- Verify `SERPAPI_API_KEY` is configured
- Check `config.search.serpapi_key` is not empty

**Code execution timeout**
- Increase `config.code_execution.timeout` value
- Check if code has infinite loops

**Router misclassification**
- For keyword issues: adjust patterns in `Router` class (src/router.py:35-104)
- For LLM issues: modify `classification_prompt` in `Router.classify_with_llm()` (src/router.py:293)
- Use `--verbose` flag to see classification confidence
- Default hybrid threshold: 0.6 (use LLM if keyword confidence < 60%)

**RAG documents not processing**
- Check vector store directory exists: `data/vector_store/`
- Verify embedding model downloaded: sentence-transformers/all-MiniLM-L6-v2
- Check document format supported: PDF, DOCX, TXT
- Review processing status in database: `rag_documents` table

**Web UI 500 errors**
- Check all required directories exist: `data/`, `uploads/`, `cache/`
- Verify database initialized: `data/history.db`
- Check logs for specific error messages
- Ensure all async operations use `await`
