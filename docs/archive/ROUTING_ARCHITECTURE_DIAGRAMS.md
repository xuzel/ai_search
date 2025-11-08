# AI Search Engine - Routing Architecture Diagrams

## 1. High-Level Query Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER SUBMITS QUERY                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Unified Query Endpoint                            │
│                   (src/web/routers/query.py:111)                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ unified_query(request, query)                              │   │
│  │ 1. Initialize agents (lazy, one-time)                      │   │
│  │ 2. Call Router.classify_hybrid()                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                HYBRID CLASSIFICATION ROUTING                         │
│           (src/router.py: classify_hybrid())                         │
│                                                                      │
│  ┌────────────────────────────┐   ┌──────────────────────────┐     │
│  │ STEP 1: Keyword-Based      │   │ STEP 2: Check Confidence │     │
│  │ classify()                 │──>│ >= 0.6?                  │     │
│  │ (Fast, Deterministic)      │   └──────┬───────────────────┘     │
│  └────────────────────────────┘          │                         │
│                                    ┌─────┴──────┐                   │
│                                 YES│             │NO                │
│                                    ▼             ▼                  │
│                            Use Keyword    Try LLM                   │
│                            Result         classify()                │
│                                    │             │                  │
│                                    └─────┬───────┘                  │
│                                          ▼                          │
│                          Return (TaskType, confidence, method)       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌───────────────┐ ┌──────────┐ ┌──────────┐
        │ Route to Agent│ │or Tool   │ │or Tool   │
        └───────────────┘ └──────────┘ └──────────┘
                │
    ┌───────────┼───────────────────────────────┐
    │           │                               │
    ▼           ▼              ▼                ▼
┌─────────┐ ┌─────────┐  ┌──────────┐  ┌──────────────┐
│RESEARCH │ │  CODE   │  │  CHAT    │  │ DOMAIN_*     │
│ Agent   │ │ Agent   │  │ Agent    │  │ Tools        │
└────┬────┘ └────┬────┘  └────┬─────┘  └──────┬───────┘
     │           │            │               │
     └───────────┴────────────┴───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Post-Processing:           │
        │ - Markdown conversion      │
        │ - Credibility scoring      │
        │ - Source reranking         │
        └────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Save to Database:          │
        │ - Conversation history     │
        │ - Metadata (type, conf.)   │
        │ - Sources (if any)         │
        └────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Render Result Template     │
        │ (result_{mode}.html)       │
        └────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ Return HTML to Browser     │
        └────────────────────────────┘
```

---

## 2. Router Classification Decision Tree

```
                         ┌─────────────────┐
                         │  Query Received │
                         └────────┬────────┘
                                  │
                   ┌──────────────────────────────┐
                   │ Check Domain-Specific First  │
                   │ (Highest Priority)           │
                   └──────────────────────────────┘
                      │ │ │ │
        ┌─────────────┘ │ │ │ └─────────────────┐
        ▼               ▼ ▼ ▼                   ▼
    WEATHER       FINANCE  ROUTING RAG        CODE Keywords?
      Match         Match   Match   Match        │
        │             │       │       │          ▼
        └─────────────┴───────┴───────┴──────►(Check Priority 2)
                                                │
                                ┌───────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │ CODE Keywords?  │
                        │ "calculate",    │
                        │ "solve", etc.   │
                        └────────┬────────┘
                                 │
                        ┌────────┴────────┐
                     YES│                 │NO
                        ▼                 ▼
                    CODE         Math Patterns?
                    (Return)      (+, -, *, /, sin, sqrt, etc.)
                                         │
                               ┌─────────┴─────────┐
                            YES│                   │NO
                               ▼                   ▼
                           CODE          Unit Conversion?
                           (Return)       (hours in day, etc.)
                                                   │
                                        ┌──────────┴──────────┐
                                     YES│                     │NO
                                        ▼                     ▼
                                    CODE          Calculation Indicators?
                                    (Return)      (how many, 多少, etc.)
                                                          │
                                              ┌───────────┴───────────┐
                                           YES│                       │NO
                                              ▼                       ▼
                                          CODE          RESEARCH Keywords?
                                          (Return)      (search, find, etc.)
                                                                │
                                              ┌─────────────────┴────────────┐
                                           YES│                              │NO
                                              ▼                              ▼
                                          RESEARCH         Question Mark?
                                          (Return)              │
                                                    ┌───────────┴───────────┐
                                                 YES│                       │NO
                                                    ▼                       ▼
                                                RESEARCH                  CHAT
                                                (Return)                (Return)
