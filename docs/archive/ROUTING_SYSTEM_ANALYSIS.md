# AI Search Engine - Routing System Analysis

## Executive Summary

The current routing system is a **hybrid keyword + LLM-based classifier** that intelligently routes user queries to specialized agents (Research, Code, Chat) and domain-specific tools (Weather, Finance, Routing, RAG). This analysis examines the architecture, identifies pain points, and provides recommendations for optimizing to LLM-based routing with advanced prompt engineering.

---

## 1. Current Architecture Overview

### 1.1 Router Class (`src/router.py`)

The `Router` is the central routing component with three classification methods:

#### A. **Keyword-Based Classification** (`Router.classify()`)
- **Speed**: Very fast, no LLM calls
- **Accuracy**: Good for explicit keywords, limited for ambiguous queries
- **Priority Order** (highest to lowest):
  1. Domain-specific queries (Weather, Finance, Routing, RAG)
  2. CODE keywords ("calculate", "solve", "plot", "code", etc.)
  3. Mathematical patterns (operators: `+-*/^`, functions: `sin()`, `sqrt()`)
  4. Unit conversion patterns (e.g., "hours in a week")
  5. Calculation indicators ("how many", "多少")
  6. RESEARCH keywords ("search", "find", "explain", etc.)
  7. Question marks (lowest priority)

**Task Types Defined** (in `TaskType` enum):
```python
RESEARCH = "research"          # Web search needed
CODE = "code"                  # Code execution needed
CHAT = "chat"                  # General conversation
RAG = "rag"                    # Document Q&A
DOMAIN_WEATHER = "domain_weather"
DOMAIN_FINANCE = "domain_finance"
DOMAIN_ROUTING = "domain_routing"
```

#### B. **LLM-Based Classification** (`Router.classify_with_llm()`)
- **Speed**: Slower (requires LLM inference)
- **Accuracy**: Higher for ambiguous, complex, or multilingual queries
- **Method**: Uses a carefully crafted classification prompt in Chinese/English
- **Returns**: `(TaskType, confidence_score)`
- **Fallback**: Reverts to keyword classification if LLM fails

#### C. **Hybrid Classification** (`Router.classify_hybrid()`) - RECOMMENDED
- **Strategy**: Combines keyword (fast) + LLM (accurate)
- **Logic**:
  1. Try keyword-based classification first
  2. If confidence >= 0.6 (threshold), use keyword result
  3. If confidence < 0.6, use LLM for higher accuracy
  4. If LLM unavailable, fallback to keyword result
- **Returns**: `(TaskType, confidence_score, method_used)`

### 1.2 Routing Integration Points

#### Web API (`src/web/routers/query.py`)
```
User Query
    ↓
unified_query() endpoint
    ↓
Router.classify_hybrid()
    ↓
Task Type Determined
    ↓
Route to Agent:
├─ RESEARCH → handle_research() → ResearchAgent
├─ CODE → handle_code() → CodeAgent
├─ CHAT → handle_chat() → ChatAgent
├─ DOMAIN_WEATHER → handle_weather() → WeatherTool
├─ DOMAIN_FINANCE → handle_finance() → FinanceTool
├─ DOMAIN_ROUTING → handle_routing() → RoutingTool
└─ RAG → (in future)
    ↓
Database: save_conversation() with metadata
    ↓
Render Result Template
```

#### CLI (`src/main.py`)
- `ask --auto` command uses `Router.classify_hybrid()` for auto-routing
- `--llm/--no-llm` flag to control LLM usage
- `--verbose` shows detection confidence and method

### 1.3 Agent Architecture

All agents follow a similar pattern:

**ResearchAgent** (`src/agents/research_agent.py`)
```python
research(query) → {
    "query": str,
    "plan": dict,              # Search strategy
    "sources": list,           # URLs with title, snippet
    "summary": str             # LLM-synthesized answer
}
```

**CodeAgent** (`src/agents/code_agent.py`)
```python
solve(problem) → {
    "problem": str,
    "code": str,               # Generated Python code
    "output": str,             # Code execution output
    "error": str,              # Error if execution failed
    "explanation": str,        # LLM explanation
    "success": bool
}
```

