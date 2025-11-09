# AI Search Engine - Comprehensive Technical Inventory

**Project**: Production-grade LLM-powered search engine  
**Codebase Size**: ~22,700 lines of Python code  
**Test Coverage**: 173 test functions across 11 test files  
**Architecture**: Modular agent + router pattern with async-first design  

---

## 1. PROJECT STRUCTURE OVERVIEW

### Root Directory Layout
```
ai_search/
├── src/                          # Main source code (~15,000 LOC)
│   ├── agents/                   # 4 agent types
│   ├── routing/                  # Dual-path classification system
│   ├── tools/                    # 20+ specialized tools
│   ├── llm/                      # Multi-provider LLM management
│   ├── utils/                    # Configuration, logging, helpers
│   ├── web/                      # FastAPI web application
│   └── workflow/                 # Multi-step task orchestration
├── tests/                        # Comprehensive test suite
├── examples/                     # Usage examples
├── docs/                         # Documentation
├── config/                       # Configuration files
└── data/                         # Runtime data (cache, vectors, history)
```

### High-Level Data Flow
```
User Input
    ↓
[Router - Classification]
    ├─ KeywordRouter (fast path, ~10ms)
    └─ LLMRouter (accurate path, with fallback)
    ↓
[Agent Selection]
    ├─ ResearchAgent
    ├─ CodeAgent
    ├─ ChatAgent
    ├─ RAGAgent
    └─ DomainTools
    ↓
[Tool Execution - Parallel/Sequential]
    ├─ SearchTool
    ├─ CodeExecutor
    ├─ VectorStore
    ├─ WeatherTool
    ├─ FinanceTool
    └─ OCR/Vision Tools
    ↓
[LLM Synthesis - Multi-provider with fallback]
    ├─ OpenAI (GPT)
    ├─ DashScope (Qwen)
    ├─ DeepSeek
    ├─ Ollama
    └─ OpenAI-compatible endpoints
    ↓
[Response - Streaming/Cached]
```

---

## 2. AGENT IMPLEMENTATIONS

All agents are **async-first** with interface from `src/agents/`:

### 2.1 ResearchAgent (`research_agent.py`)
**Purpose**: Web research with multi-query synthesis  
**Key Methods**:
- `research(query, show_progress)` - Orchestrates full research workflow
- `_generate_search_plan(query)` - Creates search queries via LLM
- `_synthesize_information()` - Combines scraped content into answer

**Workflow**:
1. Generate search plan (3-5 queries)
2. Execute parallel searches (SearchTool + trafilatura)
3. Scrape top 5 results with content extraction
4. LLM synthesis with citations

**Configuration** (from `config.yaml`):
- `max_queries`: 5 (default)
- `top_results_per_query`: 3
- `summary_max_tokens`: 500

---

### 2.2 CodeAgent (`code_agent.py`)
**Purpose**: Code generation + secure execution + explanation  
**Key Methods**:
- `solve(problem, show_progress)` - Full code execution pipeline
- `_generate_code(problem)` - LLM code generation
- `_explain_results()` - Post-execution analysis

**Workflow**:
1. Generate Python code via LLM (supports markdown code blocks)
2. Validate with SecurityValidator (AST-based)
3. Execute in SandboxExecutor (Docker or subprocess)
4. Analyze and explain results

**Security Layers**:
- **Layer 1**: AST validation (pattern detection, import whitelist)
- **Layer 2**: Docker sandbox (optional, with resource limits)
- **Layer 3**: Subprocess timeout (30s default, configurable)

---

### 2.3 RAGAgent (`rag_agent.py`)
**Purpose**: Document Q&A with semantic search  
**Key Methods**:
- `ingest_document(file_path)` - Process single document
- `ingest_directory(directory_path)` - Batch document processing
- `query(question, top_k)` - Semantic search + LLM synthesis
- `get_stats()` - Vector store statistics

**Workflow**:
1. Document processing (PDF/TXT/MD/DOCX) via DocumentProcessor
2. Advanced PDF handling (AdvancedPDFProcessor for OCR/complex layouts)
3. Chunking (semantic/fixed/recursive strategies)
4. Embedding via sentence-transformers (384-dim model)
5. Vector storage in ChromaDB with caching
6. Query: similarity search → similarity threshold filter → LLM synthesis