```

---

## 3. Keyword-Based vs LLM-Based Classification

```
                    Query Input
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
    ┌──────────────┐            ┌──────────────────┐
    │   KEYWORD    │            │   LLM-BASED      │
    │   METHOD     │            │   METHOD         │
    └──┬───────────┘            └────┬─────────────┘
       │                             │
       │ Speed: VERY FAST            │ Speed: MODERATE
       │ Accuracy: GOOD (explicit)   │ Accuracy: EXCELLENT
       │ Cost: FREE                  │ Cost: LLM API calls
       │ Overhead: 0 ms              │ Overhead: 100-500 ms
       │                             │
       │ Returns:                    │ Returns:
       │ - TaskType                  │ - TaskType
       │ - Confidence (0.5-1.0)      │ - Confidence (0.0-1.0)
       │                             │
       └───────────────┬─────────────┘
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
        Use if High      Use if Low
        Confidence       Confidence
        (>= 0.6)         (< 0.6)
              │                 │
              └────────┬────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Final Classification │
            │ (Task Type + Score)  │
            └─────────────────────┘
```

---

## 4. Task Type to Agent/Tool Mapping

```
┌──────────────────────────────────────────────────────────────────────┐
│                    TASK TYPE ROUTING TABLE                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ RESEARCH                                                             │
│ ├─ Agent: ResearchAgent                                             │
│ ├─ Tools: SearchTool, ScraperTool                                   │
│ ├─ Handler: handle_research()                                       │
│ ├─ Output: {summary, sources, plan}                                 │
│ └─ Post-processing: Markdown, Reranking, Credibility Scoring       │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ CODE                                                                 │
│ ├─ Agent: CodeAgent                                                 │
│ ├─ Tools: CodeExecutor                                              │
│ ├─ Handler: handle_code()                                           │
│ ├─ Output: {code, output, error, explanation, success}             │
│ └─ Post-processing: Code Highlighting, Error Analysis               │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ CHAT                                                                 │
│ ├─ Agent: ChatAgent                                                 │
│ ├─ Tools: None (LLM only)                                           │
│ ├─ Handler: handle_chat()                                           │
│ ├─ Output: {message, answer}                                        │
│ └─ Post-processing: Markdown Conversion                             │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ DOMAIN_WEATHER                                                       │
│ ├─ Agent: None (Direct Tool)                                        │
│ ├─ Tools: WeatherTool                                               │
│ ├─ Handler: handle_weather()                                        │
│ ├─ Output: {summary, sources}                                       │
│ └─ Post-processing: Markdown Conversion                             │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ DOMAIN_FINANCE                                                       │
│ ├─ Agent: None (Direct Tool)                                        │
│ ├─ Tools: FinanceTool                                               │
│ ├─ Handler: handle_finance()                                        │
│ ├─ Output: {summary, sources}                                       │
│ └─ Post-processing: Markdown Conversion                             │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ DOMAIN_ROUTING                                                       │
│ ├─ Agent: None (Direct Tool)                                        │
│ ├─ Tools: RoutingTool                                               │
│ ├─ Handler: handle_routing()                                        │
│ ├─ Output: {summary, sources}                                       │
│ └─ Post-processing: Markdown Conversion                             │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ RAG                                                                  │
│ ├─ Agent: RAGAgent                                                  │
│ ├─ Tools: VectorStore, Reranker (optional)                          │
│ ├─ Handler: handle_rag()                                            │
│ ├─ Output: {answer, sources, relevance}                             │
│ └─ Post-processing: Markdown Conversion                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. LLM Provider Fallback Chain

```
                     Classification Request
                              │
                              ▼
                   ┌─────────────────────────┐
                   │ Start with Primary      │
                   │ Provider (DashScope)    │
                   └────────────┬────────────┘
                                │
                     ┌──────────┴──────────┐
                    YES│                   │NO
                        ▼                   ▼
                   Success?         ┌──────────────┐
                     │              │ DashScope    │
                     │              │ Available?   │
                     │              └─────┬────────┘
                     │                    │
                     │           ┌────────┴────────┐
                     │          NO│                 │YES
                     │           ▼                   ▼
                     │    Try Next     Log Warning &
                     │    Provider     Continue
                     │      │                │
                     │      ▼                ▼
                     │   (OpenAI,      Log Warning &
                     │    DeepSeek,    Try Next
                     │    Ollama)      Provider
                     │      │
                     │      ▼
                     │  All Failed?
                     │      │
                     │  ┌───┴────┐
                     │ NO│        │YES
                     │   ▼        ▼
                     │ Return  Fallback to
                     │ Result  Keyword
                     │          Routing
                     │
                     └────┬─────┘
                          ▼
                   Final Classification
```