**ChatAgent** (`src/agents/chat_agent.py`)
```python
chat(message) → str            # Direct LLM response
```

### 1.4 Tool Selection

**Static Tool Selection** (based on TaskType):
- `SearchTool` → ResearchAgent
- `CodeExecutor` → CodeAgent
- `ScraperTool` → ResearchAgent
- `WeatherTool` → DOMAIN_WEATHER handler
- `FinanceTool` → DOMAIN_FINANCE handler
- `RoutingTool` → DOMAIN_ROUTING handler

**Optional Tools** (applied post-routing):
- `HybridReranker` / `Reranker` → Re-ranks research results by relevance
- `CredibilityScorer` → Scores source credibility (URL patterns, etc.)

---

## 2. Current Limitations & Pain Points

### 2.1 Keyword-Based Classification Issues

| Issue | Impact | Example |
|-------|--------|---------|
| **Ambiguous queries** | Misclassification | "How is the weather today?" contains "weather" + "how" (calculation indicator) |
| **Multilingual nuances** | Failed detection | Chinese questions with different question marks or phrasing |
| **Context-dependent queries** | False positives | "Convert my feelings" → mistaken for unit conversion |
| **Multi-intent queries** | Single classification only | "Find the weather in NYC and convert it to Fahrenheit" |
| **Domain specificity** | Hard-coded keywords | Finance queries need current market context, not just keyword matching |
| **Edge cases** | Incorrect routing | "What is the price?" (ambiguous: asking for code/finance/general) |

### 2.2 LLM Classification Limitations

| Issue | Impact | Mitigation |
|-------|--------|-----------|
| **Latency** | Slower response | Hybrid approach minimizes LLM usage |
| **Token usage** | Cost inefficiency | Concise prompts + fallback to keyword |
| **JSON parsing fragility** | Potential failures | Regex extraction helps but not foolproof |
| **Instruction ambiguity** | Inconsistent results | Needs more detailed prompt engineering |
| **Context limitations** | No conversation history | Treats each query independently |

### 2.3 Tool Selection Limitations

1. **No dynamic tool selection** - Tools are statically mapped to task types
2. **No multi-tool orchestration** - Can't use multiple tools for single query
3. **No tool capability awareness** - Router doesn't know what tools can do
4. **No fallback mechanism** - If tool fails, no alternative selection

---

## 3. LLM Classification Deep Dive

### 3.1 Current Prompt (in `Router.classify_with_llm()`)

**Strengths:**
- Bilingual (English + Chinese)
- Clear category definitions with examples
- Explicit priority rules at bottom
- JSON output format
- Lower temperature (0.3) for consistency

**Weaknesses:**
- Generic examples don't cover edge cases
- No explanation of confidence scoring
- Single-turn prompt (no conversation context)
- Prompt is in Chinese, LLMs trained on English may perform differently
- No few-shot examples for complex cases

### 3.2 LLM Manager Architecture (`src/llm/manager.py`)

**Provider Support:**
- OpenAI (gpt-3.5-turbo, gpt-4, etc.)
- Aliyun DashScope (Qwen models)
- DeepSeek
- Ollama (local)
- OpenAI-compatible endpoints

**Fallback Strategy:**
1. Try preferred provider
2. Try primary provider (first initialized)
3. Try remaining providers in order
4. Raise error if all fail

**Configuration** (`src/utils/config.py`):
- Each provider has `enabled` flag
- Respects environment variables with `${VAR}` substitution
- Temperature configurable per provider

---

## 4. Data Flow Analysis

### 4.1 Query Lifecycle (Web UI)