**Components**:
- **DocumentProcessor**: PDF/DOCX/TXT extraction (PyMuPDF, python-docx)
- **AdvancedPDFProcessor**: Intelligent page type detection (text/scanned/complex)
- **SmartChunker**: 3 strategies (fixed, semantic, recursive)
- **VectorStore**: Chroma with query/embedding caching

---

### 2.4 ChatAgent (`chat_agent.py`)
**Purpose**: General conversation with history  
**Key Methods**:
- `chat(message)` - Single turn with history
- `clear_history()` - Reset conversation
- `set_system_prompt()` - Configure system behavior

**Features**:
- Maintains last 20 messages for context
- LLM fallback chain (OpenAI → DashScope → others)
- Streaming support via Server-Sent Events

---

## 3. ROUTING SYSTEM (`src/routing/`)

### Unified Architecture with Dual-Path Strategy

#### 3.1 Task Types (`task_types.py`)
```python
class TaskType(Enum):
    # Core (4)
    RESEARCH = "research"
    CODE = "code"  
    CHAT = "chat"
    RAG = "rag"
    
    # Domain-specific (3)
    DOMAIN_WEATHER = "domain_weather"
    DOMAIN_FINANCE = "domain_finance"
    DOMAIN_ROUTING = "domain_routing"
    
    # Multimodal (2)
    MULTIMODAL_OCR = "multimodal_ocr"
    MULTIMODAL_VISION = "multimodal_vision"
    
    # Orchestration (1)
    WORKFLOW = "workflow"
```

#### 3.2 Router Implementations

**BaseRouter** (`base.py`):
- Abstract interface all routers inherit from
- Defines `RoutingDecision` dataclass with:
  - `primary_task_type`: TaskType
  - `task_confidence`: 0.0-1.0
  - `reasoning`: explanation
  - `tools_needed`: List[ToolRequirement]
  - `multi_intent`: boolean
  - `alternative_task_types`: fallback options
  - `metadata`: routing hints

---

**KeywordRouter** (`keyword_router.py`) - **Fast Path**
- **Latency**: ~10ms
- **Accuracy**: 60-70% for clear queries
- **Strategy**: Regex pattern matching with priority ordering

**Keyword Groups**:
```
RESEARCH_KEYWORDS    → "search", "find", "查询", "explain"
CODE_KEYWORDS        → "compute", "calculate", "solve", "plot"
RAG_KEYWORDS         → "document", "file", "pdf"
WEATHER_KEYWORDS     → "weather", "temperature", "forecast"
FINANCE_KEYWORDS     → "stock", "price", "market", "crypto"
ROUTING_KEYWORDS     → "route", "navigate", "direction"
```

**Confidence Calculation**:
- High (0.8-1.0): Multiple keyword matches
- Medium (0.5-0.8): Single strong keyword + math patterns
- Low (<0.5): Weak signals or ambiguous

---

**LLMRouter** (`llm_router.py`) - **Accurate Path**
- **Latency**: 1-3 seconds
- **Accuracy**: 85-95% for ambiguous queries
- **Strategy**: LLM semantic understanding

**Prompts**:
- Supports both English and Chinese
- Returns JSON with task type, confidence, reasoning
- Handles multi-intent queries

---

**HybridRouter** (`hybrid_router.py`) - **Default**
- **Strategy**: Keyword-first with LLM fallback
- **Threshold**: 0.7 confidence (configurable)
- **Caching**: 1000-entry LRU cache for speed

**Decision Flow**:
1. Try KeywordRouter (10ms)
2. If confidence ≥ threshold → return
3. Otherwise → LLMRouter (1-3s) for accuracy
4. Check cache first (O(1) lookups)

---

**RouterFactory** (`factory.py`)
```python
RouterFactory.create_router('hybrid', llm_manager, config)
RouterFactory.create_from_config(config, llm_manager)
```

---

## 4. TOOL IMPLEMENTATIONS (`src/tools/`)

### 4.1 Core Search & Scraping

**SearchTool** (`search.py`)
- **Provider**: SerpAPI (primary), Google Search (fallback)
- **Features**:
  - Batch search support
  - Automatic retry (3 attempts, exponential backoff)
  - Result parsing (title, URL, snippet)
  - Configurable result count

---

**ScraperTool** (`scraper.py`)
- **Backend**: trafilatura (web extraction) + aiohttp (async HTTP)
- **Features**:
  - Async concurrent scraping (max_workers=5)
  - HTML → main content extraction
  - User-agent rotation
  - Timeout handling (10s default)
  - Batch scraping API

