# System Architecture Diagrams

This document contains architecture diagrams for the AI Search Engine.

## System Overview

```mermaid
graph TB
    User[User Interface] --> WebUI[Web UI / CLI]
    WebUI --> Router{Router System}

    Router -->|RESEARCH| ResearchAgent[Research Agent]
    Router -->|CODE| CodeAgent[Code Agent]
    Router -->|CHAT| ChatAgent[Chat Agent]
    Router -->|RAG| RAGAgent[RAG Agent]
    Router -->|DOMAIN_*| DomainTools[Domain Tools]
    Router -->|WORKFLOW| WorkflowEngine[Workflow Engine]

    ResearchAgent --> SearchTool[Search Tool]
    ResearchAgent --> ScraperTool[Scraper Tool]
    ResearchAgent --> LLM[LLM Manager]

    CodeAgent --> CodeExecutor[Code Executor]
    CodeAgent --> LLM

    ChatAgent --> LLM

    RAGAgent --> VectorStore[Vector Store]
    RAGAgent --> DocumentProcessor[Document Processor]
    RAGAgent --> LLM

    DomainTools --> Weather[Weather Tool]
    DomainTools --> Finance[Finance Tool]
    DomainTools --> Routing[Routing Tool]

    LLM --> OpenAI[OpenAI]
    LLM --> DashScope[Aliyun DashScope]
    LLM --> DeepSeek[DeepSeek]
    LLM --> Ollama[Ollama Local]

    VectorStore --> ChromaDB[(ChromaDB)]

    WebUI --> Database[(SQLite DB)]

    style Router fill:#f9f,stroke:#333,stroke-width:4px
    style LLM fill:#bbf,stroke:#333,stroke-width:2px
    style VectorStore fill:#bfb,stroke:#333,stroke-width:2px
```

## Routing System Architecture

```mermaid
graph LR
    Query[User Query] --> RouterFactory{Router Factory}

    RouterFactory --> KeywordRouter[Keyword Router]
    RouterFactory --> LLMRouter[LLM Router]
    RouterFactory --> HybridRouter[Hybrid Router]

    KeywordRouter --> Patterns[Pattern Matching]
    Patterns --> Keywords[Keywords Check]
    Patterns --> Regex[Regex Check]
    Keywords --> Decision1[Routing Decision]
    Regex --> Decision1

    LLMRouter --> LLMCall[LLM Classification]
    LLMCall --> JSONParse[Parse JSON Response]
    JSONParse --> Decision2[Routing Decision]

    HybridRouter --> Step1[1. Keyword Router]
    Step1 --> ConfCheck{Confidence >= 0.6?}
    ConfCheck -->|Yes| Decision3[Routing Decision]
    ConfCheck -->|No| Step2[2. LLM Router]
    Step2 --> Decision3

    Decision1 --> TaskType[Task Type + Confidence]
    Decision2 --> TaskType
    Decision3 --> TaskType

    style HybridRouter fill:#f96,stroke:#333,stroke-width:3px
    style TaskType fill:#6f6,stroke:#333,stroke-width:2px
```

## Research Agent Flow

```mermaid
sequenceDiagram
    participant User
    participant Router
    participant ResearchAgent
    participant LLM
    participant SearchTool
    participant ScraperTool
    participant Synthesizer

    User->>Router: Query: "What is quantum computing?"
    Router->>Router: Classify query
    Router->>ResearchAgent: TaskType.RESEARCH

    ResearchAgent->>LLM: Generate search plan
    LLM-->>ResearchAgent: ["quantum computing basics", "applications", "vs classical"]

    ResearchAgent->>SearchTool: Execute 3 searches (parallel)
    SearchTool-->>ResearchAgent: 15 results (5 per query)

    ResearchAgent->>ScraperTool: Scrape top 8 URLs (parallel)
    ScraperTool-->>ResearchAgent: Extracted content

    ResearchAgent->>ResearchAgent: Score credibility
    ResearchAgent->>LLM: Synthesize summary from content
    LLM-->>ResearchAgent: Final summary

    ResearchAgent-->>User: {summary, sources, plan}
```

## Code Execution Security (3-Layer)

