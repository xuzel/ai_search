# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Search Engine** - A production-grade LLM-powered search engine (~15,000 lines of Python) with multiple specialized modes:
- **Research Mode**: Web search (SerpAPI), content scraping (trafilatura), and LLM-based synthesis
- **Code Mode**: Python code generation and secure sandbox execution
- **Chat Mode**: Conversational AI with streaming responses
- **RAG Mode**: Document Q&A with semantic search and optional reranking
- **Domain Tools**: Weather (OpenWeatherMap), Finance (Alpha Vantage/yfinance), Routing (OpenRouteService)
- **Multimodal**: OCR (PaddleOCR) and Vision API (Gemini)
- **Workflow**: Multi-step task orchestration with DAG execution

The core innovation is an intelligent **Router** (`src/routing/`) that classifies queries with dual-path strategy:
- **Fast path**: Keyword/regex patterns with ~10ms latency
- **Accurate path**: LLM-based classification with fallback support
- **Hybrid mode**: Uses keyword confidence threshold (default 0.6) to decide which path

## Development Quick Start

### Initial Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up API keys (all optional except for intended features)
export DASHSCOPE_API_KEY="your-key"        # For Qwen models
export OPENAI_API_KEY="your-key"           # For GPT models
export SERPAPI_API_KEY="your-key"          # For web search
export GOOGLE_API_KEY="your-key"           # For Vision/Gemini
export OPENWEATHERMAP_API_KEY="your-key"   # For weather
export ALPHA_VANTAGE_API_KEY="your-key"    # For stock data
```

### Running the Application

**Web UI** (recommended for development):
```bash
python -m src.web.app              # FastAPI dev server with reload
# Access at http://localhost:8000
```

**CLI** (for testing specific modes):
```bash
python -m src.main search "query"   # Research mode
python -m src.main solve "problem"  # Code execution mode
python -m src.main ask "question" --auto  # Auto-routing
python -m src.main chat             # Interactive chat
python -m src.main info             # System status
```

### Testing & Quality
```bash
# Run all tests with coverage
pytest tests/                       # 173 test functions across 11 test files

# Run specific test suites
pytest tests/test_routing.py -v     # Router/classification tests
pytest tests/test_agents.py         # Agent functionality
pytest tests/test_code_security.py  # Security validation
pytest tests/test_workflow.py       # Workflow engine
pytest tests/test_web_api.py        # Web endpoints

# With markers
pytest tests/ -m "not requires_api" # Skip tests needing API keys
pytest tests/ -m security           # Security tests only
pytest tests/ -m "integration or e2e"  # Integration tests