---

### 4.2 Code Execution (`code_executor.py` + `sandbox_executor.py`)

**Three-Layer Security Architecture**:

**Layer 1: AST-based Validation** (`code_validator.py`)
- Analyzes code structure before execution
- Detects dangerous patterns: `eval`, `exec`, `__import__`, `globals`, `vars`
- Validates imports against SecurityLevel whitelist
- Cannot be bypassed with obfuscation

**SecurityLevel Options**:
```
STRICT     → Basic Python only (no imports)
MODERATE   → + math, datetime, json, statistics [DEFAULT]
PERMISSIVE → + numpy, pandas, scipy, matplotlib, sympy
```

---

**Layer 2: Docker Sandbox** (if available)
- Isolated container execution
- Resource limits:
  - Memory: 256MB (default, configurable)
  - CPU: 1 core (configurable)
  - Timeout: 30s (configurable)
- Network disabled (always)
- Read-only filesystem
- Unprivileged user execution

---

**Layer 3: Subprocess Fallback**
- Process isolation
- Timeout enforcement
- Output size limits (100KB default)
- Environment variable isolation

**API**:
```python
executor = CodeExecutor(
    timeout=30,
    security_level=SecurityLevel.MODERATE,
    enable_docker=True
)
result = await executor.execute(code)
# Returns: {success, output, error, execution_time, validation_errors}
```

---

### 4.3 RAG Components

**VectorStore** (`vector_store.py`)
- **Backend**: ChromaDB (persistent, local)
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- **Features**:
  - Query result caching (1000 entries, 3600s TTL)
  - Embedding caching
  - Metadata filtering
  - Similarity search with score threshold
  - Collection management

**API**:
```python
vector_store = VectorStore(
    persist_directory="./data/vector_store",
    collection_name="documents",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
vector_store.add_documents(texts, metadatas)
results = vector_store.similarity_search(query, k=10)
# Returns: [{text, score, metadata}, ...]
```

---

**DocumentProcessor** (`document_processor.py`)
- **Formats Supported**: PDF, TXT, MD, DOCX
- **PDF Extraction**: PyMuPDF (fast, accurate)
- **DOCX Parsing**: python-docx
- **Returns**: List[{content, metadata}] per page/section

---

**AdvancedPDFProcessor** (`advanced_pdf_processor.py`)
- **Intelligent Page Detection**:
  - Text pages → standard extraction
  - Scanned pages → PaddleOCR processing
  - Complex layouts → adaptive handling
- **Features**:
  - Page type distribution tracking
  - OCR for non-digital PDFs
  - Table extraction (experimental)

---

**SmartChunker** (`chunking.py`)
- **Strategies**:
  - `fixed`: Character-based with overlap (default: 512 chars, 77 char overlap)
  - `semantic`: Smart sentence/paragraph boundaries
  - `recursive`: Hierarchical splitting for nested structures
- **Metadata Attachment**: chunk_index, total_chunks, strategy

---

**Reranker System**:
- **Base Reranker** (`reranker_base.py`): BGE reranker interface
- **HybridReranker** (`reranker_hybrid.py`): Hybrid scoring
- **Configuration**:
  - Optional (disabled by default)
  - Model: BAAI/bge-reranker-large
  - Top-k: 3 (after reranking)

---

### 4.4 Domain Tools

**WeatherTool** (`weather_tool.py`)
- **Provider**: OpenWeatherMap API (pyowm library)
- **Methods**:
  - `get_current_weather(location)` - Current conditions
  - `get_forecast(location, days)` - 5-day forecast
- **Data**: Temperature, humidity, wind, clouds, rain
- **Config**: Units (metric/imperial), language (zh_cn/en)

---

**FinanceTool** (`finance_tool.py`)
- **Primary**: Alpha Vantage API (detailed data)
- **Fallback**: yfinance (free, fast)
- **Methods**:
  - `get_stock_price(symbol)` - Current price + OHLCV
  - `get_daily_data(symbol, days)` - Historical prices
  - `get_intraday(symbol)` - 5-minute candles
- **Features**: Auto-fallback on API errors, caching (5-min TTL)

---

**RoutingTool** (`routing_tool.py`)
- **Provider**: OpenRouteService API
- **Methods**:
  - `get_directions(start, end, mode)` - Route planning
  - `get_distance(start, end)` - Distance calculation
