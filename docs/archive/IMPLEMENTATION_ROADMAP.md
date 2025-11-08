# LLM-Based Routing Implementation Roadmap

## Phase 1: Enhanced Prompt Engineering (Week 1) - PRIORITY: HIGH

### 1.1 Improve Classification Prompt

**Current Location:** `src/router.py:294-337`

**Actions:**

1. **Add Few-Shot Examples**
   - Include 8-10 real-world examples per category
   - Cover edge cases (ambiguous, multilingual, domain-specific)
   - Show correct classification with reasoning

2. **Separate Language-Specific Prompts**
   - Detect query language (English vs Chinese)
   - Use optimized prompts for each language
   - Improve accuracy for non-English queries

3. **Enhance Confidence Scoring Guidance**
   - Explain confidence ranges clearly
   - Provide examples of high/medium/low confidence queries
   - Help LLM calibrate scoring

**Code Implementation:**

```python
# In src/router.py

async def classify_with_llm(
    query: str,
    llm_manager: "LLMManager",
) -> tuple[TaskType, float]:
    """Enhanced version with better prompting"""
    
    # Detect language
    from langdetect import detect
    try:
        lang = detect(query)
    except:
        lang = 'en'
    
    # Select appropriate prompt
    if lang.startswith('zh'):
        prompt = get_chinese_classification_prompt()
    else:
        prompt = get_english_classification_prompt()
    
    # Add few-shot examples
    prompt += "\n" + get_few_shot_examples(lang)
    
    # Add query
    prompt += f"\n用户查询: \"{query}\"" if lang.startswith('zh') else f"\nUser Query: \"{query}\""
    
    # ... rest of implementation
```

### 1.2 Create Prompt Templates

**New File:** `src/router/prompts.py`

```python
"""Classification prompts for different languages and scenarios"""

ENGLISH_CLASSIFICATION_PROMPT = """
You are an expert query classifier for an AI system with specialized capabilities.

Task Categories:
1. **RESEARCH** - Information lookup queries requiring web search
   - Examples: "What is machine learning?", "Latest AI news"
   - Indicators: search, find, explain, tell me about, what is

2. **CODE** - Computation/programming queries requiring code execution
   - Examples: "Calculate 2^10", "How many hours in 7 days?"
   - Indicators: calculate, solve, compute, formula, code generation

3. **CHAT** - General conversation not requiring external tools
   - Examples: "Hello!", "How are you?", "Tell me a joke"
   - Indicators: Greetings, general discussion, no specific task

4. **DOMAIN_WEATHER** - Real-time weather information
   - Examples: "What's the weather today?", "Rain forecast for tomorrow"
   - Indicators: weather, temperature, forecast, rain, snow

5. **DOMAIN_FINANCE** - Stock/market data queries
   - Examples: "AAPL stock price", "Bitcoin value today"
   - Indicators: stock, price, market, cryptocurrency, trading

6. **DOMAIN_ROUTING** - Navigation and directions
   - Examples: "Route from NYC to Boston", "How to get to..."
   - Indicators: route, direction, navigate, distance, driving

7. **RAG** - Document-based Q&A
   - Examples: "Summarize this PDF", "What does the document say about..."
   - Indicators: document, PDF, file, report analysis

Confidence Scoring:
- HIGH (0.85-1.0): Clear intent, explicit keywords, unambiguous
- MEDIUM (0.65-0.84): Some keywords, but could have alternatives
- LOW (0.40-0.65): Ambiguous, missing context
- VERY LOW (<0.40): Unclear intent, conflicting signals

Few-Shot Examples:
- "Calculate the factorial of 10" → CODE (confidence: 0.95)
- "What's the weather?" → DOMAIN_WEATHER (confidence: 0.90)
- "Tell me about AI" → RESEARCH (confidence: 0.85)
- "Price of Apple stock" → DOMAIN_FINANCE (confidence: 0.88)
- "How are you doing?" → CHAT (confidence: 0.92)
- "Convert 5 kilometers to miles" → CODE (confidence: 0.85)
- "Can you help me?" → CHAT (confidence: 0.80)
- "Summarize the attached document" → RAG (confidence: 0.90)

Priority Rules:
- Domain-specific queries take highest priority (WEATHER, FINANCE, ROUTING, RAG)
- If domain-specific keywords present, classify accordingly
- Otherwise, distinguish between CODE, RESEARCH, and CHAT

Respond ONLY in JSON format:
{
    "task_type": "RESEARCH|CODE|CHAT|DOMAIN_WEATHER|DOMAIN_FINANCE|DOMAIN_ROUTING|RAG",
    "confidence": <0.0-1.0>,
    "reasoning": "Brief explanation of classification"
}
"""

CHINESE_CLASSIFICATION_PROMPT = """
你是一个高级查询分类器，为一个具有专业功能的AI系统工作。

任务类别：
1. **RESEARCH** - 信息查询，需要网络搜索
   - 例子: "什么是机器学习?", "最新的AI新闻"
   - 指示词: 搜索, 查询, 查找, 了解, 什么是

2. **CODE** - 计算/编程查询，需要代码执行
   - 例子: "计算2^10", "7天有多少小时?"
   - 指示词: 计算, 计数, 求解, 公式, 写代码

3. **CHAT** - 通用对话，不需要外部工具
   - 例子: "你好!", "你好吗?", "讲个笑话"
   - 指示词: 问候, 通常讨论, 没有特定任务

4. **DOMAIN_WEATHER** - 实时天气信息
   - 例子: "今天天气怎样?", "明天会下雨吗?"
   - 指示词: 天气, 温度, 预报, 下雨, 下雪

5. **DOMAIN_FINANCE** - 股票/市场数据查询
   - 例子: "苹果股票价格", "比特币今天的价值"
   - 指示词: 股票, 股价, 市场, 加密货币, 交易

6. **DOMAIN_ROUTING** - 导航和路线
   - 例子: "从纽约到波士顿的路线", "怎么去..."
   - 指示词: 路线, 导航, 方向, 距离, 驾驶

7. **RAG** - 基于文档的问答
   - 例子: "总结这个PDF", "文档中说什么..."
   - 指示词: 文档, PDF, 文件, 报告分析

...
"""
```