```mermaid
graph TB
    Code[Python Code Input] --> Layer1[Layer 1: AST Validation]

    Layer1 --> ParseAST[Parse to AST]
    ParseAST --> CheckImports{Check Imports}
    CheckImports -->|Whitelist| CheckPatterns{Check Patterns}
    CheckImports -->|Not Allowed| Reject1[❌ Reject]
    CheckPatterns -->|Safe| Layer2[Layer 2: RestrictedPython]
    CheckPatterns -->|Dangerous| Reject2[❌ Reject]

    Layer2 --> CompileRestricted[Compile in Restricted Mode]
    CompileRestricted --> CheckEnabled{Docker Enabled?}
    CheckEnabled -->|No| Execute1[Execute Locally]
    CheckEnabled -->|Yes| Layer3[Layer 3: Docker Sandbox]

    Layer3 --> CreateContainer[Create Isolated Container]
    CreateContainer --> SetLimits[Set Resource Limits]
    SetLimits --> DisableNetwork[Disable Network]
    DisableNetwork --> ReadOnlyFS[Read-Only Filesystem]
    ReadOnlyFS --> Execute2[Execute in Container]

    Execute1 --> Output[✅ Safe Output]
    Execute2 --> Output

    style Layer1 fill:#faa,stroke:#333,stroke-width:2px
    style Layer2 fill:#ffa,stroke:#333,stroke-width:2px
    style Layer3 fill:#afa,stroke:#333,stroke-width:2px
    style Output fill:#6f6,stroke:#333,stroke-width:3px
    style Reject1 fill:#f66,stroke:#333,stroke-width:2px
    style Reject2 fill:#f66,stroke:#333,stroke-width:2px
```

## RAG System Architecture

```mermaid
graph TB
    subgraph Ingestion
        Upload[Document Upload] --> DocProcessor[Document Processor]
        DocProcessor --> ExtractText[Extract Text]
        ExtractText --> Chunker[Smart Chunker]
        Chunker --> Semantic[Semantic Chunking]
        Chunker --> Fixed[Fixed Size Chunking]
        Chunker --> Recursive[Recursive Chunking]
        Semantic --> Chunks[Text Chunks]
        Fixed --> Chunks
        Recursive --> Chunks
        Chunks --> Embedder[Embedding Model]
        Embedder --> VectorDB[(Vector Store)]
    end

    subgraph Retrieval
        Query[User Query] --> EmbedQuery[Embed Query]
        EmbedQuery --> VectorDB
        VectorDB --> TopK[Top K Results]
        TopK --> Reranker{Reranker Enabled?}
        Reranker -->|Yes| BGE[BGE Reranker]
        Reranker -->|Yes| CrossEncoder[Cross Encoder]
        Reranker -->|No| Context
        BGE --> HybridRank[Hybrid Ranking]
        CrossEncoder --> HybridRank
        HybridRank --> Context[Final Context]
        Context --> LLM[LLM]
        LLM --> Answer[Answer + Sources]
    end

    style VectorDB fill:#9cf,stroke:#333,stroke-width:2px
    style LLM fill:#bbf,stroke:#333,stroke-width:2px
    style Answer fill:#6f6,stroke:#333,stroke-width:3px
```

## Web Application Architecture

```mermaid
graph TB
    subgraph Client
        Browser[Web Browser]
        Browser --> HTMX[HTMX]
    end

    subgraph FastAPI Application
        HTMX --> Middleware[Middleware Layer]
        Middleware --> CORS[CORS]
        Middleware --> RateLimit[Rate Limiter]
        Middleware --> Static[Static Files]

        RateLimit --> RouterLayer[Router Layer]

        RouterLayer --> MainRouter[Main Router /]
        RouterLayer --> QueryRouter[Query Router /query]
        RouterLayer --> SearchRouter[Search Router /search]
        RouterLayer --> CodeRouter[Code Router /code]
        RouterLayer --> ChatRouter[Chat Router /chat]
        RouterLayer --> RAGRouter[RAG Router /rag]
        RouterLayer --> ToolsRouter[Tools Router /tools]
        RouterLayer --> WorkflowRouter[Workflow Router /workflow]
        RouterLayer --> HistoryRouter[History Router /history]

        QueryRouter --> Dependencies[Dependencies]
        Dependencies --> LLMDep[LLM Manager]
        Dependencies --> ToolsDep[Tools]
        Dependencies --> FormatDep[Formatters]

        QueryRouter --> Templates[Jinja2 Templates]
        Templates --> BaseTemplate[base.html]
        Templates --> Components[components/*.html]
    end

    subgraph Backend Services
        LLMDep --> Agents[Agents]
        ToolsDep --> Tools[Tools]
        Agents --> ExternalAPIs[External APIs]
    end

    subgraph Data Layer
        RouterLayer --> DBLayer[Database Layer]
        DBLayer --> SQLite[(SQLite DB)]
        SQLite --> ConvHistory[conversation_history]
        SQLite --> RAGDocs[rag_documents]
    end

    style FastAPI fill:#0a9,stroke:#333,stroke-width:3px
    style SQLite fill:#9cf,stroke:#333,stroke-width:2px
```