- **Modes**: Driving, cycling, foot, wheelchair
- **Output**: Distance, duration, geometry

---

### 4.5 Multimodal Tools

**OCRTool** (`ocr_tool.py`)
- **Engine**: PaddleOCR (supports Chinese + English)
- **Methods**:
  - `extract_text(image_path)` - Full text extraction
  - `extract_structured(image_path)` - Bounding boxes + confidence
- **Features**:
  - GPU/CPU acceleration
  - Angle classification
  - Batch processing support

---

**VisionTool** (`vision_tool.py`)
- **Provider**: Google Gemini Vision API
- **Model**: gemini-2.0-flash-exp (configurable)
- **Methods**:
  - `analyze_image(image_path, prompt)` - Custom analysis
  - `describe_image(image_path)` - Auto-description
- **Features**:
  - Image resize (preserves aspect ratio)
  - Configurable max dimensions (4096px default)

---

**CredibilityScorer** (`credibility_scorer.py`)
- **Purpose**: Score search result source trustworthiness
- **Scoring**:
  - Domain reputation (0.0-1.0)
  - Content quality indicators
  - Red flags detection
  - Freshness penalty
- **Score Ranges**:
  - 0.90-1.0: Academic/government/tier-1 news
  - 0.70-0.89: Professional/tier-2 news
  - 0.50-0.69: Forums/blogs
  - <0.50: Unreliable sources

---

## 5. LLM PROVIDER SYSTEM (`src/llm/`)

### 5.1 Architecture

**BaseLLM** (`base.py`) - Abstract interface
```python
class BaseLLM(ABC):
    async def complete(messages, temperature, max_tokens) -> str
    async def is_available() -> bool
```

---

**Supported Providers**:

| Provider | Model | Type | Status |
|----------|-------|------|--------|
| OpenAI | gpt-3.5-turbo (configurable) | API | ✅ Enabled |
| DashScope (Aliyun) | qwen-max | API | ✅ Enabled |
| DeepSeek | deepseek-chat | API | Optional |
| Ollama | llama2 (local) | Local | Optional |
| OpenAI-compatible | Custom endpoint | Local/API | Optional |

---

**LLMManager** (`manager.py`)
- **Singleton Pattern**: Single instance per application
- **Fallback Chain**:
  1. Preferred provider (if specified)
  2. Primary provider (first initialized)
  3. Remaining providers in order

**Initialization Logic**:
```python
for provider_config in CONFIG:
    if provider_config.enabled AND provider_config.api_key:
        initialize(provider)
```

**API**:
```python
manager = LLMManager(config)
response = await manager.complete(
    messages=[{"role": "user", "content": "..."}],
    temperature=0.7,
    max_tokens=2000,
    preferred_provider="openai"  # optional fallback hint
)
```

**Provider-Specific Features**:
- OpenAI: Temperature, top_p, frequency_penalty, presence_penalty
- DashScope: Qwen-specific optimizations for Chinese
- Custom endpoints: Parameter passthrough

---

## 6. WEB APPLICATION (`src/web/`)

### 6.1 FastAPI Application (`app.py`)

**Structure**:
```
FastAPI App (uvicorn)
├── Middleware
│   ├── CORS (configurable origins)
│   ├── Rate Limiting (slowapi)
│   └── Error Handling
├── Lifespan Events
│   ├── Startup: Database init, vector store warm-up
│   └── Shutdown: Connection pool cleanup
├── Static Files Mount
│   ├── /static → HTML/CSS/JS
│   └── /uploads → User documents/images
└── Routers (9 total)
```

**Configuration**:
- Host/Port: Configurable via env vars
- CORS Origins: Environment-based whitelist
- Template Engine: Jinja2
- Database: Async SQLite (aiosqlite)

---

### 6.2 Routes (`src/web/routers/`)

**Main Router** (`main.py`)
- `/` - Home page

---

**Query Router** (`query.py`) - **Central Intelligence Dispatcher**
- `/query` (POST) - Unified query endpoint
- **Workflow**:
  1. Route query via HybridRouter
  2. Select appropriate agent
  3. Execute with dependency injection
  4. Save to conversation history
  5. Return formatted response

---

**RAG Router** (`rag.py`) - **Document Q&A**
- `GET /rag` - RAG page
- `POST /rag/upload` - Document upload + ingestion
- `POST /rag/query` - Query documents
- `GET /rag/documents` - List ingested documents
- `DELETE /rag/document/{id}` - Remove document
- `GET /rag/stats` - Vector store statistics

