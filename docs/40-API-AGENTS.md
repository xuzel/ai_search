# 🔌 Agents API完整文档

> **目标**: Agents API的详细参考和集成指南

---

## 📋 API概述

Agents API提供对AI Search Engine各个Agent的直接访问接口。

---

## 🧩 Agent接口

### ResearchAgent

```python
# 初始化
from src.agents import ResearchAgent
agent = ResearchAgent(llm_manager, search_tool, scraper_tool, config)

# 执行
result = await agent.execute({
    "query": "人工智能的最新进展"
})

# 响应格式
{
    "query": "...",
    "summary": "...",
    "sources": ["url1", "url2", ...],
    "plan": {"queries": [...]}
}
```

### CodeAgent

```python
from src.agents import CodeAgent
agent = CodeAgent(llm_manager, code_executor, config)

result = await agent.execute({
    "problem": "计算斐波那契数列"
})

{
    "code": "...",
    "output": "...",
    "explanation": "..."
}
```

### RAGAgent

```python
from src.agents import RAGAgent
agent = RAGAgent(llm_manager, vector_store, reranker)

result = await agent.execute({
    "question": "文档中说了什么?"
})

{
    "answer": "...",
    "sources": [{"text": "...", "page": 1}]
}
```

---

## 🌐 HTTP API (Web)

### 统一查询接口

```
POST /query
Content-Type: application/json

{
    "query": "用户查询内容"
}

Response:
{
    "task_type": "research",
    "result": {...}
}
```

---

## 🚀 使用示例

### Python

```python
import asyncio
from src.agents import ResearchAgent

async def main():
    result = await agent.research("AI")
    print(result["summary"])

asyncio.run(main())
```

### cURL

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "AI最新进展"}'
```

---

## 📌 下一步

- [41-API-TOOLS.md](41-API-TOOLS.md) - Tools API
- [42-API-WEB-ENDPOINTS.md](42-API-WEB-ENDPOINTS.md) - Web端点