```
1. USER SUBMITS QUERY
   ↓
2. /query endpoint (query.py:111)
   - Receives query via POST form
   - Calls initialize_agents() (lazy initialization)
   
3. CLASSIFICATION
   - Router.classify_hybrid(query, llm_manager)
   - Returns: (TaskType, confidence, method)
   - Logs: "Classified as {task_type} with confidence {confidence:.2f}"
   
4. AGENT EXECUTION (based on TaskType)
   - RESEARCH: handle_research() 
     * ResearchAgent.research(query)
     * Returns: {summary, sources, plan}
   
   - CODE: handle_code()
     * CodeAgent.solve(query)
     * Returns: {code, output, error, explanation, success}
   
   - CHAT: handle_chat()
     * ChatAgent.chat(query)
     * Returns: {message, answer}
   
   - DOMAIN_*: handle_weather() / handle_finance() / handle_routing()
     * Tool-specific handlers
     * Returns: {summary, sources}

5. POST-PROCESSING
   - Markdown conversion (research, chat, rag)
   - Credibility scoring (research sources)
   - Source reranking (if enabled)
   
6. DATABASE STORAGE
   - save_conversation(mode, query, response, metadata)
   - Metadata includes: task_type, confidence, sources
   
7. TEMPLATE RENDERING
   - Select template: f"components/result_{mode}.html"
   - Pass: request, query, result, task_type, confidence
```

### 4.2 Agent-Tool Coupling

**ResearchAgent** requires:
- `llm_manager` - for search plan generation & synthesis
- `search_tool` - for web search (SerpAPI)
- `scraper_tool` - for content extraction
- `config` - for parameters (max_queries, top_results, etc.)

**CodeAgent** requires:
- `llm_manager` - for code generation
- `code_executor` - for safe code execution
- `config` - for timeout, allowed imports, etc.

**ChatAgent** requires:
- `llm_manager` - for conversation

---

## 5. Prompt Engineering Opportunities

### 5.1 Classification Prompt Improvements

**Current Issues:**
- Prompt is static, doesn't adapt to query complexity
- No examples for edge cases (multi-intent, domain-specific jargon)
- Confidence scoring not explained
- No context about user's history or preferences

**Recommended Enhancements:**

1. **Few-Shot Learning**
   ```
   Classification Prompt (Improved):
   - Include 5-10 examples per category
   - Cover edge cases and ambiguous queries
   - Show reasoning for borderline cases
   ```

2. **Dynamic Prompt Adaptation**
   ```
   IF query contains {keyword1} AND {keyword2}:
       → Use specialized prompt for multi-intent detection
   IF query is very short (< 20 chars):
       → Use prompt for intent inference without keywords
   IF language is Chinese:
       → Use Chinese-optimized prompt
   IF language is English:
       → Use English-optimized prompt
   ```

3. **Confidence Scoring Guide**
   ```
   Confidence formula:
   - High (>0.8): Clear keywords + domain-specific context
   - Medium (0.5-0.8): Some keywords + possible alternatives
   - Low (<0.5): Ambiguous or missing context
   ```

4. **Multi-Label Classification Option**
   ```
   Instead of single TaskType, optionally return:
   {
       "primary_task_type": "RESEARCH",
       "secondary_task_types": ["CODE"],  # Optional
       "confidence": 0.75,
       "requires_multiple_steps": true
   }
   ```

### 5.2 Tool Selection Prompt Engineering

**New Approach: Tool-Aware Routing**

Instead of TaskType → Agent → Tools, use:

```
Query Classification + Tool Selection:

1. STEP 1: Understand Query Intent
   - What does user want to accomplish?
   - What information do they need?
   - What's the context?

2. STEP 2: Recommend Tool Chain
   - Which tools are needed? (Search, Code, Vision, RAG, etc.)
   - In what order?
   - With what parameters?

3. STEP 3: Select Agent Coordinator
   - Single-agent task? Use specialized agent
   - Multi-tool task? Use workflow/orchestration agent
```

**Example Prompt:**

```
You are a task router. Analyze the user query and recommend:
1. Required tools (search, code_execution, document_qa, weather, finance, vision, ocr)
2. Tool parameters (e.g., search_depth, code_type)
3. Orchestration needed (sequential, parallel, conditional)

Query: "{query}"

Respond in JSON:
{
    "primary_task": "RESEARCH|CODE|CHAT|WORKFLOW",
    "tools_needed": ["search", "scraper"],
    "parameters": {"search_depth": "medium", "top_k": 5},
    "orchestration": "sequential",
    "confidence": 0.9,
    "reasoning": "..."
}
```