---

**Search Router** (`search.py`)
- `POST /search` - Direct web search

---

**Code Router** (`code.py`)
- `POST /code/execute` - Execute Python code

---

**Chat Router** (`chat.py`)
- `POST /chat` - Streaming chat via SSE
- `GET /chat` - Chat page

---

**Multimodal Router** (`multimodal.py`)
- `GET /multimodal` - Multimodal page
- `POST /multimodal/ocr` - Extract text from image
- `POST /multimodal/vision` - Analyze image with vision

---

**Tools Router** (`tools.py`) - **Domain-Specific Tools**
- `POST /tools/weather` - Weather query
- `POST /tools/finance` - Stock/crypto data
- `POST /tools/routing` - Route directions

---

**Workflow Router** (`workflow.py`) - **Multi-Step Tasks**
- `POST /workflow` - Execute workflow
- `GET /workflow/status/{id}` - Check workflow status

---

**History Router** (`history.py`)
- `GET /history` - Conversation history
- `DELETE /history/{id}` - Delete conversation

---

### 6.3 Database Layer (`database.py`)

**Connection Pool**:
- **Type**: Custom async connection pool (DatabasePool class)
- **Size**: 5 connections (configurable)
- **Mode**: SQLite with WAL (Write-Ahead Logging)

**Schema**:

```sql
conversation_history(
    id INTEGER PRIMARY KEY,
    mode TEXT,              -- research, code, chat, rag, weather, etc.
    query TEXT,
    response TEXT,
    metadata JSON,          -- Extra context (routing info, etc.)
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

rag_documents(
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE,
    file_hash TEXT,         -- SHA-256 deduplication
    original_filename TEXT,
    filepath TEXT,
    file_type TEXT,         -- pdf, txt, md, docx
    file_size INTEGER,
    upload_timestamp TIMESTAMP,
    processing_status TEXT, -- processing, completed, failed
    vector_ids TEXT,        -- JSON array of vector store IDs
    chunk_count INTEGER,
    metadata JSON,
    created_at TIMESTAMP
);
```

**Indexes**:
- conversation_history: (created_at, mode)
- rag_documents: (upload_timestamp, processing_status)

**API**:
```python
await database.save_conversation(mode, query, response, metadata)
await database.get_conversation_history(limit=50, offset=0)
await database.save_rag_document(file_info)
await database.get_rag_documents()
```

---

### 6.4 File Upload Management (`upload_manager.py`)

**UploadManager**:
- **Deduplication**: SHA-256 hash-based
- **Organization**: Type-based directories
  - `uploads/rag_documents/` - Documents for RAG
  - `uploads/images/` - Images for vision
  - `uploads/temp/` - Temporary files
- **Validation**: MIME type + extension checking
- **Security**: Filename sanitization

---

### 6.5 Middleware (`middleware/`)

**Rate Limiter** (`rate_limiter.py`)
- **Backend**: slowapi (based on Flask-Limiter)
- **Limits**:
  - Query: 30 requests/minute
  - Upload: 10 requests/minute
  - Search: 50 requests/minute
  - Chat: 100 requests/minute
- **Storage**: In-memory (per-process)

---

## 7. WORKFLOW ENGINE (`src/workflow/`)

### 7.1 Architecture

**Purpose**: Multi-step task orchestration with DAG execution

**Components**:

---

**WorkflowEngine** (`workflow_engine.py`)

**Task Model**:
```python
@dataclass
class Task:
    id: str                          # Unique identifier
    name: str                        # Human-readable name
    func: Callable                   # Async function to execute
    args: tuple                      # Positional arguments
    kwargs: dict                     # Keyword arguments
    dependencies: Set[str]           # Dependent task IDs
    retry_count: int = 3             # Retry on failure
    timeout: Optional[float] = None  # Execution timeout
    on_success: Optional[Callable]   # Success callback
    on_failure: Optional[Callable]   # Failure callback
```

**ExecutionModes**:
- `SEQUENTIAL` - Execute tasks one by one
- `PARALLEL` - Execute all tasks simultaneously
- `DAG` - Execute based on dependency graph (topological sort)

