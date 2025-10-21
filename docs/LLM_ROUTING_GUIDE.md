# LLM-Based Smart Routing Guide

## Overview

路由系统现在支持 **三种分类方法**，从快速到准确：

1. **Keyword-based** (纯关键字) - 快速，基于规则
2. **LLM-based** (纯LLM) - 准确，语义理解
3. **Hybrid** (混合) - **推荐使用** - 结合速度和准确性

## 三种分类方法

### 1. Keyword-Based Classification (传统方法)

使用 `Router.classify(query)` 和 `Router.get_confidence(query, task_type)`

**优点：**
- ⚡ 速度快（毫秒级）
- 💰 无API调用成本
- 🎯 对明确的查询准确率高

**缺点：**
- ❌ 对复杂/模糊查询效果差
- ❌ 多语言支持有限
- ❌ 无语义理解

**例子：**
```python
from src.router import Router

# 清晰的计算问题
task_type = Router.classify("Calculate 2^20")
# 返回：TaskType.CODE (confidence: 90%)

# 模糊的查询
task_type = Router.classify("7乘以8等于多少")
# 返回：TaskType.CHAT (confidence: 50%)  ❌ 错误！应该是CODE
```

### 2. LLM-Based Classification (纯LLM方法)

使用 `await Router.classify_with_llm(query, llm_manager)`

**优点：**
- 🧠 语义理解强
- 🌍 多语言支持好
- 📝 处理复杂查询
- 🎯 准确率高

**缺点：**
- 🐢 速度慢（1-3秒）
- 💰 每次调用都要API请求
- 📉 依赖LLM质量

**例子：**
```python
import asyncio
from src.router import Router
from src.llm import LLMManager

async def test():
    llm_manager = LLMManager(config)

    # 模糊的查询
    task_type, confidence = await Router.classify_with_llm(
        "7乘以8等于多少",
        llm_manager
    )
    # 返回：(TaskType.CODE, 0.99) ✅ 正确！

    # 复杂的查询
    task_type, confidence = await Router.classify_with_llm(
        "如何解决二次方程",
        llm_manager
    )
    # 返回：(TaskType.RESEARCH, 0.85) ✅ 正确！

asyncio.run(test())
```

### 3. Hybrid Classification (混合方法 - 推荐)

使用 `await Router.classify_hybrid(query, llm_manager, use_llm_threshold=0.6)`

**这是推荐的方法！** 结合了两种方法的优势。

**工作流程：**
```
1. 先用关键字快速分类
   ↓
2. 检查置信度
   ├─ 置信度高 (≥ 0.6) → 使用关键字结果 (快速✅)
   └─ 置信度低 (< 0.6) → 用LLM重新分类 (准确✅)
```

**返回值：**
```python
task_type, confidence, method = await Router.classify_hybrid(query, llm_manager)
# task_type: TaskType (CODE|RESEARCH|CHAT)
# confidence: float (0.0 - 1.0)
# method: str ("keyword" | "llm" | "keyword_fallback")
```

**优点：**
- ⚡ 通常很快（关键字结果高置信度时）
- 🧠 对模糊查询准确（LLM接管）
- 💰 减少API调用（只在需要时调用LLM）
- 🎯 综合准确率最高

**例子：**
```python
import asyncio
from src.router import Router

async def test():
    task_type, confidence, method = await Router.classify_hybrid(query, llm_manager)

    # 清晰的计算 → 关键字处理
    # "Calculate 2^20"
    # 返回：(TaskType.CODE, 0.90, "keyword")

    # 模糊的查询 → LLM处理
    # "7乘以8等于多少"
    # 返回：(TaskType.CODE, 0.99, "llm")

    # 研究问题 → 关键字处理
    # "What is AI?"
    # 返回：(TaskType.RESEARCH, 0.90, "keyword")
```

## CLI 使用

### 使用混合分类（默认，推荐）
```bash
python -m src.main ask "你的查询" --auto -v
```
输出：
```
Detected: code (confidence: 99.0%, method: llm)
```

### 禁用LLM，仅使用关键字
```bash
python -m src.main ask "你的查询" --auto --no-llm -v
```
输出：
```
Detected: code (confidence: 75.0%, method: keyword)
```

### 使用纯LLM分类
目前CLI中没有直接选项，需要手动调用：
```python
import asyncio
from src.router import Router
from src.llm import LLMManager
from src.utils import get_config

async def main():
    config = get_config()
    llm_manager = LLMManager(config)
    task_type, confidence = await Router.classify_with_llm(query, llm_manager)

asyncio.run(main())
```

## 性能对比

| 方法 | 速度 | 准确度 | 成本 | 复杂度 |
|------|------|--------|------|--------|
| Keyword | ⚡⚡⚡ | ⭐⭐ | 免费 | 简单 |
| LLM | 🐢 | ⭐⭐⭐⭐⭐ | 高 | 中等 |
| Hybrid | ⚡⚡ | ⭐⭐⭐⭐⭐ | 中 | 中等 |

## 配置

### 调整LLM阈值

在 `src/main.py` 的 `ask()` 函数中修改：