---

## 6. Hybrid Classification Algorithm

```
ALGORITHM: classify_hybrid(query, llm_manager, use_llm_threshold=0.6)

INPUT: query (string), llm_manager (LLMManager), threshold (float)
OUTPUT: (TaskType, confidence, method_used)

BEGIN:
    ┌─────────────────────────────────────────┐
    │ STEP 1: Fast Keyword Classification     │
    │ task_type := classify(query)            │
    │ confidence := get_confidence(query, *)  │
    └─────────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────┐
    │ STEP 2: Check Confidence Threshold      │
    │ IF confidence >= use_llm_threshold:     │
    │     RETURN (task_type, conf, "keyword") │
    │ ELSE:                                   │
    │     GOTO STEP 3                         │
    └─────────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────┐
    │ STEP 3: LLM Not Available?              │
    │ IF llm_manager is None:                 │
    │     RETURN (task_type, conf, "keyword") │
    │ ELSE:                                   │
    │     GOTO STEP 4                         │
    └─────────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────┐
    │ STEP 4: Call LLM Classification         │
    │ TRY:                                    │
    │   (task_type, confidence) :=            │
    │     await classify_with_llm(query, *)   │
    │   RETURN (task_type, conf, "llm")       │
    │ EXCEPT:                                 │
    │   GOTO STEP 5                           │
    └─────────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────┐
    │ STEP 5: LLM Failed, Use Keyword Result  │
    │ RETURN (task_type, conf, "keyword_fb")  │
    └─────────────────────────────────────────┘

END

TIME COMPLEXITY: O(1) for keyword path, O(n) for LLM path
SPACE COMPLEXITY: O(1)
```

---

## 7. Confidence Scoring Breakdown

```
┌────────────────────────────────────────────────────────────────────┐
│                  CONFIDENCE SCORE CALCULATION                      │
└────────────────────────────────────────────────────────────────────┘

FOR CODE CLASSIFICATION:
┌──────────────────────────────────────────────────────────────────┐
│ Base Score: 0.50                                                 │
│                                                                  │
│ + 0.25 × (# of explicit CODE keywords found)                    │
│   Keywords: calculate, compute, solve, plot, code, etc.         │
│   Max contribution: 0.25                                         │
│                                                                  │
│ + 0.15 × (# of math patterns found)                             │
│   Patterns: +, -, *, /, sin(), sqrt(), ∑, ∫, etc.              │
│   Max contribution: 0.15                                         │
│                                                                  │
│ + 0.20 × (# of unit conversion patterns)                        │
│   Patterns: "hours in day", "miles to km", etc.                 │
│   Max contribution: 0.20                                         │
│                                                                  │
│ + 0.10 × (# of calculation indicators)                          │
│   Keywords: how many, 多少, 几个, convert, etc.                │
│   Max contribution: 0.10                                         │
│                                                                  │
│ = Total (capped at 1.0)                                         │
└──────────────────────────────────────────────────────────────────┘

FOR RESEARCH CLASSIFICATION:
┌──────────────────────────────────────────────────────────────────┐
│ Base Score: 0.50                                                 │
│                                                                  │
│ + 0.25 × (# of RESEARCH keywords found)                         │
│   Keywords: search, find, explain, tell, what, etc.             │
│   Max contribution: 0.25                                         │
│                                                                  │
│ + 0.15 if ends with question mark (? or ？)                     │
│   Max contribution: 0.15                                         │
│                                                                  │
│ = Total (capped at 1.0)                                         │
└──────────────────────────────────────────────────────────────────┘

INTERPRETATION:
┌─────────────────────────────────────────────────────────────────┐
│ 0.85 - 1.00  │ HIGH       │ Very confident, clear task type     │
│ 0.65 - 0.84  │ MEDIUM     │ Fairly confident, some alternatives │
│ 0.50 - 0.64  │ MEDIUM-LOW │ Borderline, may need LLM            │
│ < 0.50       │ LOW        │ Ambiguous, likely needs LLM         │
└─────────────────────────────────────────────────────────────────┘

THRESHOLD (use_llm_threshold):
   Keyword confidence >= 0.60  → Use keyword result (fast)
   Keyword confidence < 0.60   → Use LLM (accurate but slower)
```