**Workflow Result**:
```python
@dataclass
class WorkflowResult:
    success: bool
    results: Dict[str, Any]          # task_id → result
    errors: Dict[str, Exception]     # task_id → error
    execution_time: float
    task_count: int
    completed_count: int
    failed_count: int
```

**API**:
```python
workflow = WorkflowEngine()
workflow.add_task(
    id="search_weather",
    name="Get Beijing weather",
    func=weather_tool.get_current_weather,
    kwargs={"location": "Beijing"},
    timeout=10
)
workflow.add_task(
    id="format_response",
    name="Format results",
    func=format_func,
    dependencies={"search_weather"},
    timeout=5
)
result = await workflow.execute(mode=ExecutionMode.DAG)
print(result.results["format_response"])
```

---

**TaskDecomposer** (`task_decomposer.py`)

**Purpose**: Break complex queries into subtasks via LLM

**Available Tools**:
- search: Web search
- code: Python execution
- rag: Document Q&A
- weather: Weather lookup
- finance: Stock/crypto data
- routing: Route planning
- chat: General conversation

**Subtask Model**:
```python
@dataclass
class SubTask:
    id: str                    # e.g., "subtask_1"
    description: str           # "Get weather in Beijing"
    tool: str                  # "weather"
    query: str                 # "Beijing"
    dependencies: List[str]    # ["subtask_1"]
    output_variable: str       # "beijing_weather"
```

**API**:
```python
decomposer = TaskDecomposer(llm_manager)
plan = await decomposer.decompose(
    "Compare weather in Beijing and Tokyo, then find flights"
)
# Returns TaskPlan with ordered subtasks
for subtask in plan.subtasks:
    result = await execute_tool(subtask.tool, subtask.query)
```

---

**ResultAggregator** (`result_aggregator.py`)

**Purpose**: Combine subtask results for final synthesis

**Features**:
- Handles missing/failed subtasks
- Context preservation across steps
- LLM-based result synthesis
- Handles variable substitution

---

## 8. CONFIGURATION SYSTEM (`src/utils/config.py`)

**Pydantic-based Type-Safe Configuration**

**Structure**:
```python
class Config:
    llm: LLMConfig              # Provider configs
    search: SearchConfig        # Web search settings
    code_execution: CodeExecutionConfig
    research: ResearchConfig
    rag: RAGConfig
    domain_tools: DomainToolsConfig
    routing: RoutingConfig
    cli: CLIConfig
    cache: CacheConfig
```

---

**Loading Priority** (highest to lowest):
1. Environment variables (e.g., `${OPENAI_API_KEY}`)
2. `config.yaml` direct values
3. Pydantic model defaults

**YAML Syntax**:
```yaml
llm:
  openai_enabled: true
  openai_api_key: ${OPENAI_API_KEY}  # Env var substitution
  openai_model: gpt-3.5-turbo
  openai_temperature: 0.7

code_execution:
  timeout: 30
  security_level: moderate
  enable_docker: true
```

**Supported Environment Variables**:
- `OPENAI_API_KEY` - OpenAI GPT models
- `DASHSCOPE_API_KEY` - Aliyun Qwen (primary Chinese model)
- `DEEPSEEK_API_KEY` - DeepSeek API
- `SERPAPI_API_KEY` - Web search
- `GOOGLE_API_KEY` - Gemini Vision
- `OPENWEATHERMAP_API_KEY` - Weather data
- `ALPHA_VANTAGE_API_KEY` - Stock data (primary)
- `OPENROUTESERVICE_API_KEY` - Route planning

---

## 9. TESTING INFRASTRUCTURE

### Test Organization (173 functions across 11 files)

**Test Files**:

| File | Functions | Categories |
|------|-----------|------------|
| `test_routing.py` | 25+ | Router logic, task types, classification |
| `test_agents.py` | 20+ | RAG, Chat, Research agent behavior |
| `test_code_security.py` | 35+ | AST validation, sandboxing, security |
| `test_tools.py` | 25+ | Search, scraper, chunking, processors |
| `test_workflow.py` | 20+ | DAG execution, task decomposition |
| `test_web_api.py` | 15+ | FastAPI endpoints, responses |
| `test_complete_system.py` | 10+ | End-to-end workflows |
| `test_performance.py` | 8+ | Load testing, benchmarks |
| `test_load.py` | 5+ | Concurrent load tests |
| Other files | 10+ | Legacy/archive tests |

---

