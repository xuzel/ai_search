# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

This is an AI Search Engine - a multi-modal LLM-powered system that automatically routes user queries to appropriate handlers: web research, code execution, or chat.

### Common Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main ask "your query" --auto

# Run tests
pytest tests/

# Run specific test
pytest tests/test_router.py -v

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/

# Run all quality checks
black src/ && flake8 src/ && mypy src/ && pytest tests/
```

### Useful Commands for Development

```bash
# Test search functionality
python -m src.main search "artificial intelligence"

# Test code execution
python -m src.main solve "Calculate 10!"

# Interactive chat mode
python -m src.main chat

# Show system info (check configured providers)
python -m src.main info

# Single test with output
pytest tests/test_router.py::test_name -v -s
```

## Architecture Overview

### Core Data Flow

```
User Input (CLI)
    ↓
Router (Classify task type)
    ├─→ CODE: Math/unit conversion questions
    ├─→ RESEARCH: Information queries/real-time data
    └─→ CHAT: General conversation
    ↓
Three Agent Types:
    ├─→ Research Agent: Search → Scrape → Synthesize
    ├─→ Code Agent: Generate code → Execute → Explain
    └─→ Chat Agent: Direct LLM conversation
    ↓
LLMManager (Unified interface with fallback support)
    ├─→ Primary provider (e.g., Aliyun DashScope)
    ├─→ Fallback providers (OpenAI, DeepSeek, etc.)
    └─→ Local models (Ollama)
    ↓
Output (Formatted results with sources/explanations)
```

### Key Components

#### 1. **Router** (`src/router.py`)
Routes queries to appropriate agents based on content analysis.

**Classification Priority:**
1. CODE keywords (`calculate`, `solve`, `计算`)
2. Math patterns (`^`, `!`, operators)
3. Unit conversion patterns (e.g., "hours in a week")
4. Calculation indicators + time/unit units (`多少` + time words)
5. Research keywords (`search`, `find`, `查询`)
6. Question mark (`?` or `？`) - lowest priority

**Important:** The router intelligently discriminates between:
- Calculation questions: "一週有多少小時？" → CODE (static calculation)
- Real-time queries: "澳門現在的濕度是多少？" → RESEARCH (requires current data)

**Detection logic:**
- Detects real-time keywords: `now`, `current`, `today`, `現在`, `实时`
- Supports both English and Chinese question marks
- Includes unit conversion regex patterns for common conversions

#### 2. **Agents** (`src/agents/`)

**Research Agent** (`research_agent.py`)
- Generates search query plans via LLM
- Performs concurrent searches (SerpAPI)
- Scrapes content from results (Trafilatura)
- Synthesizes information back to user with citations
- Handles multiple search queries with fallbacks

**Code Agent** (`code_agent.py`)
- Generates Python code for problems
- Executes in sandboxed subprocess with:
  - 30-second timeout (configurable)
  - Resource/output limits
  - Import restrictions (math, numpy, pandas, sympy, etc.)
- Provides detailed explanations of results

**Chat Agent** (`chat_agent.py`)
- Direct conversation with LLM
- Maintains conversation history
- Stateful across turns

#### 3. **LLMManager** (`src/llm/manager.py`)
Unified interface supporting multiple providers with automatic fallback.

**Key Features:**
- **Three-layer priority for provider selection:**
  1. Preferred provider (if specified)
  2. Primary provider (first configured)
  3. Remaining providers (in order)
- **Automatic fallback:** If primary provider fails, tries next in list
- **Multi-provider initialization:** Reads enabled flags from config
- **Supported providers:**
  - OpenAI-compatible APIs (OpenAI, DashScope, DeepSeek, local servers)
  - Ollama (local models)
  - Custom implementations via `BaseLLM` interface

#### 4. **Configuration System** (`src/utils/config.py`)

**Three-layer config priority (highest to lowest):**
1. Environment variables (most specific)
2. YAML config with `${VAR_NAME}` substitution
3. YAML hardcoded values

**Example YAML with env substitution:**
```yaml
search:
  serpapi_key: ${SERPAPI_API_KEY}  # Automatically replaced from .env
```

**Automatic env var replacement:**
The system recursively processes config files, replacing all `${VARIABLE}` patterns with environment variable values. Falls back to literal value if variable not found.

#### 5. **Search & Scraping**
- **SearchTool** (`tools/search.py`): Async SerpAPI integration with retry logic
- **ScraperTool** (`tools/scraper.py`): Concurrent content extraction using Trafilatura
- Both support concurrent operations via asyncio

#### 6. **Code Execution Safety** (`tools/code_executor.py`)
```python
Safety measures:
- Subprocess isolation (not eval/exec in main process)
- 30-second execution timeout
- Max 1000 output lines
- Import whitelist: math, numpy, pandas, scipy, sympy, statistics, matplotlib
- Dangerous pattern detection (file ops, network, etc.)
```

## Important Configuration Details

### LLM Provider Setup

**Aliyun DashScope (current primary):**
```yaml
llm:
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```

**OpenAI Compatibility:**
The system uses OpenAI-compatible interface, so any OpenAI API-compatible service works:
```python
# Custom base_url support in OpenAIClient
# Allows pointing to different endpoints while using OpenAI client library
```

### Environment Variable Loading

The system uses `python-dotenv` to load from `.env`. Important files:
- `.env` - User's local environment variables (not in git)
- `.env.example` - Template with all available variables
- `config/config.yaml` - Static config with placeholders

### API Key Substitution Flow

```
.env file
  ↓ (loaded by python-dotenv)
