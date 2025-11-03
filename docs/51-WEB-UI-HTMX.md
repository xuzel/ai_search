# ⚡ HTMX交互开发

> **目标**: HTMX用法和动态交互实现

---

## 🚀 HTMX基础

### 核心属性

```html
<!-- 发送请求 -->
<button hx-post="/endpoint" hx-target="#result">
  点击
</button>

<!-- 替换目标 -->
<div hx-swap="innerHTML">内容</div>

<!-- 加载指示 -->
<div hx-indicator="#spinner">加载中...</div>
```

---

## 💻 常见模式

### 动态搜索

```html
<form hx-post="/search" hx-target="#results">
  <input type="text" name="query" />
</form>
```

### 分页

```html
<button hx-get="/page/2" hx-swap="outerHTML">
  下一页
</button>
```

### 自动刷新

```html
<div hx-get="/status" 
     hx-trigger="every 1s">
  状态
</div>
```

---

## 🔧 FastAPI集成

```python
@router.post("/search")
async def search(query: str):
    result = await agent.execute({"query": query})
    return templates.TemplateResponse("result.html", {
        "result": result
    })
```

---

## 📌 下一步

- [60-CONFIGURATION-LLM.md](60-CONFIGURATION-LLM.md) - LLM配置

