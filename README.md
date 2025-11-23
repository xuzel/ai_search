# AI Search Engine

<div align="center">

**An intelligent multi-agent LLM system combining research, code execution, chat, RAG, and domain-specific tools**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## Overview

AI Search Engine is a production-ready LLM-powered system that intelligently routes queries to specialized agents. It supports multiple LLM providers (OpenAI, Aliyun DashScope, DeepSeek, Ollama), features secure code execution in Docker sandboxes, and provides advanced capabilities including RAG document Q&A, multimodal analysis (OCR, vision), and domain-specific tools.

### Key Highlights

- **Intelligent Query Routing**: Automatically classifies queries and routes to appropriate agents (research, code, chat, RAG, multimodal)
- **Multi-LLM Support**: Flexible provider system with automatic fallback (OpenAI, Aliyun Qwen, DeepSeek, Ollama, any OpenAI-compatible API)
- **Secure Code Execution**: 3-layer security (AST validation, Docker sandbox with resource limits, timeout enforcement)
- **RAG System**: ChromaDB-powered document Q&A with semantic chunking and hybrid reranking
- **Multimodal**: OCR (PaddleOCR) and vision analysis (Aliyun Qwen3-VL-Plus)
- **Domain Tools**: Weather, finance (stocks), routing/directions
- **Production-Ready**: FastAPI web UI, rate limiting, CORS, async SQLite history, comprehensive logging

---

## Features

### Core Capabilities

| Feature | Description | Status |
|---------|-------------|--------|
| **Research Agent** | Web search + scraping + LLM summarization | ✅ |
| **Code Agent** | Generate & execute Python code securely | ✅ |
| **Chat Agent** | General conversation with context | ✅ |
| **RAG Agent** | Document Q&A with vector search | ✅ |
| **Master Agent** | Intelligent orchestration & multi-modal PDF analysis | ✅ |

### Advanced Features

- **Routing System**: Keyword-based, LLM-based, and hybrid routing with confidence scoring
- **Workflow Engine**: Multi-step task orchestration with DAG execution
- **Security**: Docker sandbox, AST validation, resource limits (memory, CPU, network isolation)
- **Caching**: Redis/SQLite-based caching with TTL
- **Rate Limiting**: Token bucket algorithm with memory/Redis backend
- **Multimodal**:
  - OCR: Text extraction from images (Chinese/English)
  - Vision: Image analysis, document understanding, chart interpretation
- **Domain Tools**:
  - Weather: OpenWeatherMap API integration
  - Finance: Stock data (Alpha Vantage + yfinance fallback)
  - Routing: Directions via OpenRouteService

### Web Interface

- FastAPI-based REST API with async support
- Real-time streaming responses (SSE)
- File upload support (PDF, DOCX, images)
- Query history with SQLite
- Rate limiting and CORS configuration
- Responsive UI with syntax highlighting

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│              (Web UI / CLI / API Endpoints)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Routing System                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Keyword   │  │     LLM     │  │   Hybrid    │         │
│  │   Router    │  │   Router    │  │   Router    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Research │  │   Code   │  │   Chat   │  │   RAG    │   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Master Agent (Orchestrator)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                       Tool Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Search  │  │ Scraper  │  │  Code    │  │  Vector  │   │
│  │   Tool   │  │   Tool   │  │ Executor │  │  Store   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Weather  │  │ Finance  │  │ Routing  │  │   OCR    │   │
│  │   Tool   │  │   Tool   │  │   Tool   │  │   Tool   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Vision Tool (Qwen3-VL-Plus)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   LLM    │  │  Docker  │  │ ChromaDB │  │  SQLite  │   │
│  │ Manager  │  │ Sandbox  │  │  Vector  │  │ History  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Overview

#### **Routing System** (`src/routing/`)
- **KeywordRouter**: Fast pattern matching (no LLM calls)
- **LLMRouter**: LLM-based classification (high accuracy)
- **HybridRouter**: Keyword first, LLM fallback (recommended)

#### **Agents** (`src/agents/`)
- **ResearchAgent**: Web search → scraping → LLM summarization
- **CodeAgent**: Generate & execute Python code with security validation
- **ChatAgent**: Context-aware conversation
- **RAGAgent**: Document ingestion & semantic search
- **MasterAgent**: Intelligent orchestration & multi-modal PDF analysis

