# LLM-Based 智能路由系统实现指南

## 📋 概述

本文档介绍如何将旧的关键字匹配路由系统替换为新的 LLM-based 智能路由系统。

### 核心改进

| 方面 | 旧系统 | 新系统 |
|-----|-------|-------|
| **方法** | 关键字匹配 | LLM + Prompt Engineering |
| **准确性** | ~90% | ~95%+ |
| **灵活性** | 固定规则 | 动态理解 |
| **多意图** | ❌ 不支持 | ✅ 自动检测 |
| **工具选择** | 静态映射 | 动态推理 |
| **语言支持** | 基础 | 优化的中文支持 |
| **理由追踪** | ❌ 无 | ✅ 完整的推理过程 |

## 🏗️ 新架构

```
用户查询
    ↓
┌─────────────────────────────────┐
│ ChineseIntelligentRouter        │
│ (中文优化智能路由器)             │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ LLM Prompt Engineering          │
│ - 完整的上下文理解               │
│ - 多意图识别                     │
│ - 工具推荐                       │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ RoutingDecision                 │
│ - primary_task_type             │
│ - tools_needed                  │
│ - confidence                    │
│ - multi_intent                  │
│ - follow_up_questions           │
└─────────────────────────────────┘
    ↓
   Agent 执行
```

## 📦 新文件结构

```
src/
├── llm_router.py              # 通用 LLM 智能路由器
├── cn_llm_router.py           # 中文优化版本
└── (web/routers/query.py)     # 需要更新集成
```

## 🚀 快速开始

### 1. 基本使用

```python
from src.llm import LLMManager
from src.cn_llm_router import ChineseIntelligentRouter
from src.utils.config import get_config

# 初始化
config = get_config()
llm_manager = LLMManager(config=config)
router = ChineseIntelligentRouter(llm_manager)

# 路由查询
decision = await router.route_query("计算 2 的 100 次方")

# 使用决策
print(f"任务类型: {decision.primary_task_type.value}")
print(f"置信度: {decision.task_confidence}")
print(f"需要的工具: {[tool.tool_name for tool in decision.tools_needed]}")
print(f"是否多意图: {decision.multi_intent}")
```

### 2. Web UI 集成（推荐）

```python
# 在 src/web/routers/query.py 中修改

from src.cn_llm_router import ChineseIntelligentRouter

async def unified_query(request: Request, query: str = Form(...)):
    """使用 LLM 智能路由的统一查询端点"""

    # 初始化智能路由器
    router = ChineseIntelligentRouter(request.app.state.llm_manager)

    # 获取路由决策
    routing_decision = await router.route_query(
        query=query,
        context={
            'language': 'zh',
            'location': request.headers.get('cf-ipcountry', 'unknown')
        },
        conversation_history=None  # 可选：传递对话历史
    )

    # 根据决策执行相应的 Agent
    if routing_decision.primary_task_type == TaskType.RESEARCH:
        return await handle_research(routing_decision, query, request)
    elif routing_decision.primary_task_type == TaskType.CODE:
        return await handle_code(routing_decision, query, request)
    # ... 其他类型

    # 返回带有路由信息的结果
    return {
        'result': result,
        'routing': {
            'task_type': routing_decision.primary_task_type.value,
            'confidence': routing_decision.task_confidence,
            'reasoning': routing_decision.reasoning,
            'tools_used': [tool.tool_name for tool in routing_decision.tools_needed],
            'processing_time_estimate': routing_decision.estimated_processing_time
        }
    }
```

## 🔌 与现有系统的兼容性

### 旧系统保持可用

旧的关键字路由系统（`src/router.py`）仍然可用作为：
1. **快速回退** - 如果 LLM 调用失败
2. **缓存热启动** - 在 LLM 启动期间使用
3. **低延迟模式** - 需要超快响应时的选项

### 过渡策略

```python
# 混合方法：先快速路由，再用 LLM 验证
from src.router import Router
from src.cn_llm_router import ChineseIntelligentRouter

async def hybrid_route(query, llm_manager):
    # 方案 1：快速路由
    quick_type, quick_confidence = Router.classify_hybrid(query)

    # 方案 2：如果置信度低，使用 LLM
    if quick_confidence < 0.6:
        llm_router = ChineseIntelligentRouter(llm_manager)
        return await llm_router.route_query(query)
    else:
        # 构建简单的 RoutingDecision
        return simple_routing_decision(quick_type)
```

## 📊 性能指标

### 时间成本

| 操作 | 时间 | 说明 |
|-----|------|------|
| 关键字匹配 | ~5ms | 旧系统 |
| LLM 推理 | 300-800ms | 新系统（取决于模型） |
| 返回结果 | <100ms | 都支持 |

### 建议配置

**对于生产环境**:
- 启用 LLM 缓存（Redis/Memcached）
- 设置 LLM 调用超时 ~3 秒
- 降低温度到 0.2-0.3 以保证一致性

## 🎯 关键特性详解

### 1. 多意图检测

