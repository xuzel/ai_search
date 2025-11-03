# 🧠 智能路由与分类器

> **目标**: 深入理解Router的工作原理、分类策略和优化方法

智能路由是AI Search Engine的核心功能,它决定了用户查询应该由哪个Agent处理。

---

## 📋 Router概述

Router负责将用户查询分类到正确的任务类型,支持三种分类策略:

1. **关键词分类** (快速): ~5ms 延迟
2. **LLM分类** (精确): ~500ms 延迟
3. **混合分类** (平衡): 动态选择

---

## 🎯 任务类型

```python
class TaskType(Enum):
    RESEARCH = "research"           # 网页搜索研究
    CODE = "code"                   # 代码生成执行
    CHAT = "chat"                   # 对话聊天
    RAG = "rag"                     # 文档检索
    DOMAIN_WEATHER = "domain_weather"   # 天气查询
    DOMAIN_FINANCE = "domain_finance"   # 金融数据
    DOMAIN_ROUTING = "domain_routing"   # 路由导航
```

---

## 🔍 关键词分类

### 工作原理

关键词分类使用预定义的关键词列表和正则表达式模式进行快速匹配。

**优点**:
- 速度极快 (~5ms)
- 无需API调用
- 可预测性强

**缺点**:
- 准确度相对较低
- 难以处理歧义查询

### 关键词定义

```python
# 研究模式关键词
RESEARCH_KEYWORDS = [
    "search", "find", "查询", "搜索", "查找",
    "what is", "who is", "explain"
]

# 代码模式关键词
CODE_KEYWORDS = [
    "compute", "calculate", "solve", "plot",
    "计算", "求解", "画图"
]

# 数学模式检测
MATH_PATTERNS = [
    r'[\+\-\*\/\^]',      # 数学运算符
    r'\d+\.\d+',            # 小数
    r'sin|cos|tan|log|sqrt'  # 数学函数
]
```

### 分类流程

```python
def classify(self, query: str) -> TaskType:
    query_lower = query.lower()
    
    # 1. 检查域名工具关键词(优先级最高)
    if any(kw in query_lower for kw in WEATHER_KEYWORDS):
        return TaskType.DOMAIN_WEATHER
    
    # 2. 检查数学模式
    if self._has_math_pattern(query):
        return TaskType.CODE
    
    # 3. 检查代码关键词
    if any(kw in query_lower for kw in CODE_KEYWORDS):
        return TaskType.CODE
    
    # 4. 检查研究关键词
    if any(kw in query_lower for kw in RESEARCH_KEYWORDS):
        return TaskType.RESEARCH
    
    # 5. 默认: 聊天模式
    return TaskType.CHAT
```

---

## 🤖 LLM分类

### 工作原理

使用LLM进行语义理解,能够准确识别用户意图。

**优点**:
- 准确度高 (~95%)
- 能处理歧义
- 支持复杂查询

**缺点**:
- 延迟较高 (~500ms)
- 需要API调用
- 有成本

### 提示词设计

```python
classification_prompt = f"""
Classify the following user query into ONE of these task types:

1. RESEARCH: Web search, information gathering
   Examples: "latest AI news", "Python tutorials"

2. CODE: Math calculation, code generation
   Examples: "calculate 2^10", "fibonacci sequence"

3. CHAT: Casual conversation
   Examples: "hello", "how are you"

4. RAG: Document-related questions
   Examples: "what does document say about X"

5. DOMAIN_WEATHER: Weather queries
   Examples: "weather in Beijing", "今天天气"

6. DOMAIN_FINANCE: Stock/finance queries
   Examples: "AAPL stock price", "特斯拉股票"

7. DOMAIN_ROUTING: Navigation/routing
   Examples: "route from A to B", "从北京到上海"

Query: "{query}"

Return JSON: {{"task_type": "...", "confidence": 0.0-1.0, "reason": "..."}}
"""
```

### 返回格式

```json
{
  "task_type": "CODE",
  "confidence": 0.95,
  "reason": "Query contains mathematical calculation"
}
```

---

## ⚖️ 混合分类

### 工作原理

结合关键词和LLM的优势,动态选择分类策略。

**策略**:
1. 先用关键词分类
2. 如果置信度 >= threshold,直接返回
3. 否则调用LLM再次分类