```python
task_type, confidence, method = asyncio.run(
    Router.classify_hybrid(query, llm_manager, use_llm_threshold=0.6)  # 调整这个值
)
```

- **0.5**: 更倾向使用LLM（更准确但更慢）
- **0.6**: 平衡（默认推荐）
- **0.8**: 更倾向使用关键字（更快但较准确）

### 调整LLM温度

在 `classify_with_llm()` 中修改：

```python
response = await llm_manager.complete(
    messages=[...],
    temperature=0.3,  # 调整这个值 (0.0-1.0)
    max_tokens=200,
)
```

- 低温度（0.1-0.3）: 更确定的分类
- 中温度（0.5）: 平衡
- 高温度（0.7-1.0）: 更多样化的结果

## 测试示例

```python
import asyncio
from src.router import Router
from src.llm import LLMManager
from src.utils import get_config

async def test_routing():
    config = get_config()
    llm_manager = LLMManager(config)

    queries = [
        "一周有多少小时？",           # 明确的计算
        "7乘以8等于多少",             # 简单计算（关键字识别不了）
        "编写一个排序算法",           # 编程任务
        "澳门现在的温度是多少",       # 实时信息
        "什么是人工智能",             # 知识查询
        "你好，你好吗",               # 闲聊
    ]

    for query in queries:
        print(f"\nQuery: {query}")

        # Keyword
        kw_type = Router.classify(query)
        kw_conf = Router.get_confidence(query, kw_type)
        print(f"  Keyword:  {kw_type.value:10} ({kw_conf:.0%})")

        # LLM
        llm_type, llm_conf = await Router.classify_with_llm(query, llm_manager)
        print(f"  LLM:      {llm_type.value:10} ({llm_conf:.0%})")

        # Hybrid
        hybrid_type, hybrid_conf, method = await Router.classify_hybrid(query, llm_manager)
        print(f"  Hybrid:   {hybrid_type.value:10} ({hybrid_conf:.0%}, {method})")

asyncio.run(test_routing())
```

## 常见问题

### Q: 什么时候应该用纯关键字？
**A:** 当你需要速度且查询清晰时。例如在CLI中快速测试明确的计算问题。

### Q: 什么时候应该用LLM？
**A:** 当需要最高准确度且LLM调用成本可接受时。例如在后台服务中处理复杂查询。

### Q: 混合方法的成本是多少？
**A:** 取决于有多少查询落在"低置信度"区间。通常：
- 高置信度查询（90%）: 0 API调用（用关键字）
- 低置信度查询（10%）: 1 API调用（用LLM）
- **平均成本降低70%**相比纯LLM方法

### Q: 如何在生产环境中使用？
**A:** 推荐混合方法：
```python
# 在服务启动时
llm_manager = LLMManager(config)

# 每次分类请求
task_type, confidence, method = await Router.classify_hybrid(
    query,
    llm_manager,
    use_llm_threshold=0.6
)

# 记录用于分析
logger.info(f"Routed to {task_type.value} via {method}")
```

## 扩展和定制

### 修改LLM分类提示词

编辑 `src/router.py` 中的 `classify_with_llm()` 方法的 `classification_prompt`：

```python
classification_prompt = f"""你的自定义提示词
...
用户查询: "{query}"
...
"""
```

### 添加新的分类类型

1. 在 `TaskType` enum 中添加新类型
2. 更新分类提示词
3. 更新关键字列表
4. 在代理和主程序中处理新类型

### 使用其他LLM提供商

由于系统使用 `LLMManager`，自动支持所有配置的提供商：
- OpenAI
- Anthropic Claude
- Aliyun DashScope
- DeepSeek
- Local Ollama
- 任何OpenAI兼容的API

只需在 `config.yaml` 中配置相应提供商。

## 调试

### 启用详细日志

```bash
export LOG_LEVEL=DEBUG
python -m src.main ask "query" --auto -v
```

### 获取分类详情

```python
task_type, confidence, method = await Router.classify_hybrid(query, llm_manager)
print(f"Task: {task_type.value}")
print(f"Confidence: {confidence}")
print(f"Method: {method}")  # "keyword", "llm", or "keyword_fallback"
```

### 比较三种方法

```python
# Keyword
kw_task = Router.classify(query)
kw_conf = Router.get_confidence(query, kw_task)

# LLM
llm_task, llm_conf = await Router.classify_with_llm(query, llm_manager)

# Hybrid
hybrid_task, hybrid_conf, method = await Router.classify_hybrid(query, llm_manager)

print(f"Keyword: {kw_task.value} ({kw_conf:.0%})")
print(f"LLM:     {llm_task.value} ({llm_conf:.0%})")
print(f"Hybrid:  {hybrid_task.value} ({hybrid_conf:.0%}, {method})")
```

## 总结

| 方法 | 何时使用 | 命令 |
|------|---------|------|
| Keyword | 快速测试 | `--auto --no-llm` |
| LLM | 最高准确度 | 手动调用 `classify_with_llm()` |
| **Hybrid** | **生产环境（默认）** | `--auto` |

**推荐：** 在生产环境中使用混合方法，享受速度和准确度的最佳平衡。
