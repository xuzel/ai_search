# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Search Engine - An LLM-powered search engine with three core modes:
- **Research Mode**: Web search, content scraping, and LLM-based synthesis
- **Code Mode**: Generates and executes Python code for math/computation problems
- **Chat Mode**: General conversational AI

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
- Uses TaskType enum: `RESEARCH`, `CODE`, `CHAT`

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
  - `database.py`: SQLite async database for conversation history (using aiosqlite)
  - `routers/`: Separate routers for each mode (main, search, code, chat, history)
  - `templates/`: Jinja2 templates with base layout and component partials
  - `static/`: CSS (warm neutral theme), JS (HTMX utilities)
- **Features**:
  - Unified search box with auto-routing
  - Code syntax highlighting (Pygments)
  - Markdown rendering for research summaries
  - Streaming chat responses (SSE)
  - Full conversation history with search/filter/delete
- **Database Schema** (src/web/database.py:18):
  - Table: `conversation_history` (id, timestamp, mode, query, response, metadata)
  - Indexes on timestamp and mode for fast queries

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
- Base template: `templates/base.html` (includes HTMX, CSS)
- Use Jinja2 template inheritance: `{% extends "base.html" %}`
- HTMX attributes for dynamic updates:
  - `hx-post="/endpoint"` - POST request
  - `hx-target="#element-id"` - Target for response
  - `hx-swap="innerHTML"` - How to swap content
  - `hx-indicator="#loading"` - Show loading state

**Styling:**
- CSS variables defined in `static/css/style.css`
- Warm neutral color scheme: `--bg-primary`, `--accent-warm`, etc.
- Responsive design with mobile breakpoints
- Component classes: `.card`, `.btn`, `.form-input`

**Database Operations:**
- All database functions are async (use `await`)
- Import from `src.web.database`
- Always save conversations after completion: `await database.save_conversation(mode, query, response, metadata)`

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

### Modifying Router Classification

**Keyword patterns** (`src/router.py`):
- `RESEARCH_KEYWORDS`: Triggers research mode
- `CODE_KEYWORDS`: Triggers code execution
- `CALCULATION_INDICATORS`: Catches questions like "how many hours in a week"
- `MATH_PATTERNS`: Regex patterns for math operators/symbols
- `UNIT_CONVERSION_PATTERNS`: Regex for unit conversion questions

**LLM classification** (`Router.classify_with_llm`):
- Modify prompt in `classification_prompt` string (src/router.py:241)
- Returns JSON with `{"task_type": "CODE|RESEARCH|CHAT", "confidence": 0.0-1.0, "reason": "..."}`

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
```

## API Keys Configuration Priority

1. Environment variables (`.env` file)
2. `config/config.yaml` using `${VAR}` syntax
3. Direct values in `config.yaml` (not recommended for secrets)

## Common Troubleshooting

**"No LLM providers available"**
- Check that at least one provider has `enabled: true` in config.yaml
- Verify API key is set (environment variable or config)
- Check `LLMManager._initialize_providers()` logs

**Research mode fails**
- Verify `SERPAPI_API_KEY` is configured
- Check `config.search.serpapi_key` is not empty

**Code execution timeout**
- Increase `config.code_execution.timeout` value
- Check if code has infinite loops

**Router misclassification**
- For keyword issues: adjust patterns in `Router` class
- For LLM issues: modify `classification_prompt` in `Router.classify_with_llm()`
- Use `--verbose` flag to see classification confidence
