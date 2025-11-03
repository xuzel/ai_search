# 🌐 Web端点接口文档

> **目标**: Web API端点的完整参考

---

## 📋 端点列表

### 查询端点

```
POST /query
POST /query/stream (流式)
GET /query/history
```

### RAG端点

```
POST /rag/upload
POST /rag/query
DELETE /rag/delete/{doc_id}
```

### 工具端点

```
GET /tools
GET /tools/weather
GET /tools/finance
GET /tools/routing
```

### 工作流端点

```
POST /workflow/create
POST /workflow/execute
GET /workflow/{id}
```

---

## 🔗 详细端点

### POST /query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "问题内容"}'
```

---

## 📌 下一步

查看具体功能文档或开发指南。

