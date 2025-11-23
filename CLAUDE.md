# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Search Engine - An LLM-powered multi-agent system combining research, code execution, chat, RAG, and domain-specific tools (weather, finance, routing). Built with FastAPI, supports multiple LLM providers (OpenAI, Aliyun DashScope, DeepSeek, Ollama), and features intelligent query routing.

**Primary Language:** Python 3.8+
**Main Branch:** master

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys (DASHSCOPE_API_KEY, SERPAPI_API_KEY, etc.)
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_routing.py

# Run tests by marker
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m "not requires_api"  # Skip tests requiring API keys

# Run single test function
pytest tests/test_routing.py::test_keyword_router
```

**Note:** Test configuration in `pytest.ini` - coverage reports to `htmlcov/`, `coverage.xml`, `coverage.json`

### Web Server
```bash
# Development server with hot reload
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000

# Production (set WEB_HOST/WEB_PORT in .env)
python -m src.web.app

# Access at: http://localhost:8000
```

### CLI Commands
```bash
# Research query
python -m src.main search "your research query"

# Code execution
python -m src.main solve "calculate fibonacci(100)"

# Auto-routed query (uses routing system)
python -m src.main ask "What's the weather in Beijing?"

# Interactive chat
python -m src.main chat

# System info
python -m src.main info
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## Architecture Overview

### Core Components

**1. Routing System (`src/routing/`)**
- **Purpose:** Intelligent query classification to route requests to appropriate agents
- **Flow:** User Query → Router → RoutingDecision (TaskType + confidence) → Agent
- **Router Types:**
  - `KeywordRouter`: Pattern matching (fast, no LLM calls)
  - `LLMRouter`: LLM-based classification (accurate, requires API)
  - `HybridRouter`: Keyword first, LLM fallback (recommended)
- **Factory:** Use `create_router(config, llm_manager, router_type='hybrid')` from `src/routing/factory.py`
- **TaskTypes:** RESEARCH, CODE, CHAT, RAG, WORKFLOW, DOMAIN_WEATHER, DOMAIN_FINANCE, DOMAIN_ROUTING, MULTIMODAL_OCR, MULTIMODAL_VISION

**2. Agents (`src/agents/`)**
- `ResearchAgent`: Web search + scraping + LLM summarization
- `CodeAgent`: Generates & executes Python code securely
- `ChatAgent`: General conversation
- `RAGAgent`: Document Q&A with vector store (ChromaDB)

**3. LLM Manager (`src/llm/manager.py`)**
- **Multi-provider support** with automatic fallback
- **Supported providers:**
  - OpenAI (gpt-3.5-turbo, gpt-4)
  - Aliyun DashScope (qwen models) - default if enabled
  - DeepSeek (deepseek-chat)
  - Ollama (local models)
  - Any OpenAI-compatible API
- **Configuration:** `config/config.yaml` under `llm:` section
- **Key methods:** `generate()`, `generate_streaming()`, `list_providers()`

**4. Code Execution Security (`src/tools/code_executor.py`, `code_validator.py`, `sandbox_executor.py`)**
- **3-layer defense:**
  1. **AST Validation:** Static analysis blocks dangerous patterns (eval, exec, file ops)
  2. **Docker Sandbox:** Isolated containers with resource limits (default: 256MB RAM, 1 CPU)
  3. **Subprocess Fallback:** Timeout enforcement if Docker unavailable
- **Security Levels:** STRICT (no imports) | MODERATE (math, datetime, json) | PERMISSIVE (numpy, pandas)
- **Configuration:** `config/config.yaml` under `code_execution:` section
- **Important:** Docker must be running for secure execution. Set `enable_docker: true` in config.

**5. Domain Tools (`src/tools/`)**
- `WeatherTool`: OpenWeatherMap API integration
- `FinanceTool`: Stock data (Alpha Vantage + yfinance fallback)
- `RoutingTool`: Directions/routes (OpenRouteService API)
- `VisionTool`: Image analysis (Google Gemini Vision)
- `OCRTool`: Text extraction from images (PaddleOCR)
- `SearchTool`: Web search (SerpAPI)
- `ScraperTool`: Web content extraction (trafilatura + BeautifulSoup)

**6. RAG System (`src/agents/rag_agent.py`, `src/tools/vector_store.py`, `src/tools/chunking.py`)**
- **Embedding model:** sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- **Vector DB:** ChromaDB (persisted to `./data/vector_store/`)
- **Chunking strategies:** fixed | semantic | recursive (configured in `config/config.yaml`)
- **Retrieval:** Top-K similarity search with optional reranking (BGE reranker)