# Code quality
black src/ tests/                   # Format code
flake8 src/ tests/                  # Lint
mypy src/                           # Type checking (strict mode)
autoflake --remove-all-unused-imports --recursive src/  # Remove dead imports
```

## Architecture Overview

The system follows a **modular agent + router pattern** with ~15k lines across 70+ Python files.

### High-Level Data Flow
```
User Input → Router (Classification) → Agent Selection → Tool Execution → LLM Synthesis → Response
```

### Routing System (`src/routing/`)
- **Dual-path classification**:
  - `KeywordRouter` (src/routing/keyword_router.py): Regex/pattern matching with priority ordering
  - `LLMRouter` (src/routing/llm_router.py): LLM-based classification for ambiguous cases
  - `HybridRouter` (src/routing/hybrid_router.py): Combines both with confidence threshold
- **Task types**: TaskType enum in `src/routing/task_types.py`
- **Factory pattern**: `RouterFactory` creates appropriate router based on config
- Returns `RoutingDecision` with confidence scores, tool requirements, and alternatives

### Agents (`src/agents/`)
Each agent inherits from `BaseAgent` and implements async `execute()`:
- **ResearchAgent**: Generates search queries → parallel SerpAPI calls → content scraping (trafilatura) → LLM synthesis
- **CodeAgent**: Code generation → validation (SecurityValidator) → sandbox execution → explanation
- **ChatAgent**: Streaming responses via SSE
- **RAGAgent**: Vector retrieval (ChromaDB) → optional reranking → LLM synthesis

### LLM Manager (`src/llm/manager.py`)
- **Multi-provider support**: OpenAI, DashScope (Qwen), DeepSeek, Ollama, any OpenAI-compatible endpoint
- **Fallback strategy**: Tries providers in order: preferred → primary → remaining
- **Provider initialization**: Only initializes enabled providers with valid API keys
- All providers inherit from `BaseLLM` interface

### Tools (`src/tools/`)
**Core tools**:
- `SearchTool` (search.py): SerpAPI integration with caching
- `ScraperTool` (scraper.py): Async HTTP + trafilatura extraction
- `CodeExecutor` (code_executor.py): Subprocess isolation with timeout, import whitelist, pattern detection
- `VectorStore` (vector_store.py): ChromaDB wrapper with async methods

**Advanced tools**:
- `DocumentProcessor` (document_processor.py): PDF/DOCX/TXT extraction
- `ChunkingTool` (chunking.py): Semantic/fixed/recursive chunking strategies
- `Reranker` (reranker.py): BGE-based result reranking (optional)
- `CredibilityScorer` (credibility_scorer.py): Source trust scoring

**Domain tools**:
- `WeatherTool` (weather_tool.py): OpenWeatherMap API
- `FinanceTool` (finance_tool.py): Alpha Vantage (primary) + yfinance (fallback)
- `RoutingTool` (routing_tool.py): OpenRouteService directions

**Multimodal**:
- `OCRTool` (ocr_tool.py): PaddleOCR for Chinese/English text extraction
- `VisionTool` (vision_tool.py): Gemini Vision API for image understanding

### Workflow Engine (`src/workflow/`)
- **DAG execution**: Task decomposition + topological execution
- `WorkflowEngine` (workflow_engine.py): Orchestrates multi-step tasks
- `TaskDecomposer` (task_decomposer.py): Breaks complex queries into subtasks

### Configuration System (`src/utils/config.py`)
- **Pydantic models** for type-safe config validation
- **Environment variable substitution**: `${VAR_NAME}` syntax in YAML
- **Caching**: `get_config()` returns singleton instance
- **Provider control**: `enabled: true/false` flags for each LLM/tool
- **Nested structure**: Separate sections for llm, search, code_execution, rag, domain_tools

### Entry Points

**CLI** (`src/main.py`):
- Typer-based CLI with commands: `search`, `solve`, `ask`, `chat`, `info`
- Async entry points with `asyncio.run()`
- Global singleton instances for llm_manager, agents, tools

**Web UI** (`src/web/`):
- **FastAPI** application with async routes
- **Jinja2 templates** + **HTMX** (no heavy JS dependencies)
- **Route organization**:
  - `app.py`: Main application, CORS, lifespan events, dependency injection
  - `routers/`: Modular route handlers (main, query, search, code, chat, rag, multimodal, workflow, tools, history)
  - `dependencies/`: Shared dependencies (tools, formatters, core setup)
  - `middleware/`: Rate limiting, CORS, error handling
  - `database.py`: Async SQLite with aiosqlite for conversation/document history
  - `upload_manager.py`: File handling with SHA-256 deduplication

- **Database**:
  - `conversation_history`: Query/response pairs with timestamps
  - `rag_documents`: Document metadata, processing status, vector store IDs
  - Indexes on timestamp, mode, upload_timestamp for query performance

**Programmatic API** (`src/__init__.py`):
```python
from src.agents import ResearchAgent, CodeAgent, ChatAgent, RAGAgent
from src.llm import LLMManager
from src.routing import RouterFactory
from src.tools import SearchTool, CodeExecutor, VectorStore
from src.utils import get_config
```

## Development Patterns

### Web Route Development
When adding a new endpoint:
```python
# 1. Create router in src/web/routers/
from fastapi import APIRouter, Request, Form
router = APIRouter()

# 2. Define async route
@router.post("/endpoint")
async def my_handler(request: Request, param: str = Form(...)):
    templates = request.app.state.templates
    # Get injected dependencies
    llm_manager = request.app.state.llm_manager
    search_tool = request.app.state.search_tool

    # Process with agents/tools
    result = await some_agent.execute(param)

    # Save to database
    await database.save_conversation("mode", param, result, {})

    # Return template response
    return templates.TemplateResponse("template.html", {
        "request": request,
        "result": result
    })