#### **Tools** (`src/tools/`)
- **SearchTool**: SerpAPI integration
- **ScraperTool**: Web content extraction (trafilatura + BeautifulSoup)
- **CodeExecutor**: Secure code execution (Docker + AST validation)
- **VectorStore**: ChromaDB with sentence-transformers embeddings
- **VisionTool**: Image analysis via Aliyun Qwen3-VL-Plus
- **OCRTool**: Text extraction from images (PaddleOCR)
- **WeatherTool**, **FinanceTool**, **RoutingTool**: Domain-specific APIs

#### **LLM Manager** (`src/llm/`)
- Unified interface for multiple providers
- Automatic fallback on errors
- Streaming support
- Token usage tracking

---

## Quick Start

### Prerequisites

- Python 3.8+ (tested on 3.12)
- Docker (for secure code execution)
- API keys for desired services

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai_search.git
cd ai_search

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# At minimum, you need:
#   - DASHSCOPE_API_KEY (Aliyun DashScope for LLM + Vision)
#   - SERPAPI_API_KEY (for web search)
```

### Configuration

Edit `config/config.yaml` to enable/disable features and configure providers:

```yaml
llm:
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max

search:
  provider: serpapi
  serpapi_key: ${SERPAPI_API_KEY}

code_execution:
  security_level: moderate  # strict, moderate, permissive
  enable_docker: true
  memory_limit: "256m"
```

### Running the Application

#### Web Server (Recommended)

```bash
# Development mode (hot reload)
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m src.web.app
```

Access the web UI at: `http://localhost:8000`

#### CLI Mode

```bash
# Research query
python -m src.main search "What are the latest developments in quantum computing?"

# Code execution
python -m src.main solve "Calculate the 100th Fibonacci number"

# Auto-routed query (intelligent routing)
python -m src.main ask "What's the weather in Beijing?"

# Interactive chat
python -m src.main chat

# System info
python -m src.main info
```

---

## Usage Examples

### 1. Research Query (Web Search + Summarization)

**CLI:**
```bash
python -m src.main search "Explain transformers in deep learning"
```

**API:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain transformers in deep learning"}'
```

### 2. Code Execution

**CLI:**
```bash
python -m src.main solve "Write a function to check if a number is prime, then test it with 17"
```

**API:**
```bash
curl -X POST http://localhost:8000/code \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate factorial of 20"}'
```

### 3. RAG Document Q&A

**Upload document:**
```bash
curl -X POST http://localhost:8000/rag/upload \
  -F "file=@paper.pdf"
```

**Ask questions:**
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main contribution of this paper?"}'
```

### 4. Multimodal Analysis

**OCR (text extraction):**
```bash
curl -X POST http://localhost:8000/multimodal/ocr \
  -F "file=@screenshot.png"
```

**Vision (image understanding):**
```bash
curl -X POST http://localhost:8000/multimodal/vision \
  -F "file=@chart.png" \
  -F "prompt=Describe this chart in detail"
```

### 5. Domain Tools

**Weather:**
```bash
curl -X POST http://localhost:8000/tools/weather \
  -H "Content-Type: application/json" \
  -d '{"city": "Beijing"}'
```

**Stock data:**
```bash
curl -X POST http://localhost:8000/tools/finance/stock \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

---

## API Documentation

Once the server is running, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Unified query endpoint (intelligent routing) |
| `/search` | POST | Research query (web search) |
| `/code` | POST | Code generation & execution |
| `/chat` | POST | Chat conversation |
| `/rag/upload` | POST | Upload document |
| `/rag/query` | POST | Query documents |
| `/multimodal/ocr` | POST | Extract text from image |
| `/multimodal/vision` | POST | Analyze image |
| `/tools/weather` | POST | Get weather data |
| `/tools/finance/stock` | POST | Get stock data |
| `/history` | GET | Query history |

---

## Configuration

### LLM Providers

The system supports multiple LLM providers configured in `config/config.yaml`:

```yaml
llm:
  # Aliyun DashScope (Qwen models) - Default
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1

  # OpenAI
  openai:
    enabled: false
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo

  # DeepSeek
  openai_compatible:
    deepseek:
      enabled: false
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-chat
      base_url: https://api.deepseek.com

  # Ollama (local)
  ollama:
    enabled: false
    base_url: http://localhost:11434
    model: llama2
