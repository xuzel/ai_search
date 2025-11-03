# 🔄 数据流程架构

> **目标**: 理解系统中的数据流动、处理管道和存储策略

---

## 🌊 整体数据流

```
用户输入 (Web/CLI/API)
  ↓
系统入口 (FastAPI/Typer)
  ↓
Router分类
  ↓
Agent处理
  ├─ 调用LLM
  ├─ 使用Tools
  └─ 处理数据
  ↓
结果返回
  ├─ Web: HTMX更新
  ├─ CLI: 格式化输出
  └─ API: JSON响应
  ↓
数据库保存
  ├─ 对话历史 (SQLite)
  ├─ 向量数据 (ChromaDB)
  └─ 缓存 (Redis/SQLite)
```

---

## 📊 ResearchAgent数据流

```
用户查询: "AI的最新进展"
  ↓
Router分类 → RESEARCH
  ↓
ResearchAgent.execute()
  ├─ Step 1: 生成搜索计划
  │   ├─ LLM分解查询
  │   └─ 生成子查询列表
  │
  ├─ Step 2: 并发搜索
  │   ├─ SearchTool.search(query1)
  │   ├─ SearchTool.search(query2)
  │   └─ SearchTool.search(query3)
  │   ↓
  │   搜索结果: [15条结果]
  │
  ├─ Step 3: 选择URL
  │   ↓
  │   Top 9个URL
  │
  ├─ Step 4: 并发爬取
  │   ├─ ScraperTool.scrape(url1)
  │   ├─ ScraperTool.scrape(url2)
  │   └─ ...
  │   ↓
  │   网页内容
  │
  ├─ Step 5: 内容预处理
  │   ├─ HTML清理
  │   ├─ 去除噪音
  │   └─ 内容分段
  │
  ├─ Step 6: 综合总结
  │   ├─ 构建context
  │   ├─ 调用LLM
  │   └─ 生成答案
  │
  └─ Step 7: 返回结果
      {
        "query": "...",
        "summary": "...",
        "sources": [...],
        "plan": {...}
      }
  ↓
保存历史
  ├─ SQLite: 对话记录
  ├─ Cache: 搜索结果缓存
  └─ S3: 日志存储
```

---

## 💻 CodeAgent数据流

```
数学问题: "计算斐波那契数列"
  ↓
Router分类 → CODE
  ↓
CodeAgent.execute()
  ├─ Step 1: LLM生成代码
  │   ├─ 编写Python代码
  │   └─ 添加注释
  │
  ├─ Step 2: 代码验证
  │   ├─ 语法检查
  │   ├─ 导入白名单检查
  │   └─ 危险模式检测
  │
  ├─ Step 3: 沙箱执行
  │   ├─ 创建隔离进程
  │   ├─ 设置超时 (30s)
  │   └─ 执行代码
  │   ↓
  │   执行结果
  │
  ├─ Step 4: 结果处理
  │   ├─ 捕获stdout
  │   ├─ 捕获stderr
  │   └─ 限制行数 (1000)
  │
  └─ Step 5: 结果解释
      ├─ LLM解释输出
      └─ 格式化答案
  ↓
返回给用户
  {
    "code": "...",
    "output": "...",
    "explanation": "..."
  }
```

---

## 📚 RAGAgent数据流

```
文档上传
  ↓
Step 1: 文档处理
  ├─ 读取文件 (PDF/DOCX/TXT)
  ├─ 提取文本
  └─ 去重/清理
  ↓
Step 2: 分段 (Chunking)
  ├─ 策略: fixed/semantic/recursive
  ├─ 块大小: 512字符
  ├─ 重叠: 15%
  └─ 最小块: 100字符
  ↓
Step 3: Embedding
  ├─ 模型: sentence-transformers
  ├─ 维度: 384
  ├─ 批处理
  └─ 并发处理
  ↓
Step 4: 存储
  ├─ ChromaDB持久化
  ├─ 元数据索引
  └─ 向量索引
  ↓
用户查询: "文档中说什么?"
  ↓
Step 5: 检索
  ├─ Query embedding
  ├─ 相似度搜索
  ├─ 返回Top-10
  └─ 余弦相似度 > 0.7
  ↓
Step 6: Reranking (可选)
  ├─ 二次排序
  ├─ 返回Top-3
  └─ 更高精度
  ↓
Step 7: 答案生成
  ├─ 构建context
  ├─ 调用LLM
  └─ 生成答案
  ↓
返回结果
  {
    "answer": "...",
    "sources": [chunks]
  }
```

---

## 💾 存储架构

### SQLite (对话历史)

```python
# 表结构
conversation_history (
  id: INT PRIMARY KEY,
  timestamp: DATETIME,
  mode: VARCHAR(20),        # research/code/chat/rag
  query: TEXT,
  response: TEXT,
  metadata: JSON
)

# 索引
CREATE INDEX idx_timestamp ON conversation_history(timestamp)
CREATE INDEX idx_mode ON conversation_history(mode)
```

### ChromaDB (向量存储)

```python
# 集合结构
{
  "id": "doc_chunk_1",
  "embedding": [0.1, 0.2, ...],  # 384维向量
  "metadatas": {
    "source": "file.pdf",
    "page": 1,
    "chunk": 0
  },
  "documents": "文本内容..."
}
```

### 缓存 (Redis/SQLite)

```python
cache_key = f"search:{query_hash}"
cache_ttl = 3600  # 1小时

# 缓存搜索结果
{
  "query": "...",
  "results": [...]
}
```

---

## ⚡ 性能优化

### 1. 并发处理

```python
# 并发搜索
results = await asyncio.gather(
    search_tool.search(q1),
    search_tool.search(q2),
    search_tool.search(q3)
)
```

### 2. 缓存策略

```python
# 缓存搜索结果
if query in cache:
    return cache[query]
result = await search()
cache[query] = result
```

### 3. 连接池

```python
# HTTP连接复用
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(limit=100)
)
```

### 4. 批处理

```python
# 批量embedding
embeddings = model.encode(
    documents,
    batch_size=32
)
```

---

## 📊 数据大小估计

| 操作 | 数据量 | 处理时间 |
|------|--------|----------|
| 单次搜索 | 15条结果 | 100ms |
| 9个URL爬取 | ~1MB | 2-5s |
| Embedding 9个块 | 4.5KB | 50ms |
| LLM综合 | 全文 | 1-2s |
| **总耗时** | - | **3-8s** |

---

## 📌 下一步

- [20-FEATURE-RESEARCH.md](20-FEATURE-RESEARCH.md) - 研究功能
- [23-FEATURE-RAG.md](23-FEATURE-RAG.md) - RAG功能
- [40-API-AGENTS.md](40-API-AGENTS.md) - Agents API

---

**理解数据流有助于性能优化和故障排查! 🚀**