---

## 6. Architecture Recommendations

### 6.1 Phase 1: Enhanced Prompt Engineering (Low Effort, High Impact)

**Improvements to current `Router.classify_with_llm()`:**

```python
# 1. Add few-shot examples to prompt
few_shot_examples = """
Examples:
- "How many hours in a day?" → CODE (calculation)
- "What's the weather today?" → DOMAIN_WEATHER (real-time data)
- "Explain machine learning" → RESEARCH (needs context)
- "Calculate 2^10" → CODE (explicit math)
- "Is AAPL stock up today?" → DOMAIN_FINANCE (market data)
- "Hi there" → CHAT (greeting)
"""

# 2. Improve confidence scoring explanation
confidence_guide = """
Confidence Scoring:
- HIGH (0.85-1.0): Clear keywords + unambiguous intent
- MEDIUM (0.65-0.85): Some indicators but could be alternative
- LOW (<0.65): Ambiguous or missing context
"""

# 3. Add language detection
language = detect_language(query)
prompt = (
    get_classification_prompt(language) +
    few_shot_examples +
    confidence_guide +
    f"\nQuery: {query}"
)
```

### 6.2 Phase 2: Multi-Intent & Orchestration (Medium Effort, High Impact)

**Add support for workflows:**

```python
class Router:
    @staticmethod
    async def classify_with_tools(
        query: str,
        llm_manager: LLMManager,
    ) -> dict:
        """
        Returns:
        {
            "primary_task": TaskType,
            "secondary_tasks": [TaskType],  # Optional
            "tools": [str],                 # Tool names
            "workflow": str,                # "sequential" | "parallel" | "conditional"
            "parameters": dict,             # Tool-specific params
            "confidence": float
        }
        """
```

**Example Workflow Orchestration:**

```
Query: "Find Apple stock price and convert it to different currencies"

Result:
{
    "primary_task": TaskType.DOMAIN_FINANCE,
    "secondary_tasks": [TaskType.CODE],
    "tools": ["finance_tool", "code_executor"],
    "workflow": "sequential",
    "parameters": {
        "finance_symbol": "AAPL",
        "currencies": ["EUR", "GBP", "JPY"],
        "code_task": "currency_conversion"
    }
}

Execution:
1. FinanceTool.get_stock_info("AAPL") → {price: 150.25}
2. CodeAgent.solve("Convert 150.25 USD to EUR, GBP, JPY") → {code, output}
```

### 6.3 Phase 3: Adaptive Routing (Higher Effort, Strategic Value)

**Learn from history:**

```python
class AdaptiveRouter:
    """
    Learns from user's historical queries to improve routing accuracy.
    
    - Track misclassifications (user corrections)
    - Learn user-specific preferences
    - Adjust confidence thresholds per category
    """
    
    async def classify_adaptive(
        self,
        query: str,
        user_id: str,
        llm_manager: LLMManager,
    ) -> tuple[TaskType, float]:
        """
        Routes considering:
        1. Query content
        2. User's history (past queries & corrections)
        3. Query similarity to past queries
        """
```

### 6.4 Phase 4: Context-Aware Routing (Advanced)

**Support conversation context:**

```python
class ContextualRouter:
    """
    Routes considering conversation history.
    
    Example:
    User: "Show me AAPL stock price"      → DOMAIN_FINANCE
    Assistant: [Shows price: $150]
    User: "Convert to EUR"                 → Understands context from history
    Route: CODE (currency conversion)
    
    Without context: Could be ambiguous
    With context: Clear task
    """
```

---

## 7. Detailed Component Analysis

### 7.1 Router Keywords & Patterns

**Current Keywords (by Category):**