```

### Code Execution Security

```yaml
code_execution:
  # Security level (strict/moderate/permissive)
  security_level: moderate

  # Docker sandbox
  enable_docker: true
  memory_limit: "256m"
  cpu_limit: 1.0
  enable_network: false

  # AST validation
  enable_validation: true

  # Timeouts
  timeout: 30
  max_output_lines: 1000
```

**Security Levels:**
- **strict**: No imports, math operations only
- **moderate**: + safe libraries (math, datetime, json, itertools) **[RECOMMENDED]**
- **permissive**: + data science libraries (numpy, pandas, scipy, matplotlib)

### RAG Configuration

```yaml
rag:
  enabled: true
  embedding_model: "BAAI/bge-large-zh-v1.5"  # 1024-dim Chinese/English

  chunking:
    strategy: "semantic"  # fixed, semantic, recursive
    chunk_size: 768
    chunk_overlap: 115

  retrieval:
    top_k: 20
    similarity_threshold: 0.5

  reranking:
    enabled: false
    model: "BAAI/bge-reranker-large"
```

---

## Development

### Project Structure

```
ai_search/
├── src/
│   ├── agents/              # Agent implementations
│   ├── routing/             # Query routing system
│   ├── tools/               # Tool implementations
│   ├── llm/                 # LLM provider integrations
│   ├── workflow/            # Workflow engine
│   ├── web/                 # FastAPI web application
│   │   ├── routers/         # API endpoints
│   │   ├── dependencies/    # Dependency injection
│   │   └── templates/       # HTML templates
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── config/                  # Configuration files
├── data/                    # Vector store & uploads
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
└── README.md               # This file
```

### Running Tests

```bash
# All tests with coverage
pytest

# Specific test file
pytest tests/test_routing.py

# By marker
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m "not requires_api"  # Skip tests requiring API keys

# With coverage report
pytest --cov=src --cov-report=html
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

### Adding a New Agent

1. Create agent class in `src/agents/`:
```python
class MyAgent:
    def __init__(self, llm_manager, config):
        self.llm = llm_manager
        self.config = config

    async def process(self, query: str) -> Dict[str, Any]:
        # Implementation
        pass
```

2. Add to `src/agents/__init__.py`

3. Register in routing system (if needed)

### Adding a New Tool

1. Create tool in `src/tools/`:
```python
class MyTool:
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        # Implementation
        pass
```

2. Add configuration to `config/config.yaml`

3. Create dependency in `src/web/dependencies/tools.py`

4. Add API endpoint in `src/web/routers/`

---

## Troubleshooting

### Common Issues

**"No LLM providers available"**
- Check `.env` has valid API keys
- Ensure `config.yaml` has `enabled: true` for at least one provider

**Docker permission errors**
- Ensure Docker daemon is running
- Check user has Docker permissions: `docker ps`

**Import errors**
- Install dependencies: `pip install -r requirements.txt`

**Test failures**
- Check API keys are set for `@pytest.mark.requires_api` tests
- Run without API tests: `pytest -m "not requires_api"`

**Rate limit errors**
- Check `RATE_LIMIT_STORAGE` in `.env`
- Disable: `RATE_LIMIT_ENABLED=false`

### Logging

Configure logging in `.env`:

```bash
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=standard         # standard, detailed, json
LOG_FILE=logs/app.log       # Optional: log to file
```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Commit** changes: `git commit -m "Add my feature"`
4. **Push** to branch: `git push origin feature/my-feature`
5. **Submit** a pull request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to functions
- Write unit tests for new features
- Update documentation
- Run tests and linting before submitting

---

## Security

### Code Execution

The system implements 3-layer security for code execution:

1. **AST Validation**: Static analysis blocks dangerous patterns (eval, exec, file I/O, network)
2. **Docker Sandbox**: Isolated containers with resource limits
3. **Timeout Enforcement**: Prevents infinite loops

**IMPORTANT**: Always run with Docker enabled in production (`enable_docker: true`)

### API Keys

- Never commit `.env` file to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use rate limiting in production

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **FastAPI** for the excellent web framework
- **OpenAI** for the standardized API format
- **Aliyun DashScope** for Qwen LLM and vision models
- **ChromaDB** for the vector database
- **PaddleOCR** for OCR capabilities
- **Sentence Transformers** for embeddings

---

## Contact

For questions, issues, or suggestions:

- **Issues**: [GitHub Issues](https://github.com/yourusername/ai_search/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai_search/discussions)

---

<div align="center">

**Made with ❤️ by [Your Name]**

[⬆ Back to Top](#ai-search-engine)

</div>