---

## 8. Proposed Multi-Intent Workflow Routing

```
(This is a future enhancement)

Query: "Find Apple stock price and convert to multiple currencies"

                         Query Input
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
         ▼                                       ▼
    ┌────────────┐                    ┌──────────────────┐
    │ Extract    │                    │ Detect Multiple  │
    │ Keywords   │                    │ Intents          │
    └────────────┘                    └──────────────────┘
         │                                       │
         │ Primary: "Apple stock price"         │
         │ Secondary: "convert currencies"      │
         │                                       │
         └───────────────────┬───────────────────┘
                             │
                             ▼
                   ┌──────────────────────┐
                   │ Classify Primary:    │
                   │ DOMAIN_FINANCE       │
                   └──────────────────────┘
                             │
                             ▼
                   ┌──────────────────────┐
                   │ Classify Secondary:  │
                   │ CODE                 │
                   └──────────────────────┘
                             │
                             ▼
                   ┌──────────────────────┐
                   │ Create Workflow:     │
                   │ 1. FinanceTool       │
                   │    → {price: 150}    │
                   │ 2. CodeAgent         │
                   │    → convert(150 USD)│
                   └──────────────────────┘
                             │
                             ▼
                   ┌──────────────────────┐
                   │ Execute in Sequence  │
                   │ (Sequential Workflow)│
                   └──────────────────────┘
                             │
                             ▼
                   ┌──────────────────────┐
                   │ Merge Results        │
                   │ Stock info + Rates   │
                   └──────────────────────┘
```

---

## 9. Data Flow: End-to-End

```
                    ┌─────────────────────────────────────────┐
                    │   1. USER INTERFACE (Web Browser)       │
                    │   - Text input: "Calculate 2^10"        │
                    │   - Submits POST to /query              │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │   2. FASTAPI ENDPOINT           │
                    │   - Receives form data          │
                    │   - Initializes agents          │
                    │   - Calls Router.classify()     │
                    └────────────────┬────────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────┐
        │                                                      │
        ▼                                                      ▼
┌──────────────────────┐                         ┌────────────────────┐
│ 3A. KEYWORD-BASED    │                         │ 3B. LLM-BASED      │
│ - Matches CODE       │                         │ - Sends prompt to  │
│   keywords           │                         │   LLM API          │
│ - Returns CODE       │                         │ - Parses JSON resp │
│ - Confidence: 0.85   │                         │ - Returns CODE     │
└──────────────────────┘                         │ - Confidence: 0.92 │
        │                                        └────────────────────┘
        │                    (confidence >= 0.6)
        └────────────────────┬──────────────────┘
                             │
                    ┌────────▼───────────┐
                    │ 4. ROUTE TO AGENT  │
                    │ CodeAgent.solve()  │
                    └────────┬───────────┘
                             │
            ┌────────────────┴──────────────────┐
            │                                   │
            ▼                                   ▼
    ┌───────────────────┐           ┌──────────────────┐
    │ 5A. GENERATE CODE │           │ 6. VALIDATE CODE │
    │ - LLM generates:  │           │ - Check imports  │
    │   import math     │           │ - Check patterns │
    │   print(2**10)    │           │ - Status: VALID  │
    └───────────────────┘           └──────────────────┘
                                            │
                                            ▼
                                    ┌──────────────────┐
                                    │ 7. EXECUTE CODE  │
                                    │ - Run sandbox    │
                                    │ - Output: "1024" │
                                    └────────┬─────────┘
                                             │
                    ┌────────────────────────┴────────────────────┐
                    │                                             │
                    ▼                                             ▼
        ┌─────────────────────┐                   ┌──────────────────────┐
        │ 8. EXPLAIN RESULTS  │                   │ 9. POST-PROCESS      │
        │ "2^10 equals 1024"  │                   │ - Markdown to HTML   │
        └─────────────────────┘                   │ - Add syntax colors  │
                    │                             └──────────────────────┘
                    │                                     │
                    └─────────────┬─────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ 10. SAVE TO DATABASE       │
                    │ - Mode: "code"             │
                    │ - Query: "Calculate 2^10"  │
                    │ - Response: "1024"         │
                    │ - Metadata: {type, conf}   │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ 11. RENDER TEMPLATE        │
                    │ - Load result_code.html    │
                    │ - Pass: query, result,     │
                    │   confidence, sources      │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ 12. RETURN HTML TO BROWSER │
                    │ - Display in UI            │
                    │ - Show explanation        │
                    │ - Show code + output      │
                    └────────────────────────────┘
```