## LLM Manager Fallback

```mermaid
graph LR
    Request[LLM Request] --> Manager[LLM Manager]

    Manager --> Preferred{Preferred Provider?}
    Preferred -->|Yes| TryPreferred[Try Preferred]
    Preferred -->|No| Primary[Try Primary]

    TryPreferred --> Check1{Success?}
    Check1 -->|Yes| Return1[Return Response]
    Check1 -->|No| Primary

    Primary --> Check2{Success?}
    Check2 -->|Yes| Return2[Return Response]
    Check2 -->|No| Secondary[Try Secondary]

    Secondary --> Check3{Success?}
    Check3 -->|Yes| Return3[Return Response]
    Check3 -->|No| Tertiary[Try Tertiary]

    Tertiary --> Check4{Success?}
    Check4 -->|Yes| Return4[Return Response]
    Check4 -->|No| Error[❌ All Providers Failed]

    style Manager fill:#bbf,stroke:#333,stroke-width:3px
    style Error fill:#f66,stroke:#333,stroke-width:2px
    style Return1 fill:#6f6,stroke:#333,stroke-width:2px
    style Return2 fill:#6f6,stroke:#333,stroke-width:2px
    style Return3 fill:#6f6,stroke:#333,stroke-width:2px
    style Return4 fill:#6f6,stroke:#333,stroke-width:2px
```

## Workflow Execution Modes

### Sequential Mode

```mermaid
graph LR
    Start[Start] --> TaskA[Task A]
    TaskA --> TaskB[Task B]
    TaskB --> TaskC[Task C]
    TaskC --> End[End]

    style TaskA fill:#9cf
    style TaskB fill:#9cf
    style TaskC fill:#9cf
```

### Parallel Mode

```mermaid
graph TB
    Start[Start] --> Split{Split}
    Split --> TaskA[Task A]
    Split --> TaskB[Task B]
    Split --> TaskC[Task C]
    TaskA --> Join{Join}
    TaskB --> Join
    TaskC --> Join
    Join --> End[End]

    style TaskA fill:#9cf
    style TaskB fill:#9cf
    style TaskC fill:#9cf
```

### DAG Mode

```mermaid
graph TB
    Start[Start] --> TaskA[Task A]
    TaskA --> TaskB[Task B]
    TaskA --> TaskC[Task C]
    TaskB --> TaskD[Task D]
    TaskC --> TaskD
    TaskD --> End[End]

    style TaskA fill:#9cf
    style TaskB fill:#9cf
    style TaskC fill:#9cf
    style TaskD fill:#9cf
```

## Caching Strategy

```mermaid
graph TB
    Request[Request] --> CacheCheck{Cache Hit?}

    CacheCheck -->|Yes| ValidCheck{Valid TTL?}
    CacheCheck -->|No| Process

    ValidCheck -->|Yes| Return1[Return Cached]
    ValidCheck -->|No| Invalidate[Invalidate Cache]
    Invalidate --> Process

    Process[Process Request] --> Result[Generate Result]
    Result --> Store[Store in Cache]
    Store --> Return2[Return Result]

    subgraph Cache Types
        RouterCache[Router Cache<br/>TTL: 3600s]
        VectorCache[Vector Search Cache<br/>TTL: 3600s<br/>Max: 1000 items]
        LRUCache[LRU Cache<br/>Evict: Least Recently Used]
    end

    style Return1 fill:#6f6,stroke:#333,stroke-width:2px
    style Return2 fill:#9cf,stroke:#333,stroke-width:2px
```

## Data Flow - Complete Query

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant R as Router
    participant A as Agent
    participant T as Tools
    participant L as LLM
    participant D as Database

    U->>W: Submit Query
    W->>R: Route Query

    R->>R: Keyword Classification
    alt confidence >= 0.6
        R->>A: Direct to Agent
    else confidence < 0.6
        R->>L: LLM Classification
        L-->>R: Task Type
        R->>A: Route to Agent
    end

    A->>T: Use Tools
    T-->>A: Tool Results

    A->>L: Generate Response
    L-->>A: LLM Response

    A-->>W: Final Result
    W->>D: Save to History
    W-->>U: Display Result