| Category | Keywords | Language Support |
|----------|----------|------------------|
| RESEARCH | search, find, 查询, 搜索, explain, tell me, what is | EN, ZH |
| CODE | compute, calculate, solve, 计算, formula, algorithm | EN, ZH |
| WEATHER | weather, temperature, 天气, 温度, forecast | EN, ZH |
| FINANCE | stock, price, 股票, 股价, crypto, bitcoin | EN, ZH |
| ROUTING | route, direction, 路线, 导航, from-to pattern | EN, ZH |
| RAG | document, file, pdf, 文档, 文件 | EN, ZH |

**Math Patterns:**
- Operators: `+ - * / ^`
- Functions: `sin()`, `cos()`, `sqrt()`, `log()`
- Symbols: `∑ ∫ ∂ √ π ∞`
- Decimals: `\d+\.\d+` (float numbers)

**Unit Conversion Patterns:**
- Time: "hours in a day", "days in a week", "小时 in a day"
- Distance: "miles to kilometers", "meters to feet"
- Weight: "pounds to kilograms"

### 7.2 Confidence Scoring Logic

**Current Implementation** (`Router.get_confidence()`):

```python
score = 0.5  # Base score

# For CODE classification:
+ 0.25 per explicit CODE keyword match
+ 0.15 per math pattern match
+ 0.20 per unit conversion pattern match
+ 0.10 per calculation indicator match
→ Capped at 1.0

# For RESEARCH classification:
+ 0.25 per RESEARCH keyword match
+ 0.15 if ends with question mark
→ Capped at 1.0
```