Environment variables
  ↓ (matched by _substitute_env_vars())
config/config.yaml with ${VARIABLE} placeholders
  ↓ (recursive substitution)
Final Config object with actual values
```

## Common Issues and Solutions

### SerpAPI Returns 401 Unauthorized
**Cause:** API key not properly loaded (usually env var substitution issue)
**Fix:**
1. Verify `.env` file exists and has correct `SERPAPI_API_KEY`
2. Check `config.yaml` uses `${SERPAPI_API_KEY}` syntax (not literal value)
3. Restart Python process to reload env vars
4. Run: `python -c "from src.utils import get_config; print(config.search.serpapi_key[:20] + '...')"`

### Typer Flag Parameters Not Working
**Cause:** Version mismatch between typer and click
**Fix:** Install latest typer compatible version
```bash
pip install --upgrade typer  # Should be >= 0.19.0
```
**Note:** Parameters must match CLI flag names (e.g., `--auto` → parameter `auto`, not `auto_mode`)

### Chinese Question Marks Not Detected
**Cause:** Router only checking for ASCII `?` (U+003F), not Chinese `？` (U+FF1F)
**Status:** Fixed in latest version - both are detected
**Details:** See `QUESTION_MARKS` constant in `router.py`

### Real-time Data vs Calculation Misclassification
**Problem:** "澳門現在的濕度是多少？" was being classified as CODE instead of RESEARCH
**Solution:** Added real-time keyword detection (`現在`, `current`, etc.) to discriminate
**Code:** Priority 4 in `router.classify()` method

## Testing Strategy

### Router Tests (`tests/test_router.py`)
Tests query classification logic:
- Math pattern detection
- Keyword matching
- Unit conversion patterns
- Real-time vs calculation discrimination
- Multilingual support (English + Chinese)

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_router.py -v

# Single test
pytest tests/test_router.py::test_classify_math -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/
```

## Key Implementation Notes

### Async Pattern
- All agents use `async def` with proper `await` calls
- Concurrent operations via `asyncio.gather()`
- Research Agent batches searches and scraping concurrently

### Error Handling Strategy
- Agents gracefully degrade: Research continues with fewer results if some searches fail
- LLMManager automatic fallback: Primary provider fails → try next
- All external API calls have retry logic (tenacity library)

### Adding New LLM Providers
1. Create class inheriting `BaseLLM` in `src/llm/`
2. Implement `async complete()` and `is_available()` methods
3. Register in `LLMManager._initialize_providers()`
4. Add config section in `config.yaml`
5. Add corresponding fields to `LLMConfig` pydantic model

### Adding New Search Providers
1. Add `_search_newprovider()` method to `SearchTool`
2. Update `search()` method routing logic
3. Update config system if new config fields needed

## Code Style

The project uses:
- **Formatting:** Black (with default config)
- **Linting:** Flake8
- **Type Checking:** MyPy
- **Docstrings:** Google-style for public APIs
- **Logging:** Python's built-in logging via `get_logger()`

## Documentation Resources

- **ARCHITECTURE.md** - Detailed system design
- **README.md** - User-facing documentation
- **QUICKSTART.md** - Getting started guide
- **TROUBLESHOOTING.md** - Common issues
- **MODEL_SELECTION_GUIDE.md** - Provider selection logic
- **CONFIG_PRIORITY.md** (if exists) - Configuration layer explanation

## Critical Path for Common Tasks

### Debug Query Classification Issue
```
1. Open src/router.py
2. Add test case to reproduce issue
3. Run: pytest tests/test_router.py -v -s
4. Check classify() priority order matches expectations
5. May need to adjust CALCULATION_INDICATORS, RESEARCH_KEYWORDS, or regex patterns
```

### Add Support for New API Provider
```
1. Check src/llm/base.py for BaseLLM interface
2. Create new class in src/llm/ inheriting BaseLLM
3. Implement complete() and is_available() methods
4. Update LLMConfig in src/utils/config.py
5. Register in LLMManager._initialize_providers()
6. Test with: python -m src.main info
```

### Debug Search Results Issue
```
1. Check SerpAPI key in config: python -m src.main info
2. Test direct search: python -c "from src.utils import get_config; config = get_config(); print(config.search.serpapi_key)"
3. Check scraper: Verify trafilatura can extract content from target URL
4. Review research_agent logs for individual failure points
```

## Performance Considerations

- **Concurrent operations:** Research Agent uses `asyncio.gather()` for parallel search + scraping
- **Code execution:** Subprocess isolation adds ~100ms overhead but necessary for safety
- **LLM latency:** OpenAI-compatible APIs typically 1-5 seconds per request
- **Search latency:** SerpAPI typically 0.5-2 seconds per query
- **Scraping latency:** 0.5-3 seconds per page depending on size

## Multi-language Support

The system is designed for multilingual use:
- **Router:** Supports both English and Chinese keywords, patterns, operators
- **Question marks:** Handles ASCII `?` and Chinese `？`
- **Calculation indicators:** `多少`, `几个`, `how many`, `how much`, etc.
- **Time units:** `小时`, `小時`, `天`, `week`, `年`, `month`, etc.
- **LLM:** Inherits language capability from underlying model (DashScope supports Chinese natively)

**Note:** Adding new language support requires:
1. Update keyword lists (CODE_KEYWORDS, RESEARCH_KEYWORDS, CALCULATION_INDICATORS)
2. Update pattern regex if needed
3. May need specific model tuning for language
