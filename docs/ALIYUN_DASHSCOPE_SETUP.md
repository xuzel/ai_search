# 阿里云 DashScope 配置指南

本指南说明如何配置和使用阿里云 DashScope（通义千问 Qwen 模型）。

## 📋 快速开始（3步）

### 1. 获取 API 密钥

访问阿里云 DashScope 控制台：
- **地址**: https://dashscope.console.aliyun.com/
- **步骤**:
  1. 登录或注册阿里云账号
  2. 进入 "API密钥管理"
  3. 创建新的 API 密钥
  4. 复制密钥

### 2. 配置 .env 文件

```bash
# 编辑 .env 文件
DASHSCOPE_API_KEY=your-actual-dashscope-api-key-here
```

### 3. 验证配置

```bash
# 查看配置状态
python -m src.main info

# 应该看到：DashScope provider initialized
```

---

## 🔧 详细配置说明

### 方法1：使用 .env 文件（推荐）

```bash
# 1. 复制示例文件
cp .env.example .env

# 2. 编辑 .env，添加 DashScope API 密钥
DASHSCOPE_API_KEY=your-api-key-here

# 3. 验证
python -m src.main info
```

### 方法2：编辑 config/config.yaml

```yaml
llm:
  # Aliyun DashScope Configuration
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max         # 或其他可用模型
    temperature: 0.7
    max_tokens: 20000
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    provider_name: "Aliyun DashScope"
```

### 方法3：Python 代码直接使用

```python
from src.llm import OpenAIClient

client = OpenAIClient(
    api_key="your-dashscope-api-key",
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    provider_name="Aliyun DashScope"
)
```

---

## 📝 可用模型

| 模型 | 描述 | Max Tokens | 适用场景 |
|------|------|------------|--------|
| `qwen3-max` | 最强大的模型 | 20000 | 复杂推理、长文本 |
| `qwen3-turbo` | 平衡性能和速度 | 20000 | 通用任务 |
| `qwen3-32b-turbo` | 32B 参数模型 | 8000 | 代码、数学 |
| `qwen2-72b-instruct` | 72B 参数模型 | 4096 | 高质量输出 |
| `qwen2-57b-a14b` | MoE 模型 | 4096 | 高效推理 |
| `qwen2-14b-instruct` | 14B 参数模型 | 8192 | 轻量级任务 |

**推荐**：
- 默认使用 `qwen3-max` （最佳质量）
- 成本优化使用 `qwen3-turbo` （更便宜）

---

## 💡 使用示例

### 示例1：简单对话

```bash
python -m src.main ask "你好，请介绍一下自己" --auto
```

### 示例2：代码生成

```bash
python -m src.main solve "写一个Python函数，计算斐波那契数列"
```

### 示例3：数据分析

```bash
python -m src.main ask "分析这个数据集的特点"
```

### 示例4：研究模式

```bash
python -m src.main search "最新的AI技术进展"
```

---

## 🔍 常见问题排查

### 问题1：API 密钥无效

**错误信息**:
```
Error code: 401 - {'error': {'message': 'Incorrect API key provided'}}
```

**解决方案**:
1. 检查 API 密钥是否正确复制
2. 确保使用了 `DASHSCOPE_API_KEY` 而不是 `OPENAI_API_KEY`
3. 检查 API 密钥是否已启用
4. 访问控制台重新生成密钥: https://dashscope.console.aliyun.com/

### 问题2：模型不存在

**错误信息**:
```
Error: Model not found
```

**解决方案**:
1. 检查模型名称拼写
2. 确认该模型在您的账号中可用
3. 查看官方文档获取最新模型列表

### 问题3：配置没有被加载

**错误信息**:
```
No LLM providers configured
```

**解决方案**:
1. 检查 .env 文件是否存在且有效
2. 运行 `python -c "from src.utils import get_config; print(get_config().llm.dashscope_api_key[:10])"`
3. 验证 config/config.yaml 中 DashScope 配置正确

### 问题4：速度慢或超时

**原因**:
- 网络延迟
- 模型处理时间长
- 请求超时设置太短

**解决方案**:
```yaml
# 增加超时时间
code_execution:
  timeout: 60  # 从 30 改为 60
```

---

## 🚀 快速工作流

```bash
# 1. 进入项目
cd /Users/sudo/PycharmProjects/ai_search

# 2. 激活环境
conda activate hw_llm_deepsearch

# 3. 配置 API 密钥
cp .env.example .env
# 编辑 .env，添加 DASHSCOPE_API_KEY

# 4. 验证配置
python -m src.main info
# 应该看到：DashScope provider initialized

# 5. 开始使用
python -m src.main ask "你好" --auto

# 6. 交互式聊天
python -m src.main chat
```

---

## 📊 价格对比

| 模型 | 输入价格 | 输出价格 | 相比OpenAI |
|------|---------|---------|-----------|
| qwen3-max | ¥0.006/1K | ¥0.018/1K | 便宜70% |
| qwen3-turbo | ¥0.002/1K | ¥0.006/1K | 便宜85% |
| GPT-4 | $0.03/1K | $0.06/1K | — |
| GPT-3.5-turbo | $0.0005/1K | $0.0015/1K | 类似 |

**建议**: 使用 `qwen3-turbo` 可以显著降低成本。

---

## 🔗 官方资源

- **DashScope 控制台**: https://dashscope.console.aliyun.com/
- **API 文档**: https://help.aliyun.com/zh/dashscope/developer-reference/
- **GitHub**: https://github.com/aliyun/dashscope-sdk
- **模型文档**: https://help.aliyun.com/zh/dashscope/latest/models/

---

## ✅ 配置验证清单

- [ ] 获取了 DashScope API 密钥
- [ ] 添加到 .env 文件中为 `DASHSCOPE_API_KEY`
- [ ] 运行 `python -m src.main info` 看到 "DashScope provider initialized"
- [ ] 测试 `python -m src.main ask "test" --auto` 成功
- [ ] 在 config/config.yaml 中选择了喜欢的模型

---

## 💾 多提供商配置

如果要同时使用多个提供商（DashScope + OpenAI + DeepSeek）：

```yaml
llm:
  # OpenAI
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}

  # DashScope (默认)
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}

  # DeepSeek
  openai_compatible:
    deepseek:
      enabled: true
      api_key: ${DEEPSEEK_API_KEY}
```

系统会优先使用 DashScope，如果失败会自动尝试其他提供商。

---

**更新于**: 2024年10月20日

祝您使用阿里云 DashScope 愉快！🎉