**Test Markers** (pytest):
- `@pytest.mark.unit` - Single component tests
- `@pytest.mark.integration` - Multi-component tests
- `@pytest.mark.e2e` - Full workflow tests
- `@pytest.mark.security` - Security validation
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.requires_api` - Needs API keys

---

**Coverage Report**:
- Generated HTML: `htmlcov/`
- JSON: `coverage.json`
- XML: `coverage.xml`
- **Goal**: Maintain >70% coverage

---

**Configuration** (`pytest.ini`):
```ini
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
timeout = 300
addopts = -v --cov=src --cov-report=html
```

---

## 10. KEY IMPLEMENTATION DETAILS

### 10.1 Async Architecture
- **Entire codebase is async-first**
- All I/O operations use `async`/`await`
- Event loop managed by FastAPI/asyncio
- No blocking calls in request handlers

**Pattern**:
```python
async def agent.execute():
    result = await tool.query()
    response = await llm_manager.complete()
    return response
```

---

### 10.2 Error Handling & Fallback
- **LLM Fallback**: Provider chain (primary → secondary → others)
- **Tool Fallback**: Finance tool (Alpha Vantage → yfinance)
- **Router Fallback**: Keyword (fast) → LLM (accurate)
- **Code Execution**: Docker → Subprocess → Error
- **Retry Logic**: tenacity library with exponential backoff

---

### 10.3 Performance Optimizations

**Caching**:
- Query cache (VectorStore): 1000 entries, 3600s TTL
- Embedding cache: Avoid re-embedding same text
- Routing cache (HybridRouter): 1000-entry LRU
- Search cache (optional): requests-cache integration

**Concurrency**:
- Batch search via asyncio.gather()
- Parallel scraping (max_workers=5)
- Workflow parallel execution mode
- Connection pooling (database)

**Performance Targets**:
- Keyword routing: <50ms
- LLM routing: 1-3 seconds
- Vector search: <100ms (with cache hits)
- Web scraping: 2-5 seconds (5 URLs)

---

### 10.4 Security Model

**Code Execution** (3 layers):
1. AST validation (pattern detection)
2. Docker sandbox (if available)
3. Subprocess timeout (fallback)

**API Keys**:
- Stored in environment variables
- Never logged or exposed
- Secret sanitizer removes from logs

**Web Security**:
- CORS whitelist (configurable)
- Rate limiting (slowapi)
- File upload validation
- SQL injection protection (SQLite prepared statements)

---

### 10.5 Logging System

**Logger Setup** (`src/utils/logger.py`):
```python
logger = get_logger(__name__)
logger.info("message")
logger.error("error", exc_info=True)
```

**Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Features**:
- Structured logging (JSON optional)
- Request ID tracking (for distributed tracing)
- Secret sanitization (removes API keys)

---

## 11. DEPENDENCY INJECTION & INITIALIZATION

**Web Application Dependencies** (`src/web/dependencies/`):
```python
def get_router() -> BaseRouter
def get_research_agent() -> ResearchAgent
def get_code_agent() -> CodeAgent
def get_rag_agent() -> RAGAgent
def get_weather_tool() -> WeatherTool
def get_finance_tool() -> FinanceTool
```

**Initialization Pattern**:
```python
# In main.py or app startup
config = get_config()
llm_manager = LLMManager(config)
router = RouterFactory.create_from_config(config, llm_manager)
research_agent = ResearchAgent(llm_manager, search_tool, scraper_tool)
```

---

## 12. ENTRY POINTS

### CLI (`src/main.py`)
**Commands** (Typer-based):
- `python -m src.main search "query"` - Web research
- `python -m src.main solve "problem"` - Code execution
- `python -m src.main ask "question" --auto` - Auto-routing
- `python -m src.main chat` - Interactive conversation
- `python -m src.main info` - System information

---

### Web UI
**Start**: `python -m src.web.app` or `uvicorn src.web.app:app --reload`  
**Default URL**: `http://localhost:8000`

---

## 13. PRODUCTION-READY FEATURES

✅ **Implemented**:
- Multi-provider LLM support with fallback
- Comprehensive error handling
- Async concurrency throughout
- Database connection pooling
- Rate limiting
- Logging and monitoring hooks
- Configuration management
- Security validation (code execution)
- Test coverage (173 tests)
- Documentation (CLAUDE.md, docstrings)
- Performance optimization (caching, batching)

---

## 14. LIMITATIONS & KNOWN ISSUES