```

## Module Dependencies

```mermaid
graph TB
    subgraph Core
        Config[Config]
        Logger[Logger]
        Utils[Utils]
    end

    subgraph LLM Layer
        LLMManager[LLM Manager]
        OpenAIClient[OpenAI Client]
        OllamaClient[Ollama Client]
    end

    subgraph Routing Layer
        BaseRouter[Base Router]
        KeywordRouter[Keyword Router]
        LLMRouter[LLM Router]
        HybridRouter[Hybrid Router]
        RouterFactory[Router Factory]
    end

    subgraph Agent Layer
        ResearchAgent[Research Agent]
        CodeAgent[Code Agent]
        ChatAgent[Chat Agent]
        RAGAgent[RAG Agent]
    end

    subgraph Tools Layer
        SearchTool[Search Tool]
        ScraperTool[Scraper Tool]
        CodeExecutor[Code Executor]
        VectorStore[Vector Store]
        DomainTools[Domain Tools]
    end

    subgraph Workflow Layer
        WorkflowEngine[Workflow Engine]
        TaskDecomposer[Task Decomposer]
        ResultAggregator[Result Aggregator]
    end

    subgraph Web Layer
        FastAPIApp[FastAPI App]
        Routers[Routers]
        Database[Database]
        Middleware[Middleware]
    end

    Config --> LLMManager
    Config --> BaseRouter
    Logger --> LLMManager
    Logger --> BaseRouter

    LLMManager --> OpenAIClient
    LLMManager --> OllamaClient

    BaseRouter --> KeywordRouter
    BaseRouter --> LLMRouter
    BaseRouter --> HybridRouter
    RouterFactory --> KeywordRouter
    RouterFactory --> LLMRouter
    RouterFactory --> HybridRouter

    LLMRouter --> LLMManager
    HybridRouter --> KeywordRouter
    HybridRouter --> LLMRouter

    ResearchAgent --> LLMManager
    ResearchAgent --> SearchTool
    ResearchAgent --> ScraperTool
    CodeAgent --> LLMManager
    CodeAgent --> CodeExecutor
    ChatAgent --> LLMManager
    RAGAgent --> LLMManager
    RAGAgent --> VectorStore

    WorkflowEngine --> TaskDecomposer
    WorkflowEngine --> ResultAggregator
    TaskDecomposer --> LLMManager
    ResultAggregator --> LLMManager

    FastAPIApp --> Routers
    FastAPIApp --> Middleware
    Routers --> RouterFactory
    Routers --> ResearchAgent
    Routers --> CodeAgent
    Routers --> ChatAgent
    Routers --> RAGAgent
    Routers --> DomainTools
    Routers --> WorkflowEngine
    Routers --> Database

    style Config fill:#fcc
    style LLMManager fill:#bbf
    style HybridRouter fill:#f9f
    style FastAPIApp fill:#0a9
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Internet
        Users[Users]
    end

    subgraph Load Balancer
        LB[Nginx / AWS ALB]
    end

    subgraph Application Layer
        App1[FastAPI Instance 1]
        App2[FastAPI Instance 2]
        App3[FastAPI Instance 3]
        App4[FastAPI Instance 4]
    end

    subgraph Caching Layer
        Redis[(Redis Cache)]
    end

    subgraph Database Layer
        PostgreSQL[(PostgreSQL)]
        ChromaDB[(ChromaDB)]
    end

    subgraph External Services
        OpenAI[OpenAI API]
        SerpAPI[SerpAPI]
        Weather[Weather API]
        Finance[Finance API]
    end

    Users --> LB
    LB --> App1
    LB --> App2
    LB --> App3
    LB --> App4

    App1 --> Redis
    App2 --> Redis
    App3 --> Redis
    App4 --> Redis

    App1 --> PostgreSQL
    App2 --> PostgreSQL
    App3 --> PostgreSQL
    App4 --> PostgreSQL

    App1 --> ChromaDB
    App2 --> ChromaDB
    App3 --> ChromaDB
    App4 --> ChromaDB

    App1 --> OpenAI
    App1 --> SerpAPI
    App1 --> Weather
    App1 --> Finance

    style LB fill:#0a9,stroke:#333,stroke-width:3px
    style Redis fill:#f66,stroke:#333,stroke-width:2px
    style PostgreSQL fill:#9cf,stroke:#333,stroke-width:2px
    style ChromaDB fill:#9f9,stroke:#333,stroke-width:2px
```
