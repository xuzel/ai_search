Architecture
============

This document describes the system architecture of the AI Search Engine.

System Overview
---------------

The AI Search Engine is a modular, LLM-powered search and question-answering system with intelligent routing.

.. code-block:: text

   ┌─────────────────────────────────────────────────────────┐
   │                      User Input                          │
   └──────────────────────┬──────────────────────────────────┘
                          │
                          ▼
   ┌─────────────────────────────────────────────────────────┐
   │                  Router (Hybrid)                         │
   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
   │  │  Keyword    │  │     LLM     │  │   Hybrid    │     │
   │  │   Router    │  │   Router    │  │   Router    │     │
   │  └─────────────┘  └─────────────┘  └─────────────┘     │
   └──────────────────────┬──────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │   Research   │ │     Code     │ │     RAG      │
   │    Agent     │ │    Agent     │ │    Agent     │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          ▼                ▼                ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │   Search     │ │     Code     │ │   Vector     │
   │   + Scrape   │ │  Executor    │ │    Store     │
   └──────────────┘ └──────────────┘ └──────────────┘

Core Modules
------------

Routing Module
~~~~~~~~~~~~~~

**Purpose**: Classify queries and route to appropriate agents

**Components**:

* ``KeywordRouter``: Fast pattern matching (8ms avg)
* ``LLMRouter``: Accurate LLM classification (100ms avg)
* ``HybridRouter``: Combines both (uses keyword if confidence ≥ 60%)

**Flow**:

1. Query received
2. Keyword router analyzes patterns
3. If confidence < threshold, use LLM router
4. Return ``RoutingDecision`` with task type and confidence

Agents Module
~~~~~~~~~~~~~

**Purpose**: Execute specific task types

**Components**:

* ``ResearchAgent``: Web research (search → scrape → synthesize)
* ``CodeAgent``: Code generation and execution
* ``ChatAgent``: Conversational AI
* ``RAGAgent``: Document Q&A with vector search

**Agent Lifecycle**:

1. Receive task from router
2. Execute task-specific logic
3. Use appropriate tools
4. Return structured result

Tools Module
~~~~~~~~~~~~

**Purpose**: Provide specialized utilities

**Categories**:

* **Search Tools**: SerpAPI integration, web scraping
* **Code Tools**: Safe execution, validation, sandbox
* **RAG Tools**: Vector store, document processing, chunking
* **Domain Tools**: Weather, finance, routing
* **Multimodal Tools**: OCR, vision API

LLM Module
~~~~~~~~~~

**Purpose**: Unified LLM provider management

**Features**:

* Multi-provider support (OpenAI, Aliyun, DeepSeek, Ollama)
* Automatic fallback on provider failure
* Provider priority: preferred → primary → remaining

**Providers**:

.. code-block:: text

   ┌────────────────────────────────────────┐
   │         LLM Manager                     │
   ├────────────────────────────────────────┤
   │  ┌──────────┐  ┌──────────┐           │
   │  │  OpenAI  │  │ DashScope│  ...      │
   │  └──────────┘  └──────────┘           │
   │         ▲            ▲                 │
   │         │            │                 │
   │    ┌────┴────────────┴────┐           │
   │    │   BaseLLM Interface  │           │
   │    └──────────────────────┘           │
   └────────────────────────────────────────┘

Workflow Module
~~~~~~~~~~~~~~~

**Purpose**: Orchestrate multi-step tasks

**Execution Modes**:

* ``SEQUENTIAL``: Run tasks one by one
* ``PARALLEL``: Run all tasks simultaneously
* ``DAG``: Execute based on dependency graph

**Components**:

* ``WorkflowEngine``: Core execution engine
* ``TaskDecomposer``: Break complex queries into subtasks
* ``ResultAggregator``: Combine multiple results

Web Module
~~~~~~~~~~

**Purpose**: FastAPI web interface

**Architecture**:

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │         FastAPI Application              │
   ├─────────────────────────────────────────┤
   │  Routers:                                │
   │  - main (/)                              │
   │  - query (/query)                        │
   │  - search, code, chat, rag               │
   │  - multimodal, tools, workflow           │
   │  - history                               │
   ├─────────────────────────────────────────┤
   │  Middleware:                             │
   │  - CORS                                  │
   │  - Rate Limiting                         │
   │  - Static Files                          │
   ├─────────────────────────────────────────┤
   │  Dependencies:                           │
   │  - LLM Manager                           │
   │  - Tools                                 │
   │  - Formatters                            │
   ├─────────────────────────────────────────┤
   │  Database:                               │
   │  - SQLite (async)                        │
   │  - Conversation history                  │
   │  - RAG documents                         │
   └─────────────────────────────────────────┘

Data Flow
---------

