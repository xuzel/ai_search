# Architecture Diagrams

Comprehensive architecture diagrams for the AI Search Engine.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Routing System](#routing-system)
3. [Agent Workflows](#agent-workflows)
4. [Security Architecture](#security-architecture)
5. [RAG System](#rag-system)
6. [Web Architecture](#web-architecture)
7. [LLM Management](#llm-management)
8. [Workflow Engine](#workflow-engine)
9. [Data Flow](#data-flow)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Web UI / CLI / API)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Router System                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Keyword    │  │     LLM      │  │   Hybrid     │         │
│  │   Router     │  │   Router     │  │   Router     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────┬────────────┬────────────┬────────────┬────────────┘
             │            │            │            │
     ┌───────┼────────────┼────────────┼────────────┼───────┐
     │       │            │            │            │       │
     ▼       ▼            ▼            ▼            ▼       ▼
┌─────────┐ ┌──────┐ ┌────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
│Research │ │ Code │ │  Chat  │ │   RAG   │ │  Domain  │ │Workflow  │
│ Agent   │ │Agent │ │ Agent  │ │  Agent  │ │  Tools   │ │  Engine  │
└────┬────┘ └──┬───┘ └───┬────┘ └────┬────┘ └────┬─────┘ └────┬─────┘
     │         │         │           │           │            │
     ▼         ▼         ▼           ▼           ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Tools Layer                             │
│  Search │ Scraper │ Code Executor │ Vector Store │ Domain APIs  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LLM Manager                               │
│  OpenAI │ DashScope │ DeepSeek │ Ollama │ Custom                │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Map

```
User Query
    │
    ├─→ [Router] ─→ Decision (Task Type + Confidence)
    │       │
    │       └─→ [Agent] ─→ Execute Task
    │              │
    │              ├─→ [Tools] ─→ Fetch Data
    │              │
    │              └─→ [LLM] ─→ Generate Response
    │
    └─→ [Database] ─→ Save History
```

---

## Routing System

### Hybrid Router Flow

```
User Query: "What is the weather in Beijing?"
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│                    Hybrid Router                           │
├───────────────────────────────────────────────────────────┤
│  Step 1: Keyword Router                                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  • Check WEATHER_KEYWORDS: ["weather", "temperature"]│ │
│  │  • Match found: "weather" in query                   │ │
│  │  • Task Type: DOMAIN_WEATHER                         │ │
│  │  • Confidence: 0.95                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                            │
│  Decision Point: confidence (0.95) >= threshold (0.6)     │
│  ✓ Use Keyword Router result (skip LLM)                   │
└───────────────────────────────────────────────────────────┘
    │
    ▼
Routing Decision:
  - Task Type: DOMAIN_WEATHER
  - Confidence: 0.95
  - Tools Needed: [WeatherTool]
  - Reasoning: "Weather keyword detected"
```

### Router Priority Flow

```
Query Input
    │
    ├─→ Domain-Specific Keywords? (WEATHER, FINANCE, ROUTING)
    │   └─→ YES → High Confidence (0.9+) → Direct Route
    │
    ├─→ RAG Keywords? ("in the document", "according to")
    │   └─→ YES → High Confidence (0.85+) → RAG Agent
    │
    ├─→ Code Keywords? ("calculate", "compute", "convert")
    │   └─→ YES → Medium Confidence (0.7+) → Code Agent
    │
    ├─→ Research Keywords? ("what is", "search for")
    │   └─→ YES → Medium Confidence (0.7+) → Research Agent
    │
    └─→ No Clear Keywords
        └─→ Low Confidence (< 0.6) → Call LLM Router
            └─→ LLM Analysis → Final Decision
```

### Task Type Classification

```
┌──────────────────────────────────────────────────────────┐
│                      Task Types                           │
├──────────────────────────────────────────────────────────┤
│  RESEARCH           Web search + synthesis               │
│  CODE               Code generation + execution          │
│  CHAT               Conversational AI                    │
│  RAG                Document Q&A                         │
│  DOMAIN_WEATHER     Weather queries                      │
│  DOMAIN_FINANCE     Stock/finance queries                │
│  DOMAIN_ROUTING     Navigation/directions                │
│  WORKFLOW           Multi-step task orchestration        │
└──────────────────────────────────────────────────────────┘
```

---

## Agent Workflows

### Research Agent - Complete Flow

```
1. QUERY ANALYSIS
   User: "What are the latest developments in quantum computing?"
   │
   ▼
2. SEARCH PLAN GENERATION (LLM)
   Prompt: "Generate 3-5 search queries for this topic"
   │
   ▼
   Queries:
   - "quantum computing 2024 breakthroughs"
   - "quantum computing recent developments"
   - "quantum computing applications news"
   │
   ▼
3. WEB SEARCH (Parallel)
   ┌─────────────┬─────────────┬─────────────┐
   │  Query 1    │  Query 2    │  Query 3    │
   │  SerpAPI    │  SerpAPI    │  SerpAPI    │
   │  3 results  │  3 results  │  3 results  │
   └──────┬──────┴──────┬──────┴──────┬──────┘
          └─────────────┴─────────────┘
                       │
   Total: 9 search results
   │
   ▼
4. WEB SCRAPING (Parallel - Top 8 URLs)
   ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
   │ URL1 │ URL2 │ URL3 │ URL4 │ URL5 │ URL6 │ URL7 │ URL8 │
   └──┬───┴──┬───┴──┬───┴──┬───┴──┬───┴──┬───┴──┬───┴──┬───┘
      └──────┴──────┴──────┴──────┴──────┴──────┴──────┘
                              │
   Extracted: 8 text documents (~2000 words each)
   │
   ▼
5. CREDIBILITY SCORING
   For each source:
   - Domain authority (0-1)
   - Content quality (0-1)
   - Recency score (0-1)
   - Final score: weighted average
   │
   Filter: Keep sources with score > 0.6
   │
   ▼
6. SYNTHESIS (LLM)
   Prompt: "Synthesize a summary from these sources..."
   Context: Top 5 credible sources
   │
   ▼
7. FINAL RESULT
   {
     "query": "...",
     "plan": ["query1", "query2", "query3"],
     "sources": [
       {"url": "...", "title": "...", "score": 0.85},
       ...
     ],
     "summary": "Comprehensive summary...",
     "timestamp": "2025-11-05T..."
   }
```

### Code Agent - Execution Flow

```
1. QUERY
   User: "Calculate the factorial of 10"
   │
   ▼
2. CODE GENERATION (LLM)
   Prompt: "Generate Python code to solve this problem"
   │
   ▼
   Generated Code:
   ┌─────────────────────────────────────┐
   │ def factorial(n):                   │
   │     if n <= 1:                      │
   │         return 1                    │
   │     return n * factorial(n - 1)     │
   │                                     │
   │ result = factorial(10)              │
   │ print(f"Factorial of 10: {result}") │
   └─────────────────────────────────────┘
   │
   ▼
3. SECURITY VALIDATION (3 Layers)
   │
   ├─→ LAYER 1: AST Validation
   │   ├─ Parse to AST ✓
   │   ├─ Check imports (none) ✓
   │   ├─ Check dangerous patterns (eval, exec, os) ✓
   │   └─ Result: PASS
   │
   ├─→ LAYER 2: RestrictedPython (if enabled)
   │   ├─ Compile in restricted mode ✓
   │   ├─ Verify scope restrictions ✓
   │   └─ Result: PASS
   │
   └─→ LAYER 3: Docker Sandbox (if enabled)
       ├─ Create isolated container
       ├─ Set resource limits (512MB RAM, 1 CPU)
       ├─ Disable network
       ├─ Read-only filesystem
       └─ Ready for execution
   │
   ▼
4. EXECUTION
   Execute code with timeout (30s)
   │
   ▼
   Output: "Factorial of 10: 3628800"
   Exit Code: 0
   Duration: 0.023s
   │
   ▼
5. RESULT FORMATTING
   {
     "code": "def factorial(n): ...",
     "output": "Factorial of 10: 3628800",
     "execution_time": "0.023s",
     "success": true,
     "explanation": "The factorial function..."
   }
```

### RAG Agent - Document Q&A Flow

```
INGESTION PHASE
───────────────
1. Document Upload
   File: "research_paper.pdf" (5 pages, 10,000 words)
   │
   ▼
2. Text Extraction
   DocumentProcessor → Extract text from PDF
   │
   ▼
3. Chunking
   SmartChunker (semantic strategy)
   ├─ Chunk 1: "Introduction..." (500 words)
   ├─ Chunk 2: "Methodology..." (500 words)
   ├─ Chunk 3: "Results..." (500 words)
   └─ ... (20 chunks total)
   │
   ▼
4. Embedding
   sentence-transformers/all-MiniLM-L6-v2
   Each chunk → 384-dim vector
   │
   ▼
5. Vector Store
   ChromaDB: Store 20 vectors with metadata
   Index created: Ready for search

RETRIEVAL PHASE
────────────────
1. Query
   "What methodology was used in the study?"
   │
   ▼
2. Query Embedding
   Same model → 384-dim query vector
   │
   ▼
3. Similarity Search
   ChromaDB cosine similarity
   │
   ▼
   Top 10 chunks (similarity > 0.7):
   ├─ Chunk 2: similarity=0.92
   ├─ Chunk 5: similarity=0.87
   ├─ Chunk 8: similarity=0.81
   └─ ... (10 total)
   │
   ▼
4. Reranking (if enabled)
   Hybrid Reranker (BGE + CrossEncoder)
   │
   ▼
   Top 5 chunks after reranking:
   ├─ Chunk 2: score=0.95
   ├─ Chunk 8: score=0.89
   ├─ Chunk 5: score=0.85
   └─ ... (5 total)
   │
   ▼
5. Context Building
   Concatenate top 5 chunks (2500 words)
   │
   ▼
6. LLM Generation
   Prompt:
   ┌────────────────────────────────────────┐
   │ Context: [5 relevant chunks]           │
   │                                        │
   │ Question: What methodology was used    │
   │ in the study?                          │
   │                                        │
   │ Instructions: Answer based on context  │
   │ only. Cite sources.                    │
   └────────────────────────────────────────┘
   │
   ▼
7. Final Answer
   {
     "answer": "The study used a mixed-methods approach...",
     "sources": [
       {"chunk_id": 2, "text": "Methodology section...", "score": 0.95},
       {"chunk_id": 8, "text": "Data collection...", "score": 0.89}
     ],
     "confidence": 0.92
   }
```

---

## Security Architecture

### Code Execution Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    CODE INPUT (Untrusted)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: AST (Abstract Syntax Tree) Validation                  │
├─────────────────────────────────────────────────────────────────┤
│ Step 1: Parse to AST                                            │
│   try:                                                           │
│     tree = ast.parse(code)                                      │
│   except SyntaxError:                                           │
│     REJECT: "Invalid Python syntax"                             │
│                                                                  │
│ Step 2: Check Imports                                           │
│   Whitelist: [math, statistics, datetime, json, ...]           │
│   for node in ast.walk(tree):                                  │
│     if isinstance(node, ast.Import):                           │
│       if node.module not in WHITELIST:                         │
│         REJECT: "Unauthorized import: {module}"                │
│                                                                  │
│ Step 3: Detect Dangerous Patterns                              │
│   Dangerous: [eval, exec, compile, __import__, os.system, ...]│
│   for node in ast.walk(tree):                                  │
│     if matches_dangerous_pattern(node):                        │
│       REJECT: "Dangerous pattern detected"                     │
│                                                                  │
│ Result: ✓ PASS → Continue to Layer 2                           │
│         ✗ FAIL → Reject execution                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ (if PASS)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: RestrictedPython Execution                             │
├─────────────────────────────────────────────────────────────────┤
│ Compile in Restricted Mode:                                     │
│   - Restricted builtins (no open, eval, exec)                  │
│   - Limited globals scope                                       │
│   - No attribute access to dangerous objects                    │
│   - No write access to external state                           │
│                                                                  │
│ Safe Builtins Only:                                             │
│   {                                                              │
│     'print': safe_print,                                        │
│     'range': range,                                             │
│     'len': len,                                                 │
│     'abs': abs,                                                 │
│     # ... limited set                                           │
│   }                                                              │
│                                                                  │
│ Result: ✓ Code compiled successfully                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    Docker Enabled?
                             │
                    ┌────────┴────────┐
                    │                 │
                   YES               NO
                    │                 │
                    ▼                 ▼
┌─────────────────────────────┐  ┌────────────────────────┐
│ LAYER 3: Docker Sandbox     │  │ Execute Locally        │
├─────────────────────────────┤  │ (RestrictedPython)     │
│ 1. Create Container         │  └────────┬───────────────┘
│    Image: python:3.11-slim  │           │
│                              │           │
│ 2. Set Resource Limits      │           │
│    - Memory: 512MB          │           │
│    - CPU: 1.0 core          │           │
│    - Disk: 100MB            │           │
│                              │           │
│ 3. Security Configuration   │           │
│    - Network: DISABLED      │           │
│    - Filesystem: READ-ONLY  │           │
│    - User: non-root         │           │
│    - Capabilities: DROPPED  │           │
│                              │           │
│ 4. Timeout                  │           │
│    - Max execution: 30s     │           │
│    - Kill on timeout        │           │
│                              │           │
│ 5. Execute Code             │           │
│    docker run --rm \        │           │
│      --network=none \       │           │
│      --memory=512m \        │           │
│      --cpus=1.0 \           │           │
│      --read-only \          │           │
│      python:3.11-slim \     │           │
│      python -c "$CODE"      │           │
└────────────┬────────────────┘           │
             │                            │
             └────────────┬───────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │     ✓ SAFE EXECUTION            │
        │     Capture output (max 1000    │
        │     lines)                       │
        │     Return result                │
        └─────────────────────────────────┘
```

### Security Validation Example

```
INPUT CODE:
───────────
import os
result = os.system("rm -rf /")

LAYER 1 VALIDATION:
───────────────────
✗ FAIL at "Check Imports"
  → Module 'os' not in whitelist
  → REJECT before execution

─────────────────────────────────────

INPUT CODE:
───────────
eval("__import__('os').system('ls')")

LAYER 1 VALIDATION:
───────────────────
✗ FAIL at "Dangerous Pattern Detection"
  → Pattern 'eval' detected
  → REJECT before execution

─────────────────────────────────────

INPUT CODE:
───────────
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

print(factorial(10))

LAYER 1 VALIDATION:
───────────────────
✓ PASS: Syntax valid
✓ PASS: No imports
✓ PASS: No dangerous patterns

LAYER 2 VALIDATION:
───────────────────
✓ PASS: Compiled in restricted mode
✓ PASS: Safe builtins only

LAYER 3 (if Docker enabled):
─────────────────────────────
✓ PASS: Executed in isolated container
✓ OUTPUT: "3628800"
✓ EXIT CODE: 0
✓ DURATION: 0.023s
```

---

## RAG System

### Vector Store Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ChromaDB                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Collection: "documents"                                    │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Document 1                                           │  │ │
│  │  │    • ID: "doc1_chunk0"                               │  │ │
│  │  │    • Vector: [0.23, -0.45, 0.12, ...] (384-dim)     │  │ │
│  │  │    • Metadata: {source: "file.pdf", page: 1}        │  │ │
│  │  │    • Text: "Introduction to quantum..."             │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Document 2                                           │  │ │
│  │  │    • ID: "doc1_chunk1"                               │  │ │
│  │  │    • Vector: [-0.15, 0.67, -0.23, ...] (384-dim)    │  │ │
│  │  │    • Metadata: {source: "file.pdf", page: 2}        │  │ │
│  │  │    • Text: "Methodology section..."                 │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │  ... (thousands of documents)                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Indexing: HNSW (Hierarchical Navigable Small World)           │
│  Distance Metric: Cosine Similarity                            │
│  Persistence: /data/vector_store/                              │
└─────────────────────────────────────────────────────────────────┘
```

### Chunking Strategies

```
SEMANTIC CHUNKING
─────────────────
Input: "Quantum computing is... [5000 words] ...future applications."

Algorithm:
1. Split into sentences
2. Calculate sentence embeddings
3. Find semantic boundaries (similarity drop > threshold)
4. Create chunks at boundaries

Output:
├─ Chunk 1: "Quantum computing is... [450 words] ...basic principles."
│  (Topic: Introduction)
├─ Chunk 2: "The quantum bit... [520 words] ...superposition states."
│  (Topic: Qubits)
└─ Chunk 3: "Applications include... [480 words] ...future prospects."
   (Topic: Applications)

Advantages: Semantically coherent chunks
Disadvantages: Variable chunk sizes

FIXED SIZE CHUNKING
───────────────────
Input: "Quantum computing is... [5000 words]"

Algorithm:
1. Split at fixed word count (500 words)
2. Add overlap (50 words)

Output:
├─ Chunk 1: Words 1-500
├─ Chunk 2: Words 451-950 (50 word overlap)
├─ Chunk 3: Words 901-1400 (50 word overlap)
└─ ... (10 chunks total)

Advantages: Predictable chunk sizes, simple
Disadvantages: May split semantic units

RECURSIVE CHUNKING
──────────────────
Input: Large document

Algorithm:
1. Try to split at paragraph boundaries
2. If chunk still too large, split at sentence boundaries
3. If still too large, split at word boundaries

Output: Chunks that respect document structure

Advantages: Preserves structure
Disadvantages: More complex implementation
```

### Reranking Pipeline

```
INITIAL RETRIEVAL
─────────────────
Query: "What is quantum entanglement?"
│
▼ Vector Search (top_k=10)
│
Results:
├─ Doc 1: similarity=0.82
├─ Doc 2: similarity=0.79
├─ Doc 3: similarity=0.76
├─ Doc 4: similarity=0.74
├─ Doc 5: similarity=0.72
├─ Doc 6: similarity=0.71
├─ Doc 7: similarity=0.69
├─ Doc 8: similarity=0.68
├─ Doc 9: similarity=0.66
└─ Doc 10: similarity=0.64

RERANKING PHASE
───────────────
│
├─→ BGE Reranker
│   Model: BAAI/bge-reranker-large
│   ├─ Doc 1: score=0.91
│   ├─ Doc 3: score=0.88
│   ├─ Doc 2: score=0.84
│   ├─ Doc 5: score=0.79
│   └─ Doc 4: score=0.76
│
├─→ Cross-Encoder Reranker
│   Model: cross-encoder/ms-marco-MiniLM-L-6-v2
│   ├─ Doc 1: score=0.89
│   ├─ Doc 2: score=0.87
│   ├─ Doc 3: score=0.85
│   ├─ Doc 4: score=0.81
│   └─ Doc 6: score=0.78
│
└─→ Hybrid Ranking
    Weight: BGE (0.6) + CrossEncoder (0.4)
    ├─ Doc 1: 0.91*0.6 + 0.89*0.4 = 0.902
    ├─ Doc 3: 0.88*0.6 + 0.85*0.4 = 0.868
    ├─ Doc 2: 0.84*0.6 + 0.87*0.4 = 0.852
    ├─ Doc 5: 0.79*0.6 + 0.00*0.4 = 0.474
    └─ Doc 4: 0.76*0.6 + 0.81*0.4 = 0.780

FINAL TOP 5
───────────
1. Doc 1 (score=0.902)
2. Doc 3 (score=0.868)
3. Doc 2 (score=0.852)
4. Doc 4 (score=0.780)
5. Doc 6 (score=0.312)

→ Significant improvement in relevance!
```

---

## Web Architecture

### FastAPI Application Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                           │
├─────────────────────────────────────────────────────────────────┤
│  Startup Events:                                                 │
│    - Initialize database                                         │
│    - Load LLM manager                                           │
│    - Initialize tools                                           │
│    - Create upload directories                                  │
│                                                                  │
│  Middleware Stack:                                              │
│    1. CORS (Cross-Origin Resource Sharing)                     │
│    2. Rate Limiting (SlowAPI)                                  │
│    3. Static Files (/static)                                   │
│    4. Session Middleware                                       │
│                                                                  │
│  Routers:                                                       │
│    ┌──────────────────────────────────────────────────────┐   │
│    │ / (main)           → Homepage, health check          │   │
│    │ /query             → Unified query with auto-routing │   │
│    │ /search            → Research mode                   │   │
│    │ /code              → Code generation/execution       │   │
│    │ /chat              → Chat mode (SSE streaming)       │   │
│    │ /rag               → RAG document upload & query     │   │
│    │ /multimodal        → OCR & Vision                    │   │
│    │ /tools             → Domain tools (weather, finance) │   │
│    │ /workflow          → Multi-step workflows            │   │
│    │ /history           → Conversation history            │   │
│    └──────────────────────────────────────────────────────┘   │
│                                                                  │
│  Dependencies (Dependency Injection):                           │
│    - get_config()                                              │
│    - get_llm_manager()                                         │
│    - get_templates()                                           │
│    - get_tools()                                               │
│                                                                  │
│  Templates (Jinja2):                                           │
│    - base.html (main layout with HTMX)                        │
│    - components/*.html (reusable components)                   │
│                                                                  │
│  Database (SQLite):                                            │
│    - conversation_history table                                │
│    - rag_documents table                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
Browser Request
    │
    ▼
┌─────────────────────┐
│  CORS Middleware    │ ← Check origin, add headers
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Rate Limit Check    │ ← Check: 30 req/min per IP
└──────────┬──────────┘
           │
           ├─→ Rate Exceeded → 429 Too Many Requests
           │
           ▼ (allowed)
┌─────────────────────┐
│  Router Matching    │ ← Match URL to router
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Dependencies       │ ← Inject LLM, tools, config
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Route Handler       │ ← Execute business logic
│  - Parse request    │
│  - Call agent       │
│  - Format response  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Template Rendering  │ ← Render Jinja2 template
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Save to Database   │ ← Save conversation history
└──────────┬──────────┘
           │
           ▼
     HTTP Response
     (HTML via HTMX)
```

### HTMX Interaction Pattern

```
User Clicks Submit Button
    │
    ▼
┌──────────────────────────────────────┐
│  <form hx-post="/query"              │
│        hx-target="#result"           │
│        hx-indicator="#loading">      │
│    <input name="query" />            │
│    <button type="submit">Search</button>│
│  </form>                             │
└──────────────────────────┬───────────┘
                           │
    HTMX intercepts submit │
                           │
                           ▼
                  POST /query (AJAX)
                           │
                           ▼
              ┌────────────────────────┐
              │  FastAPI Handler       │
              │  - Process query       │
              │  - Generate response   │
              │  - Render partial HTML │
              └────────┬───────────────┘
                       │
                       ▼
            Return HTML Fragment
            (not full page)
                       │
                       ▼
        ┌──────────────────────────────┐
        │  HTMX receives response      │
        │  - Find #result element      │
        │  - Replace innerHTML         │
        │  - Hide #loading indicator   │
        └──────────────────────────────┘
                       │
                       ▼
              Updated UI (no page reload!)
```

---

## LLM Management

### Provider Fallback Chain

```
LLM Request
    │
    ├─→ Preferred Provider Specified?
    │   │
    │   ├─→ YES: Try Preferred First
    │   │   └─→ OpenAI (preferred)
    │   │       ├─→ Success → Return
    │   │       └─→ Fail → Continue to Primary
    │   │
    │   └─→ NO: Skip to Primary
    │
    ▼
Try Primary Provider (first initialized)
    │
    ├─→ DashScope (primary)
    │   ├─→ API Key Valid?
    │   │   ├─→ YES: Make Request
    │   │   │   ├─→ Success (200) → Return Response
    │   │   │   ├─→ Rate Limit (429) → Wait & Retry
    │   │   │   └─→ Error (500) → Next Provider
    │   │   └─→ NO: Next Provider
    │
    ▼
Try Secondary Provider
    │
    ├─→ DeepSeek
    │   ├─→ Success → Return Response
    │   └─→ Fail → Next Provider
    │
    ▼
Try Tertiary Provider
    │
    ├─→ Ollama (local)
    │   ├─→ Server Running?
    │   │   ├─→ YES: Success → Return Response
    │   │   └─→ NO: Next Provider
    │
    ▼
All Providers Failed
    │
    └─→ Raise RuntimeError("No LLM providers available")
```

### Provider Configuration Matrix

```
┌──────────────┬─────────────┬──────────────┬─────────────┬──────────┐
│ Provider     │ Enabled     │ API Key      │ Model       │ Priority │
├──────────────┼─────────────┼──────────────┼─────────────┼──────────┤
│ OpenAI       │ ✓ Yes       │ sk-xxx***    │ gpt-4       │ 2        │
│ DashScope    │ ✓ Yes       │ sk-yyy***    │ qwen-max    │ 1 (prim) │
│ DeepSeek     │ ✗ No        │ (not set)    │ -           │ -        │
│ Ollama       │ ✓ Yes       │ (not needed) │ llama2      │ 3        │
│ Custom       │ ✗ No        │ (not set)    │ -           │ -        │
└──────────────┴─────────────┴──────────────┴─────────────┴──────────┘

Fallback Order: DashScope → OpenAI → Ollama

Example Flow:
1. Request arrives
2. Try DashScope (primary) → Rate limited (429)
3. Try OpenAI (secondary) → Success!
4. Return OpenAI response
```

---

## Workflow Engine

### DAG Execution

```
Workflow: "Research Pipeline"
Mode: DAG (Directed Acyclic Graph)

Task Graph:
                  ┌───────┐
                  │ Task A│ (no dependencies)
                  │Search │
                  └───┬───┘
                      │
              ┌───────┴───────┐
              │               │
              ▼               ▼
         ┌────────┐      ┌────────┐
         │ Task B │      │ Task C │
         │ Scrape │      │Summarize│
         └────┬───┘      └────┬───┘
              │               │
              └───────┬───────┘
                      │
                      ▼
                 ┌─────────┐
                 │ Task D  │
                 │ Combine │
                 └─────────┘

Execution Timeline:
───────────────────

t=0s    Start
        │
        └─→ Task A starts (no deps)

t=2s    Task A completes
        │
        ├─→ Task B starts (dep: A)
        └─→ Task C starts (dep: A) [parallel]

t=5s    Task B completes

t=6s    Task C completes
        │
        └─→ Task D starts (deps: B, C)

t=8s    Task D completes
        │
        └─→ Workflow complete

Total Duration: 8s
Parallelism: Tasks B & C ran concurrently
```

### Task Retry Logic

```
Task: "Fetch Data from API"
Retry Count: 3
Timeout: 10s

Execution Attempts:
───────────────────

Attempt 1:
  Start: t=0s
  │
  ├─→ Execute task
  │   └─→ Network timeout after 10s
  │
  └─→ FAIL (timeout)
      │
      └─→ Retry? (1/3) → YES

Attempt 2:
  Start: t=10s (immediate retry)
  │
  ├─→ Execute task
  │   └─→ HTTP 500 Error
  │
  └─→ FAIL (server error)
      │
      └─→ Retry? (2/3) → YES

Attempt 3:
  Start: t=11s (immediate retry)
  │
  ├─→ Execute task
  │   └─→ HTTP 200 OK
  │       Data: {...}
  │
  └─→ SUCCESS
      │
      └─→ Return result

Total Attempts: 3
Final Status: SUCCESS
Duration: 13s (including retries)
```

---

## Data Flow

### Complete Query Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                       USER SUBMITS QUERY                         │
│              "What are the latest AI developments?"             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ WEB UI (FastAPI)                                                 │
│  POST /query                                                     │
│    - Extract query from form                                     │
│    - Log request                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ ROUTER SYSTEM                                                    │
│  Step 1: Keyword Router                                         │
│    - Check patterns: RESEARCH_KEYWORDS                          │
│    - Match: "what are" → RESEARCH                               │
│    - Confidence: 0.75                                           │
│                                                                  │
│  Step 2: Confidence Check                                       │
│    - 0.75 >= 0.6 (threshold) → USE KEYWORD RESULT              │
│    - (Skip LLM router)                                          │
│                                                                  │
│  Result: TaskType.RESEARCH, confidence=0.75                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESEARCH AGENT                                                   │
│  Phase 1: Planning                                              │
│    LLM Call #1: "Generate 3 search queries"                     │
│    → ["AI developments 2024", "latest AI research", ...]       │
│                                                                  │
│  Phase 2: Search (Parallel)                                     │
│    SerpAPI Call #1: "AI developments 2024"                      │
│    SerpAPI Call #2: "latest AI research"                        │
│    SerpAPI Call #3: "AI breakthroughs"                          │
│    → 15 total results                                           │
│                                                                  │
│  Phase 3: Scrape (Parallel)                                     │
│    Scrape URL #1, #2, #3, ... #8                               │
│    → 8 documents (~16,000 words)                                │
│                                                                  │
│  Phase 4: Synthesis                                             │
│    LLM Call #2: "Synthesize summary from sources"              │
│    → Final summary (~500 words)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ FORMAT RESPONSE                                                  │
│  {                                                               │
│    "query": "What are the latest AI developments?",            │
│    "task_type": "RESEARCH",                                     │
│    "plan": ["query1", "query2", "query3"],                     │
│    "sources": [                                                 │
│      {"url": "...", "title": "...", "score": 0.85},           │
│      ...                                                        │
│    ],                                                           │
│    "summary": "Recent AI developments include...",             │
│    "duration": "12.3s"                                          │
│  }                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ SAVE TO DATABASE                                                 │
│  INSERT INTO conversation_history (                             │
│    timestamp, mode, query, response, metadata                   │
│  ) VALUES (                                                      │
│    '2025-11-05 10:30:45',                                       │
│    'research',                                                   │
│    'What are the latest AI developments?',                     │
│    '{"summary": "...", "sources": [...]}',                     │
│    '{"duration": "12.3s", "confidence": 0.75}'                 │
│  )                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ RENDER RESPONSE (Jinja2 Template)                               │
│  Template: components/result_research.html                      │
│    - Display summary                                            │
│    - Show sources with scores                                   │
│    - Add "Read More" links                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ HTMX UPDATES DOM                                                 │
│  Replace #result div with rendered HTML                         │
│  (No full page reload)                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ USER SEES      │
                    │ RESULT         │
                    └────────────────┘

Total Time: ~12.3s
LLM Calls: 2
API Calls: 11 (3 search + 8 scrape)
Database Writes: 1
```

---

## Deployment Architecture

### Production Deployment (AWS Example)

```
┌─────────────────────────────────────────────────────────────────┐
│                          INTERNET                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ AWS ROUTE 53 (DNS)                                               │
│   ai-search.example.com → ALB                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ AWS APPLICATION LOAD BALANCER                                    │
│   - SSL/TLS Termination (ACM Certificate)                       │
│   - Health Checks: /health                                       │
│   - Sticky Sessions: Enabled                                     │
│   - Request Routing: Round Robin                                 │
└────────┬────────┬────────┬────────┬────────────────────────────┘
         │        │        │        │
         ▼        ▼        ▼        ▼
┌────────────┬────────────┬────────────┬────────────┐
│   ECS      │   ECS      │   ECS      │   ECS      │
│ Container  │ Container  │ Container  │ Container  │
│ Instance 1 │ Instance 2 │ Instance 3 │ Instance 4 │
│            │            │            │            │
│ FastAPI    │ FastAPI    │ FastAPI    │ FastAPI    │
│ 4 workers  │ 4 workers  │ 4 workers  │ 4 workers  │
│            │            │            │            │
│ Resources: │ Resources: │ Resources: │ Resources: │
│ 2 vCPU     │ 2 vCPU     │ 2 vCPU     │ 2 vCPU     │
│ 4 GB RAM   │ 4 GB RAM   │ 4 GB RAM   │ 4 GB RAM   │
└────┬───────┴────┬───────┴────┬───────┴────┬───────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┬─────────────┬──────────────┐
│   ElastiCache│   RDS       │   S3         │
│   (Redis)    │ (PostgreSQL)│   (Storage)  │
│              │             │              │
│   Caching:   │  Database:  │   Files:     │
│   - Queries  │  - History  │   - Documents│
│   - Vectors  │  - Users    │   - Uploads  │
│   - Sessions │  - Metadata │   - Logs     │
│              │             │              │
│   6 GB       │   50 GB     │   500 GB     │
│   Multi-AZ   │   Multi-AZ  │   Multi-AZ   │
└──────────────┴─────────────┴──────────────┘

EXTERNAL SERVICES:
├─→ OpenAI API (https://api.openai.com)
├─→ Aliyun DashScope API
├─→ SerpAPI (https://serpapi.com)
├─→ OpenWeatherMap API
└─→ Alpha Vantage API

MONITORING & LOGGING:
├─→ CloudWatch Logs
├─→ CloudWatch Metrics
├─→ X-Ray Tracing
└─→ SNS Alerts
```

### Scaling Strategy

```
HORIZONTAL SCALING
──────────────────
Auto Scaling Group Configuration:
  Min Instances: 2
  Max Instances: 10
  Desired: 4

Scale-Out Triggers:
  - CPU > 70% for 5 minutes → +2 instances
  - Memory > 80% for 5 minutes → +2 instances
  - Request queue > 100 → +1 instance

Scale-In Triggers:
  - CPU < 30% for 10 minutes → -1 instance
  - Request queue < 20 for 10 minutes → -1 instance

VERTICAL SCALING
────────────────
Instance Types:
  Development: t3.medium (2 vCPU, 4 GB)
  Production:  c5.xlarge (4 vCPU, 8 GB)
  High Load:   c5.2xlarge (8 vCPU, 16 GB)

DATABASE SCALING
────────────────
Read Replicas:
  Primary: us-east-1a (write)
  Replica 1: us-east-1b (read)
  Replica 2: us-east-1c (read)

Connection Pooling:
  Max Connections: 100
  Pool Size: 20
  Pool Timeout: 30s

CACHING SCALING
───────────────
Redis Cluster:
  Nodes: 3 (primary + 2 replicas)
  Memory: 6 GB per node
  Eviction Policy: allkeys-lru
```

---

## Summary

This document provides comprehensive architecture diagrams covering:

1. ✅ System Overview - High-level component interaction
2. ✅ Routing System - Multi-strategy query classification
3. ✅ Agent Workflows - Detailed execution flows
4. ✅ Security Architecture - 3-layer code execution security
5. ✅ RAG System - Vector store and retrieval pipeline
6. ✅ Web Architecture - FastAPI application structure
7. ✅ LLM Management - Provider fallback and configuration
8. ✅ Workflow Engine - DAG execution and task management
9. ✅ Data Flow - Complete query lifecycle
10. ✅ Deployment Architecture - Production deployment pattern

**Total**: 50+ diagrams in ASCII and Mermaid format

See `docs/diagrams/system_overview.md` for Mermaid diagrams that can be rendered in GitHub, GitLab, or documentation tools.