# 3. Register in app.py
app.include_router(router, prefix="/api", tags=["tag"])
```

### Database Operations
All async, use `aiosqlite`:
```python
from src.web.database import (
    save_conversation,
    get_rag_documents,
    save_rag_document,
    update_rag_document_status,
    delete_rag_document
)

# Always await and handle properly
await save_conversation(mode, query, response, metadata)
```

### File Uploads
```python
from src.web.upload_manager import save_uploaded_file

# Deduplicates by SHA-256 hash
file_info = await save_uploaded_file(upload_file, "rag_documents")
# Returns: {filename, saved_filename, filepath, file_hash}
```

### Adding New Routing Logic
Routers are plugins via factory pattern:
```python
# 1. Create new router class in src/routing/
class MyRouter(BaseRouter):
    async def route(self, query: str) -> RoutingDecision:
        # Classification logic
        return RoutingDecision(
            query=query,
            primary_task_type=TaskType.RESEARCH,
            task_confidence=0.95,
            reasoning="...",
            tools_needed=[...]
        )

# 2. Register in RouterFactory (src/routing/factory.py)
# 3. Set in config: routing.strategy: "my_router"
```

### Adding New Security Rules
Code executor has pattern-based security (`src/tools/code_executor.py`):
```python
# Update dangerous patterns
DANGEROUS_PATTERNS = [
    r'exec\s*\(',
    r'eval\s*\(',
    r'__import__',
    r'globals\s*\(',
    # Add more patterns as needed
]

# Update allowed imports in config.yaml
code_execution:
  allowed_imports:
    - numpy
    - pandas
    # Add safe modules
```

### Adding a New LLM Provider
For OpenAI-compatible providers:
```python
# 1. Add config to config.yaml
llm:
  my_provider:
    enabled: true
    api_key: ${MY_API_KEY}
    model: my-model-name
    base_url: https://api.example.com/v1  # If non-standard

# 2. Add to config model (src/utils/config.py)
class LLMConfig:
    my_provider: OpenAICompatibleConfig = Field(...)

# 3. LLMManager auto-initializes via factory
# (src/llm/manager.py already handles OpenAI-compatible)
```

For custom APIs:
```python
# 1. Create client in src/llm/
class MyClient(BaseLLM):
    async def complete(self, prompt: str) -> str: ...
    async def is_available(self) -> bool: ...

# 2. Register in LLMManager._initialize_providers()
if config.llm.my_provider.enabled:
    self.providers.append(MyClient(...))
```

### Adding a New Domain Tool
Follow the pattern in `src/tools/`:
```python
# 1. Implement tool
class MyTool:
    async def query(self, params: Dict) -> Dict:
        # Call external API
        # Return structured result

# 2. Add to config.yaml with enabled flag
domain_tools:
  my_tool:
    enabled: true
    api_key: ${KEY}

# 3. Add keyword patterns to KeywordRouter
MYTOOL_KEYWORDS = ["pattern1", "pattern2", ...]

# 4. Add TaskType if needed
class TaskType(Enum):
    DOMAIN_MYTOOL = "domain_mytool"
```

### Testing Organization
173 test functions across 11 files with pytest markers:
```bash
# By marker (see pytest.ini)
pytest tests/ -m unit              # Unit tests
pytest tests/ -m integration       # Multi-component tests
pytest tests/ -m e2e              # Full workflows
pytest tests/ -m security         # Security validation