**Issues:**
- Simple additive model (doesn't account for conflicts)
- No penalty for contradictory signals
- No context weighting (e.g., "current" weather > "historical" weather)
- No learning from past mistakes

### 7.3 LLM Provider Configuration

**Available Providers:**

```yaml
# config/config.yaml

llm:
  openai:
    enabled: false
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
    base_url: https://api.openai.com/v1
  
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  
  ollama:
    enabled: false
    base_url: http://localhost:11434
    model: llama2
```

**Initialization Order** (in `LLMManager._initialize_providers()`):
1. OpenAI (if enabled + API key)
2. DashScope (if enabled + API key) ← Primary if enabled
3. DeepSeek (if enabled + API key)
4. Local OpenAI-compatible (if enabled)
5. Ollama (if enabled)

**Fallback During Classification:**
If DashScope (primary) fails during `classify_with_llm()`:
1. Try next available provider
2. Log warning
3. If all LLM providers fail, fallback to keyword classification

---

## 8. Web UI Integration

### 8.1 Query Endpoint Flow

**File:** `src/web/routers/query.py`

```python
@router.post("/query")
async def unified_query(request: Request, query: str = Form(...)):
    """
    Main unified query endpoint
    1. Initializes agents (lazy, one-time)
    2. Classifies query (hybrid keyword + LLM)
    3. Routes to appropriate handler
    4. Post-processes result
    5. Saves to database
    6. Renders HTML response
    """
```

**Classification Result Usage:**
```python
task_type, confidence, reason = await Router.classify_hybrid(
    query, 
    llm_manager=llm_manager
)

# Route based on task_type
if task_type == TaskType.RESEARCH:
    result = await handle_research(query)
    mode = "research"
elif task_type == TaskType.CODE:
    result = await handle_code(query)
    mode = "code"
# ... etc
```

**Metadata Storage:**
```python
await database.save_conversation(
    mode=mode,
    query=query,
    response=response_text,
    metadata=json.dumps({
        "task_type": task_type.value,
        "confidence": confidence,
        "sources": result.get('sources', [])
    })
)
```

### 8.2 Type Indicator Display

**File:** `src/web/routers/query.py:362-400`

```python
@router.post("/classify")
async def classify_query(request: Request, query: str = Form(...)):
    """
    Optional: Show user the detected mode before execution
    Returns HTML badge with icon + confidence percentage
    """
    task_type, confidence, reason = await Router.classify_hybrid(query, llm_manager)
    
    return f"""
    <div class="search-type-indicator">
        <span>Detected mode:</span>
        <span class="search-type-badge badge-{color}">
            {icon} {label} - {int(confidence * 100)}% confidence
        </span>
    </div>
    """
```

---

## 9. Testing & Validation

### 9.1 Current Test Coverage

**Test Files:**
- `tests/test_router.py` - Router classification tests
- `tests/test_basic_functions.py` - Basic functionality
- `tests/comprehensive_test.py` - Full system testing
- `tests/test_complete_system.py` - Integration tests

### 9.2 Testing Recommendations

**For improved routing:**

```python
# Test cases for classification

test_cases = {
    # Unambiguous CODE
    ("Calculate 2^10", TaskType.CODE, confidence=0.9),
    ("What is 5 * 8?", TaskType.CODE, confidence=0.85),
    
    # Ambiguous - needs LLM
    ("What is the price?", confidence=<0.6),  # Should trigger LLM
    ("Tell me about stocks", confidence=<0.7),  # Could be RESEARCH or DOMAIN_FINANCE
    
    # Weather with calculation indicator
    ("How many degrees is it?", TaskType.DOMAIN_WEATHER),  # Not CODE!
    ("Convert weather to Celsius", TaskType.CODE),  # Should be CODE for conversion
    
    # Multi-intent (future)
    ("Get AAPL price and calculate tax", confidence_multi=true),
    
    # Edge cases
    ("", TaskType.CHAT),  # Empty query
    ("???", TaskType.CHAT),  # Only question marks
    ("你好", TaskType.CHAT),  # Greeting in Chinese
}
```

---

## 10. Summary: Current State vs. Ideal State

### Current State (Keyword-Heavy)

✓ **Strengths:**
- Fast (no LLM overhead)
- Predictable (deterministic keywords)
- Low cost (no API calls)
- Bilingual support
- Clear fallback behavior

✗ **Weaknesses:**
- Limited accuracy on ambiguous queries
- Can't handle context
- No learning capability
- Rigid categories
- Single-classification model

### Ideal State (LLM-Enhanced)

✓ **Future Strengths:**
- High accuracy across diverse queries
- Context-aware (conversation history)
- Multi-intent support (workflows)
- Adaptive (learns from corrections)
- Explainable (clear reasoning)

✗ **Future Considerations:**
- Latency (mitigated by hybrid approach)
- Cost (minimized with thoughtful prompting)
- Complexity (need careful architecture)

---

## 11. Recommended Implementation Path

### **Quick Wins (Week 1):**
1. ✅ Enhance classification prompt with few-shot examples
2. ✅ Add language detection to choose appropriate prompt
3. ✅ Improve confidence scoring with weighted factors
4. ✅ Add test cases for edge cases

### **Medium-Term (Week 2-3):**
1. Implement tool-aware routing (tools + parameters)
2. Add workflow orchestration support
3. Create multi-intent detection
4. Implement adaptive confidence thresholds

### **Long-Term (Future):**
1. Context-aware routing (conversation history)
2. Learning from corrections (user feedback)
3. A/B testing framework for router improvements
4. Analytics dashboard for routing performance

---

## Appendix: File Reference

| File | Purpose | Key Functions |
|------|---------|---|
| `src/router.py` | Core routing logic | `classify()`, `classify_with_llm()`, `classify_hybrid()`, `get_confidence()` |
| `src/web/routers/query.py` | Web API integration | `unified_query()`, `classify_query()`, handler functions |
| `src/agents/research_agent.py` | Research execution | `research()`, `_generate_search_plan()`, `_synthesize_information()` |
| `src/agents/code_agent.py` | Code execution | `solve()`, `_generate_code()`, `_explain_results()` |
| `src/agents/chat_agent.py` | Chat interface | `chat()` |
| `src/llm/manager.py` | LLM provider management | `complete()`, `_initialize_providers()`, fallback logic |
| `src/utils/config.py` | Configuration loading | `load_config()`, `get_config()`, environment variable substitution |
| `src/web/app.py` | FastAPI application | Router registration, middleware, startup/shutdown |
| `config/config.yaml` | Configuration file | LLM providers, API keys, agent parameters |

