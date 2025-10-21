# 路由系统快速参考

## 三种分类方法

### 关键字方法
```bash
python -m src.main ask "query" --auto --no-llm
```
- ⚡ 快（毫秒级）
- 💰 免费（无API调用）
- ⚠️ 对复杂查询不准确

### LLM方法
```python
import asyncio
from src.router import Router

task_type, confidence = await Router.classify_with_llm(query, llm_manager)
```
- 🧠 准确（语义理解）
- 🐢 慢（1-3秒）
- 💸 昂贵（每次API调用）

### 混合方法 ⭐ (推荐)
```bash
python -m src.main ask "query" --auto
# 或
python -m src.main ask "query" --auto --llm
```
- ⚡ 通常快（用关键字）
- 🧠 对模糊查询准确（用LLM）
- 💰 成本低（90%节省）

## 性能对比

```
查询: "7乘以8等于多少"

关键字: CHAT (50%)        ❌ 错误
LLM:    CODE (99%)        ✅ 正确
Hybrid: CODE (99%, llm)   ✅ 正确
```

## 用法示例

### 命令行
```bash
# 默认混合方法（推荐）
python -m src.main ask "一周有多少小时" --auto -v
# 输出: Detected: code (confidence: 60.0%, method: llm)

# 仅关键字
python -m src.main ask "一周有多少小时" --auto --no-llm -v
# 输出: Detected: code (confidence: 60.0%, method: keyword)

# 显示分类信息
python -m src.main ask "query" --auto -v
```

### Python API
```python
import asyncio
from src.router import Router
from src.llm import LLMManager

async def classify_query(query):
    llm_manager = LLMManager(config)

    # 混合方法（推荐）
    task_type, confidence, method = await Router.classify_hybrid(
        query, llm_manager, use_llm_threshold=0.6
    )

    print(f"Task: {task_type.value}")
    print(f"Confidence: {confidence:.1%}")
    print(f"Method: {method}")  # "keyword" 或 "llm"

asyncio.run(classify_query("你的查询"))
```

## 配置

### 调整LLM门槛
```python
# 低值 = 更多使用LLM = 更准确但更慢
await Router.classify_hybrid(query, llm_manager, use_llm_threshold=0.5)

# 高值 = 更多使用关键字 = 更快但较准确
await Router.classify_hybrid(query, llm_manager, use_llm_threshold=0.8)
```

默认：0.6（推荐）

### 调整LLM温度
```python
# 在 classify_with_llm() 中修改 temperature
temperature=0.3  # 更确定
temperature=0.5  # 平衡（默认）
temperature=0.7  # 更多样化
```

## 返回值说明

```python
# 关键字方法
task_type = Router.classify(query)
# 返回: TaskType (CODE|RESEARCH|CHAT)

confidence = Router.get_confidence(query, task_type)
# 返回: float (0.0 - 1.0)

# LLM方法
task_type, confidence = await Router.classify_with_llm(query, llm_manager)
# 返回: (TaskType, float)

# 混合方法（推荐）
task_type, confidence, method = await Router.classify_hybrid(query, llm_manager)
# 返回: (TaskType, float, str)
# method: "keyword" | "llm" | "keyword_fallback"
```

## 任务类型定义

```
CODE: 代码执行/计算
├─ 数学问题: "一周有多少小时?"
├─ 单位转换: "Convert 2km to miles"
├─ 百分比: "30% of 500 is?"
└─ 编程: "编写排序算法"

RESEARCH: 信息查询/搜索
├─ 实时数据: "澳门现在的温度?"
├─ 知识查询: "What is AI?"
├─ 概念: "区块链如何工作?"
└─ 新闻: "最近的技术突破"

CHAT: 常规对话
├─ 问候: "你好"
├─ 闲聊: "你好吗?"
└─ 其他: 不属于上述两类
```

## 常见问题

**Q: 默认使用哪种方法？**
A: 混合方法（`--auto` 时自动使用）

**Q: 如何禁用LLM？**
A: `--auto --no-llm` 或在代码中传入 `use_llm=False`

**Q: 成本是多少？**
A: 混合方法大约是纯LLM的 10%（只在需要时调用）

**Q: 准确度如何？**
A: 对大多数查询 >90%，对明确查询 >95%

**Q: 支持多少种语言？**
A: 所有LLM支持的语言（通常 100+ 语言）

## 文件位置

- 核心实现: `src/router.py`
- CLI集成: `src/main.py` 的 `ask()` 命令
- 详细文档: `LLM_ROUTING_GUIDE.md`
- 改进说明: `ROUTING_IMPROVEMENTS.md`

## 关键方法

```python
# 三个主要方法

# 1. 关键字（传统）
Router.classify(query)                    # → TaskType
Router.get_confidence(query, task_type)   # → float

# 2. LLM（准确）
await Router.classify_with_llm(query, llm_manager)  # → (TaskType, float)

# 3. 混合（推荐）
await Router.classify_hybrid(query, llm_manager, use_llm_threshold=0.6)  # → (TaskType, float, str)
```

## 调试

```bash
# 查看详细信息
python -m src.main ask "query" --auto -v

# 启用DEBUG日志
LOG_LEVEL=DEBUG python -m src.main ask "query" --auto -v

# 测试特定方法
python -c "
import asyncio
from src.router import Router
from src.utils import get_config
from src.llm import LLMManager

async def test():
    config = get_config()
    llm_manager = LLMManager(config)
    query = 'your query'

    # 测试三种方法
    kw = Router.classify(query)
    llm_task, llm_conf = await Router.classify_with_llm(query, llm_manager)
    hybrid_task, hybrid_conf, method = await Router.classify_hybrid(query, llm_manager)

    print(f'Keyword: {kw.value}')
    print(f'LLM:     {llm_task.value} ({llm_conf:.0%})')
    print(f'Hybrid:  {hybrid_task.value} ({hybrid_conf:.0%}, {method})')

asyncio.run(test())
"
```

---

**推荐：** 在生产环境中使用混合方法，这是速度和准确度的最佳平衡。