Research Query Flow
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Query: "What is quantum computing?"
      │
      ▼
   [Router] → TaskType.RESEARCH (confidence: 0.95)
      │
      ▼
   [ResearchAgent]
      │
      ├─→ [LLM] Generate search plan
      │     → ["quantum computing basics",
      │        "quantum vs classical computing",
      │        "quantum computing applications"]
      │
      ├─→ [SearchTool] Execute searches (parallel)
      │     → 15 total results (5 queries × 3 results)
      │
      ├─→ [ScraperTool] Scrape top 8 URLs (parallel)
      │     → Extract text content
      │
      ├─→ [CredibilityScorer] Score sources
      │     → Filter by credibility
      │
      └─→ [LLM] Synthesize summary
            → Final summary with sources

Code Query Flow
~~~~~~~~~~~~~~~

.. code-block:: text

   Query: "Calculate factorial of 10"
      │
      ▼
   [Router] → TaskType.CODE (confidence: 0.98)
      │
      ▼
   [CodeAgent]
      │
      ├─→ [LLM] Generate Python code
      │     → def factorial(n): ...
      │
      ├─→ [CodeValidator] Validate code
      │     ✓ AST parsing
      │     ✓ Import whitelist check
      │     ✓ Dangerous pattern check
      │
      └─→ [CodeExecutor] Execute in sandbox
            → Output: 3628800

RAG Query Flow
~~~~~~~~~~~~~~

.. code-block:: text

   Query: "What methodology was used?"
      │
      ▼
   [Router] → TaskType.RAG (confidence: 0.92)
      │
      ▼
   [RAGAgent]
      │
      ├─→ [VectorStore] Similarity search
      │     ├─→ [EmbeddingModel] Embed query
      │     ├─→ [ChromaDB] Search vectors
      │     └─→ Top 10 chunks
      │
      ├─→ [Reranker] Rerank results (optional)
      │     └─→ Top 5 chunks
      │
      └─→ [LLM] Generate answer from context
            → Answer + source references

Security Architecture
---------------------

Code Execution Security (3-Layer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Layer 1: AST Validation**

* Parse code into AST
* Check imports against whitelist
* Detect dangerous patterns (eval, exec, os.system)

**Layer 2: RestrictedPython**

* Compile code in restricted mode
* Prevent unauthorized access

**Layer 3: Docker Sandbox**

* Isolated container
* Resource limits (CPU, memory)
* Network disabled
* Read-only filesystem

**Flow**:

.. code-block:: text

   Code Input
      │
      ▼
   ┌──────────────────┐
   │ AST Validator    │  ← Layer 1
   │ ✓ Parse AST      │
   │ ✓ Check imports  │
   │ ✓ Check patterns │
   └────────┬─────────┘
            │ (if valid)
            ▼
   ┌──────────────────┐
   │ Restricted Exec  │  ← Layer 2
   │ ✓ Compile        │
   │ ✓ Restrict scope │
   └────────┬─────────┘
            │ (if enabled)
            ▼
   ┌──────────────────┐
   │ Docker Sandbox   │  ← Layer 3
   │ ✓ Isolated       │
   │ ✓ Limited        │
   └────────┬─────────┘
            │
            ▼
      Safe Execution

Caching Strategy
----------------

Query Routing Cache
~~~~~~~~~~~~~~~~~~~

* Cache routing decisions
* TTL: 3600s (1 hour)
* Key: query hash

Vector Search Cache
~~~~~~~~~~~~~~~~~~~

* Cache similarity search results
* TTL: 3600s (1 hour)
* Key: query + k + filter hash
* Invalidate on document add/delete

LRU Cache
~~~~~~~~~

* Max size: 1000 items
* Eviction: Least recently used

Scalability
-----------

Horizontal Scaling
~~~~~~~~~~~~~~~~~~

* Multiple web workers (uvicorn workers)
* Stateless API (can run multiple instances)
* Shared Redis cache (distributed caching)
* Load balancer (nginx, AWS ALB)

Vertical Scaling
~~~~~~~~~~~~~~~~

* Increase worker processes
* Use GPU for embeddings
* Optimize chunk size and batch size

Database Scaling
~~~~~~~~~~~~~~~~

* Use PostgreSQL for production
* Connection pooling
* Read replicas for heavy read workloads

Performance Metrics
-------------------

Target Performance
~~~~~~~~~~~~~~~~~~

* Router classification: < 100ms
* Keyword router: ~8ms
* LLM router: ~100ms
* Vector search (k=10): < 500ms (~235ms actual)
* Code execution: < 2s (~1.5s actual)
* API health endpoint: < 50ms (~9ms actual)
* Router throughput: > 50 q/s (~90 q/s actual)

Resource Usage
~~~~~~~~~~~~~~

* Vector store (1000 docs): ~235MB
* Router (1000 calls): ~12MB increase
* Cache speedup: ~19x faster on cache hit

Design Patterns
---------------

**Strategy Pattern**: Router implementations

**Factory Pattern**: Router factory, LLM client factory

**Observer Pattern**: Workflow callbacks

**Dependency Injection**: FastAPI dependencies

**Repository Pattern**: Database operations

**Adapter Pattern**: LLM providers

Future Enhancements
-------------------

* Add more LLM providers (Claude, Gemini)
* Implement graph-based RAG
* Add streaming responses for all modes
* Implement user authentication
* Add analytics dashboard
* Support more document formats
* Add multi-language support
* Implement caching with Redis