---

## 10. Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         REQUEST HANDLER                              │
│                     (src/web/routers/query.py)                       │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌──────────────┐  ┌────────────────┐
│   ROUTER      │  │ LLM MANAGER  │  │ AGENTS         │
│ (router.py)   │  │ (manager.py) │  │ (agents/*.py)  │
├───────────────┤  ├──────────────┤  ├────────────────┤
│ classify()    │  │ complete()   │  │ ResearchAgent  │
│ classify_llm()│  │ providers    │  │ CodeAgent      │
│ classify_*()  │  │ fallback     │  │ ChatAgent      │
└───────┬───────┘  └──────────────┘  └────────┬───────┘
        │                                      │
        │ calls classify_with_llm()            │
        │ ┌─────────────────────────────────┐  │
        │ │ Sends prompt to LLM             │  │
        │ │ Parses JSON response            │  │
        │ │ Returns (TaskType, confidence)  │  │
        │ └─────────────────────────────────┘  │
        │                                      │
        └──────────────┬───────────────────────┘
                       │
            ┌──────────┴───────────┬──────────────┬───────────┐
            │                      │              │           │
            ▼                      ▼              ▼           ▼
     ┌─────────────┐      ┌────────────┐  ┌────────────┐ ┌─────────┐
     │ TOOLS       │      │ DATABASE   │  │ TEMPLATES  │ │ LLM API │
     ├─────────────┤      ├────────────┤  ├────────────┤ ├─────────┤
     │SearchTool   │      │ save_conv()│  │ result_*   │ │OpenAI   │
     │CodeExecutor │      │ get_history│  │ .html      │ │DashScope│
     │ScraperTool  │      │            │  │            │ │DeepSeek │
     │WeatherTool  │      │            │  │            │ │Ollama   │
     │FinanceTool  │      │            │  │            │ │Local    │
     │RoutingTool  │      │            │  │            │ │         │
     │ etc.        │      │            │  │            │ │         │
     └─────────────┘      └────────────┘  └────────────┘ └─────────┘
```

---

## 11. Current Pain Points Matrix

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ROUTING SYSTEM PAIN POINTS                        │
├──────────────────┬──────────────────┬─────────────────┬──────────────┤
│ PAIN POINT       │ CURRENT IMPACT   │ AFFECTED AREAS  │ WORKAROUND   │
├──────────────────┼──────────────────┼─────────────────┼──────────────┤
│                  │                  │                 │              │
│ Ambiguous Queries│ HIGH             │ RESEARCH vs CHAT│ Use LLM when │
│ "What's the      │ Misclassification│ WEATHER vs CODE │ confidence   │
│ weather?"        │ rate: ~15%       │                 │ < 0.6        │
│                  │                  │                 │              │
├──────────────────┼──────────────────┼─────────────────┼──────────────┤
│                  │                  │                 │              │
│ Multi-Intent     │ MEDIUM           │ Query execution │ Only route   │
│ Queries          │ Can only handle  │ Workflow support│ primary task │
│ "Find price and  │ primary task     │                 │              │
│ calculate tax"   │                  │                 │              │
│                  │                  │                 │              │
├──────────────────┼──────────────────┼─────────────────┼──────────────┤
│                  │                  │                 │              │
│ Context Loss     │ LOW              │ Conversation    │ Stateless    │
│ Sequential       │ Each query       │ Sequential      │ routing,     │
│ queries lose     │ classified       │ follow-up qs.   │ no history   │
│ context          │ independently    │                 │ awareness    │
│                  │                  │                 │              │
├──────────────────┼──────────────────┼─────────────────┼──────────────┤
│                  │                  │                 │              │
│ LLM Latency      │ MEDIUM           │ User perception │ Hybrid       │
│ Classification   │ 100-500ms added  │ Response time   │ approach     │
│ slower than      │ per query        │                 │ minimizes    │
│ keywords         │                  │                 │ LLM usage    │
│                  │                  │                 │              │
├──────────────────┼──────────────────┼─────────────────┼──────────────┤
│                  │                  │                 │              │
│ No Tool Fallback │ LOW              │ Tool failures   │ Restart      │
│ If tool fails,   │ Rare in practice │ Error handling  │ request or   │
│ can't try        │ but critical     │                 │ manual rework│
│ alternative      │ when it happens  │                 │              │
│                  │                  │                 │              │
└──────────────────┴──────────────────┴─────────────────┴──────────────┘
```