### 1.3 Add Language Detection

**Dependencies to Add:**

```bash
pip install langdetect
```

**Implementation:**

```python
# In src/router.py

def detect_query_language(query: str) -> str:
    """
    Detect query language.
    
    Returns: 'zh', 'en', or other language code
    """
    try:
        from langdetect import detect
        lang = detect(query)
        return lang[:2]  # Return just language code
    except:
        # Default to English if detection fails
        return 'en'
```

---

## Phase 2: Multi-Intent & Workflow Support (Week 2-3) - PRIORITY: MEDIUM

### 2.1 Add Tool-Aware Classification

**New Method:** `Router.classify_with_tools()`

```python
@staticmethod
async def classify_with_tools(
    query: str,
    llm_manager: "LLMManager",
) -> dict:
    """
    Extended classification that includes tool recommendations.
    
    Returns:
    {
        "primary_task": TaskType,
        "secondary_tasks": [TaskType],          # Optional
        "tools_needed": ["search", "code_exec"],
        "parameters": {
            "search_depth": "medium",
            "code_type": "calculation",
            ...
        },
        "workflow": "sequential|parallel|conditional",
        "confidence": 0.85,
        "reasoning": "..."
    }
    """
    
    prompt = """You are a task router. Analyze the query and recommend:
1. Primary task type
2. Required tools (if any)
3. Tool parameters
4. Execution workflow (sequential, parallel, or conditional)

Available tools:
- search: Web search via SerpAPI
- code_execution: Python code execution
- document_qa: Query uploaded documents (RAG)
- weather: Real-time weather data
- finance: Stock market data
- routing: Route/navigation planning
- vision: Image analysis
- ocr: Text extraction from images

Query: "{query}"

Respond in JSON:
{{
    "primary_task": "RESEARCH|CODE|CHAT|...",
    "secondary_tasks": [],
    "tools_needed": [],
    "parameters": {{}},
    "workflow": "sequential",
    "confidence": 0.85,
    "reasoning": "..."
}}
"""
    # ... implementation
```

### 2.2 Create Workflow Orchestrator

**New Class:** `src/router/workflow_orchestrator.py`

```python
class WorkflowOrchestrator:
    """Manages multi-step query execution"""
    
    def __init__(self, agents: dict, tools: dict):
        self.agents = agents
        self.tools = tools
    
    async def execute_workflow(self, workflow_plan: dict) -> dict:
        """
        Execute a multi-step workflow.
        
        workflow_plan = {
            "steps": [
                {
                    "type": "search",
                    "params": {"query": "..."},
                    "output_var": "search_results"
                },
                {
                    "type": "code",
                    "params": {"problem": "Calculate based on {search_results}"},
                    "output_var": "calculation"
                }
            ],
            "final_merge": true
        }
        """
        results = {}
        
        for step in workflow_plan["steps"]:
            step_type = step["type"]
            params = step["params"]
            output_var = step["output_var"]
            
            # Substitute variables from previous steps
            for key, value in params.items():
                if isinstance(value, str) and "{" in value:
                    for prev_var, prev_result in results.items():
                        value = value.replace(f"{{{prev_var}}}", str(prev_result))
                    params[key] = value
            
            # Execute step
            if step_type == "search":
                result = await self.agents["research"].research(params["query"])
            elif step_type == "code":
                result = await self.agents["code"].solve(params["problem"])
            # ... other step types
            
            results[output_var] = result
        
        return results
```

