# 🎯 模型选择机制详解

系统如何在多个LLM模型之间进行选择。

## 📊 决策流程图

```
用户请求
    ↓
┌─────────────────────────────────────┐
│ 是否指定了 preferred_provider?      │
└─────────────────────────────────────┘
    │
    ├─── 是 ──→ 使用指定的提供商
    │
    └─── 否 ──→ 使用主提供商 (_primary_provider)
            ↓
        ┌─────────────────────┐
        │ 是否还有其他提供商?  │
        └─────────────────────┘
            │
            ├─── 是 ──→ 如果主提供商失败，自动尝试其他
            │
            └─── 否 ──→ 使用唯一的提供商
```

## 🔄 三层优先级系统

### 第1层：用户显式指定
```python
# 用户明确指定使用哪个提供商
response = await llm_manager.complete(
    messages=[...],
    preferred_provider="dashscope"  # ← 最高优先级
)
```

**优先级**: ⭐⭐⭐⭐⭐ (最高)

### 第2层：主提供商（Primary Provider）
```python
# config.yaml 中第一个启用的提供商
# 自动成为主提供商
self._primary_provider = "dashscope"
```

**优先级**: ⭐⭐⭐⭐ (高)

### 第3层：故障转移（Fallback）
```python
# 主提供商失败时，自动尝试其他已启用的提供商
# 按照配置中的顺序依次尝试
```

**优先级**: ⭐⭐⭐ (中)

---

## 📝 当前配置分析

### 您的配置：

```yaml
llm:
  # 1. OpenAI - 禁用
  openai:
    enabled: false
    api_key: ${OPENAI_API_KEY}

  # 2. DashScope - 启用 ✅
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max

  # 3. DeepSeek - 禁用
  openai_compatible:
    deepseek:
      enabled: false

  # 4. Local Compatible - 禁用
  local_compatible:
    enabled: false

  # 5. Ollama - 禁用
  ollama:
    enabled: false
```

### 决策结果：

```
初始化顺序:
1. OpenAI ................................. ❌ 跳过 (disabled)
2. DashScope .............................. ✅ 初始化成功 → 设为主提供商
3. DeepSeek .............................. ❌ 跳过 (disabled)
4. Local Compatible ...................... ❌ 跳过 (disabled)
5. Ollama ................................ ❌ 跳过 (disabled)

结果:
  主提供商: dashscope
  可用提供商: [dashscope]
  备用方案: 无 (如果 DashScope 失败则报错)
```

---

## 🔧 如何修改模型选择

### 方式1：启用多个提供商（推荐）

```yaml
llm:
  dashscope:
    enabled: true          # 主提供商 (第1优先)
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max

  deepseek:
    enabled: true          # 备用提供商 (第2优先)
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-chat

  openai:
    enabled: true          # 第三备用 (第3优先)
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
```

**优势**:
- ✅ DashScope 不可用时自动转移到 DeepSeek
- ✅ DeepSeek 不可用时自动转移到 OpenAI
- ✅ 提高系统可靠性

### 方式2：切换主提供商

只需修改配置中的启用顺序：

```yaml
# 改为使用 OpenAI 作为主提供商
openai:
  enabled: true           # 现在是第一个 → 成为主提供商

dashscope:
  enabled: true           # 改为备用
```

### 方式3：在代码中动态指定

```python
# 直接调用时指定
response = await llm_manager.complete(
    messages=[{"role": "user", "content": "问题"}],
    preferred_provider="openai"  # 临时使用 OpenAI
)
```

---

## 📊 提供商初始化优先级表

| 顺序 | 提供商 | 优先级 | 状态 |
|-----|--------|--------|------|
| 1 | OpenAI | ⭐⭐⭐⭐ | ❌ 禁用 |
| 2 | DashScope | ⭐⭐⭐⭐⭐ | ✅ **主提供商** |
| 3 | DeepSeek | ⭐⭐⭐ | ❌ 禁用 |
| 4 | Local Compatible | ⭐⭐ | ❌ 禁用 |
| 5 | Ollama | ⭐ | ❌ 禁用 |

**说明**:
- 初始化时按顺序从上到下
- 第一个成功初始化的成为"主提供商"
- 目前只有 DashScope 启用

---

## 🚀 实际运作流程

### 场景1：用户不指定提供商（默认）

```bash
python -m src.main ask "你好"
```