| Issue | Workaround |
|-------|-----------|
| Rare router misclassifications | Use HybridRouter, reduce confidence threshold |
| RAG retrieval quality varies | Enable reranking, tune similarity_threshold |
| Code execution timeouts possible | Increase timeout for complex code |
| Web UI async errors | Ensure all database calls are awaited |
| API rate limits | Implement caching (trafilatura has built-in) |

---

## 15. QUICK REFERENCE: ARCHITECTURE PATTERNS

### 1. Agent Pattern
```python
class MyAgent:
    def __init__(self, llm_manager, config):
        self.llm = llm_manager
        self.config = config
    
    async def execute(self, query):
        # Process via agents/tools
        result = await self.tool.query()
        response = await self.llm.complete()
        return response
```

### 2. Router Pattern
```python
class MyRouter(BaseRouter):
    async def route(self, query):
        decision = RoutingDecision(
            query=query,
            primary_task_type=TaskType.RESEARCH,
            task_confidence=0.8,
            reasoning="...",
            tools_needed=[...]
        )
        return decision
```

### 3. Tool Pattern
```python
class MyTool:
    async def query(self, params):
        # Call external API
        result = await api_call()
        return formatted_result
```

---

## 16. KEY FILES SUMMARY

| Component | File | LOC | Purpose |
|-----------|------|-----|---------|
| Research Agent | `agents/research_agent.py` | 237 | Web research orchestration |
| Code Agent | `agents/code_agent.py` | 212 | Code execution + explanation |
| RAG Agent | `agents/rag_agent.py` | 362 | Document Q&A |
| Chat Agent | `agents/chat_agent.py` | 64 | Conversation |
| Hybrid Router | `routing/hybrid_router.py` | 120 | Main routing logic |
| Keyword Router | `routing/keyword_router.py` | 200+ | Fast classification |
| LLM Router | `routing/llm_router.py` | 150+ | Accurate classification |
| Code Executor | `tools/code_executor.py` | 250+ | Secure code execution |
| Vector Store | `tools/vector_store.py` | 200+ | ChromaDB wrapper |
| Search Tool | `tools/search.py` | 100+ | SerpAPI integration |
| Scraper Tool | `tools/scraper.py` | 150+ | Web content extraction |
| Smart Chunker | `tools/chunking.py` | 200+ | Text chunking strategies |
| LLM Manager | `llm/manager.py` | 150+ | Multi-provider LLM |
| Web App | `web/app.py` | 115 | FastAPI application |
| Database | `web/database.py` | 200+ | SQLite wrapper |
| Query Router | `web/routers/query.py` | 462 | Central dispatcher |
| RAG Router | `web/routers/rag.py` | 352 | Document Q&A endpoint |
| Workflow Engine | `workflow/workflow_engine.py` | 594 | DAG execution |
| Task Decomposer | `workflow/task_decomposer.py` | 401 | Query decomposition |

---

## 17. TOTAL PROJECT STATISTICS

| Metric | Count |
|--------|-------|
| Total Python Lines | 22,700+ |
| Source Code Lines (src/) | 15,000+ |
| Test Lines | 5,000+ |
| Major Classes | 20+ |
| Agent Types | 4 |
| Router Types | 3 |
| Tool Implementations | 20+ |
| Web Endpoints | 40+ |
| Test Functions | 173 |
| Supported LLM Providers | 4+ |
| Domain Tools | 3 |
| Multimodal Capabilities | 2 |
| Configuration Parameters | 50+ |
| Dependencies | 50+ |

---

## 18. RECOMMENDED USAGE EXAMPLES

**Research Query**:
```python
router = HybridRouter(llm_manager)
decision = await router.route("Latest AI breakthroughs")
agent = ResearchAgent(llm_manager, search_tool, scraper_tool)
result = await agent.research(decision.query)
```

**Code Execution**:
```python
agent = CodeAgent(llm_manager, code_executor)
result = await agent.solve("Find prime numbers up to 100")
```

**Document Q&A**:
```python
rag_agent = RAGAgent(llm_manager)
await rag_agent.ingest_document("document.pdf")
answer = await rag_agent.query("What is the main topic?")
```

**Workflow**:
```python
workflow = WorkflowEngine()
workflow.add_task("search", search_func, timeout=5)
workflow.add_task("analyze", analyze_func, dependencies={"search"})
result = await workflow.execute(ExecutionMode.DAG)
```