---

## Phase 3: Adaptive Routing (Week 3-4) - PRIORITY: MEDIUM-HIGH

### 3.1 Track Misclassifications

**New Table:** `conversation_history` additions

```python
# Add these columns to track routing accuracy
"""
- id (existing)
- timestamp (existing)
- mode (existing)
- query (existing)
- response (existing)
- metadata (existing)
+ detected_task_type (new)      # What router classified as
+ detected_confidence (new)     # Router's confidence
+ user_correction (new)         # Did user correct the classification?
+ corrected_task_type (new)     # What it should have been
"""
```

### 3.2 Learn from Corrections

**New Class:** `src/router/adaptive_router.py`

```python
class AdaptiveRouter(Router):
    """Learns from user corrections to improve routing"""
    
    def __init__(self, database):
        self.database = database
        self.user_patterns = {}
    
    async def record_correction(
        self,
        query: str,
        detected_type: TaskType,
        corrected_type: TaskType,
        user_id: str = None,
    ):
        """
        Record when user corrects router classification.
        Use this data to improve future routing.
        """
        await self.database.save_routing_feedback(
            query=query,
            detected_type=detected_type,
            corrected_type=corrected_type,
            user_id=user_id,
            timestamp=datetime.now()
        )
        
        # Update user patterns
        if user_id:
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = {}
            
            key = (detected_type, corrected_type)
            self.user_patterns[user_id][key] = \
                self.user_patterns[user_id].get(key, 0) + 1
    
    async def classify_adaptive(
        self,
        query: str,
        user_id: str = None,
        llm_manager: Optional["LLMManager"] = None,
    ) -> tuple[TaskType, float]:
        """
        Classify considering user history.
        
        If user frequently corrects CODE → RESEARCH,
        lower confidence for CODE classification.
        """
        # Get base classification
        task_type, confidence, method = await self.classify_hybrid(
            query, llm_manager
        )
        
        # Adjust based on user history
        if user_id and user_id in self.user_patterns:
            corrections = self.user_patterns[user_id]
            for (detected, corrected), count in corrections.items():
                if detected == task_type and count > 2:
                    # User frequently corrects this type
                    confidence *= 0.8  # Lower confidence
        
        return task_type, confidence
```

---

## Phase 4: Context-Aware Routing (Week 4-5) - PRIORITY: LOW

### 4.1 Maintain Conversation Context

**New Module:** `src/router/context_manager.py`

```python
class ConversationContext:
    """Maintains conversation context for routing decisions"""
    
    def __init__(self, max_history: int = 10):
        self.history = []
        self.max_history = max_history
    
    def add_exchange(
        self,
        query: str,
        task_type: TaskType,
        response: str
    ):
        """Add query-response pair to history"""
        self.history.append({
            "query": query,
            "task_type": task_type,
            "response": response,
            "timestamp": datetime.now()
        })
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_context_prompt(self) -> str:
        """Generate context for classification prompt"""
        if not self.history:
            return ""
        
        context = "Previous conversation:\n"
        for exchange in self.history[-3:]:  # Last 3 exchanges
            context += f"- Query: {exchange['query']}\n"
            context += f"  Type: {exchange['task_type'].value}\n"
        
        return context
    
    def clear(self):
        """Clear conversation history"""
        self.history = []
```

### 4.2 Context-Aware Classification

```python
async def classify_with_context(
    query: str,
    context: ConversationContext,
    llm_manager: "LLMManager",
) -> tuple[TaskType, float]:
    """
    Classify considering conversation history.
    
    Example:
    Assistant: "AAPL is at $150"
    User: "Convert to EUR"
    
    Without context: Ambiguous ("convert" could be unit conversion)
    With context: Clear CODE task (currency conversion)
    """
    
    context_prompt = context.get_context_prompt()
    
    prompt = f"""
    {context_prompt}
    
    Now the user asks: "{query}"
    
    Considering the conversation history, what is the task type?
    
    Respond in JSON:
    {{
        "task_type": "...",
        "confidence": 0.85,
        "reasoning": "..."
    }}
    """
    
    # ... classification logic
```