**执行步骤**:
```
1. 用户输入: "你好"
2. ChatAgent 调用 llm_manager.complete()
3. preferred_provider = None (未指定)
4. 使用主提供商: dashscope
5. 调用 dashscope 的 API
6. 返回结果
```

### 场景2：用户指定提供商

```bash
python -m src.main ask "你好" --prefer openai
```

**执行步骤**:
```
1. 用户输入: "你好"
2. 指定了 preferred_provider = "openai"
3. 但 OpenAI 未启用 → 错误!
4. 应该改为: python -m src.main ask "你好" --prefer dashscope
```

### 场景3：多提供商自动转移

如果启用了多个提供商：

```bash
python -m src.main ask "你好"
```

**执行步骤**:
```
1. 尝试 DashScope (主提供商)
   └─ ✅ 成功 → 返回结果

或者如果 DashScope 失败:
   └─ ❌ 失败 → 尝试下一个

2. 尝试 DeepSeek
   └─ ✅ 成功 → 返回结果

或者如果 DeepSeek 也失败:
   └─ ❌ 失败 → 尝试下一个

3. 尝试 OpenAI
   └─ ✅ 成功 → 返回结果

或者全部失败:
   └─ ❌ 报错: All LLM providers failed
```

---

## 💡 如何查看当前使用的模型

### 方法1：查看日志

```bash
python -m src.main ask "test" --verbose 2>&1 | grep -i "using"
```

**输出示例**:
```
DEBUG - Using dashscope for completion
```

### 方法2：查看配置信息

```bash
python -m src.main info
```

**输出示例**:
```
Configuration:
  LLM providers: dashscope
```

### 方法3：查看代码

```python
from src.utils import get_config
from src.llm import LLMManager

config = get_config()
llm = LLMManager(config=config)

print(f"Available providers: {llm.list_providers()}")
print(f"Primary provider: {llm._primary_provider}")
```

---

## 🔍 模型选择的完整代码逻辑

```python
async def complete(self, messages, preferred_provider=None, ...):
    """生成完成"""

    provider_order = []

    # 步骤1: 如果指定了首选提供商，放在最前面
    if preferred_provider and preferred_provider in self.providers:
        provider_order.append(preferred_provider)

    # 步骤2: 加入主提供商
    if self._primary_provider and self._primary_provider not in provider_order:
        provider_order.append(self._primary_provider)

    # 步骤3: 加入其他所有提供商
    for name in self.providers:
        if name not in provider_order:
            provider_order.append(name)

    # 步骤4: 按顺序尝试每个提供商
    for provider_name in provider_order:
        try:
            provider = self.providers[provider_name]

            # 检查是否可用
            if not await provider.is_available():
                logger.warning(f"{provider_name} not available, trying next...")
                continue

            # 使用该提供商
            logger.debug(f"Using {provider_name} for completion")
            return await provider.complete(messages, ...)

        except Exception as e:
            logger.warning(f"{provider_name} failed: {e}")
            continue

    # 步骤5: 全部失败
    raise RuntimeError("All LLM providers failed")
```

---

## 📋 最佳实践

### ✅ 推荐配置

```yaml
llm:
  # 主提供商 (最经济)
  dashscope:
    enabled: true

  # 备用1 (中等成本)
  deepseek:
    enabled: true

  # 备用2 (高性能)
  openai:
    enabled: true
```

**优势**:
- 成本优先使用便宜的
- 自动故障转移保证可用性
- 高度可靠

### ❌ 不推荐

```yaml
# 只启用一个提供商，没有备用
openai:
  enabled: true

# 其他都禁用
```

**问题**:
- 如果 OpenAI 不可用，整个系统崩溃
- 缺乏灵活性

---

## 🎯 总结

**系统如何选择模型**:

1. **用户明确指定** → 使用指定的
2. **用户未指定** → 使用主提供商
3. **主提供商失败** → 自动尝试其他提供商
4. **全部失败** → 报错

**当前状态**:
- ✅ 只有 DashScope 启用
- ✅ DashScope 是主提供商
- ⚠️ 没有备用方案

**建议**:
- 启用多个提供商以提高可靠性
- 根据需要在代码中指定提供商
- 定期检查日志了解使用情况

---

**需要帮助？**
- 查看 `DASHSCOPE_SETUP_GUIDE.md` 了解配置
- 查看 `API_ENDPOINTS_GUIDE.md` 了解不同提供商
- 查看 `CUSTOM_URL_SETUP.md` 了解自定义 URL