# Key test files
tests/test_routing.py             # Router classification logic
tests/test_agents.py              # Agent execution paths
tests/test_code_security.py       # Code executor safety rules
tests/test_tools.py               # Individual tool functionality
tests/test_workflow.py            # Workflow engine DAG execution
tests/test_performance.py         # Load and benchmark tests
tests/test_web_api.py             # FastAPI endpoints
tests/test_complete_system.py     # End-to-end integration
```

## Key Implementation Details

### Async Architecture
The entire codebase is async-first:
- **Agents**: All `execute()` methods are async coroutines
- **Tools**: Database, HTTP calls, file operations are async
- **Web routes**: FastAPI routes are async handlers
- **CLI**: Entry points use `asyncio.run()` to run async code
- Always use `await` when calling async functions; never block the event loop

### Configuration & Secrets
Pydantic-based config with three-level fallback:
1. Environment variables (highest priority): `${VAR_NAME}` substitution in YAML
2. `config.yaml` direct values
3. Defaults from Pydantic models

Common keys:
- `DASHSCOPE_API_KEY`: Aliyun Qwen (Chinese-focused)
- `OPENAI_API_KEY`: GPT models
- `SERPAPI_API_KEY`: Web search (required for research mode)
- `GOOGLE_API_KEY`: Gemini Vision
- `OPENWEATHERMAP_API_KEY`, `ALPHA_VANTAGE_API_KEY`, `OPENROUTESERVICE_API_KEY`: Domain tools

### LLM Provider Strategy
- **Singleton pattern**: `LLMManager` initialized once via `get_config()`
- **Initialization**: Only creates providers with `enabled: true` AND valid API key
- **Fallback chain**: Tries providers in order → `preferred` → `primary` → `remaining`
- **Per-request**: Automatically falls back if a provider fails
- Each provider implements `BaseLLM` interface with `complete()` and `is_available()`

### Database (async SQLite)
- `src/web/database.py` uses `aiosqlite` for async SQL
- Schema: `conversation_history` (Q&A pairs) + `rag_documents` (metadata/vector IDs)
- **Indexing**: timestamp, mode, upload_timestamp, processing_status for O(1) queries
- **Usage**: Always `await` db calls; use context managers for transactions

### File Upload Security
- **Deduplication**: SHA-256 hashing to prevent duplicate uploads
- **Validation**: MIME type + extension checking
- **Isolation**: Files stored by type (rag_documents/, images/, temp/)
- **Naming**: Timestamps prevent filename collisions

### Security Model
`CodeExecutor` has 3-layer protection:
1. **Pattern detection**: Regex blocklist (eval, exec, __import__, etc.)
2. **Import whitelist**: Only allowed modules (numpy, pandas, scipy, etc.)
3. **Subprocess isolation**: Runs in separate process with timeout (default 30s)

## Project Status & Common Issues

### What Works Well
- ✅ **Modular architecture**: Easy to add new agents, tools, routes
- ✅ **Test coverage**: 173 tests covering all major components
- ✅ **Production ready**: Async concurrency, error handling, security
- ✅ **Extensible routing**: Plugin-based router system with factory pattern
- ✅ **Multi-provider**: LLM fallback, domain tools, multimodal

### Known Limitations & Workarounds
| Issue | Workaround |
|-------|-----------|
| Rare router misclassifications | Use `HybridRouter` (default), increase LLM threshold if needed |
| RAG retrieval quality | Enable reranking in config, tune top_k and similarity_threshold |
| Code execution timeouts | Increase `code_execution.timeout` or optimize the code |
| Web UI async errors | Ensure all database/tool calls are awaited; check logs |
| API rate limits | Implement caching (trafilatura has built-in; add more) |

### Troubleshooting by Symptom
**Router routing wrong tasks:**
- Check `src/routing/keyword_router.py` patterns match your domain
- See `RoutingDecision` object's `reasoning` field for explanation
- Reduce hybrid threshold (default 0.6) to use LLM more often

**RAG documents stuck "processing":**
- Check `data/vector_store/` directory exists and is writable
- Verify embedding model downloaded: `sentence-transformers/all-MiniLM-L6-v2`
- Look for errors in logs; check `rag_documents` table status

**Research mode no results:**
- Verify `SERPAPI_API_KEY` set and not rate-limited
- Check `config.search.results_per_query` (default 5) is reasonable
- Look at SerpAPI dashboard for quota usage

**Web UI crashes:**
- Check all required dirs exist: `data/`, `uploads/`, `src/web/templates/`, `src/web/static/`
- Verify database initialized: `data/history.db` (auto-created on first run)
- Enable logging to see full traceback; check stderr for async errors