---

## Integration Checklist

### For Phase 1 (This Week):
- [ ] Create `src/router/prompts.py` with language-specific prompts
- [ ] Add language detection to `classify_with_llm()`
- [ ] Add few-shot examples to prompts
- [ ] Add test cases for ambiguous queries
- [ ] Test with both English and Chinese queries
- [ ] Update documentation with new prompt format

### For Phase 2:
- [ ] Implement `Router.classify_with_tools()`
- [ ] Create `WorkflowOrchestrator` class
- [ ] Add workflow execution logic
- [ ] Create tests for multi-intent queries
- [ ] Update web UI to show detected tools
- [ ] Handle tool parameter extraction

### For Phase 3:
- [ ] Add database columns for routing feedback
- [ ] Implement `AdaptiveRouter.record_correction()`
- [ ] Create UI for user corrections
- [ ] Build analytics dashboard for routing accuracy
- [ ] Implement feedback loop

### For Phase 4:
- [ ] Implement `ConversationContext` class
- [ ] Add context to classification prompts
- [ ] Test context-aware routing
- [ ] Measure improvement from context usage

---

## Testing Strategy

### Test Cases to Add:

```python
# tests/test_router_improvements.py

test_cases = {
    # Ambiguous cases (should trigger LLM)
    ("What is the price?", {
        "min_confidence": 0.5,
        "method": "should_use_llm"
    }),
    ("How many calories?", {
        "min_confidence": 0.5,
        "method": "should_use_llm"
    }),
    
    # Language-specific
    ("今天天气怎么样?", {
        "expected_type": TaskType.DOMAIN_WEATHER,
        "language": "chinese"
    }),
    ("天气の状況は?", {  # Japanese
        "method": "should_handle_gracefully"
    }),
    
    # Multi-intent (future)
    ("Find AAPL price and convert to EUR", {
        "primary_task": TaskType.DOMAIN_FINANCE,
        "secondary_tasks": [TaskType.CODE],
        "tools": ["finance_tool", "code_executor"]
    }),
    
    # Edge cases
    ("", {
        "expected_type": TaskType.CHAT,
        "reason": "empty_query"
    }),
    ("?" * 10, {
        "expected_type": TaskType.CHAT,
        "reason": "only_punctuation"
    }),
}

# Metrics to track
metrics = {
    "classification_accuracy": "% of correct classifications",
    "ambiguous_query_accuracy": "% accuracy on <0.6 confidence queries",
    "avg_llm_latency": "Average time for LLM classification",
    "user_correction_rate": "% of queries user corrects",
    "multilingual_accuracy": "Accuracy on non-English queries",
}
```

---

## Performance Considerations

### Latency Budget:
- Keyword classification: <5ms
- LLM classification: 100-500ms (async, acceptable)
- Total: <600ms per query (user perceivable)

### Cost Optimization:
- Keyword classification avoids 40% of queries (cost: 0)
- LLM classification only for 60% (cost: 0.0005-0.001 per query)
- Estimated cost: ~$0.10 per 1000 queries

### Caching Opportunities:
- Cache classification for identical queries
- Cache LLM responses by query hash
- TTL: 1 hour (reasonable for fresh data)

---

## Success Metrics

Define what "better routing" means:

1. **Accuracy**: Classification matches intended task type
   - Target: >95% for explicit keywords, >85% for ambiguous

2. **User Satisfaction**: Users don't need to correct router
   - Target: <5% manual corrections needed

3. **Latency**: Response time acceptable to users
   - Target: <2 seconds total (including LLM if needed)

4. **Cost**: LLM usage economical
   - Target: <$0.20 per user per day average

5. **Multi-Intent Support**: Handle complex queries
   - Target: 90% of multi-intent queries handled correctly

---

## Files to Create/Modify

**New Files:**
- `src/router/prompts.py` - Language-specific classification prompts
- `src/router/workflow_orchestrator.py` - Multi-step execution
- `src/router/adaptive_router.py` - Learning from feedback
- `src/router/context_manager.py` - Conversation context
- `tests/test_router_improvements.py` - Comprehensive tests

**Modified Files:**
- `src/router.py` - Add new methods, enhance existing
- `src/web/routers/query.py` - Integrate improvements
- `src/web/database.py` - Add new columns for feedback
- `config/config.yaml` - Add routing parameters

**Documentation:**
- `ROUTING_SYSTEM_ANALYSIS.md` (this document)
- `ROUTING_ARCHITECTURE_DIAGRAMS.md`
- `IMPLEMENTATION_ROADMAP.md` (this file)

