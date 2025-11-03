# 🛠️ Tools API完整文档

> **目标**: Tools API的详细参考

---

## 📋 工具接口

### SearchTool

```python
from src.tools import SearchTool

tool = SearchTool(provider="serpapi", api_key="...")
results = await tool.search("Python编程")
```

### ScraperTool

```python
from src.tools import ScraperTool

tool = ScraperTool()
content = await tool.scrape("https://example.com")
```

### CodeExecutor

```python
from src.tools import CodeExecutor

executor = CodeExecutor()
result = executor.execute("print(2**10)")
```

### VectorStore

```python
from src.tools import VectorStore

store = VectorStore(config)
chunks = await store.query("query text", top_k=10)
```

---

## 🎯 工具列表

| 工具 | 功能 | 使用 |
|------|------|------|
| SearchTool | 网页搜索 | await tool.search(query) |
| ScraperTool | 内容爬取 | await tool.scrape(url) |
| CodeExecutor | 代码执行 | result = executor.execute(code) |
| VectorStore | 向量检索 | chunks = await store.query(query) |
| OCRTool | 文字识别 | text = await tool.ocr(image) |
| VisionTool | 图像理解 | desc = await tool.describe(image) |