```python
async def classify_hybrid(
    self, 
    query: str, 
    threshold: float = 0.8
) -> dict:
    # Step 1: 关键词分类
    keyword_result = self.classify(query)
    keyword_confidence = self._calculate_confidence(query, keyword_result)
    
    # Step 2: 检查置信度
    if keyword_confidence >= threshold:
        return {
            "task_type": keyword_result,
            "confidence": keyword_confidence,
            "method": "keyword"
        }
    
    # Step 3: LLM分类
    llm_result = await self.classify_with_llm(query)
    llm_result["method"] = "llm_fallback"
    
    return llm_result
```

### 置信度计算

```python
def _calculate_confidence(self, query: str, task_type: TaskType) -> float:
    query_lower = query.lower()
    
    # 检查匹配的关键词数量
    if task_type == TaskType.RESEARCH:
        matches = sum(1 for kw in RESEARCH_KEYWORDS if kw in query_lower)
        return min(0.5 + matches * 0.15, 0.95)
    
    # 检查数学模式
    if task_type == TaskType.CODE:
        math_matches = sum(1 for pattern in MATH_PATTERNS 
                          if re.search(pattern, query))
        return min(0.6 + math_matches * 0.2, 0.95)
    
    return 0.5  # 默认置信度
```

---

## 📊 分类示例

### 示例1: 研究查询

**查询**: "人工智能的最新进展是什么?"

**关键词分类**:
- 匹配关键词: "是什么" → RESEARCH
- 置信度: 0.85
- 延迟: 5ms

**结果**: RESEARCH (无需LLM)

---

### 示例2: 代码查询

**查询**: "计算2的10次方"

**关键词分类**:
- 匹配关键词: "计算"
- 匹配模式: 数字 + 运算
- 置信度: 0.9
- 延迟: 5ms

**结果**: CODE (无需LLM)

---

### 示例3: 歧义查询

**查询**: "今天"

**关键词分类**:
- 无明确匹配
- 置信度: 0.3
- → 触发LLM分类

**LLM分类**:
- 分析: 可能是天气查询
- 返回: DOMAIN_WEATHER
- 置信度: 0.75
- 延迟: 520ms

**结果**: DOMAIN_WEATHER (LLM fallback)

---

## 🎯 优化策略

### 1. 关键词优化

定期更新关键词列表:

```python
# 添加新的领域关键词
RESEARCH_KEYWORDS.extend([
    "最新", "新闻", "趋势", "发展"
])

# 添加多语言支持
CODE_KEYWORDS.extend([
    "運算", "算出"  # 繁体中文
])
```

### 2. 模式优化

改进正则表达式匹配:

```python
# 单位转换模式
UNIT_CONVERSION_PATTERNS = [
    r'(\d+)\s*(hours?|days?|weeks?)\s*in\s*a\s*(week|month|year)',
    r'(\d+)(米|公里|千米)换算成(英里|码)',
]
```

### 3. 缓存策略

缓存LLM分类结果:

```python
classification_cache = {}

async def classify_with_cache(self, query: str) -> dict:
    if query in classification_cache:
        return classification_cache[query]
    
    result = await self.classify_with_llm(query)
    classification_cache[query] = result
    return result
```

---

## 📈 性能指标

| 方法 | 延迟 | 准确度 | 成本 |
|------|------|--------|------|
| 关键词 | ~5ms | 75-80% | 免费 |
| LLM | ~500ms | 90-95% | ¥0.001/次 |
| 混合 | 5-520ms | 85-95% | ¥0.0002/次 |

---

## 🔧 配置选项

在 `config/config.yaml` 中配置路由策略:

```yaml
router:
  strategy: "hybrid"  # keyword / llm / hybrid
  hybrid_threshold: 0.8
  llm_provider: "dashscope"
  enable_cache: true
  cache_ttl: 3600
```

---

## 📌 下一步

- [12-AGENT-SYSTEM.md](12-AGENT-SYSTEM.md) - Agent系统详解
- [13-DATA-FLOW.md](13-DATA-FLOW.md) - 数据流程
- [27-FEATURE-ROUTING.md](27-FEATURE-ROUTING.md) - 路由工具

---

**掌握路由机制是理解系统的关键! 🚀**