**7. Workflow Engine (`src/workflow/workflow_engine.py`)**
- **Multi-step task orchestration** with dependency management
- **Execution modes:** SEQUENTIAL | PARALLEL | DAG (dependency graph)
- **Features:** Error recovery, retry logic, progress tracking
- **Task decomposer:** LLM-powered breakdown of complex queries into subtasks

### Web Application Structure (`src/web/`)

**FastAPI Routers:**
- `/` - Main UI (templates)
- `/query` - Unified query endpoint (intelligent routing)
- `/search` - Research endpoint
- `/code` - Code execution
- `/chat` - Chat interface
- `/rag` - Document upload & Q&A
- `/multimodal` - OCR & vision
- `/tools` - Weather, finance, routing
- `/workflow` - Multi-step tasks
- `/history` - Query history (SQLite)

**Database:** SQLite (`src/web/database.py`) with async connection pooling

**Middleware:**
- Rate limiting (slowapi) - configurable via `RATE_LIMIT_ENABLED` env var
- CORS (configured via `CORS_ORIGINS` env var)

## Configuration

**Primary config:** `config/config.yaml`
**Environment vars:** `.env` (copy from `.env.example`)

**Key configuration sections:**
- `llm:` - LLM provider settings (enabled, api_key, model, base_url)
- `search:` - Search provider (serpapi_key required)
- `code_execution:` - Security level, Docker settings, timeouts
- `rag:` - Embedding model, chunking strategy, retrieval params
- `domain_tools:` - Weather, finance, routing API keys

**LLM Provider Priority:**
1. First enabled provider with valid API key becomes primary
2. DashScope (Aliyun Qwen) is default if enabled
3. Fallback to other providers if primary fails

## Important Patterns

### Adding a New Agent
1. Create class in `src/agents/` inheriting from a base pattern (see existing agents)
2. Implement core methods (e.g., `research()`, `solve()`, `chat()`)
3. Add to `src/agents/__init__.py` exports
4. Register in appropriate router (if new TaskType needed)

### Adding a New Router Type
1. Create router class in `src/routing/` inheriting from `BaseRouter`
2. Implement `route(query, context) -> RoutingDecision`
3. Add to `RouterFactory.create_router()` in `src/routing/factory.py`
4. Update `TaskType` enum in `src/routing/task_types.py` if new task types needed

### Adding a New Domain Tool
1. Create tool class in `src/tools/` with standard interface (async methods)
2. Add configuration to `config/config.yaml` under `domain_tools:`
3. Create dependency function in `src/web/dependencies/tools.py`
4. Add routing patterns to keyword router (if applicable)
5. Add API endpoint in `src/web/routers/tools.py`

### Modifying Security Settings
- **Never disable validation** (`enable_validation: true`) in production
- Security level changes in `config.yaml` affect allowed imports
- Docker required for production-grade isolation
- Network access disabled by default (`enable_network: false`)

### Working with Tests
- Use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.requires_api`
- Mock external APIs in unit tests (see `tests/conftest.py` for fixtures)
- Run integration tests only when API keys available
- `tests/archive/` contains legacy test files - prefer tests in root `tests/` directory

## Data Persistence

- **Vector store:** `./data/vector_store/` (ChromaDB)
- **Query history:** SQLite DB (location in `database.py`)
- **Uploads:** `src/web/uploads/` (rag_documents/, images/, temp/)
- **Cache:** `./cache/` (if cache enabled in config)

## Security Considerations

1. **API Keys:** Never commit `.env` file - use `.env.example` as template
2. **Code Execution:** Always runs through validation + sandbox (unless explicitly disabled)
3. **CORS:** Set specific origins in production (`CORS_ORIGINS=https://example.com`)
4. **Rate Limiting:** Enabled by default, configure storage backend for production (Redis recommended)
5. **Input Sanitization:** Secret sanitizer in `src/utils/secret_sanitizer.py` removes sensitive data from logs

## Logging

- **Configuration:** Set `LOG_LEVEL`, `LOG_FORMAT`, `LOG_FILE` in `.env`
- **Formats:** standard | detailed (includes file/line) | json (structured)
- **Logger:** Use `from src.utils import get_logger; logger = get_logger(__name__)`

## Common Debugging

- **"No LLM providers available":** Check `.env` has valid API keys and `config.yaml` has `enabled: true`
- **Docker permission errors:** Ensure Docker daemon running and user has permissions
- **Import errors:** Install dependencies with `pip install -r requirements.txt`
- **Test failures:** Check if API keys set for `@pytest.mark.requires_api` tests
- **Rate limit errors:** Check `RATE_LIMIT_STORAGE` env var or disable with `RATE_LIMIT_ENABLED=false`