```python
query = "查找最新的 AI 论文，分析其数学公式，然后计算其平均页数"

decision = await router.route_query(query)

# 结果
decision.multi_intent  # True
decision.tools_needed  # [search, scraper, code_executor]
```

### 2. 工具推荐

LLM 不仅识别任务类型，还推荐具体的工具：

```python
decision.tools_needed[0].tool_name       # "search"
decision.tools_needed[0].confidence      # 0.95
decision.tools_needed[0].reasoning       # "用户需要互联网搜索最新信息"
decision.tools_needed[0].required_params # {"query": "AI papers"}
```

### 3. 澄清问题生成

对于歧义查询，LLM 可以生成澄清问题：

```python
query = "告诉我关于云的信息"

decision = await router.route_query(query)

decision.confidence           # 0.45 (低置信度)
decision.follow_up_questions  # [
                              #   "您是指云计算、天气中的云，还是云存储？"
                              # ]
```

### 4. 处理时间估计

```python
# 帮助 UI 显示加载进度
decision.estimated_processing_time  # 3.5 秒

# 在 UI 中
<div class="progress-bar" data-time="3500"></div>
```

## 🧪 测试

### 运行测试

```bash
# 运行所有 LLM 路由测试
pytest tests/test_llm_router.py -v

# 运行特定测试
pytest tests/test_llm_router.py::TestChineseOptimization -v

# 运行中文示例测试
pytest tests/test_llm_router.py::test_all_chinese_examples -v
```

### 测试覆盖

- ✅ 英文研究查询
- ✅ 英文代码查询
- ✅ 中文"什么是"查询
- ✅ 中文代码查询
- ✅ 多意图查询
- ✅ 天气查询
- ✅ 导航查询
- ✅ 金融查询
- ✅ 错误处理

## 📈 预期改进

### 准确性

- **旧系统**: 90% (关键字匹配)
- **新系统**: 95-98% (LLM + Prompt)
- **改进**: +5-8%

### 用户满意度

- 更准确的路由
- 更清晰的处理过程
- 支持复杂的多意图查询
- 自动澄清歧义

### 维护成本

- **旧系统**: 频繁需要调整关键字列表
- **新系统**: Prompt 工程（更灵活）
- 减少硬编码规则

## ⚙️ 配置

### 环境变量

```bash
# 启用 LLM 路由（推荐）
USE_LLM_ROUTING=true

# 路由超时（秒）
ROUTING_TIMEOUT=3

# 最低置信度阈值
MIN_ROUTING_CONFIDENCE=0.5

# 启用缓存
ROUTING_CACHE_ENABLED=true
ROUTING_CACHE_TTL=3600
```

### config.yaml

```yaml
routing:
  use_llm: true
  model: "claude-3-haiku"  # 快速且成本效率高
  temperature: 0.3
  timeout: 3
  cache:
    enabled: true
    ttl: 3600
```

## 🐛 故障排除

### 问题 1：LLM 路由响应缓慢

**症状**: 路由需要 >1 秒

**解决方案**:
1. 检查 LLM 模型延迟
2. 启用缓存
3. 降低温度到 0.1
4. 使用较小的模型（Haiku）

### 问题 2：不准确的路由决策

**症状**: "什么是 X" 仍被分类为 CHAT

**解决方案**:
1. 调整 prompt 中的中文示例
2. 增加 few-shot 示例
3. 检查 LLM 模型质量
4. 增加置信度阈值

### 问题 3：缺少工具信息

**症状**: `tools_needed` 为空

**解决方案**:
1. 检查 LLM 响应格式
2. 验证 JSON 解析
3. 查看错误日志
4. 升级到更好的模型

## 📚 参考资源

### 文档
- `src/llm_router.py` - 完整的实现代码
- `src/cn_llm_router.py` - 中文优化版本
- `tests/test_llm_router.py` - 完整的测试套件

### Prompt Engineering 最佳实践

1. **使用结构化格式** (JSON) 便于解析
2. **提供清晰的定义** 每个任务类型
3. **包含 few-shot 示例** 改进理解
4. **使用中文示例** 对中文查询
5. **设置低温度** (0.2-0.3) 保证一致性

## 🎓 下一步

### Phase 1: 基本集成（当前）
- ✅ 创建 LLM 路由器
- ✅ 中文 prompt 优化
- ⏳ Web UI 集成
- ⏳ 测试和验证

### Phase 2: 高级功能
- 上下文感知路由
- 用户偏好学习
- A/B 测试不同 prompt
- 性能监控和日志

### Phase 3: 生产优化
- 缓存和性能调优
- 成本优化（模型选择）
- 灾难恢复策略
- 监控和告警

## 💡 最佳实践

1. **总是提供回退** - 如果 LLM 失败，使用旧系统
2. **记录路由决策** - 用于后续分析和改进
3. **定期审查 prompt** - 根据用户反馈调整
4. **测试多个语言** - 不仅仅是中文
5. **监控成本** - LLM API 调用可能很昂贵

## 📞 支持

如有问题，请参考：
- 项目 Issues: GitHub Issues
- 技术文档: `/docs/` 文件夹
- 代码注释: 源代码中的详细注释
